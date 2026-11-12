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

- Closed: 2026-11-12T19:46:01Z
- Contractor: claudine-colbert
- Paths changed: 7
- Deviations: 0
- Tree: tree 5b4c292d8b4f9bb741e0bfe537f4168d82f8d477
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 5 s: ops/bin/template --test
- Gate: exit 0 in 1 s: tools/test/test_filing.py

## Narrative

I applied the prepared field-guide patch from intake in the packet worktree with git apply, then read the change through the packet diff: seven paths, all in scope, 208 lines added and 1 removed. The new runbook docs/ops/specs/runbook/shipping.md is byte for byte the guide held in intake; RUNBOOK-04 registers it, and the index, the manual, the start page and the two instruction files each gain one pointer to it, so a resident who may carry a function finds one maintained guide from every door. Before applying, I ran a close on purpose with nothing changed, and the tool refused it because nothing in scope had changed, as the onboarding asked. I edited nothing beyond the seven named paths, altered no text of the patch, and ran no suite outside the gates this close runs. Deviations: none.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-12T19:50:33Z
- Tree: tree 5b4c292d8b4f9bb741e0bfe537f4168d82f8d477

## Audit note

PASS. The change is the prepared patch and nothing else: its patch-id equals that of the patch in intake, and the new runbook docs/ops/specs/runbook/shipping.md is byte for byte the guide held in intake, which I read whole before this packet opened. Seven paths, all in scope, 208 lines added and 1 removed.

Each door gains one pointer and says the same thing: AGENTS.md extends its sentence on the packet spec; CLAUDE.md, the manual and the start page each add one short paragraph or line; the index adds one entry; the runbook registry adds RUNBOOK-04, the next free number after 01 to 03, naming the tool and the contract. The guide's own header names that registry entry, so the two agree. The objective needs nothing more.

The gates fit a document-only change: help, template and filing. I ran all three again on an export of this exact tree, and each exited 0. The narrative counts no deviation and describes what the diff shows.
