# Technical Specification: tablet

Script: `Sessions/ops/lib/scripts/tablet.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_tablet.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/build_tablet_codex_successor.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Build a current-version, CLI-native Codex successor from a copied session body." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/tablet-remote-device-successor-20260807.md` (2026-08-07); 3 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/build_tablet_codex_successor.py` (sha256 `72129c800e67661c0ce6e4c051238f0d7b9213b2de3dade4432eda371fcb04ea`) was copied to `ops/lib/scripts/tablet.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/tablet.py`. Options as the script declares them:
   - `--evidence`: copied donor body; opened read-only
   - `--scaffold`: container minted by the current CLI; supplies session_meta
   - `--capsule`: lineage capsule text
   - `--cwd`: destination working directory
   - `--originator`: (no help text in the script)
   - `--source`: (no help text in the script)
   - `--out-dir`: (no help text in the script)
3. Reads and writes: as the docstring states (3013 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/tablet-remote-device-successor-20260807.md` is the earliest of 3 receipt(s) naming `build_tablet_codex_successor.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "The Remote Device tablet body of 2026-07-22 is the case that motivated it: - the donor ran VS Code on Windows (`codex_vscode`, `cwd c:\Users\Highs`) at CLI `0.145.0-alpha.27`; the successor must run the Codex CLI at the current version, so scaffolding cannot simply be carried across; - no container can be created by hand on the destination, because the destination is a tablet the operator holds and this agent must not touch." It also states that the evidence body is opened read-only and is never modified.
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/build_tablet_codex_successor.py` until Control repoints them; this room's own documents name `ops/lib/scripts/tablet.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
