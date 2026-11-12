# DP-SES-0003: Let a packet scope name a policy snapshot

- Packet: DP-SES-0003
- Branch: agent/dp-ses-0003-2026-11-12
- Base: commit e2c459eca6135cd00bfc679e146cd4e81e0e6633
- Opened: 2026-11-12T21:00:22Z
- Integrator: session-doctor
- Contractor: claudine-colbert
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: RoR-25: a fault in the packet tool is mended by a packet

## Objective

Mend one defect of the packet tool so that a policy amendment can travel as a packet. The leaf's public check holds back any short run of hexadecimal, so open refuses a scope that names a policy snapshot or its authority leaf, whose file names carry the first eight characters of the policy's hash as the authorization check requires. The fix is one pattern in public_problems: a leaf may name a policy snapshot or its authority leaf, and nothing that only resembles one; one test is widened and one added. The change is prepared by the tool's writer as the patch storage/intake/DP-SES-snapshot-names.patch; the Contractor applies it in the worktree, reads what it applied, and closes. The gate will print a NOTICE because the packet changes the tool that judges it; that is expected.

## Scope

- ops/lib/scripts/packet.py
- tools/test/test_packet.py
- docs/ops/specs/scripts/packet.md
- docs/ops/specs/tools/test/packet.md
- docs/ops/registry/test.md
- docs/INDEX.md

## Gates

- full

## Results

- Closed: 2026-11-12T21:16:07Z
- Contractor: claudine-colbert
- Paths changed: 6
- Deviations: 0
- Tree: tree ab2be106a9f6cc4fb73c9830b7fba2b4b0854c45
- Gate: exit 0 in 0 s: tools/test/test_alerts.py
- Gate: exit 0 in 0 s: tools/test/test_alerts_arity.py
- Gate: exit 0 in 0 s: tools/test/test_archive.py
- Gate: exit 0 in 0 s: tools/test/test_bloat.py
- Gate: exit 0 in 0 s: tools/test/test_capsule.py
- Gate: exit 0 in 0 s: tools/test/test_chamber.py
- Gate: exit 0 in 15 s: tools/test/test_closeout.py
- Gate: exit 0 in 0 s: tools/test/test_condense.py
- Gate: exit 0 in 0 s: tools/test/test_conflicts.py
- Gate: exit 0 in 3 s: tools/test/test_constitution.py
- Gate: exit 0 in 0 s: tools/test/test_custody.py
- Gate: exit 0 in 0 s: tools/test/test_dossier.py
- Gate: exit 0 in 0 s: tools/test/test_elide.py
- Gate: exit 0 in 0 s: tools/test/test_estimate.py
- Gate: exit 0 in 1 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: tools/test/test_fingerprint.py
- Gate: exit 0 in 0 s: tools/test/test_gate.py
- Gate: exit 0 in 8 s: tools/test/test_gauge.py
- Gate: exit 0 in 0 s: tools/test/test_history.py
- Gate: exit 0 in 4 s: tools/test/test_identity.py
- Gate: exit 0 in 0 s: tools/test/test_identity_held.py
- Gate: exit 0 in 0 s: tools/test/test_images.py
- Gate: exit 0 in 0 s: tools/test/test_inventory.py
- Gate: exit 0 in 0 s: tools/test/test_items.py
- Gate: exit 0 in 0 s: tools/test/test_janitor.py
- Gate: exit 0 in 0 s: tools/test/test_limits.py
- Gate: exit 0 in 0 s: tools/test/test_media.py
- Gate: exit 0 in 16 s: tools/test/test_mind.py
- Gate: exit 0 in 0 s: tools/test/test_miner.py
- Gate: exit 0 in 3 s: tools/test/test_myself.py
- Gate: exit 0 in 1 s: tools/test/test_name_counts.py
- Gate: exit 0 in 4 s: tools/test/test_notice.py
- Gate: exit 0 in 65 s: tools/test/test_packet.py
- Gate: exit 0 in 6 s: tools/test/test_prepare.py
- Gate: exit 0 in 0 s: tools/test/test_pressure.py
- Gate: exit 0 in 0 s: tools/test/test_prime.py
- Gate: exit 0 in 1 s: tools/test/test_pycharm.py
- Gate: exit 0 in 19 s: tools/test/test_redact.py
- Gate: exit 0 in 0 s: tools/test/test_reid.py
- Gate: exit 0 in 0 s: tools/test/test_resources.py
- Gate: exit 0 in 0 s: tools/test/test_retention.py
- Gate: exit 0 in 2 s: tools/test/test_ror_join.py
- Gate: exit 0 in 670 s: tools/test/test_rotate.py
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

I applied the prepared patch from intake in the packet worktree with git apply and read the change through the packet diff: six paths, all in scope, its lines equal to the patch. The public check of the packet tool now reads the path of a policy snapshot or of its authority leaf under archives with the short hash set aside, so a scope that names them can open, while a name that only resembles one, with another extension, a longer hash, another folder or no folder, is still held back. One leaf test is widened to prove both directions and one open test is added, and the test count in its specification, the registry row and the index moves from ninety to ninety-one. Before closing I ran the packet suite in the worktree: ninety-one tests passed and it left no file behind. I changed no line beyond the patch and did not touch the redaction tool itself. Deviations: none.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-12T21:18:55Z
- Tree: tree ab2be106a9f6cc4fb73c9830b7fba2b4b0854c45

## Audit note

PASS. The change is the prepared patch and nothing else: its patch-id equals that of the patch in intake. One pattern in public_problems rewrites the path of a policy snapshot or its authority leaf to a name without the hash before the redaction check reads the text. The two names are exactly those the authorization check requires, and four such pairs already stand in archives. The spec, the test spec, the registry and the index carry the new count of ninety-one tests, so nothing the objective needs is missing.

I ran the suite on an export of this tree behind my masked runner: ninety-one passed. Of four mutants of my own to the pattern, three were caught by name, by the test that a leaf holds nothing a public record may not. Those mutants dropped the guard before the name, allowed a longer hash, or allowed any extension.

Two notes for a later packet, not conditions. First, dropping the guard after the name breaks no test, though the code is right: a name with a suffix, such as an extra extension, is refused. One near case of that kind would prove it. Second, the exemption takes any eight hexadecimal digits in that path, not only the policy's own hash, so a short run that is not a hash could stand in a leaf in that one form. Binding it to the hash of the policy text in the worktree would make it exact.

The gates fit a code change to the tool: full, every suite and both self-tests, all exit 0. The narrative counts no deviation and describes what the diff shows.
