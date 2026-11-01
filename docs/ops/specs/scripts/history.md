# Technical Specification: history

Script: `Sessions/ops/lib/scripts/history.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_history.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/inspect_compacted_history.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Inspect Codex compacted-history rows without modifying session files." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/compacted-history-inspection-20260623.md` (2026-06-23); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/inspect_compacted_history.py` (sha256 `28b769cd11f1c7f215fd9e7466386840e8602f5a27e763a66485c5671f7388d2`) was copied to `ops/lib/scripts/history.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1).
2. Command line: `python3 -I -B ops/lib/scripts/history.py`. Options as the script declares them:
   - `--session`: Explicit session JSONL to inspect.
   - `--latest`: Inspect the newest largest live session.
   - `--codex-home`: (no help text in the script)
   - `--evidence-dir`: (no help text in the script)
   - `--max-largest-items`: (no help text in the script)
   - `--hash`: Compute SHA-256 for the source session.
3. Reads and writes: as the docstring states (69 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/compacted-history-inspection-20260623.md` is the earliest of 1 receipt(s) naming `inspect_compacted_history.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Inspect Codex compacted-history rows without modifying session files."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/inspect_compacted_history.py` until Control repoints them; this room's own documents name `ops/lib/scripts/history.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
