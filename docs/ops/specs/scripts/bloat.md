# Technical Specification: bloat

Script: `Sessions/ops/lib/scripts/bloat.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_bloat.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/analyze_codex_session_bloat.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Analyze Codex session JSONL pressure without modifying session files." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/current-continuity-round9-number9-vm-staging-20260702.md` (2026-07-02); 2 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/analyze_codex_session_bloat.py` (sha256 `440d24606d610858eb8c2ce2682678d0f983a4d71eac9b7822de869e71bf1a7f`) was copied to `ops/lib/scripts/bloat.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1).
2. Command line: `python3 -I -B ops/lib/scripts/bloat.py`. Options as the script declares them:
   - `--session`: Explicit session JSONL or JSONL backup to analyze.
   - `--latest`: Analyze the largest newest session under CODEX_HOME sessions.
   - `--codex-home`: (no help text in the script)
   - `--inventory-dir`: (no help text in the script)
   - `--max-largest-lines`: (no help text in the script)
   - `--hash`: Compute SHA-256 for the source session.
   - `--reducer-inventory`: Write reducer policy inventory outputs with category percentages and reduce status.
3. Reads and writes: as the docstring states (69 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/current-continuity-round9-number9-vm-staging-20260702.md` is the earliest of 2 receipt(s) naming `analyze_codex_session_bloat.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Analyze Codex session JSONL pressure without modifying session files."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/analyze_codex_session_bloat.py` until Control repoints them; this room's own documents name `ops/lib/scripts/bloat.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
