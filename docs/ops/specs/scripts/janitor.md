# Technical Specification: janitor

Script: `Sessions/ops/lib/scripts/janitor.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_janitor.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/codex_claim_janitor.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Release writer claims the remote daemon is squatting on, automatically." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/joy-anne-enrollment-and-shannon-plant-reconciliation-20260812.md` (2026-08-12); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/codex_claim_janitor.py` (sha256 `50649955463dba7f7ba8342090c686e40cde6b41dfcb332bc57010b560695a26`) was copied to `ops/lib/scripts/janitor.py` on 2026-11-01 with 1 edit(s): / "check_codex_thread_writer_conflicts.py" -> / "conflicts.py" (1).
2. Command line: `python3 -I -B ops/lib/scripts/janitor.py`; the script declares no argparse options (it reads its inputs from fixed paths or from the environment, as its docstring says).
3. Reads and writes: as the docstring states (1635 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/joy-anne-enrollment-and-shannon-plant-reconciliation-20260812.md` is the earliest of 1 receipt(s) naming `codex_claim_janitor.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Editor and terminal claims mean a human is (or recently was) present, and this tool does not outrank humans."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/codex_claim_janitor.py` until Control repoints them; this room's own documents name `ops/lib/scripts/janitor.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
- Runs its action when invoked with any arguments, `--help` included; it is never run by a test.
