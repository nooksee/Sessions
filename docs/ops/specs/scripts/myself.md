<!-- redact: public copy; source sha256 37d9a07dfd0f60901f58abf7e02d797e307112bbc34a2edaee5c91cfdf1f1fdf; rules 8; mode history; words 2; sessions 0 whole, 0 truncated; host paths 0; decisions 0 -->
# Technical Specification: myself

Script: `Sessions/ops/lib/scripts/myself.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_myself.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/check_myself.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "[words sha256=a3651b719ee3084d4966966fd10c5bf4f9da29f4c7fab4fb1908ec8db936b7ff]" (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/resident-self-check-canary-20260809.md` (2026-08-09); 10 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/check_myself.py` (sha256 `e4b2fad6d0d64d223fe904626374d5b3cbf993cafcbac876b336c2ed3baf3bc8`) was copied to `ops/lib/scripts/myself.py` on 2026-11-01 with 1 edit(s): parents[1] -> parents[3] (1).
2. Command line: `python3 -I -B ops/lib/scripts/myself.py`; the script declares no argparse options (it reads its inputs from fixed paths or from the environment, as its docstring says).
3. Reads and writes: as the docstring states (463 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/resident-self-check-canary-20260809.md` is the earliest of 10 receipt(s) naming `check_myself.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "[words sha256=d96e83608b65c40f1db5ca030ea3591febd404c82db13310192be97c07c435d5]"
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/check_myself.py` until Control repoints them; this room's own documents name `ops/lib/scripts/myself.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
