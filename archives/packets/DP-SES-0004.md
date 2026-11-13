# DP-SES-0004: Amend the policy: mind, functions and the packet route

- Packet: DP-SES-0004
- Branch: agent/dp-ses-0004-2026-11-12
- Base: commit aa33c50675e7d50c18026649f02f5cac54e03061
- Opened: 2026-11-12T22:21:43Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: The operator's ratification of 2026-11-12 under PoT 7.1 and 7.3, entered by this packet as RoR-26

## Objective

Apply the amendment to the policy that the operator ratified after the reviews of PoT 7.3: four clauses changed (1.2.10, 4.1.7, 4.2.4, 6.1.4) and two added (4.1.10, 4.1.11), so that the policy states the pointer-first mind, the Orchestrator, the four delivery functions and the packet route, with the two sentences the reviewers changed. Change the dependent readers in the same packet (PoT 7.2): the constraints, the instruction file, the manual, the packet and mind specifications, the field guide, and the loop line of help with its specification. Add what the authorization check couples to the exact text: the snapshot, the authority leaf, their two admission lines, and the ratification as the last ledger entry. Bring the board's lines to the amended policy.

## Scope

- PoT.md
- RoR.md
- NOW.md
- .gitignore
- archives/PoT-db1586ff.md
- archives/PoT-authority-db1586ff.md
- ops/lib/manifests/CONSTRAINTS.md
- CLAUDE.md
- docs/MANUAL.md
- docs/ops/specs/scripts/packet.md
- docs/ops/specs/scripts/mind.md
- docs/ops/specs/runbook/shipping.md
- ops/bin/help
- docs/ops/specs/binaries/help.md

## Gates

- full

## Results

- Closed: 2026-11-12T22:35:27Z
- Contractor: session-doctor
- Paths changed: 14
- Deviations: 1
- Tree: tree a8ccb32ac8d5bd4a3f3d4ec9b903ebafd7d556e7
- Gate: exit 0 in 1 s: tools/test/test_alerts.py
- Gate: exit 0 in 0 s: tools/test/test_alerts_arity.py
- Gate: exit 0 in 0 s: tools/test/test_archive.py
- Gate: exit 0 in 0 s: tools/test/test_bloat.py
- Gate: exit 0 in 0 s: tools/test/test_capsule.py
- Gate: exit 0 in 0 s: tools/test/test_chamber.py
- Gate: exit 0 in 24 s: tools/test/test_closeout.py
- Gate: exit 0 in 0 s: tools/test/test_condense.py
- Gate: exit 0 in 1 s: tools/test/test_conflicts.py
- Gate: exit 0 in 5 s: tools/test/test_constitution.py
- Gate: exit 0 in 0 s: tools/test/test_custody.py
- Gate: exit 0 in 0 s: tools/test/test_dossier.py
- Gate: exit 0 in 0 s: tools/test/test_elide.py
- Gate: exit 0 in 0 s: tools/test/test_estimate.py
- Gate: exit 0 in 1 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: tools/test/test_fingerprint.py
- Gate: exit 0 in 0 s: tools/test/test_gate.py
- Gate: exit 0 in 7 s: tools/test/test_gauge.py
- Gate: exit 0 in 0 s: tools/test/test_history.py
- Gate: exit 0 in 5 s: tools/test/test_identity.py
- Gate: exit 0 in 0 s: tools/test/test_identity_held.py
- Gate: exit 0 in 0 s: tools/test/test_images.py
- Gate: exit 0 in 0 s: tools/test/test_inventory.py
- Gate: exit 0 in 0 s: tools/test/test_items.py
- Gate: exit 0 in 0 s: tools/test/test_janitor.py
- Gate: exit 0 in 0 s: tools/test/test_limits.py
- Gate: exit 0 in 0 s: tools/test/test_media.py
- Gate: exit 0 in 20 s: tools/test/test_mind.py
- Gate: exit 0 in 0 s: tools/test/test_miner.py
- Gate: exit 0 in 3 s: tools/test/test_myself.py
- Gate: exit 0 in 2 s: tools/test/test_name_counts.py
- Gate: exit 0 in 4 s: tools/test/test_notice.py
- Gate: exit 0 in 68 s: tools/test/test_packet.py
- Gate: exit 0 in 6 s: tools/test/test_prepare.py
- Gate: exit 0 in 0 s: tools/test/test_pressure.py
- Gate: exit 0 in 0 s: tools/test/test_prime.py
- Gate: exit 0 in 2 s: tools/test/test_pycharm.py
- Gate: exit 0 in 21 s: tools/test/test_redact.py
- Gate: exit 0 in 0 s: tools/test/test_reid.py
- Gate: exit 0 in 0 s: tools/test/test_resources.py
- Gate: exit 0 in 0 s: tools/test/test_retention.py
- Gate: exit 0 in 2 s: tools/test/test_ror_join.py
- Gate: exit 0 in 576 s: tools/test/test_rotate.py
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

The policy is amended as the operator ratified it after the four reviews of PoT 7.3: clauses 1.2.10, 4.1.7, 4.2.4 and 6.1.4 changed, and 4.1.10 and 4.1.11 added, so that it states the pointer-first mind, the Orchestrator, the four delivery functions and the packet route. Two sentences differ from the proposal, on the reviewers' exact words: 4.2.4 says the mind tool works under the mind contract, and 6.1.4 says that no change takes another route and that the packet contract states the limits of its enforcement. Each was changed so the policy does not claim an enforcement a tool does not have. The proposer's patch was applied for the readers; two of its sentences were narrowed to the policy's clause, in the constraints and in the mind specification, because the mind tool's screen refuses a contract's clause number. The loop line of help and its specification no longer place the operator's yes before the mind. The snapshot and the authority leaf are added under archives with their two admission lines, and RoR-26 is the last ledger entry; it records one textual safeguard retired as RoR-22 directed and one added. The board's lines follow. The policy's SHA-256 is the one RoR-26 names, and the authorization check passed on this exact content in a scratch clone before the close. Not adopted: the Auditor's three advisories. Deviations: 1. The packet's rules allow no Git command by hand; I ran clone, apply, add and commit in a scratch clone of my own, which touched no branch of the room, to run the authorization check before closing.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-12T22:37:48Z
- Tree: tree a8ccb32ac8d5bd4a3f3d4ec9b903ebafd7d556e7

## Audit note

PASS, the independent audit of PoT 7.3. The policy text is the ratified one as the Manager relays it: four clauses changed and two added, with the 6.1.4 sentence word for word as my review gave it and 4.2.4 without the claim that a tool enforces the contract; nothing else in the policy moved. The snapshot equals the new policy byte for byte, and its name and the authority leaf carry the first eight characters of the policy's own SHA-256. RoR-26 equals its private source line for line, with the Words field by digest only, and that digest is the one the authority leaf names. The ledger only grows. RoR-26 names the retired safeguard and the added one as my review asked.

I rebuilt this exact content as a commit on the base in a scratch clone of my public mirror: its tree without the leaf is this packet's tree. On it the authorization check passes, and the packet gate fails only for want of this audit. The readers equal the proposer's patch except the two sentences narrowed to the policy's clause, as my review asked; the help loop line and its spec now put the operator's go on the rotation. On the same rebuilt tree, help, template, constitution, name counts, filing, ror_join and mind all pass. The recorded full gates all exit 0.

Nothing lies outside the objective. The deviation counted, the Contractor's own scratch commits to run the authorization check, touched no branch of the room.
