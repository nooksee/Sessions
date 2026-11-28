# DP-SES-0024: Tools name no place that the parent's move removed

- Packet: DP-SES-0024
- Branch: agent/dp-ses-0024-2026-11-27
- Base: commit 35f55af07c19cfe8bbb1cfd690bcfa4b94d06cc1
- Opened: 2026-11-27T19:20:36Z
- Integrator: session-doctor
- Contractor: joe-codex
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: The operator's word of 2026-11-27 in the Integrator's window, kept in the Integrator's handoff, digest d0009d6c

## Objective

Three findings of the house check of 2026-11-27, each a tool that names a place the parent's reorganisation removed, are made right in the room. The rounds wrapper stops carrying Control's drift signal: it called an absolute path in a folder that is gone, and Control's own library now holds the detector and a wrapper that calls it. The second live Codex folder, a VM share that left the host's live tree, leaves the four tools that named it: gauge, alerts, telemetry and watch. The capsule tool is anchored on the room and names canon files that exist there, in place of the parent's old layout. Each tool's spec, suite, suite spec and registry rows follow in the same packet. History is not edited.

## Scope

- ops/lib/scripts/rounds.sh
- docs/ops/specs/scripts/rounds.md
- tools/test/test_rounds.py
- docs/ops/specs/tools/test/rounds.md
- ops/lib/scripts/gauge.py
- ops/lib/scripts/alerts.py
- ops/lib/scripts/telemetry.py
- ops/lib/scripts/watch.py
- docs/ops/specs/scripts/gauge.md
- docs/ops/specs/scripts/alerts.md
- docs/ops/specs/scripts/telemetry.md
- docs/ops/specs/scripts/watch.md
- tools/test/test_gauge.py
- tools/test/test_alerts.py
- tools/test/test_telemetry.py
- tools/test/test_watch.py
- tools/test/test_fingerprint.py
- docs/ops/specs/tools/test/gauge.md
- ops/lib/scripts/capsule.py
- docs/ops/specs/scripts/capsule.md
- tools/test/test_capsule.py
- docs/ops/registry/scripts.md
- docs/ops/registry/test.md
- docs/INDEX.md
- tools/test/test_name_counts.py
- docs/ops/specs/scripts/fingerprint.md
- NOW.md
- docs/ops/specs/runbook/port.md

## Gates

- full

## Amendments

- 2026-11-27T19:37:03Z session-doctor added docs/INDEX.md: The index describes rounds as carrying the Control source-drift wrapper, lists a drift entry, and describes the capsule tool; those lines follow the three tools.
- 2026-11-27T21:25:18Z session-doctor added tools/test/test_name_counts.py: The suite holds an exact count of host-name lines per file; its rows for gauge.py and rounds.sh count the two lines this packet removes, so the rows follow or the full gate fails.
- 2026-11-27T21:25:25Z session-doctor added docs/ops/specs/scripts/fingerprint.md: Its status line names alerts, telemetry and watch as readers through volume_root, used only for the removed folder, and says the drift step keeps its path; both follow the change.
- 2026-11-27T21:25:25Z session-doctor added NOW.md: The board's rounds line says the wrapper names a Control detector whose folder is gone; on landing that is no longer so, and the board says the present.
- 2026-11-27T21:25:25Z session-doctor added docs/ops/specs/runbook/port.md: The port runbook says the drift step stayed in the wrapper; a dated addition says it left on 2026-11-27. The record of the port itself is not rewritten.

## Results

- Closed: 2026-11-28T17:18:27Z
- Contractor: joe-codex
- Paths changed: 28
- Deviations: 0
- Tree: tree 1db36ef2e374a88f5ee61f000e19f9289c83f24f
- Gate: exit 0 in 0 s: tools/test/test_alerts.py
- Gate: exit 0 in 0 s: tools/test/test_alerts_arity.py
- Gate: exit 0 in 0 s: tools/test/test_archive.py
- Gate: exit 0 in 0 s: tools/test/test_bloat.py
- Gate: exit 0 in 0 s: tools/test/test_capsule.py
- Gate: exit 0 in 0 s: tools/test/test_chamber.py
- Gate: exit 0 in 12 s: tools/test/test_closeout.py
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
- Gate: exit 0 in 4 s: tools/test/test_gauge.py
- Gate: exit 0 in 0 s: tools/test/test_history.py
- Gate: exit 0 in 2 s: tools/test/test_identity.py
- Gate: exit 0 in 0 s: tools/test/test_identity_held.py
- Gate: exit 0 in 0 s: tools/test/test_images.py
- Gate: exit 0 in 0 s: tools/test/test_inventory.py
- Gate: exit 0 in 0 s: tools/test/test_items.py
- Gate: exit 0 in 0 s: tools/test/test_janitor.py
- Gate: exit 0 in 0 s: tools/test/test_limits.py
- Gate: exit 0 in 0 s: tools/test/test_media.py
- Gate: exit 0 in 8 s: tools/test/test_mind.py
- Gate: exit 0 in 0 s: tools/test/test_miner.py
- Gate: exit 0 in 1 s: tools/test/test_myself.py
- Gate: exit 0 in 0 s: tools/test/test_name_counts.py
- Gate: exit 0 in 3 s: tools/test/test_notice.py
- Gate: exit 0 in 2 s: tools/test/test_open.py
- Gate: exit 0 in 48 s: tools/test/test_packet.py
- Gate: exit 0 in 3 s: tools/test/test_prepare.py
- Gate: exit 0 in 0 s: tools/test/test_pressure.py
- Gate: exit 0 in 0 s: tools/test/test_prime.py
- Gate: exit 0 in 0 s: tools/test/test_pycharm.py
- Gate: exit 0 in 10 s: tools/test/test_redact.py
- Gate: exit 0 in 0 s: tools/test/test_reid.py
- Gate: exit 0 in 0 s: tools/test/test_resources.py
- Gate: exit 0 in 0 s: tools/test/test_retention.py
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 1 s: tools/test/test_ror_join.py
- Gate: exit 0 in 305 s: tools/test/test_rotate.py
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

The room rounds wrapper reports patient health without an external detector, and the four live-store defaults no longer name the retired VM share. Capsule generation is anchored on room canon; the gauge was changed by the packet Contractor under the operator direction, which also ended the former external drift binding. Audit rework corrects the index and registry entries and all three nits. PR review rework corrects telemetry guidance and states in the gauge specification and option help that explicit live roots replace the host default and drop the archived default unless archived roots are also supplied. No host file, service, timer or historical record was changed. Protocol deviations: none.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-28T17:21:06Z
- Tree: tree 1db36ef2e374a88f5ee61f000e19f9289c83f24f

## Audit note

PASS. Auditor claude-bernard, by difference from the tree I failed this morning. Read: the two files that changed, against my copy of that tree.
F1 answered: gauge.md line 37 now says that --codex-root replaces the host live-root default and drops the archived default unless --codex-archived-root is also given, and that --codex-archived-root replaces the archived default. gauge.py lines 466 and 467 do exactly that and are unchanged; only the two help strings changed, and they say the same.
Gates: the leaf records 57 of 57 at exit 0; on a copy of this tree test_gauge, test_name_counts, test_filing, test_fingerprint and help --test pass.
Audit rounds of this packet, kept here because the leaf keeps only the last: FAIL, then PASS on the second tree, FAIL on the third, and this PASS on the fourth.
