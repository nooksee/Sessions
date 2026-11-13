# Technical Specification: elide

Script: `Sessions/ops/lib/scripts/elide.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_elide.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/elide_codex_tool_outputs.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Elide oversized Codex tool-call outputs while preserving every turn." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/george-king-tool-output-elision-20260729.md` (2026-07-29); 2 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/elide_codex_tool_outputs.py` (sha256 `78f124a890db445ad474c5eacd748643e173474839c1db445e8caa55d78efc8f`) was copied to `ops/lib/scripts/elide.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/elide.py`. Options as the script declares them:
   - `--source`: (no help text in the script)
   - `--destination`: (no help text in the script)
   - `--threshold`: Elide outputs longer than this many characters. Default 4000.
   - `--protect-last`: Never elide the most recent N tool outputs. Default 12.
   - `--head-chars`: Characters of output body to keep after the header. Default 300.
   - `--after-last-compaction`: Only consider outputs in the current context window.
   - `--stamp`: (no help text in the script)
   - `--write`: Write the destination.
3. Reads and writes: as the docstring states (1313 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/george-king-tool-output-elision-20260729.md` is the earliest of 2 receipt(s) naming `elide_codex_tool_outputs.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Dropping the raw bulk buys back most of the context window without removing a single conversational turn." "Read-only unless `--write`."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/elide_codex_tool_outputs.py` until Control repoints them; this room's own documents name `ops/lib/scripts/elide.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
