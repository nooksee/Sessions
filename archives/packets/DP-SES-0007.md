# DP-SES-0007: Rename the roles: Integrator and Contractor

- Packet: DP-SES-0007
- Branch: agent/dp-ses-0007-2026-11-13
- Base: commit d0d00ea886d8ded3a8ffd05879db4bb48f155bc8
- Opened: 2026-11-13T06:23:28Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: The operator's ratification of 2026-11-13 under PoT 7.1 and 7.3, entered by this packet as RoR-28

## Objective

Apply the amendment the operator ratified after the reviews of PoT 7.3: the role of clause 4.1.3 is named Integrator; the role of clause 4.1.4 is named Contractor and takes in the duties of 4.1.5, which is retired; 4.1.11 cites the four roles by clause; and 4.1.4 carries the reviewed words that hold each holder within the scope the operator assigns and give the Integrator's rotation to the Contractor the operator assigns. Change every reader in the same packet (PoT 7.2), from the writer's second prepared patch, applied unchanged: tools, suites, specifications and documents, with a new suite that refuses the earlier names outside the ledger and the archives. Add the snapshot, the authority leaf, their admission lines and the ratification as the last ledger entry, and bring the board to it.

## Scope

- PoT.md
- RoR.md
- NOW.md
- .gitignore
- README.md
- AGENTS.md
- DOCTRINE.md
- var/README.md
- archives/PoT-744238f2.md
- archives/PoT-authority-744238f2.md
- ops/lib/manifests/CONSTRAINTS.md
- ops/lib/scripts/bloat.py
- ops/lib/scripts/closeout.py
- ops/lib/scripts/identity.py
- ops/lib/scripts/items.py
- ops/lib/scripts/prepare.py
- docs/INDEX.md
- docs/MANUAL.md
- docs/START-HERE.md
- docs/ops/README.md
- docs/ops/registry/test.md
- docs/ops/specs/
- docs/reviews/sessions-review-20261105.md
- tools/test/
- ops/src/reports/closeout.md.tpl

## Gates

- full

## Results

- Closed: 2026-11-13T06:35:23Z
- Contractor: session-doctor
- Paths changed: 109
- Deviations: 1
- Tree: tree 14be2dcf798e3992bf9653a736c923d29314e71a
- Gate: exit 0 in 1 s: tools/test/test_alerts.py
- Gate: exit 0 in 0 s: tools/test/test_alerts_arity.py
- Gate: exit 0 in 0 s: tools/test/test_archive.py
- Gate: exit 0 in 0 s: tools/test/test_bloat.py
- Gate: exit 0 in 0 s: tools/test/test_capsule.py
- Gate: exit 0 in 0 s: tools/test/test_chamber.py
- Gate: exit 0 in 17 s: tools/test/test_closeout.py
- Gate: exit 0 in 0 s: tools/test/test_condense.py
- Gate: exit 0 in 0 s: tools/test/test_conflicts.py
- Gate: exit 0 in 2 s: tools/test/test_constitution.py
- Gate: exit 0 in 0 s: tools/test/test_custody.py
- Gate: exit 0 in 0 s: tools/test/test_dossier.py
- Gate: exit 0 in 0 s: tools/test/test_elide.py
- Gate: exit 0 in 0 s: tools/test/test_estimate.py
- Gate: exit 0 in 0 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: tools/test/test_fingerprint.py
- Gate: exit 0 in 0 s: tools/test/test_gate.py
- Gate: exit 0 in 5 s: tools/test/test_gauge.py
- Gate: exit 0 in 0 s: tools/test/test_history.py
- Gate: exit 0 in 3 s: tools/test/test_identity.py
- Gate: exit 0 in 0 s: tools/test/test_identity_held.py
- Gate: exit 0 in 0 s: tools/test/test_images.py
- Gate: exit 0 in 0 s: tools/test/test_inventory.py
- Gate: exit 0 in 0 s: tools/test/test_items.py
- Gate: exit 0 in 0 s: tools/test/test_janitor.py
- Gate: exit 0 in 0 s: tools/test/test_limits.py
- Gate: exit 0 in 0 s: tools/test/test_media.py
- Gate: exit 0 in 11 s: tools/test/test_mind.py
- Gate: exit 0 in 0 s: tools/test/test_miner.py
- Gate: exit 0 in 2 s: tools/test/test_myself.py
- Gate: exit 0 in 1 s: tools/test/test_name_counts.py
- Gate: exit 0 in 3 s: tools/test/test_notice.py
- Gate: exit 0 in 5 s: tools/test/test_open.py
- Gate: exit 0 in 37 s: tools/test/test_packet.py
- Gate: exit 0 in 4 s: tools/test/test_prepare.py
- Gate: exit 0 in 0 s: tools/test/test_pressure.py
- Gate: exit 0 in 0 s: tools/test/test_prime.py
- Gate: exit 0 in 1 s: tools/test/test_pycharm.py
- Gate: exit 0 in 12 s: tools/test/test_redact.py
- Gate: exit 0 in 0 s: tools/test/test_reid.py
- Gate: exit 0 in 0 s: tools/test/test_resources.py
- Gate: exit 0 in 0 s: tools/test/test_retention.py
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 2 s: tools/test/test_ror_join.py
- Gate: exit 0 in 518 s: tools/test/test_rotate.py
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
- Gate: exit 0 in 2 s: ops/bin/template --test

## Narrative

The policy is amended as the operator ratified it after the four reviews of PoT 7.3. The role of clause 4.1.3, until now named Session Continuity Manager, is named Integrator. The role of clause 4.1.4, until now named Assistant, is named Contractor and takes in the duties of clause 4.1.5, until now named Apprentice, which is retired. Clause 4.1.11 cites the four roles by clause. Clause 4.1.4 differs from the first proposal on the Auditor's exact words: each holder works within the scope the operator assigns to it, and the Contractor the operator assigns performs the Integrator's rotation. The readers change in the same packet from the writer's second prepared patch, applied unchanged: the tools, the suites, the specifications and the documents, with a new suite that refuses the three earlier names in every tracked file outside the ledger and the archives. Mine are the four things the authorization check couples to the exact text, which are the snapshot, the authority leaf, their two admission lines and RoR-28 as the last ledger entry, and two board lines. The policy's SHA-256 is the one RoR-28 names, and the authorization check passed on this exact content in a scratch clone before the close. The registry's three role values are not changed here; they follow as their own act. Deviations: 1. The packet's rules allow no Git command by hand but the one apply; I ran clone, apply, add and commit in a scratch clone of my own, which touched no branch of the room, to run the authorization check before closing.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-13T06:55:40Z
- Tree: tree 14be2dcf798e3992bf9653a736c923d29314e71a

## Audit note

PASS, the independent audit of PoT 7.3. The policy holds exactly the four lines: 4.1.3 renamed, 4.1.4 in my reviewed words, 4.1.5 retired with its slot marked, 4.1.11 by clause. The snapshot equals the new policy, and the authority leaf and both admission lines name its hash. RoR-28 equals its private entry line for line, the Words field by digest. It states both things my review required: the two moves on paper and the clause that bounds them, and Control's earlier name left to Control's owner. Of 109 paths, 104 equal the writer's second patch applied on the base, and the rest are the Manager's coupled records and board lines.

I rebuilt this content as a commit on the base in my own scratch clone; its tree is this packet's. The authorization check passes on it, and the packet gate fails only for want of this audit. Behind my masked runner, every suite passes, test_rotate included, and the counts agree with the suites. Of six mutants of my own, five were caught by name. The survivor matches a registry role by substring; the code compares exactly, so a test with a near role would prove it.

Notes for later, not conditions. The Integrator's own rotation card names nobody until the operator's assignment is recorded somewhere a tool can read. The name check refuses one common word in every case, so a generic use can never be written. A board line asks each resident to trim its handoff where an earlier name stands; a handoff's past sections are records and should stay.
