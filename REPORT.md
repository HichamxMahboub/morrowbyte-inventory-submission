# Submission report: bundle inventory checker

The adapter now rejects inventories with missing, unexpected, duplicate or changed entries while preserving the documented JSON interface. The supplied example previously reported success despite a missing member; it now reports that member and returns invalid. A repeated name is invalid even when its hashes match, and any mismatching occurrence remains visible when another occurrence matches.

## Requirements and scope

The authority for behavior is `workspace/docs/task-contract.md`, with evidence limits in `workspace/docs/task-handoff.md`. The archived task sketch does not override these requirements. This submission uses local files and the Python standard library only. No external services, dependency installations or archive-member extraction are needed.

## Changes

| File | Change and reason |
| --- | --- |
| `workspace/task.py` | Replaced the dictionary overwrite with per-occurrence comparison and sets for seen, duplicate and changed names. Added missing/unexpected detection, sorted lists and correct status/assurance. |
| `workspace/task.py` | Added request-shape checks to reject wrong container and value types before operations can fail with AttributeError. Preserved required-key errors and stderr/exit-2 handling; added a specific excessive-nesting handler. |
| `workspace/task.py` | Enabled JSON escaping so unusual names, including escaped surrogate values accepted by the JSON reader, can be serialized without an output-encoding failure. |
| `workspace/tests/test_task.py` | Added nine initial and twelve further test methods, including enumeration of 2,331 small inventory combinations. |
| `workspace/examples/task-duplicate-request.json` | Added a repeatable wrong-hash-then-correct-hash reproduction. The supplied example remains unchanged. |
| `workspace/HANDOFF.md` | Added commands, expected outcomes and remaining evidence limits for Tessa Venn. |
| `CHOICES.md`, `evidence/` | Recorded rationale, AI use, baseline behavior and final local verification. |

The original eight smoke tests and background command implementations were retained.

## Behavior before and after

For the original `workspace/examples/task-request.json`, expected contains `x` and observed is empty. The original adapter returned empty issue lists, status `ok` and assurance `authenticated`. The corrected adapter returns:

```json
{"assurance":"inventory-only","changed":[],"duplicates":[],"missing":["x"],"status":"invalid","unexpected":[]}
```

For the new duplicate example, `x` is observed first with a differing hash and then with its expected hash. The original dictionary retained only the last hash, hiding both the mismatch and the duplicate. The corrected result contains `duplicates: ["x"]` and `changed: ["x"]`. Reversing the two observations gives the same result.

Both comparisons exit 0 because they completed successfully. Callers must read `status` to decide whether the inventory matched. Malformed requests and file errors exit 2, write an error to stderr and produce no JSON result on stdout.

## Verification

Run from the submission root:

```bash
cd workspace
python3 -B task.py --selfcheck
python3 -B -m unittest discover -s tests -v
python3 -B task.py examples/task-request.json
python3 -B task.py examples/task-duplicate-request.json
```

The final local run passed all 29 test methods: eight existing smoke tests and 21 adapter tests. These cover the four issue categories, empty matches, repeated names, any-occurrence mismatches, ordering, sorting, uniqueness, literal name handling, Unicode output and input preservation. The bounded enumeration checks every expected assignment for two names using absent/two-hash states, with all observed sequences of zero to three entries drawn from three names and two hashes: 2,331 comparisons. A separate case checks 10,001 entries with one mismatch among repeated matching entries.

Command checks cover malformed JSON, missing keys, non-object input, incorrect nested types, invalid UTF-8, a directory used as input, a nonexistent file, excessive nesting, argument counts and selfcheck. Permission denial is simulated so the check also works under elevated privileges. Error assertions include exit 2, stderr text, empty stdout and absence of a traceback.

The original adapter failed the initial regression suite before the fix. `evidence/baseline.txt` records the observed baseline and identifies it as an earlier observation. Final test output, runtime details, command results and fixture byte checks are saved in `evidence/`. Passing this suite supports the documented local behavior; it is not proof of every possible input or operating-system failure.

## Decisions and trade-offs

| Decision | Benefit | Cost or limitation |
| --- | --- | --- |
| Keep logic in `task.py` | Small patch; entry point remains easy to inspect and run. | A larger future feature set may justify separate modules. |
| Use sets and inspect every occurrence | Retains mismatch evidence and reports each issue name once. | Needs memory proportional to unique names; the request is also loaded fully into memory. |
| Sort every issue list | Deterministic consumer output regardless of input ordering. | Adds sorting work. Comparison is approximately O(E + O), plus O(K log K) for sorting output names. Here E/O are expected/observed counts and K is the total number of reported names. |
| Validate shapes, not hash formats | Rejects malformed structures clearly while respecting the task boundary. | Arbitrary string digests are compared as supplied; authenticity and digest measurement remain the reader's responsibility. |
| Catch specific expected exceptions | Provides clean user-facing errors while preserving visibility of programming defects. | Unanticipated defects, memory exhaustion and process termination are not converted into ordinary input errors. |
| Compare names literally | Avoids conflating case, Unicode spellings or path-like names. | Equivalent-looking names may differ; no path normalization or filesystem interpretation is performed. |
| Escape JSON output | Avoids encoding problems while preserving parsed JSON values. | Raw output is less readable for some Unicode names. |
| Use focused examples plus bounded enumeration | Makes key failures reproducible and tests interacting conditions. | Bounded enumeration is not exhaustive over all inventories; permission errors are mocked rather than measured on the host filesystem. |

## Remaining limits and deferred work

The adapter does not open archives, extract members, recalculate hashes, authenticate senders or establish file safety. It assumes the separate reader supplied the measured digests. Local fixtures cannot prove a real deployment, user identity or external action.

Digest-format enforcement, explicit file-size limits, streaming JSON, rejection of duplicate JSON object keys and stricter handling of unknown fields were deferred. Standard JSON decoding keeps the last value for repeated object keys; duplicate inventory names must be supplied as repeated entries in the observed list. Extra fields are ignored. None of these optional extensions is needed for the current supported input contract.

AI assisted code, test and report preparation. The verification record distinguishes executed local checks from claims that remain outside the available evidence. No claim is made about completing an interview within its time limit.
