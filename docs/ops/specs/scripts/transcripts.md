# Technical Specification: transcripts

Script: `Sessions/ops/lib/scripts/transcripts.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_transcripts.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/condense_codex_tool_transcripts.py`, which this tree no longer holds; built as it was, 2 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Condense old Codex tool transcript rows in copied JSONL candidates." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/desktop-continuity-part-ii-target7000-protect1000-20260704.md` (2026-07-04); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/condense_codex_tool_transcripts.py` (sha256 `760d6e2b00e37c02a79c6577bed029491e56751dc5bf2dc07858bcd2b114bcf6`) was copied to `ops/lib/scripts/transcripts.py` on 2026-11-01 with 2 edit(s): parents[2] -> parents[4] (1); "Sessions/Scripts/condense_codex_tool_transcripts.py" -> "Sessions/ops/lib/scripts/transcripts.py" (1).
2. Command line: `python3 -I -B ops/lib/scripts/transcripts.py`. Options as the script declares them:
   - `--source`: Copied JSONL candidate to read.
   - `--destination`: Destination derivative JSONL. Default: lab path under Sessions/Lab.
   - `--stamp`: Stable stamp for repeatable output. Default: local timestamp.
   - `--target-response-items`: Practical response-item target for the derivative. Default: 14000.
   - `--protect-last-response-items`: Preserve the latest N response items exactly. Default: 6000.
   - `--receipt-group-size`: Maximum removed response items represented by one receipt row. Default: 500.
   - `--allow-reasoning-fallback`: If paired function calls are insufficient, allow old reasoning rows to be condensed.
   - `--dry-run`: Measure only; do not write the derivative.
   - `--write-evidence`: Write evidence under Sessions/Evidence.
3. Reads and writes: as the docstring states (288 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/desktop-continuity-part-ii-target7000-protect1000-20260704.md` is the earliest of 1 receipt(s) naming `condense_codex_tool_transcripts.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "It does not edit production sessions, rewrite source sessions, copy auth files, launch Codex, or promote derivatives."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/condense_codex_tool_transcripts.py` until Control repoints them; this room's own documents name `ops/lib/scripts/transcripts.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
