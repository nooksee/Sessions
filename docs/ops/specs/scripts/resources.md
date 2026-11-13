# Technical Specification: resources

Script: `Sessions/ops/lib/scripts/resources.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_resources.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/resident_resource_collector.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Resident Resource Governor -- collector." (non-ASCII transliterated, PoT 4.3.4) (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/sessions-custody-review-and-correction-20260805.md` (2026-08-05); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/resident_resource_collector.py` (sha256 `4ebd948b998876fc57400f1ebe8758c64781bbeec46b048a9fe1335e7e76797b`) was copied to `ops/lib/scripts/resources.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/resources.py`; the script declares no argparse options (it reads its inputs from fixed paths or from the environment, as its docstring says).
3. Reads and writes: as the docstring states (1355 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/sessions-custody-review-and-correction-20260805.md` is the earliest of 1 receipt(s) naming `resident_resource_collector.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "This mirrors the Session Clinic's public aggregate contract: numbers and states leave, identity never does." "WHAT THIS DOES NOT DO." "It does not purchase, upgrade, downgrade, switch models, block launches, or change any account setting." "The supported telemetry carries plan *windows* only -- it does not expose usage-credit balance or month-to-date credit spend, and this collector does not attempt to obtain those by any other means."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/resident_resource_collector.py` until Control repoints them; this room's own documents name `ops/lib/scripts/resources.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
- Collects when invoked, `--help` included; it is never run by a test.
