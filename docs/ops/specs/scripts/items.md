# Technical Specification: items

Script: `Sessions/ops/lib/scripts/items.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_items.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/analyze_codex_response_item_pressure.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Analyze Codex JSONL response-item pressure without rewriting sessions." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/current-continuity-response-item-pressure-20260627.md` (2026-06-27); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/analyze_codex_response_item_pressure.py` (sha256 `83741d481dc848edc89828b2ad56af95ac3055e9876c43f03c839dba90ec8f55`) was copied to `ops/lib/scripts/items.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1). On 2026-11-13 one description string was reworded; no behavior changed.
2. Command line: `python3 -I -B ops/lib/scripts/items.py`. Options as the script declares them:
   - `--session`: JSONL session or copied candidate to inspect.
   - `--stamp`: Stable evidence stamp. Default: local timestamp.
   - `--max-input-items`: (no help text in the script)
   - `--target-margin`: (no help text in the script)
   - `--top-lines`: (no help text in the script)
   - `--write-evidence`: (no help text in the script)
3. Reads and writes: as the docstring states (253 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/current-continuity-response-item-pressure-20260627.md` is the earliest of 1 receipt(s) naming `analyze_codex_response_item_pressure.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Analyze Codex JSONL response-item pressure without rewriting sessions."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/analyze_codex_response_item_pressure.py` until Control repoints them; this room's own documents name `ops/lib/scripts/items.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
