# Technical Specification: dossier

Script: `Sessions/ops/lib/scripts/dossier.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_dossier.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/build_codex_session_handoff.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Build a deterministic Codex session handoff packet." (the file names no author; attributed to the file). No receipt in `Receipts/` names it (0 of 304), so who asked for it, and when, is not recorded there.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/build_codex_session_handoff.py` (sha256 `059486f4b05af16ce659616fd418cc85920842f5dd05d15e36b3da6f6d4edd7b`) was copied to `ops/lib/scripts/dossier.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1).
2. Command line: `python3 -I -B ops/lib/scripts/dossier.py`. Options as the script declares them:
   - `--inventory-dir`: (no help text in the script)
   - `--output`: Optional explicit output path.
3. Reads and writes: as the docstring states (251 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

No receipt names `build_codex_session_handoff.py`. Its history before this port is in Control's Git history of `Sessions/Scripts/`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "It does not read secrets, edit sessions, or claim that transcript content outranks canon."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/build_codex_session_handoff.py` until Control repoints them; this room's own documents name `ops/lib/scripts/dossier.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
