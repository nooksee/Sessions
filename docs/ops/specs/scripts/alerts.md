# Technical Specification: alerts

Script: `Sessions/ops/lib/scripts/alerts.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_alerts.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/clinic_alert_diff.py`, which this tree no longer holds; built as it was, 0 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Edge-triggered alert layer for the clinic rounds report." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/clinic-alert-edge-triggering-20260722.md` (2026-07-22); 6 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/clinic_alert_diff.py` (sha256 `d6a70ebbddb3bd9005ec1cc54749011c69d8e4c25b90ca2cd38e9f7e0f6e1f56`) was copied to `ops/lib/scripts/alerts.py` on 2026-11-01 with 0 edit(s): none.
2. Command line: `python3 -I -B ops/lib/scripts/alerts.py`; the script declares no argparse options (it reads its inputs from fixed paths or from the environment, as its docstring says).
3. Reads and writes: as the docstring states (1255 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/clinic-alert-edge-triggering-20260722.md` is the earliest of 6 receipt(s) naming `clinic_alert_diff.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Unchanged/chronic flags and improvements are logged but do not pop a notification." "Read-only against session files; only writes its own small state JSON." "OSAI's status tray) that must never retain a patient identifier, path, or title."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/clinic_alert_diff.py` until Control repoints them; this room's own documents name `ops/lib/scripts/alerts.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
