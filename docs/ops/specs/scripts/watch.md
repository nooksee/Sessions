# Technical Specification: watch

Script: `Sessions/ops/lib/scripts/watch.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_watch.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/watch_codex_session_size.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Watch Codex sessions and emit operator-visible warnings." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/current-continuity-round10-menu-container-failure-20260703.md` (2026-07-03); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/watch_codex_session_size.py` (sha256 `f7c6d0e1614069303a7375fee7af0906e4da59a5bef94fe7e15d5d409697f30f`) was copied to `ops/lib/scripts/watch.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/watch.py`. Options as the script declares them:
   - `--sessions-root`: Session root to scan; repeatable. Default: host + Workbench VM share, the share's root from the host fingerprint's working volume.
   - `--evidence-dir`: (no help text in the script)
   - `--warn-bytes`: (no help text in the script)
   - `--critical-bytes`: (no help text in the script)
   - `--warn-context-pct`: (no help text in the script)
   - `--critical-context-pct`: (no help text in the script)
   - `--top`: (no help text in the script)
   - `--notify`: (no help text in the script)
   - `--fail-on-critical`: (no help text in the script)
3. Reads and writes: as the docstring states (608 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/current-continuity-round10-menu-container-failure-20260703.md` is the earliest of 1 receipt(s) naming `watch_codex_session_size.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Read-only."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/watch_codex_session_size.py` until Control repoints them; this room's own documents name `ops/lib/scripts/watch.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
