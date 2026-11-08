# Technical Specification: retention

Script: `Sessions/ops/lib/scripts/retention.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_retention.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/check_session_retention.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Report, and on explicit request enforce, the official session-folder policy." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/claudine-orientation-date-correction-20260808.md` (2026-08-08); 8 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/check_session_retention.py` (sha256 `58601cb2ad89daf5936969e7e9268f352a31fa732427fb7c4b08124105d195ef`) was copied to `ops/lib/scripts/retention.py` on 2026-11-01 with 1 edit(s): SESSIONS / "Scripts/check_writer_gate.py" -> SESSIONS / "ops/lib/scripts/gate.py" (1).
2. Command line: `python3 -I -B ops/lib/scripts/retention.py`. Options as the script declares them:
   - `--sweep`: relocate non-active bodies to quarantine; never deletes
   - `--quarantine`: where `--sweep` moves bodies. Default: `Project-Archives/Session-Quarantine` on the archive volume the host fingerprint names, read only when a sweep needs it; on the operator's direction of 2026-11-08 the archive volume is the interim backup drive, while the tier-2 drive is replaced.
   - `--include-archived`: also sweep the provider's own archived_sessions folder
3. Reads and writes: as the docstring states (1751 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/claudine-orientation-date-correction-20260808.md` is the earliest of 8 receipt(s) naming `check_session_retention.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Retention is measured, never guessed, and "in use" has two independent meanings." "The second clause was learned by breaking it: the first sweep moved bodies the registry did not list but PyCharm chats still pointed at, and the Remote Device chat came back with `failed to resolve rollout path ...: file does not exist`." "Two hard refusals, because this tool moves real session bodies: * a registered active or editor-bound body is never moved, under any flag; * `--sweep` refuses to run unless the writer gate is clean, because relocating a body an editor or provider currently holds open risks a torn write."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/check_session_retention.py` until Control repoints them; this room's own documents name `ops/lib/scripts/retention.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
