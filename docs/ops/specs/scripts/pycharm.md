<!-- redact: public copy; source sha256 1cfbc5c1cb198e331000d7f51f920e3b8d43fb484fdcf3f152952ecdf114c245; rules 8; mode history; words 2; sessions 0 whole, 0 truncated; host paths 0; decisions 0 -->
# Technical Specification: pycharm

Script: `Sessions/ops/lib/scripts/pycharm.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_pycharm.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/reconcile_pycharm_ai_surfaces.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "[words sha256=0d404687d4123a4922a8f2f25c9e5014485f5c35f19345c33fc2a00ae8374678]" (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/session-control-reconciliation-20260714.md` (2026-07-14); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/reconcile_pycharm_ai_surfaces.py` (sha256 `3c666f747d3684ce30b711b15f476168ee6fa19b93cfb99f55ac09e157970111`) was copied to `ops/lib/scripts/pycharm.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/pycharm.py`. Options as the script declares them:
   - `--workspace-dir`: (no help text in the script)
   - `--task-history`: (no help text in the script)
   - `--osai-workspace`: (no help text in the script)
   - `--control-workspace`: (no help text in the script)
   - `--preview-dir`: (no help text in the script)
   - `--apply`: (no help text in the script)
   - `--custody-dir`: (no help text in the script)
3. Reads and writes: as the docstring states (507 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/session-control-reconciliation-20260714.md` is the earliest of 1 receipt(s) naming `reconcile_pycharm_ai_surfaces.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "[words sha256=4bcf9e1b52abe6ee77e11f2de29a08d8646ebfb56896512248ed8c60c05bb058]"
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/reconcile_pycharm_ai_surfaces.py` until Control repoints them; this room's own documents name `ops/lib/scripts/pycharm.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
