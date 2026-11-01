# Technical Specification: successor

Script: `Sessions/ops/lib/scripts/successor.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_successor.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/build_claude_resident.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Build a new Claude resident from a donor body." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/restoration-and-staffing-batch-20260730.md` (2026-07-30); 11 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/build_claude_resident.py` (sha256 `d07b77b797fed235ff59901dd6bec5f500e8d8f3280c1f0a3cab0d19d28fd90d`) was copied to `ops/lib/scripts/successor.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/successor.py`. Options as the script declares them:
   - `--donor`: (no help text in the script)
   - `--out`: (no help text in the script)
   - `--session-id`: (no help text in the script)
   - `--cwd`: Target project root
   - `--orientation`: (no help text in the script)
   - `--trim-to-last-compaction`: Keep only the active window: everything from the last compact_boundary row forward. Use when the donor is being rotated for size or compaction damage rather than moved rooms.
3. Reads and writes: as the docstring states (2708 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/restoration-and-staffing-batch-20260730.md` is the earliest of 11 receipt(s) naming `build_claude_resident.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "RE-ID IS SCOPED TO IDENTITY FIELDS, NEVER TO TEXT." "Rewriting any of those makes the body assert that a past measurement returned a value it did not return, that a file held content it did not hold, or that a command was run that never was." "Never inside a string, whatever that string contains.** 3." "Without an explicit orientation message a resident inherits a large transcript with no grounding and no idea it moved." "The donor body is opened read-only and never modified."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/build_claude_resident.py` until Control repoints them; this room's own documents name `ops/lib/scripts/successor.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
