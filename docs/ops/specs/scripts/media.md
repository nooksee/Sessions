# Technical Specification: media

Script: `Sessions/ops/lib/scripts/media.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_media.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/externalize_claude_image_payloads.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Move base64 media out of a Claude session body into files, losslessly." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/ward-recovery-and-instrument-repair-20260908.md` (2026-09-08); 4 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/externalize_claude_image_payloads.py` (sha256 `3c852eb0da228e2676749e3002d134bd5f538bdac71e333bad4b937ac8e849d2`) was copied to `ops/lib/scripts/media.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/media.py`. Options as the script declares them:
   - `--donor`: opened read-only
   - `--out`: (no help text in the script)
   - `--media-dir`: (no help text in the script)
   - `--rel-hint`: path shown to the resident in each placeholder
   - `--stamp`: date written into each placeholder; defaults to today. Pass an explicit value only to reproduce an earlier run.
3. Reads and writes: as the docstring states (2188 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/ward-recovery-and-instrument-repair-20260908.md` is the earliest of 4 receipt(s) naming `externalize_claude_image_payloads.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "What is deliberately NOT done: * nothing is deleted, here or anywhere; * the donor is opened read-only and never written; * non-media rows are re-serialised only if they were touched, and every row is compared for text equality afterwards by the caller's gates; * output goes beside the original as `.NEW`, per the operator's standing rule: he performs the swap himself with the application closed, because a live body is appended to every turn and a torn write there is unrecoverable." "Streaming, one line at a time: a 600 MB body must never be held in memory."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/externalize_claude_image_payloads.py` until Control repoints them; this room's own documents name `ops/lib/scripts/media.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
