# Technical Specification: estimate

Script: `Sessions/ops/lib/scripts/estimate.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_estimate.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/analyze_codex_token_context_pressure.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Estimate Codex JSONL context pressure in tokens." (the file names no author; attributed to the file). No receipt in `Receipts/` names it (0 of 304), so who asked for it, and when, is not recorded there.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/analyze_codex_token_context_pressure.py` (sha256 `f9a55060baba3b63f13e65528c6cffc4fdfd63de6d56c1869096f2f75f28153e`) was copied to `ops/lib/scripts/estimate.py` on 2026-11-01 with 0 edit(s): none. One change since, W8's second slice of 2026-11-07: the evidence folder is the room's own `logs`, found from the tool's place as `gauge.py` finds it, not a literal. It reads no private file.
2. Command line: `python3 -I -B ops/lib/scripts/estimate.py` <sessions>. Options as the script declares them:
   - `--encoding`: (no help text in the script)
   - `--warn-total-tokens`: (no help text in the script)
   - `--max-total-tokens`: (no help text in the script)
   - `--hard-trigger-tokens`: (no help text in the script)
   - `--top-rows`: (no help text in the script)
   - `--evidence-stem`: (no help text in the script)
   - `--no-evidence`: (no help text in the script)
   - `sessions` (positional)
3. Reads and writes: as the docstring states (176 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.
4. Requires the third-party module `tiktoken`; without it the script exits 1 with `Missing dependency: tiktoken`.

## Anecdotal Anchor

No receipt names `analyze_codex_token_context_pressure.py`. Its history before this port is in Control's Git history of `Sessions/Scripts/`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "This is a read-only lab tool." "It does not edit session files, promote derivatives, copy authentication files, or launch Codex."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/analyze_codex_token_context_pressure.py` until Control repoints them; this room's own documents name `ops/lib/scripts/estimate.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
