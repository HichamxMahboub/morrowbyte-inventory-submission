# Implementation choices

I repaired `workspace/task.py` while preserving its JSON-file command interface and using only Python's standard library. The comparison now reports sorted, unique missing, unexpected, duplicate and changed names. Every observed occurrence is checked, so a later correct hash cannot hide an earlier mismatch. Status is invalid whenever any issue list is nonempty; assurance is always inventory-only.

Sets keep the comparison simple and avoid losing duplicate evidence. Sorting adds output cost but makes results deterministic. Keeping the implementation in the small adapter avoids changes to the background commands.

I added lightweight shape validation and caught expected input, file and excessive-nesting errors at the command boundary. Errors use stderr and exit 2; completed comparisons exit 0 even when invalid. JSON escaping supports unusual names. Unexpected programming failures are not hidden behind a blanket exception handler.

Verification includes 29 test methods, 2,331 enumerated inventory combinations, a 10,001-entry duplicate case, command errors and input preservation. The eight existing smoke tests still pass. Evidence includes saved test output and repeatable sample and duplicate reproductions.

AI assisted the implementation, tests and documentation. A concrete local verification example: tests first reproduced the original sample's false success and the duplicate-overwrite problem, then passed after correction. Later review found a malformed expected value could raise AttributeError; explicit shape checks now reject it cleanly.

Deferred: digest-format checks, authentication, safety scanning, archive processing and resource limits. Hashes are trusted supplied values; names are compared literally. Local evidence cannot establish any deployment, sender identity or file safety.
