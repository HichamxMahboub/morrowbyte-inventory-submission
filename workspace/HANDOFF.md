# Handoff to Tessa Venn

The inventory adapter now detects missing, unexpected, repeated and changed members. A later correct observation cannot hide an earlier mismatching hash. All four issue lists are sorted; any nonempty list makes status invalid. Assurance is always inventory-only.

From this directory, with Python 3.11 or newer:

```bash
python3 -B task.py --selfcheck
python3 -B task.py examples/task-request.json
python3 -B task.py examples/task-duplicate-request.json
python3 -B -m unittest discover -s tests -v
```

Before correction, the supplied missing-member example returned status ok and assurance authenticated. It now returns missing `["x"]`, status invalid and assurance inventory-only. The new duplicate example has a wrong hash followed by the correct hash: it now returns changed `["x"]` and duplicates `["x"]`, with missing/unexpected empty and status invalid. Reversing the observations gives the same result.

Completed comparisons exit 0, including invalid inventories. Input/read errors report on stderr and exit 2. Read the result's status when deciding whether a handoff inventory matches. No input file is rewritten.

The submission's `../evidence/` directory contains the final verification log and command results. The suite has 29 test methods, including 2,331 bounded inventory combinations and the existing smoke tests. `../REPORT.md` explains changes, trade-offs and coverage; `../CHOICES.md` summarizes decisions and AI-assisted verification.

This checks supplied inventory data only. It does not establish sender identity, file safety, deployment state or external actions. Digests are assumed to have been measured by a separate trusted reader. Do not treat inventory-only as authenticated or safe, and do not extract member paths. Further archive processing or authentication would need a separate contract and evidence.
