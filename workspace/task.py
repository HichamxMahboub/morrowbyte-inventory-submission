"""Local exercise adapter. Keep the documented JSON consumer interface."""
from __future__ import annotations
import json
import pathlib
import sys

def solve(request: dict) -> dict:
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    expected = request["expected"]
    observed = request["observed"]
    if not isinstance(expected, dict):
        raise ValueError("expected must be an object")
    if not isinstance(observed, list):
        raise ValueError("observed must be a list")
    if any(not isinstance(name, str) or not isinstance(digest, str)
           for name, digest in expected.items()):
        raise ValueError("expected names and hashes must be strings")
    seen = set()
    duplicates = set()
    changed = set()

    for entry in observed:
        if not isinstance(entry, dict):
            raise ValueError("each observed entry must be an object")
        name = entry["name"]
        digest = entry["sha256"]
        if not isinstance(name, str) or not isinstance(digest, str):
            raise ValueError("observed names and hashes must be strings")
        if name in seen:
            duplicates.add(name)
        seen.add(name)

        # Check every occurrence; a later match cannot erase a mismatch.
        if name in expected and digest != expected[name]:
            changed.add(name)

    result = {
        "missing": sorted(expected.keys() - seen),
        "unexpected": sorted(seen - expected.keys()),
        "duplicates": sorted(duplicates),
        "changed": sorted(changed),
    }
    result["status"] = "invalid" if any(result.values()) else "ok"
    result["assurance"] = "inventory-only"
    return result


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == '--selfcheck':
        if sys.version_info < (3, 11):
            print('Python 3.11+ required', file=sys.stderr)
            return 2
        print(json.dumps({'ok': True, 'mode': 'local-only'}))
        return 0
    if len(sys.argv) != 2:
        print('usage: python3 -B task.py REQUEST.json', file=sys.stderr)
        return 2
    try:
        request = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
        # Escaping also keeps unusual JSON names safe for the output encoding.
        print(json.dumps(solve(request), sort_keys=True, ensure_ascii=True))
        return 0
    except RecursionError:
        print('request nesting is too deep', file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
