# DP-SES-0002: Add the field guide to shipping

- Packet: DP-SES-0002
- Branch: agent/dp-ses-0002-2026-11-12
- Base: commit b117d6426b6ce399575477cac2f5d758244c44a3
- Opened: 2026-11-12T19:39:25Z
- Integrator: session-doctor
- Contractor: claudine-colbert
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: RoR-25

## Objective

Land the field guide to shipping as the runbook docs/ops/specs/runbook/shipping.md, with its registry row and the pointers to it from the index, the manual, the start page and the two instruction files, so that every resident who may carry a function in a packet reads one maintained guide. The change is prepared as the patch storage/intake/DP-SES-0002-field-guide.patch, written by the port's writer and run through the tool on the corrected main; the Contractor applies it in the worktree with git apply, reads what it applied, and closes. Nothing beyond the seven named paths changes.

## Scope

- docs/ops/specs/runbook/shipping.md
- docs/ops/registry/runbook.md
- docs/INDEX.md
- docs/MANUAL.md
- docs/START-HERE.md
- AGENTS.md
- CLAUDE.md

## Gates

- help
- template
- filing

## Results

- Closed: 2026-11-12T20:03:16Z
- Contractor: claudine-colbert
- Paths changed: 7
- Deviations: 0
- Tree: tree 39da28fdf1a5212cf6cf7ed6fb159e386254888c
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 3 s: ops/bin/template --test
- Gate: exit 0 in 1 s: tools/test/test_filing.py

## Narrative

This close answers the one finding the review connector left on the pull request, on the field guide's paragraph about stopping a packet. The finding was right: the paragraph said the Integrator runs abandon, but the tool refuses the Integrator once the packet branch is on origin and then requires the Orchestrator or another resident with a recorded fallback. I replaced that one paragraph in docs/ops/specs/runbook/shipping.md with the operator's wording, which says who abandons before the branch is pushed and who abandons after, and that either way the work is kept as a patch. No other line of the guide and no other path changed since the last close. Deviations: none.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-12T20:05:32Z
- Tree: tree 39da28fdf1a5212cf6cf7ed6fb159e386254888c

## Audit note

PASS. Since the tree I passed before, one line changed, the paragraph on stopping a packet in the runbook; nothing else in the seven paths moved. The new wording matches the tool: abandon is the Integrator's while the branch is not on origin, and once it is, the Orchestrator's, or another registered resident's with a recorded fallback reason. That answers the review connector's finding on pull request #94, which has an accepting reply on its thread.

My earlier PASS missed that error; the connector found it. I count it against my own read.

The gates fit, and all three exited 0 again on an export of this exact tree. The narrative counts no deviation and describes what the diff shows.

For a later packet, not a condition: the guide's refusal table still sends the Integrator to abandon when origin/main moved under an open packet. That holds when the move is found before the push, which is the usual case; after the push, the tool refuses the Integrator and names the Orchestrator. The spec's recovery table has the same row, so both could name the Orchestrator once the branch is on origin.
