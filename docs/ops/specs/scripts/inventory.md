# Technical Specification: inventory

Script: `Sessions/ops/lib/scripts/inventory.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_inventory.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/inventory_codex_sessions.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Inventory local Codex session assets without modifying them." (the file names no author; attributed to the file). No receipt in `Receipts/` names it (0 of 304), so who asked for it, and when, is not recorded there.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/inventory_codex_sessions.py` (sha256 `ef333ab09fd196087e435e2a6bb99e446bcc9a01e5a973442a38da71c35d8e54`) was copied to `ops/lib/scripts/inventory.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1).
2. Command line: `python3 -I -B ops/lib/scripts/inventory.py`. Options as the script declares them:
   - `--codex-home`: (no help text in the script)
   - `--inventory-dir`: (no help text in the script)
   - `--include-archived`: Also scan archived_sessions.
   - `--inspect-lines`: Read JSONL lines for counts and largest-record statistics.
   - `--hash`: Compute SHA-256 for every discovered session file.
   - `--current-alias`: Also write codex-session-assets-current reports.
3. Reads and writes: as the docstring states (278 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

No receipt names `inventory_codex_sessions.py`. Its history before this port is in Control's Git history of `Sessions/Scripts/`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Inventory local Codex session assets without modifying them." "It does not prune, rewrite, move, delete, or archive sessions."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/inventory_codex_sessions.py` until Control repoints them; this room's own documents name `ops/lib/scripts/inventory.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
