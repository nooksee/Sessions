# Technical Specification: images

Script: `Sessions/ops/lib/scripts/images.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_images.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/externalize_codex_image_payloads.py`, which this tree no longer holds; built as it was, 2 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Build an analysis-only Codex JSONL copy with oldest image payloads externalized." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/george-tool-output-reduction-20260828.md` (2026-08-28); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/externalize_codex_image_payloads.py` (sha256 `9f3ea5175ac71b41563589efb6feeaab3ef58396e59f28f4eab828cef053e915`) was copied to `ops/lib/scripts/images.py` on 2026-11-01 with 2 edit(s): parents[2] -> parents[4] (1); "Sessions/Scripts/externalize_codex_image_payloads.py" -> "Sessions/ops/lib/scripts/images.py" (1).
2. Command line: `python3 -I -B ops/lib/scripts/images.py`. Options as the script declares them:
   - `--source`: Source JSONL to read. This must be a copied or lab source.
   - `--destination`: Destination derivative JSONL. Default: lab path under Sessions/Lab.
   - `--stamp`: Stable stamp for repeatable output. Default: local timestamp.
   - `--max-image-bytes`: Oldest image bytes to externalize. Default: 250 MiB.
   - `--write-external-images`: Write decoded/opaque image payloads under the lab artifact directory.
   - `--dry-run`: Measure only; do not write destination JSONL.
3. Reads and writes: as the docstring states (273 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/george-tool-output-reduction-20260828.md` is the earliest of 1 receipt(s) naming `externalize_codex_image_payloads.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "It does not edit live sessions, rewrite source sessions, copy auth files, launch Codex, or promote derivatives."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/externalize_codex_image_payloads.py` until Control repoints them; this room's own documents name `ops/lib/scripts/images.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
