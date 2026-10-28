# Local verification evidence

`tests.txt` contains the final full unittest output; all 29 test methods passed. The 2,331 enumerated comparisons run within one of those methods, rather than being counted as separate test methods.

`selfcheck.txt`, `missing-example.txt` and `duplicate-example.txt` contain commands, exit codes and captured stdout/stderr. Run the recorded commands from `workspace/`.

`verification.json` records the Python version, verification timestamp, result objects, CHOICES word count and SHA-256 hashes before/after the final run for all supplied fixture files and the original example. Those byte-preservation checks concern this final verification run; they are not an independently signed original-distribution baseline.

`baseline.txt` records observations made earlier in the session before the first fix. It is explicitly historical; the original adapter is not included as executable submission code.

The top-level `MANIFEST.sha256` lists every other packaged file's digest. The archive was checked for readable entries and exact content agreement with the submission files without extracting its entries. This manifest detects content differences; it is not authentication.
