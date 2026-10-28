# Current task adapter contract

Owner: Tessa Venn. Effective 2026-12-03 09:00 UTC+00:00. This small adapter is an additive task; existing world commands and formats retain their contracts. This page supersedes the earlier sketch in task-history.md.

This adapter compares a saved ZIP-member inventory without opening or extracting an archive. Input: expected (object of logical member names to lowercase SHA-256 digests), observed (list of {name,sha256} strings). Each digest is already measured by a separate trusted reader; format validation is outside this task. Return sorted lists missing (expected names absent), unexpected (observed names not expected), duplicates (each repeated observed name once), changed (expected names for which any observed digest differs), status (ok only if all four lists empty, otherwise invalid), and assurance:"inventory-only". Member order is irrelevant. A duplicate with equal bytes is still invalid. Empty inventories can match. This comparison does not authenticate a sender and does not prove files safe.

## Invocation and errors

From workspace run `python3 -B task.py examples/task-request.json`. Keep task.py as the executable entry point; implementation may use new modules or existing world functions. Input is a UTF-8 JSON file; stdout contains exactly one JSON object. Successful evaluation, including domain-level rejected results, exits 0. Malformed JSON, non-object input, missing required keys and IO errors go to stderr and exit 2, without changing input files. Error wording is open. Do not install dependencies or use network services. The contract describes the supported input shapes; validation outside them is optional.
