# Technical Specification: miner

Script: `Sessions/ops/lib/scripts/miner.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_miner.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/mine_codex_logs_compaction_events.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Read-only Codex log miner for compact and context failure evidence." (the file names no author; attributed to the file). No receipt in `Receipts/` names it (0 of 304), so who asked for it, and when, is not recorded there.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/mine_codex_logs_compaction_events.py` (sha256 `188c03a904c3d9a26487c961d36b4048d9101358d5a198af0d140702a7f35c7d`) was copied to `ops/lib/scripts/miner.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/miner.py`. Options as the script declares them:
   - `--db`: (no help text in the script)
   - `--out`: (no help text in the script)
   - `--sample-limit`: (no help text in the script)
3. Reads and writes: as the docstring states (67 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

No receipt names `mine_codex_logs_compaction_events.py`. Its history before this port is in Control's Git history of `Sessions/Scripts/`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Read-only Codex log miner for compact and context failure evidence."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/mine_codex_logs_compaction_events.py` until Control repoints them; this room's own documents name `ops/lib/scripts/miner.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
