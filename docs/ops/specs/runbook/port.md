<!-- redact: public copy; source sha256 84e09f03c9c15b3e5c2789f7fcdea515a5d9d7cefc728feb1970b4c0c00eb8ca; rules 8; mode history; words 1; sessions 0 whole, 0 truncated; host paths 0; decisions 0 -->
# Port of the Sessions room to the STELA base

Owner: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Written 2026-11-01. Convention: STELA (`Projects/STELA`).

The operator directed on 2026-11-01: "[words sha256=19f15b9b270766a195600e9add9672f0eb2e63f05963d21654a3d66e2ef1b488]". This tree is that port, done in one pass on a copy of the operator's zip of the room, for the operator to review. The original folder, the nooksee/sessions repository and the nooksee/STELA repository were not changed by it.

## The rule

Each legacy lane went to the base folder that PoT 1.1 assigns, and nowhere else: `ops/` Run, `docs/` Explain, `tools/` Prove, `storage/` Work (disposable, ignored), `archives/` Keep, `logs/` Data, `archives/receipts/` Proof, the root for canon surfaces and pointers. A retired folder is frozen unchanged under `archives/legacy/<Name>/`; a working lane is under `storage/`. Records (`archives/receipts/`, `RoR.md`, `archives/`, `logs/`, `archives/legacy/Resident-Center/`) were not reworded (PoT 1.2.13). Maintained documents had their paths rewritten to the new places, each rewrite counted in the receipt.

## Where each lane went

| From | To | Files |
| --- | --- | --- |
| `Scripts/README.md` | `archives/legacy/Scripts/README.md` | 1 |
| `Scripts/run_full_codex_rotation_20260808.py` | `archives/legacy/Scripts/run_full_codex_rotation_20260808.py` | 1 |
| `Scripts/ (38 files) and Scripts/tests/ (12 files)` | `ops/lib/scripts/ (38) and tools/test/ (12), one-word names; hashes in the receipt` | 50 |
| `Plans` | `archives/legacy/Plans` | 12 |
| `Intake` | `archives/legacy/Intake` | 5 |
| `Archived` | `archives/legacy/Archived` | 3 |
| `Attic` | `archives/legacy/Attic` | 3 |
| `Lab` | `storage/lab` | 665 |
| `Candidates` | `storage/candidates` | 376 |
| `HANDOFF.md` | `archives/legacy/HANDOFF.md` | 1 |
| `INDEX.md` | `archives/legacy/INDEX.md` | 1 |
| `START-HERE.md` | `docs/START-HERE.md` | 1 |
| `archives/legacy/Config/` | stays at the root | 1 |
| `logs/`, `archives/receipts/`, `archives/legacy/Resident-Center/`, `storage/` (existing), `docs/`, `ops/`, `tools/`, `archives/` (existing) | stay | - |

`archives/legacy/Config/resident-center-relationship.json` is bound by Control: the drift detector reads it at `Sessions/Config/` on the accepted Control ref, and Control CI binds it to Control history (`docs/ops/specs/runbook/repository.md`). It moves when Control moves it (PoT 3.4).

## What Control must still repoint

1. The rounds timer (`session-health-rounds.timer`, Control systemd) runs `Sessions/Scripts/session_health_rounds.sh`; the ported wrapper is `ops/lib/scripts/rounds.sh` and calls `telemetry.py`, `vitals.py`, `alerts.py` and `drift.py` beside it.
2. Control CI runs `Sessions/Scripts/tests`; the suites are now `tools/test/test_*.py` and the room's own workflow file already runs them.
3. Control's index still tracks the legacy Sessions paths (1,084 at the bootstrap); the retired paths need the reviewed Control change the bootstrap receipt describes.
Until these are done, the live host keeps `Scripts/` beside this layout; this tree shows the layout after them.

## Decisions left to the operator

1. The 38 one-word tool names (the map is in `docs/ops/registry/scripts.md` beside the legacy names).
2. Whether the 303 receipts that only Control tracks are admitted to this repository's Git (`.gitignore` admits 2 today).
3. Which of the frozen plans under `archives/legacy/Plans/` are still active and should be re-homed as runbook specs by their writers.
4. Reviewers for the ported tools (PoT 4.2.2); each spec carries the placeholder.

## Addition: the mind project record (2026-11-01)

The operator supplied `mind-manifest-20261101.zip`, packed by the Session Continuity Manager, and asked for it to be integrated. It went in whole, byte for byte, as `archives/mind-manifest-20261101/` (97 files; its `MANIFEST.txt` verified, 96 of 96 listed hashes). 81 of the 83 packaged files that have a counterpart in this tree are identical to it; the other 2 (`docs/ops/specs/scripts/rotate.md`, `docs/MANUAL.md`) differ only by this port's path rewrites, so the tree already holds the v2 tool (`ops/lib/scripts/mind.py`, sha256 4159b57f...), its 40 tests, and its specifications. The v1 design (`ops/bin/manifest`, the three manifests, the session-start hook) stays inside the record only: Claudio's audit did not pass it and the operator turned the design around (the record's `README.md`). Nothing was installed, wired or switched on.

Pending, named in the record and left to their owners: the RoR-3 leaf move to the `archives/` root in `mind.py`, its spec and tests (Claudine Colbert); the notebook design with the operator's sealing step; the first mind entries, each with the operator's yes.

## Second pass (2026-11-01): the STELA homes for the capitalized lanes

The operator asked why `Evidence/`, `Receipts/`, `Resident-Center/` and `Config/` had stayed, directed the extraction of the last two, said yes to the PoT revisions, and asked how STELA files evidence and receipts. STELA's root has no such lanes: proof is a ledger head over write-once leaves under `archives/`, telemetry is `logs/`, and policy that tools read is `ops/etc/`. The tree now follows that.

| From | To | Files | Why |
| --- | --- | --- | --- |
| `Resident-Center` | `archives/legacy/Resident-Center` | 192 | frozen runtime custody; source authority is Projects/Resident-Center (Control decision) |
| `Config` | `archives/legacy/Config` | 1 | the relationship contract the retired drift detector read; Control-bound |
| `archives/legacy/Resident-Center/research/resident-launcher/config/residents.json` | `ops/etc/residents.json` | 1 | copied; the frozen original stays in the archive |
| `archives/legacy/Resident-Center/data/research/resident-launcher/host-bindings.json` | `ops/etc/host-bindings.json` | 1 | copied; the frozen original stays in the archive |
| `ops/lib/scripts/drift.py` | `archives/legacy/drift/drift.py` | 1 | retired with Resident-Center and Config, its only subject |
| `docs/ops/specs/scripts/drift.md` | `archives/legacy/drift/drift.md` | 1 | retired with Resident-Center and Config, its only subject |
| `tools/test/test_drift.py` | `archives/legacy/drift/test_drift.py` | 1 | retired with Resident-Center and Config, its only subject |
| `Receipts` | `archives/receipts` | 306 | write-once records (PoT 1.1.5); STELA keeps receipts as archive leaves |
| `Evidence/ (registry and promotions)` | `ops/etc/` | 2 | authority and decisions read by tools; private, ignored by Git |
| `Evidence/ (machine-written csv, txt, json, log)` | `logs/` | 456 | telemetry (STELA logs/); ignored by Git |
| `Evidence/ (dated markdown notes, capsules, handoffs)` | `archives/legacy/Evidence/` | 31 | records, frozen; ignored by Git as before |

- `ops/lib/scripts/rounds.sh` lost its Resident Center drift step (115 lines): the detector's only subject left the room, and a detector that cannot find its subject forces a critical alert every run.
- Inside the frozen Resident Center, two files are Sessions-operational data, not product: the launcher roster (`config/residents.json`) and the host bindings. `identity.py` and `myself.py` compare the registry against them, so copies now live in `ops/etc/` beside the registry; the frozen originals stay in the archive. The launcher itself runs from the product repository, as the Control decision on source authority says; its path is the operator's wiring.
- PoT Amendment 3, candidate (`storage/PoT-amendment-3.md`): 1.1.1 gains the manifests, 1.1.6 and 1.1.7 are retired, 1.1.12 adds `logs/`, 1.3.5 and 1.3.7 take the new paths. The tree's `PoT.md` carries the candidate text; the text in force stays `archives/PoT-38854647.md` until the ledger records ratification (PoT 7.1, 7.3).
- Rewrites: 87 counted, in 50 tool and document files; records untouched (`archives/receipts/` keeps every receipt's text, including its old `Receipts/` and `Evidence/` paths).
- Measured: 344 passed, 2 skipped, 416 subtests passed in 22.05s; room runner: suites=42 failing=0; help --test: OK: help self-test passed (14/14).; template --test: OK: template self-test passed (18/18)..

## What Control must still do, after this pass

1. Repoint the rounds timer to `ops/lib/scripts/rounds.sh` and the Control CI suites to `tools/test/`.
2. Decide the frozen runtime: the launcher and the Resident Center runtime now serve from `Projects/Resident-Center` or from `archives/legacy/Resident-Center/`; the host bindings and roster at `ops/etc/` are what `identity.py` and `myself.py` read.
3. Retire the Control-side drift contract binding (`Sessions/Config/resident-center-relationship.json` on Control `main`) or re-home it; nothing in this room reads it now.
4. Ratify or amend Amendment 3 (PoT 7.3), then move the Control ignore rules for the registry and the mind leaves to the new paths.
