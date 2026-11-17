# DP-SES-0018: Amend the policy: PoT first, RoR, agents and the new seat

- Packet: DP-SES-0018
- Branch: agent/dp-ses-0018-2026-11-16
- Base: commit 2b003b63db72a4d7a9e58cebb172a9df5aee7fbc
- Opened: 2026-11-16T23:17:24Z
- Integrator: session-doctor
- Contractor: joe-codex
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: The operator's ratification of 2026-11-16 under PoT 7.1 and 7.3, words digest 98989136dcd05b31, entered by this packet as RoR-31

## Objective

Apply the amendment the operator ratified on 2026-11-16 under PoT 7.3: PoT.md becomes revision 5, sha256 a315a0e6ec4fe585aef440575692e3ec1f3c17156852215741ef7c6eb47ea134 (storage/active/pot-amendment-20261116/PoT.candidate.md), with its archive copy, its authority record and RoR-31, and every dependent reader its proposal names (proposal.md, sha256 3b75c7657d7435b0) changes with it, including the new preservation map docs/ops/pot-retired.md. The Contractor's brief, with the exact sources and their hashes: storage/active/pot-amendment-20261116/brief-contractor.md (sha256 208f27c73af215ee). Gates full, and test_rounds.py as well.

## Scope

- PoT.md
- RoR.md
- NOW.md
- README.md
- archives/PoT-a315a0e6.md
- archives/PoT-authority-a315a0e6.md
- docs/MANUAL.md
- docs/ops/pot-retired.md
- docs/ops/specs/
- ops/bin/open
- ops/bin/help
- ops/lib/manifests/CONTEXT.md
- ops/lib/manifests/CONSTRAINTS.md
- ops/lib/scripts/closeout.py
- ops/src/scripts/script.py.tpl
- ops/src/reports/
- tools/test/
- .gitignore
- docs/ops/registry/test.md

## Gates

- full

## Amendments

- 2026-11-16T23:45:49Z session-doctor added .gitignore: Contractor's finding, verified: .gitignore line 37 ignores both new archive files, which need allow lines; the test registry holds each suite's test count
- 2026-11-16T23:45:49Z session-doctor added docs/ops/registry/test.md: Contractor's finding, verified: .gitignore line 37 ignores both new archive files, which need allow lines; the test registry holds each suite's test count

## Results

- Closed: 2026-11-16T23:55:35Z
- Contractor: joe-codex
- Paths changed: 35
- Deviations: 0
- Tree: tree 37ca4270039d9cde218e1850357b640adebeed12
- Gate: exit 0 in 0 s: tools/test/test_alerts.py
- Gate: exit 0 in 0 s: tools/test/test_alerts_arity.py
- Gate: exit 0 in 0 s: tools/test/test_archive.py
- Gate: exit 0 in 0 s: tools/test/test_bloat.py
- Gate: exit 0 in 0 s: tools/test/test_capsule.py
- Gate: exit 0 in 0 s: tools/test/test_chamber.py
- Gate: exit 0 in 11 s: tools/test/test_closeout.py
- Gate: exit 0 in 0 s: tools/test/test_condense.py
- Gate: exit 0 in 0 s: tools/test/test_conflicts.py
- Gate: exit 0 in 1 s: tools/test/test_constitution.py
- Gate: exit 0 in 0 s: tools/test/test_custody.py
- Gate: exit 0 in 0 s: tools/test/test_dossier.py
- Gate: exit 0 in 0 s: tools/test/test_elide.py
- Gate: exit 0 in 0 s: tools/test/test_estimate.py
- Gate: exit 0 in 0 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: tools/test/test_fingerprint.py
- Gate: exit 0 in 0 s: tools/test/test_gate.py
- Gate: exit 0 in 3 s: tools/test/test_gauge.py
- Gate: exit 0 in 0 s: tools/test/test_history.py
- Gate: exit 0 in 1 s: tools/test/test_identity.py
- Gate: exit 0 in 0 s: tools/test/test_identity_held.py
- Gate: exit 0 in 0 s: tools/test/test_images.py
- Gate: exit 0 in 0 s: tools/test/test_inventory.py
- Gate: exit 0 in 0 s: tools/test/test_items.py
- Gate: exit 0 in 0 s: tools/test/test_janitor.py
- Gate: exit 0 in 0 s: tools/test/test_limits.py
- Gate: exit 0 in 0 s: tools/test/test_media.py
- Gate: exit 0 in 7 s: tools/test/test_mind.py
- Gate: exit 0 in 0 s: tools/test/test_miner.py
- Gate: exit 0 in 1 s: tools/test/test_myself.py
- Gate: exit 0 in 0 s: tools/test/test_name_counts.py
- Gate: exit 0 in 3 s: tools/test/test_notice.py
- Gate: exit 0 in 2 s: tools/test/test_open.py
- Gate: exit 0 in 37 s: tools/test/test_packet.py
- Gate: exit 0 in 2 s: tools/test/test_prepare.py
- Gate: exit 0 in 0 s: tools/test/test_pressure.py
- Gate: exit 0 in 0 s: tools/test/test_prime.py
- Gate: exit 0 in 0 s: tools/test/test_pycharm.py
- Gate: exit 0 in 8 s: tools/test/test_redact.py
- Gate: exit 0 in 0 s: tools/test/test_reid.py
- Gate: exit 0 in 0 s: tools/test/test_resources.py
- Gate: exit 0 in 0 s: tools/test/test_retention.py
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 0 s: tools/test/test_ror_join.py
- Gate: exit 0 in 261 s: tools/test/test_rotate.py
- Gate: exit 0 in 0 s: tools/test/test_rotation.py
- Gate: exit 0 in 0 s: tools/test/test_rounds.py
- Gate: exit 0 in 0 s: tools/test/test_sandbox.py
- Gate: exit 0 in 0 s: tools/test/test_successor.py
- Gate: exit 0 in 0 s: tools/test/test_tablet.py
- Gate: exit 0 in 0 s: tools/test/test_telemetry.py
- Gate: exit 0 in 0 s: tools/test/test_transcripts.py
- Gate: exit 0 in 0 s: tools/test/test_vitals.py
- Gate: exit 0 in 0 s: tools/test/test_watch.py
- Gate: exit 0 in 0 s: tools/test/test_workers.py
- Gate: exit 0 in 0 s: ops/bin/help --test
- Gate: exit 0 in 1 s: ops/bin/template --test

## Narrative

Applied the ratified policy amendment with its exact snapshot, authority record and corrected ledger append. Updated the preservation map, read-in and role checks, rotation routing, templates and dependent guidance while retaining the common read-in bound. Added only the two named archive exceptions and kept all earlier ledger bytes unchanged under the brief addendum. No registry, host, provider or live-session state was changed.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-17T00:08:07Z
- Tree: tree 37ca4270039d9cde218e1850357b640adebeed12

## Audit note

PASS, bound to tree 37ca4270. PoT.md and its archive equal the candidate that the Auditor passed under PoT 7.3, by SHA-256. RoR.md is main's bytes followed by RoR-31, which carries a words digest only and names the eight ended entries. The preservation map docs/ops/pot-retired.md lists the 44 retired numbers and the heading 6.2; no [Retired] line remains in PoT.md. Every reader in the proposal's list was read in its diff and is carried. Beyond the list, and sound: the open tool binds the map by hash as a fourth law file and refuses an OPEN on a missing or malformed map, with its specification and four tests; Record of Record names RoR in the contracts and help, a name only, consistent with PoT 1.3.2. Measured on a copy equal to the tree: every suite but test_rounds.py, which the Auditor does not run, and both self-tests pass, 56 of 56; the read-in shows the same 23 clauses for every reader and refuses a citation of a retired number; the repeated part is 7824 bytes against 7875; the constitution check passes on the base and this tree. Findings 0, deviations 0.
