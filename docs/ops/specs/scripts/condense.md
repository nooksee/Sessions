# Technical Specification: condense

Script: `Sessions/ops/lib/scripts/condense.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_condense.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/condense_codex_compacted_history.py`, which this tree no longer holds; built as it was, 2 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Condense old Codex compacted-history rows in copied JSONL candidates." (the file names no author; attributed to the file). No receipt in `Receipts/` names it (0 of 304), so who asked for it, and when, is not recorded there.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/condense_codex_compacted_history.py` (sha256 `af70ea42d28c55cf04a0af6917f118a22fe3164a687b0f35eec9b6a2c1de52fc`) was copied to `ops/lib/scripts/condense.py` on 2026-11-01 with 2 edit(s): parents[2] -> parents[4] (1); "Sessions/Scripts/condense_codex_compacted_history.py" -> "Sessions/ops/lib/scripts/condense.py" (1).
2. Command line: `python3 -I -B ops/lib/scripts/condense.py`. Options as the script declares them:
   - `--source`: Copied JSONL candidate to read.
   - `--destination`: Destination derivative JSONL. Default: lab path under Sessions/Lab.
   - `--stamp`: Stable stamp for repeatable output. Default: local timestamp.
   - `--keep-latest-compacted`: Preserve the latest N compacted rows exactly. Default: 32.
   - `--receipt-group-size`: Maximum condensed compacted rows represented by one receipt row. Default: 50.
   - `--dry-run`: Measure only; do not write the derivative.
   - `--write-evidence`: Write evidence under Sessions/Evidence.
3. Reads and writes: as the docstring states (274 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

No receipt names `condense_codex_compacted_history.py`. Its history before this port is in Control's Git history of `Sessions/Scripts/`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "It does not edit production sessions, rewrite source sessions, copy auth files, launch Codex, or promote derivatives."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/condense_codex_compacted_history.py` until Control repoints them; this room's own documents name `ops/lib/scripts/condense.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
