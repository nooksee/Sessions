# Technical Specification: pressure

Script: `Sessions/ops/lib/scripts/pressure.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_pressure.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/analyze_codex_compact_context_pressure.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Gate copied Codex JSONL candidates for compact/context pressure." (the file names no author; attributed to the file). No receipt in `Receipts/` names it (0 of 304), so who asked for it, and when, is not recorded there.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/analyze_codex_compact_context_pressure.py` (sha256 `b03492b3f274c7b94d0c7cfaced605aede90cfba26c9c2cad8794e67cf4039be`) was copied to `ops/lib/scripts/pressure.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1).
2. Command line: `python3 -I -B ops/lib/scripts/pressure.py`. Options as the script declares them:
   - `--session`: Copied JSONL candidate to inspect.
   - `--max-response-items`: (no help text in the script)
   - `--max-bytes`: (no help text in the script)
   - `--max-largest-line-bytes`: (no help text in the script)
   - `--stamp`: Stable evidence stamp. Default: local timestamp.
   - `--write-evidence`: (no help text in the script)
3. Reads and writes: as the docstring states (358 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

No receipt names `analyze_codex_compact_context_pressure.py`. Its history before this port is in Control's Git history of `Sessions/Scripts/`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- The docstring states no refusal condition; the port added none.
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/analyze_codex_compact_context_pressure.py` until Control repoints them; this room's own documents name `ops/lib/scripts/pressure.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
