# Technical Specification: archive

Script: `Sessions/ops/lib/scripts/archive.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_archive.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/archive_codex_session.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Archive selected Codex session files into root Backup." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/missing-residents-review-20261008.md` (2026-10-08); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/archive_codex_session.py` (sha256 `23b31900e8f32d8079e7c48159f6e7ca72cb6c94b04d1724ed1ca5f606cb600e`) was copied to `ops/lib/scripts/archive.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1).
2. Command line: `python3 -I -B ops/lib/scripts/archive.py`. Options as the script declares them:
   - `--codex-home`: (no help text in the script)
   - `--session`: Specific session file to archive.
   - `--latest`: Archive the most recently modified session JSONL.
   - `--include-paired-backup`: Also include <session>.backup when present.
   - `--backup-root`: (no help text in the script)
   - `--inventory-dir`: (no help text in the script)
   - `--label`: (no help text in the script)
   - `--apply`: Copy selected session files.
3. Reads and writes: as the docstring states (197 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/missing-residents-review-20261008.md` is the earliest of 1 receipt(s) naming `archive_codex_session.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "It never edits, prunes, moves, or deletes the source session file."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/archive_codex_session.py` until Control repoints them; this room's own documents name `ops/lib/scripts/archive.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
