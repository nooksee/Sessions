# DP-SES-0019: myself: CC GUI's permission key is not a Claude caller

- Packet: DP-SES-0019
- Branch: agent/dp-ses-0019-2026-11-24
- Base: commit 93e361403080aca5e1a44685ae766b03c85b28ca
- Opened: 2026-11-24T06:47:14Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: The operator's go of 2026-11-24 in the Integrator's window, recorded in the Integrator's handoff, digest 91f43cdd

## Objective

myself.py reads CLAUDE_SESSION_ID as a Claude caller signal. On this host only the CC GUI plugin's ai-bridge daemon sets it, as its own permission key, and it reaches every command a Codex resident runs in CC GUI. So each Codex resident there reads FAIL-CLOSED although its codex signal and its registry row agree. Retire that one entry of the environment signal map. CLAUDE_CODE_SESSION_ID stays the Claude environment signal, and the process ancestry stays the authority, so the leg can only become stricter. Add tests: a codex caller beside a CC GUI permission key passes, and CLAUDE_SESSION_ID alone is no signal. Correct the spec line.

## Scope

- ops/lib/scripts/myself.py
- tools/test/test_myself.py
- docs/ops/specs/scripts/myself.md

## Gates

- full

## Results

- Closed: 2026-11-24T15:14:17Z
- Contractor: session-doctor
- Paths changed: 3
- Deviations: 0
- Tree: tree 707144b75db8f22c50c5504e87c97d119fee5a94
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
- Gate: exit 0 in 40 s: tools/test/test_packet.py
- Gate: exit 0 in 2 s: tools/test/test_prepare.py
- Gate: exit 0 in 0 s: tools/test/test_pressure.py
- Gate: exit 0 in 0 s: tools/test/test_prime.py
- Gate: exit 0 in 0 s: tools/test/test_pycharm.py
- Gate: exit 0 in 9 s: tools/test/test_redact.py
- Gate: exit 0 in 0 s: tools/test/test_reid.py
- Gate: exit 0 in 0 s: tools/test/test_resources.py
- Gate: exit 0 in 0 s: tools/test/test_retention.py
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 1 s: tools/test/test_ror_join.py
- Gate: exit 0 in 284 s: tools/test/test_rotate.py
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

Removed CLAUDE_SESSION_ID from the environment signal map in ops/lib/scripts/myself.py, with a comment that says why. On this host only the CC GUI plugin's bridge sets that variable, as its own permission key, and it reached every command a Codex resident ran there, so the caller leg recorded a finding and the result failed closed although the codex signal and the registry row agreed. The change never alters which identity resolves, since an accepted value always had to equal a Claude ancestor's own identifier; it only stops a key that names no session from being reported as a finding, so the leg is more permissive in exactly that case. Three tests were added to tools/test/test_myself.py, and each fails against the base myself.py and passes now: a codex caller beside a plugin permission key passes, CLAUDE_SESSION_ID alone is no signal and is not named in the finding, and a Claude caller still resolves from its ancestry beside the plugin key. The spec line in docs/ops/specs/scripts/myself.md says the variable is not read and why. This rework answers the audit's two findings on the first close. There are no deviations.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-24T15:15:42Z
- Tree: tree 707144b75db8f22c50c5504e87c97d119fee5a94

## Audit note

PASS. Read by difference from the tree that failed: only the myself.py comment and one test assertion changed, and the spec is unchanged. The code is unchanged apart from the comment, by an AST comparison.
F1 is answered: the comment and the narrative now say the change never alters which identity resolves and makes the leg more permissive in one case only. That matches the measure on the suite's fixtures.
F2 is answered: the test now asserts that the caller detail does not name CLAUDE_SESSION_ID. All three new tests fail against the base myself.py, and the myself suite runs 96 of 96 on my copy of the rework. The leaf records 57 of 57 gates exit 0.
Note, not a condition: the comment's last clause names the observed key. More exactly, any CLAUDE_SESSION_ID value that the ancestry does not corroborate is no longer reported. The comment opens by saying the variable is not read, so no reader is misled.
