# DP-SES-0015: Map and board: the custody disks as they now stand

- Packet: DP-SES-0015
- Branch: agent/dp-ses-0015-2026-11-14
- Base: commit ab7eb5ca33cb2e95f9aecb099921b3cc064d0a78
- Opened: 2026-11-14T00:40:26Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claudine-colbert
- Orchestrator: jo-hamming
- Authority: RoR-25 (the board states the measured present) and PoT 5.3.3; the acting Auditor by RoR-29

## Objective

The map, the board, the manual and the custody specification still say that the third custody root sits on a failing drive whose replacement is pending. Measured on 2026-11-13: the device at that root is a 6 TB drive of another make, mounted for writing, and the failing drive is no longer attached to the host. Bring those four readers to the measured state: name the three roots and the device each stands on, say that the failing drive was replaced and which rulings of the operator count the second and third roots, and keep the interim copies on the boot drive as what they are, copies of the earlier batches. Claim nothing that was not measured: no statement that every batch is on every root.

## Scope

- NOW.md
- docs/ops/README.md
- docs/MANUAL.md
- docs/ops/specs/scripts/custody.md

## Gates

- help
- template
- role_names
- filing

## Results

- Closed: 2026-11-14T00:43:22Z
- Contractor: session-doctor
- Paths changed: 4
- Deviations: 1
- Tree: tree c77fda9b66b0948bf510b01d744854072728150c
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 5 s: ops/bin/template --test
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 1 s: tools/test/test_filing.py

## Narrative

Four readers said the third custody root sat on a failing drive with its replacement pending. Measured on 2026-11-13 from the block device list and the mounts: the three roots stand on three devices, the third is a 6 TB drive of another make mounted for writing, and no drive of the failing make is attached. The board, the map, the manual and the custody specification now say that, name the two rulings of the operator that count the second and third roots, and keep the interim copies on the boot drive as copies of the earlier batches. The map also says what was counted on that day, 90, 18 and 47 batch folders on the three roots, so that no reader takes three roots to mean every batch on each. The date of the replacement and the two rulings are taken from the Integrator's own record of 2026-11-08 and 2026-11-11, not measured today. The Auditor is the acting holder of RoR-29.
The acting Auditor failed the first tree on one count: the first root holds 92 entries, of which 90 are batch folders and two are loose files; the map and this narrative had said 92 batch folders. Corrected; the miscount was the Contractor's and is the one deviation counted.

## Audit

- Verdict: PASS
- Auditor: claudine-colbert
- Audited: 2026-11-14T00:43:44Z
- Tree: tree c77fda9b66b0948bf510b01d744854072728150c

## Audit note

The finding of my first audit is closed. Against the tree I failed, only the map's custody row changed, in one phrase: the three roots held 90, 18 and 47 batch folders, the first also holding two loose files. I recounted by type on all three roots and found the same: 90, 18 and 47 folders, and two, none and none loose files. The narrative says the same and counts the miscount as the Contractor's one deviation. The rest stands as my first audit read it: the devices and mounts as measured, no drive of the failing make attached, and the two dated claims taken from the Integrator's record supported by it and by the board on main. Verdict PASS.
