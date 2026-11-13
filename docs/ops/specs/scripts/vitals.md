# Technical Specification: vitals

Script: `Sessions/ops/lib/scripts/vitals.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_vitals.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/check_claude_session_health.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Report health for Claude Code session JSONL files." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/session-clinic-rounds-monitoring-20260717.md` (2026-07-17); 5 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/check_claude_session_health.py` (sha256 `cf7fe40612d36ecfbbbe2a855f466bfb2bb97800cee883e7ad6290b8955a72e9`) was copied to `ops/lib/scripts/vitals.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/vitals.py`. Options as the script declares them:
   - `--root`: (no help text in the script)
   - `--only-flagged`: print only rotate-soon/treat-images/CRITICAL
3. Reads and writes: as the docstring states (1906 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/session-clinic-rounds-monitoring-20260717.md` is the earliest of 5 receipt(s) naming `check_claude_session_health.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Claude Code transcripts do not carry Codex-style token telemetry, so this measures the proxies that actually predict a Claude session's failure mode: - file bytes: the whole transcript is re-read every turn." "Verdicts (image-aware and compaction-aware, because a 40 MB thread that is half images is sicker than a 40 MB thread of pure text, and a 20 MB thread that has shed 96% of its context twice is sicker than either): CRITICAL : bytes >= CRIT_BYTES or image_mb >= CRIT_IMG_MB CRITICAL-compact-treadmill: compacts >= CRIT_COMPACTS, or any compaction carrying < CRIT_CARRY_PCT compact-treadmill : compacts >= WARN_COMPACTS, or any compaction carrying < WARN_CARRY_PCT treat-images : image_mb >= WARN_IMG_MB (elide; keep every turn) rotate-soon : bytes >= WARN_BYTES healthy : otherwise Read-only." "Never modifies session files."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/check_claude_session_health.py` until Control repoints them; this room's own documents name `ops/lib/scripts/vitals.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
