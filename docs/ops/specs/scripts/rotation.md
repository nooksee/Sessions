# Technical Specification: rotation

Script: `Sessions/ops/lib/scripts/rotation.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_rotation.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/build_codex_rotation.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Rotate a Codex resident into a fresh provider-created container." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/restoration-and-staffing-batch-20260730.md` (2026-07-30); 8 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/build_codex_rotation.py` (sha256 `ff19215b3f83450662950b78b37a01cf4212bd79d749972aa46a621a2a7cf375`) was copied to `ops/lib/scripts/rotation.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/rotation.py`. Options as the script declares them:
   - `--donor`: (no help text in the script)
   - `--target`: (no help text in the script)
   - `--capsule`: LINEAGE MEMORY text
   - `--out`: (no help text in the script)
   - `--allow-imbalance`: permit a window that is nearly all operator turns
3. Reads and writes: as the docstring states (932 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/restoration-and-staffing-batch-20260730.md` is the earliest of 8 receipt(s) naming `build_codex_rotation.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "The compaction `replacement_history` is never replayed: it is already compacted state and can contain hundreds of retained user messages without their assistant replies; - a lineage capsule is inserted both as a `compacted` marker for house tooling and as a developer message the model can actually read; - only structural identifiers are rewritten." "Prose is never touched." "The donor is opened read-only and never modified."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/build_codex_rotation.py` until Control repoints them; this room's own documents name `ops/lib/scripts/rotation.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
