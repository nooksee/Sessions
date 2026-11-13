# Technical Specification: workers

Script: `Sessions/ops/lib/scripts/workers.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_workers.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/inventory_worker_threads.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Classify Codex sessions into residents, worker threads, and unknowns." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/worker-thread-doctrine-20260731.md` (2026-07-31); 4 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/inventory_worker_threads.py` (sha256 `45697c39322960d198ff79609086b89a4dd8817fe3bc1a3631c3f4bc64b8abdf`) was copied to `ops/lib/scripts/workers.py` on 2026-11-01 with 1 edit(s): parents[1] -> parents[3] (1).
2. Command line: `python3 -I -B ops/lib/scripts/workers.py`. Options as the script declares them:
   - `--json`: (no help text in the script)
   - `--archive-idle`: Move worker threads idle longer than HOURS into archived custody.
   - `--purge`: Delete worker threads idle longer than HOURS. Operator standing order 2026-08-01: subagents are disposable. Promoted residents are never eligible; see PROMOTED_GUARD.
   - `--apply`: Perform the archive or purge.
3. Reads and writes: as the docstring states (1078 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/worker-thread-doctrine-20260731.md` is the earliest of 4 receipt(s) naming `inventory_worker_threads.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Read-only." "Reports; archives only with --archive-idle and an explicit hours threshold, and never touches a file another process holds."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/inventory_worker_threads.py` until Control repoints them; this room's own documents name `ops/lib/scripts/workers.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
