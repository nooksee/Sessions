# Technical Specification: gate

Script: `Sessions/ops/lib/scripts/gate.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_gate.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/check_writer_gate.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Verify the single-writer gate before any session-body write." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/gemini-removal-and-shared-ancestry-20260805.md` (2026-08-05); 6 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/check_writer_gate.py` (sha256 `f6f3f97153c600bb23ce1503dee33615732024de2cbeebaf6dfec60b05a7f053`) was copied to `ops/lib/scripts/gate.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/gate.py`. Options as the script declares them:
   - `--file`: also verify this file is not held open
   - `--quiet`: (no help text in the script)
3. Reads and writes: as the docstring states (1046 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/gemini-removal-and-shared-ancestry-20260805.md` is the earliest of 6 receipt(s) naming `check_writer_gate.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "The rule this script enforces: identify a process by what it IS -- its resolved `/proc/PID/exe` and its argv[0] -- never by a substring of its arguments." "And never count yourself or your own ancestors." "Read-only."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/check_writer_gate.py` until Control repoints them; this room's own documents name `ops/lib/scripts/gate.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
