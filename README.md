# Diagnose a bundle inventory incident

**2026-12-03 09:00 UTC+00:00.** You are working in the fictional Morrowbyte team. Tessa sees a green handoff check even when a saved archive listing has duplicate or changed entries. Repair the local inventory checker and leave a repeatable reproduction for the next support engineer.

## Your mission

At minimum, deliver the corrected runnable `task.py` adapter, local evidence covering the mapped contract boundaries, and a short handoff for Tessa Venn. Keep the supplied JSON entry point so the colleague can run it. Existing world commands are background and need no redesign. Anything beyond that is up to you.

There is no single right answer. Choose the implementation structure, verification approach and handoff form; explain your choices in `CHOICES.md`.

## What you have

`workspace/README.md` is the source map and offline starting guide. `docs/task-contract.md` defines the current consumer behavior; `docs/task-handoff.md` defines the evidence limits. `task.py` is the draft adapter, and `examples/task-request.json` is one runnable example. Current task guidance supersedes the archived sketch. Other world material is optional.

From the exported root, setup: `cd workspace && python3 -B task.py --selfcheck` (before the clock). From workspace, sample: `python3 -B task.py examples/task-request.json`; existing tests: `python3 -B -m unittest discover -s tests -v`. Existing tests are examples, not complete proof of the new adapter.

Everything is fictional and local files are the only source of truth. Python 3.11+ standard library is sufficient; no outside research or downloads.

## Rules

- You have **50 minutes** after setup succeeds. The session is recorded.
- We encourage AI when available. Local hints also support work without it. We assess verification, not subscriptions or internet speed.
- The engineer helps only with setup, audio or time. Pause for technical interruptions and resume when usable. Make reasonable task assumptions and note them.
- Do not contact real systems or people, send messages, publish, or use real credentials. Any DEMO values are nonfunctional.

## What to send at minute 50

- Your changed workspace, local checks, and concise handoff.
- `CHOICES.md` (at most 300 words): what you built, why, what you deferred, how you checked, and one AI correction or local verification example.

Aim for a useful result by 35, verify through 45, then package. Unfinished work is fine; say what remains.

## How it is assessed

Result 35 (helps Tessa Venn), accuracy 25 (matches sources), judgment 20 (scope and trade-offs), process 20 (recorded verification). Every approach can reach full marks on the core. We do not score typing speed, tool choice, connectivity, machine speed, polish or volume.
