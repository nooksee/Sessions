# Technical Specification: conflicts

Script: `Sessions/ops/lib/scripts/conflicts.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_conflicts.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/check_codex_thread_writer_conflicts.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Detect the active-writer condition that can hang a chat on "Initializing"." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/full-codex-rotation-and-relabel-20260808.md` (2026-08-08); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/check_codex_thread_writer_conflicts.py` (sha256 `39ea9e0ad4a439927b66f20984d697e72bb094b38d194eb0fe5e1cf4928a55e9`) was copied to `ops/lib/scripts/conflicts.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/conflicts.py`. Options as the script declares them:
   - `--json`: (no help text in the script)
3. Reads and writes: as the docstring states (1515 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/full-codex-rotation-and-relabel-20260808.md` is the earliest of 1 receipt(s) naming `check_codex_thread_writer_conflicts.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Writer-conflict success therefore rules out one failure class; it does not prove that a session body will resume." "This reports, read-only: * which threads currently have a writer claim, and which process holds it; * whether that holder is an editor bridge, a visible terminal CLI, or a background daemon; * any lock whose holder is gone, which is a genuinely stale lock; * the exact command to clear it."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/check_codex_thread_writer_conflicts.py` until Control repoints them; this room's own documents name `ops/lib/scripts/conflicts.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
