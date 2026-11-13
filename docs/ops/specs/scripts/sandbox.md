# Technical Specification: sandbox

Script: `Sessions/ops/lib/scripts/sandbox.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_sandbox.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/build_codex_session_sandbox.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Prepare an isolated Codex session JSONL sandbox without launching Codex." (the file names no author; attributed to the file). No receipt in `Receipts/` names it (0 of 304), so who asked for it, and when, is not recorded there.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/build_codex_session_sandbox.py` (sha256 `4239c2d8daeff68f43c83bd72593d7f5ab6506c4d5431178e2d8d99abc84bca1`) was copied to `ops/lib/scripts/sandbox.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1).
2. Command line: `python3 -I -B ops/lib/scripts/sandbox.py`. Options as the script declares them:
   - `--source`: Source JSONL or JSONL backup to measure.
   - `--candidate`: Optional prebuilt derivative candidate. If omitted, the source is used as a baseline candidate.
   - `--dry-run`: Print the planned sandbox layout without writing files.
   - `--prepare`: Copy the candidate into an isolated sandbox and write receipts.
   - `--sandbox-root`: Parent directory for sandbox runs. Default: Sessions/Lab/Codex-Session-Sandbox.
   - `--stamp`: Optional stable run stamp for repeatable tests. Default: current local timestamp.
   - `--no-auth`: Required default posture. Accepted for explicitness; auth files are never copied by this script.
3. Reads and writes: as the docstring states (482 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

No receipt names `build_codex_session_sandbox.py`. Its history before this port is in Control's Git history of `Sessions/Scripts/`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Prepare an isolated Codex session JSONL sandbox without launching Codex." "It does not edit production session files, copy auth material, move Dropbox payload, or launch Codex."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/build_codex_session_sandbox.py` until Control repoints them; this room's own documents name `ops/lib/scripts/sandbox.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
