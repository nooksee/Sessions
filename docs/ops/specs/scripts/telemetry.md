# Technical Specification: telemetry

Script: `Sessions/ops/lib/scripts/telemetry.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_telemetry.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/check_codex_token_health.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Report token health for Codex rollout JSONL files." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/session-clinic-rounds-monitoring-20260717.md` (2026-07-17); 6 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/check_codex_token_health.py` (sha256 `c0a92fe81a887773dd4f76c60a762cf22aff218ea0321c40e4b26a0aaa1777ed`) was copied to `ops/lib/scripts/telemetry.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/telemetry.py` <paths>. Options as the script declares them:
   - `--root`: Session root to scan when no paths given.
   - `--json`: Emit JSON instead of a table.
   - `paths` (positional): Rollout JSONL files. Default: scan host + VM roots.
3. Reads and writes: as the docstring states (867 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/session-clinic-rounds-monitoring-20260717.md` is the earliest of 6 receipt(s) naming `check_codex_token_health.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Read-only." "Never modifies session files."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/check_codex_token_health.py` until Control repoints them; this room's own documents name `ops/lib/scripts/telemetry.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
