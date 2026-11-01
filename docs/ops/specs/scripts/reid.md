# Technical Specification: reid

Script: `Sessions/ops/lib/scripts/reid.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_reid.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/build_codex_session_reid_candidate.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Build a derivative Codex JSONL with structural session IDs rewritten." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/george-method-vs-round11-differential-20260703.md` (2026-07-03); 3 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/build_codex_session_reid_candidate.py` (sha256 `a9a416001eb2ec9d849606fff282040d1d3ce4c63f59a0129af20d4cf080d6c9`) was copied to `ops/lib/scripts/reid.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/reid.py`. Options as the script declares them:
   - `--source`: Source JSONL or JSONL-derived file.
   - `--destination`: Destination derivative JSONL path.
   - `--old-id`: Source session UUID to replace in structural fields.
   - `--new-id`: Target session UUID for structural fields.
   - `--target-cwd`: Optional cwd value for session_meta payloads. Omit to preserve source cwd.
   - `--target-cli-version`: Optional cli_version value for session_meta payloads. Omit to preserve source version.
   - `--dry-run`: Measure planned changes without writing output.
3. Reads and writes: as the docstring states (388 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/george-method-vs-round11-differential-20260703.md` is the earliest of 3 receipt(s) naming `build_codex_session_reid_candidate.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "It does not edit production sessions, copy auth material, update SQLite state, update the session index, launch Codex, or promote a candidate."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/build_codex_session_reid_candidate.py` until Control repoints them; this room's own documents name `ops/lib/scripts/reid.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
