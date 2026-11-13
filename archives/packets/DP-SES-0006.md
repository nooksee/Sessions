# DP-SES-0006: OPEN: believe only the leaf the packet tool last wrote

- Packet: DP-SES-0006
- Branch: agent/dp-ses-0006-2026-11-13
- Base: commit 9d794898ced7bacb2de51eaca8e9d03d1682101f
- Opened: 2026-11-13T04:00:09Z
- Integrator: session-doctor
- Contractor: claudine-colbert
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: RoR-27, and the two notes in the audit of DP-SES-0005

## Objective

Close the two gaps the Auditor noted in the audit of DP-SES-0005. First, the read-in takes a function from the open packet's leaf only when that leaf is, byte for byte, the one the packet tool last wrote, asked of the packet tool's own reader; otherwise nobody is given a function from it, all four are shown, and the reader is told why. Second, the suite proves that a registry key contained in another key is not that key, in both directions. The suite grows from 76 tests to 79, and the count is corrected wherever it is stated: the test registry, the index and the test specification. The law is not touched, so no OPEN ends. The change is prepared by the tool's writer as storage/intake/DP-SES-open-leaf-and-key.patch; the Contractor applies it in the worktree, reads it, and closes.

## Scope

- ops/bin/open
- docs/ops/specs/binaries/open.md
- tools/test/test_open.py
- docs/ops/specs/tools/test/open.md
- docs/ops/registry/test.md
- docs/INDEX.md

## Gates

- full

## Results

- Closed: 2026-11-13T04:11:04Z
- Contractor: claudine-colbert
- Paths changed: 6
- Deviations: 0
- Tree: tree 33cf87453a77708b0bcebb69534d317bf2b24d61
- Gate: exit 0 in 0 s: tools/test/test_alerts.py
- Gate: exit 0 in 0 s: tools/test/test_alerts_arity.py
- Gate: exit 0 in 0 s: tools/test/test_archive.py
- Gate: exit 0 in 0 s: tools/test/test_bloat.py
- Gate: exit 0 in 0 s: tools/test/test_capsule.py
- Gate: exit 0 in 0 s: tools/test/test_chamber.py
- Gate: exit 0 in 15 s: tools/test/test_closeout.py
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
- Gate: exit 0 in 12 s: tools/test/test_mind.py
- Gate: exit 0 in 0 s: tools/test/test_miner.py
- Gate: exit 0 in 2 s: tools/test/test_myself.py
- Gate: exit 0 in 1 s: tools/test/test_name_counts.py
- Gate: exit 0 in 3 s: tools/test/test_notice.py
- Gate: exit 0 in 4 s: tools/test/test_open.py
- Gate: exit 0 in 32 s: tools/test/test_packet.py
- Gate: exit 0 in 3 s: tools/test/test_prepare.py
- Gate: exit 0 in 0 s: tools/test/test_pressure.py
- Gate: exit 0 in 0 s: tools/test/test_prime.py
- Gate: exit 0 in 1 s: tools/test/test_pycharm.py
- Gate: exit 0 in 12 s: tools/test/test_redact.py
- Gate: exit 0 in 0 s: tools/test/test_reid.py
- Gate: exit 0 in 0 s: tools/test/test_resources.py
- Gate: exit 0 in 0 s: tools/test/test_retention.py
- Gate: exit 0 in 1 s: tools/test/test_ror_join.py
- Gate: exit 0 in 489 s: tools/test/test_rotate.py
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
- Gate: exit 0 in 3 s: ops/bin/template --test

## Narrative

I applied the prepared patch from intake in the packet worktree with git apply and read the change through the packet diff: six paths, all in scope, its lines equal to the patch. The read-in now takes a function from the open packet only when the leaf is, byte for byte, the one the packet tool last wrote, asked of that tool's own intact test; a leaf that parses but was written by another hand, or one with no line in the packet tool's ledger, gives nobody a function, all four rows are shown, and the reader is told why. Three tests are added, proving a forged leaf and an unrecorded leaf give no function and that a key contained in another key is not that key in either direction, and the count moves from seventy-six to seventy-nine in the test registry, the index and the test specification. Before closing I ran the open suite in the worktree: seventy-nine tests passed and it left no file behind. The law is not touched, and I changed no line beyond the patch. Deviations: none.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-13T04:13:15Z
- Tree: tree 33cf87453a77708b0bcebb69534d317bf2b24d61

## Audit note

PASS. The change is the prepared patch and nothing else: its patch-id equals that of the patch in intake. It closes both notes of my audit of DP-SES-0005. First, a leaf now gives a function only when it parses and the packet tool's own intact test says it is the leaf that tool last wrote; otherwise nobody is given a function, all four rows are shown, and the reader is told why. Second, the suite proves that a key contained in another is not that key, in both directions. The specification states the rule and its limit, a hand that changes both the leaf and the private ledger.

On an export of this tree behind my masked runner, the suite passes all seventy-nine at umask 0022 and 0077. Five mutants of my own were each caught by name: the intact test dropped, every leaf believed, the head returned anyway, and a key matched by substring either way. That last was the survivor of my earlier audit. Every count agrees with the suite: seventy-nine in the registry, the index and the test specification, and the seven groups exactly as the classes hold them. The gates are full and all exit 0. The law is not touched, so no OPEN ends. The narrative counts no deviation and describes what the diff shows.
