"""Contract checks for the local inventory adapter and its JSON entry point."""
from __future__ import annotations

import copy
import itertools
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest import mock

from task import main, solve


GOOD = "a" * 64
OTHER = "b" * 64
WORKSPACE = pathlib.Path(__file__).resolve().parents[1]


class InventoryTests(unittest.TestCase):
    def test_contract_examples(self) -> None:
        cases = [
            ("empty", {}, [], [], [], [], []),
            ("match", {"x": GOOD}, [{"name": "x", "sha256": GOOD}], [], [], [], []),
            ("missing", {"x": GOOD}, [], ["x"], [], [], []),
            ("unexpected", {}, [{"name": "x", "sha256": GOOD}], [], ["x"], [], []),
            ("changed", {"x": GOOD}, [{"name": "x", "sha256": OTHER}], [], [], [], ["x"]),
            ("equal duplicates", {"x": GOOD}, [{"name": "x", "sha256": GOOD}] * 3,
             [], [], ["x"], []),
            ("unexpected duplicates", {}, [{"name": "x", "sha256": GOOD}] * 2,
             [], ["x"], ["x"], []),
        ]
        for label, expected, observed, missing, unexpected, duplicates, changed in cases:
            with self.subTest(case=label):
                self.assertEqual(solve({"expected": expected, "observed": observed}), {
                    "missing": missing,
                    "unexpected": unexpected,
                    "duplicates": duplicates,
                    "changed": changed,
                    "status": "invalid" if any((missing, unexpected, duplicates, changed)) else "ok",
                    "assurance": "inventory-only",
                })

    def test_changed_duplicate_is_detected_in_either_order(self) -> None:
        entries = [{"name": "x", "sha256": OTHER}, {"name": "x", "sha256": GOOD}]
        for observed in (entries, entries[::-1]):
            with self.subTest(observed=observed):
                self.assertEqual(solve({"expected": {"x": GOOD}, "observed": observed}), {
                    "missing": [], "unexpected": [], "duplicates": ["x"],
                    "changed": ["x"], "status": "invalid", "assurance": "inventory-only",
                })

    def test_all_lists_are_sorted_and_names_are_unique(self) -> None:
        observed = [
            {"name": name, "sha256": digest}
            for name, digest in [
                ("z", OTHER), ("z", OTHER), ("a", OTHER), ("a", GOOD),
                ("extra-z", GOOD), ("extra-a", GOOD),
            ]
        ]
        self.assertEqual(solve({
            "expected": {"z": GOOD, "missing-z": GOOD, "a": GOOD, "missing-a": GOOD},
            "observed": observed,
        }), {
            "missing": ["missing-a", "missing-z"],
            "unexpected": ["extra-a", "extra-z"],
            "duplicates": ["a", "z"], "changed": ["a", "z"],
            "status": "invalid", "assurance": "inventory-only",
        })

    def test_member_order_does_not_change_result(self) -> None:
        entries = [
            {"name": "x", "sha256": OTHER},
            {"name": "x", "sha256": GOOD},
            {"name": "extra", "sha256": GOOD},
        ]
        expected_result = {
            "missing": ["missing"], "unexpected": ["extra"], "duplicates": ["x"],
            "changed": ["x"], "status": "invalid", "assurance": "inventory-only",
        }
        for observed in itertools.permutations(entries):
            self.assertEqual(solve({
                "expected": {"x": GOOD, "missing": GOOD}, "observed": list(observed),
            }), expected_result)

    def test_comparison_does_not_mutate_request(self) -> None:
        request = {"expected": {"x": GOOD}, "observed": [{"name": "x", "sha256": OTHER}]}
        original = copy.deepcopy(request)
        solve(request)
        self.assertEqual(request, original)

    def test_expected_insertion_order_is_irrelevant(self) -> None:
        observed = [{"name": "z", "sha256": OTHER}, {"name": "a", "sha256": OTHER}]
        self.assertEqual(
            solve({"expected": {"a": GOOD, "z": GOOD}, "observed": observed}),
            solve({"expected": {"z": GOOD, "a": GOOD}, "observed": observed}),
        )

    def test_names_are_compared_literally_without_filesystem_access(self) -> None:
        names = ["", "A", "a", "a/../b", "b", "../outside", "/absolute", "é", "e\u0301", "📁", "a\\b"]
        with mock.patch("builtins.open", side_effect=AssertionError("must not open members")):
            result = solve({
                "expected": {name: GOOD for name in names},
                "observed": [{"name": name, "sha256": GOOD} for name in reversed(names)],
            })
        self.assertEqual(result, {
            "missing": [], "unexpected": [], "duplicates": [], "changed": [],
            "status": "ok", "assurance": "inventory-only",
        })
        result = solve({"expected": {"A": GOOD, "é": GOOD, "a/../b": GOOD}, "observed": [
            {"name": "a", "sha256": GOOD}, {"name": "e\u0301", "sha256": GOOD},
            {"name": "b", "sha256": GOOD},
        ]})
        self.assertEqual(result["missing"], ["A", "a/../b", "é"])
        self.assertEqual(result["unexpected"], ["a", "b", "e\u0301"])

    def test_hash_format_is_not_validated(self) -> None:
        self.assertEqual(solve({
            "expected": {"x": "opaque supplied hash"},
            "observed": [{"name": "x", "sha256": "opaque supplied hash"}],
        })["status"], "ok")

    def test_small_inventory_combinations_against_contract_oracle(self) -> None:
        # Enumerate 2,331 cases, including absent, matching and differing hashes.
        records = [(name, digest) for name in ("a", "b", "extra") for digest in (GOOD, OTHER)]
        for hashes in itertools.product((None, GOOD, OTHER), repeat=2):
            expected = {name: digest for name, digest in zip(("a", "b"), hashes) if digest is not None}
            for size in range(4):
                for entries in itertools.product(records, repeat=size):
                    observed = [{"name": name, "sha256": digest} for name, digest in entries]
                    names = [name for name, _ in entries]
                    missing = sorted(name for name in expected if name not in names)
                    unexpected = sorted({name for name in names if name not in expected})
                    duplicates = sorted({name for name in names if names.count(name) > 1})
                    changed = sorted(name for name, digest in expected.items()
                                     if any(n == name and d != digest for n, d in entries))
                    self.assertEqual(solve({"expected": expected, "observed": observed}), {
                        "missing": missing, "unexpected": unexpected, "duplicates": duplicates,
                        "changed": changed,
                        "status": "invalid" if any((missing, unexpected, duplicates, changed)) else "ok",
                        "assurance": "inventory-only",
                    }, msg=repr((expected, entries)))

    def test_many_repeated_entries_are_reported_once(self) -> None:
        observed = [{"name": "x", "sha256": GOOD}] * 10000
        observed.insert(5000, {"name": "x", "sha256": OTHER})
        self.assertEqual(solve({"expected": {"x": GOOD}, "observed": observed}), {
            "missing": [], "unexpected": [], "duplicates": ["x"], "changed": ["x"],
            "status": "invalid", "assurance": "inventory-only",
        })


class CommandTests(unittest.TestCase):
    def assert_input_error(self, process: subprocess.CompletedProcess) -> None:
        self.assertEqual(process.returncode, 2, process.stderr)
        self.assertEqual(process.stdout, "")
        self.assertTrue(process.stderr.strip())
        self.assertNotIn("Traceback", process.stderr)

    def run_adapter(self, path: pathlib.Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(WORKSPACE / "task.py"), str(path)],
            capture_output=True, text=True, check=False,
        )

    def test_supplied_sample_is_invalid_with_exit_zero_and_unchanged_bytes(self) -> None:
        path = WORKSPACE / "examples" / "task-request.json"
        before = path.read_bytes()
        process = self.run_adapter(path)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stderr, "")
        self.assertEqual(json.loads(process.stdout), {
            "missing": ["x"], "unexpected": [], "duplicates": [], "changed": [],
            "status": "invalid", "assurance": "inventory-only",
        })
        self.assertEqual(path.read_bytes(), before)

    def test_matching_request_returns_one_json_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "request.json"
            path.write_text(json.dumps({
                "expected": {"preuve-é": GOOD},
                "observed": [{"name": "preuve-é", "sha256": GOOD}],
            }), encoding="utf-8")
            before = path.read_bytes()
            process = self.run_adapter(path)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stderr, "")
            self.assertEqual(json.loads(process.stdout), {
                "missing": [], "unexpected": [], "duplicates": [], "changed": [],
                "status": "ok", "assurance": "inventory-only",
            })
            self.assertEqual(path.read_bytes(), before)

    def test_bad_requests_use_stderr_and_exit_two_without_changing_input(self) -> None:
        contents = [
            "{", "[]", "null", "{}", '{"expected": {}}', '{"observed": []}',
            '{"expected": {}, "observed": [{}]}',
            '{"expected": {}, "observed": [{"name": "x"}]}',
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "request.json"
            for content in contents:
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    before = path.read_bytes()
                    process = self.run_adapter(path)
                    self.assert_input_error(process)
                    self.assertEqual(path.read_bytes(), before)

    def test_missing_file_uses_stderr_and_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "absent.json"
            process = self.run_adapter(path)
            self.assert_input_error(process)
            self.assertFalse(path.exists())

    def test_invalid_utf8_is_caught_and_input_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "request.json"
            contents = b'\xff\xfe{"expected": {}, "observed": []}'
            path.write_bytes(contents)
            self.assert_input_error(self.run_adapter(path))
            self.assertEqual(path.read_bytes(), contents)

    def test_directory_input_is_caught_without_changing_contents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)
            marker = path / "keep.txt"
            marker.write_bytes(b"unchanged")
            self.assert_input_error(self.run_adapter(path))
            self.assertEqual(list(path.iterdir()), [marker])
            self.assertEqual(marker.read_bytes(), b"unchanged")

    def test_wrong_json_types_are_caught(self) -> None:
        bad_values = [None, True, 1, 1.5, "text", [], {}]
        requests = [None, True, 1, "text", []]
        requests += [{"expected": value, "observed": []} for value in bad_values if not isinstance(value, dict)]
        requests += [{"expected": {}, "observed": value} for value in bad_values if not isinstance(value, list)]
        requests += [{"expected": {}, "observed": [value]} for value in bad_values if not isinstance(value, dict)]
        requests += [{"expected": {"x": value}, "observed": []} for value in bad_values if not isinstance(value, str)]
        requests += [{"expected": {}, "observed": [{"name": value, "sha256": GOOD}]}
                     for value in bad_values if not isinstance(value, str)]
        requests += [{"expected": {}, "observed": [{"name": "x", "sha256": value}]}
                     for value in bad_values if not isinstance(value, str)]
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "request.json"
            for request in requests:
                with self.subTest(request=request):
                    contents = json.dumps(request).encode("utf-8")
                    path.write_bytes(contents)
                    self.assert_input_error(self.run_adapter(path))
                    self.assertEqual(path.read_bytes(), contents)

    def test_deeply_nested_json_is_caught(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "request.json"
            contents = "[" * 2000 + "0" + "]" * 2000
            path.write_text(contents, encoding="utf-8")
            self.assert_input_error(self.run_adapter(path))
            self.assertEqual(path.read_text(encoding="utf-8"), contents)

    def test_permission_error_is_caught(self) -> None:
        # Mock this error so the test also works when run with elevated privileges.
        stdout, stderr = StringIO(), StringIO()
        with mock.patch.object(sys, "argv", ["task.py", "denied.json"]), \
             mock.patch.object(pathlib.Path, "read_text", side_effect=PermissionError("access denied")), \
             redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(main(), 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("access denied", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_unusual_names_round_trip_as_json(self) -> None:
        names = ["é", "📁", "line\nbreak", "\x00", "\ud800"]
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "request.json"
            path.write_text(json.dumps({"expected": {name: GOOD for name in names}, "observed": []}), encoding="utf-8")
            process = self.run_adapter(path)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stderr, "")
            self.assertEqual(json.loads(process.stdout), {
                "missing": sorted(names), "unexpected": [], "duplicates": [], "changed": [],
                "status": "invalid", "assurance": "inventory-only",
            })

    def test_argument_count_and_selfcheck(self) -> None:
        for args in ([], ["one.json", "two.json"]):
            with self.subTest(args=args):
                process = subprocess.run([sys.executable, "-B", str(WORKSPACE / "task.py"), *args],
                                         capture_output=True, text=True, check=False)
                self.assert_input_error(process)
        process = subprocess.run([sys.executable, "-B", str(WORKSPACE / "task.py"), "--selfcheck"],
                                 capture_output=True, text=True, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stderr, "")
        self.assertEqual(json.loads(process.stdout), {"ok": True, "mode": "local-only"})


if __name__ == "__main__":
    unittest.main()
