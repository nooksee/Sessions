# Technical Specification: limits

Script: `Sessions/ops/lib/scripts/limits.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_limits.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/validate_codex_session_loader_limits.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Validate copied Codex JSONL candidates against observed loader limits." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/current-continuity-round6-loader-limit-failure-20260627.md` (2026-06-27); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/validate_codex_session_loader_limits.py` (sha256 `5b4a20d9fca1e3e154081ae5bd962a557aaefa4f3d435c5434c0715f07249faf`) was copied to `ops/lib/scripts/limits.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1).
2. Command line: `python3 -I -B ops/lib/scripts/limits.py`. Options as the script declares them:
   - `--session`: JSONL session candidate to validate.
   - `--max-input-items`: Observed maximum API input item count. Default: 16384.
   - `--stamp`: Stable evidence stamp. Default: local timestamp.
   - `--write-evidence`: Write evidence files under Sessions/Evidence.
3. Reads and writes: as the docstring states (228 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/current-continuity-round6-loader-limit-failure-20260627.md` is the earliest of 1 receipt(s) naming `validate_codex_session_loader_limits.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "This script is read-only with respect to the session being inspected." "It does not edit live sessions, promote derivatives, copy auth files, or launch Codex."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/validate_codex_session_loader_limits.py` until Control repoints them; this room's own documents name `ops/lib/scripts/limits.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
