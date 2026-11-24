# DP-SES-0020: Runbook: CC GUI, the settings continuity relies on

- Packet: DP-SES-0020
- Branch: agent/dp-ses-0020-2026-11-24
- Base: commit 18f2e82b4f57c01ae1b0b5393b6277cb36713e14
- Opened: 2026-11-24T18:04:25Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: The operator's go of 2026-11-24 in the Integrator's window, recorded in the Integrator's handoff, digest d8361f6b

## Objective

Add RUNBOOK-05, a page for the CC GUI plugin, the operator's surface for the Codex residents since JetBrains AI Chat was removed. It records each setting continuity relies on, where it lives, its value, why, and who may change it; what the plugin is measured to do that bears on residents; and the re-check after any update, ending with one resident's identity check. Settings stay off-repo; what must not be published, the identity-check prompt and a masked snapshot, stays in a private kit the page names. Register the page in the runbook registry and list it in the docs index. One page per program: this page borrows nothing from another.

## Scope

- docs/ops/specs/runbook/ccgui.md
- docs/ops/registry/runbook.md
- docs/INDEX.md
- ops/src/runbook/ccgui/
- docs/MANUAL.md

## Gates

- filing
- help

## Amendments

- 2026-11-24T18:09:47Z session-doctor added ops/src/runbook/ccgui/: The operator noted the room keeps runbook working parts in ops/src/runbook; the public prompt and the re-check baseline go there, unpublishable items stay private
- 2026-11-24T18:16:00Z session-doctor added docs/MANUAL.md: The manual's label section still places Codex titles in PyCharm AI Chat, removed on 2026-11-24; the line moves to CC GUI and points to RUNBOOK-05

## Results

- Closed: 2026-11-24T19:56:39Z
- Contractor: session-doctor
- Paths changed: 6
- Deviations: 0
- Tree: tree 9e0aedfa10029b901182741aaba1f38bc01dd463
- Gate: exit 0 in 0 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: ops/bin/help --test

## Narrative

Added docs/ops/specs/runbook/ccgui.md as RUNBOOK-05, a page for the CC GUI plugin, the operator's surface for the Codex residents. It records, panel by panel, each setting continuity relies on with its value, reason and owner; what the plugin was measured to do that bears on residents; and an eight-step re-check after an update that ends with one resident's identity check. On the operator's note, the working parts sit in the runbook home, ops/src/runbook/ccgui/, with one-word names under the page's one-word name: baseline.json, the values the re-check compares against, and prompts.json, the operator's four global prompts in the Prompt Library's export format, each keeping the saved prompt's id so that an import choosing Overwrite replaces it in place. The room is written in the map's convention and the operator is named by role. After the first PASS the operator found that the page kept a private kit of tool state in storage, which PoT 1.1.4 excludes, and that the prompts named him; the page now names no kit, nothing is kept in storage, and the prompts name the role. The Wake check also asks for each check line that does not read PASS and for the path looked at when a handoff is absent, and Packet status gives the field guide's full path. The second audit found an export time no clock gave, now the file's own write time, and a login check with no recorded values, now the login file's size, time and mode, read by stat. A review on the pull request found that re-check step 2 named a notify entry that section 2 did not hold, and the Contractor found the approval entry missing the same way; section 2 and the baseline now hold both, as measured, and section 4 names the login mode as step 2 does. The manual now places Codex titles in CC GUI, keeping PyCharm AI Chat as history. The registry and the docs index list the page and its parts. The scope was amended twice. No setting was changed and no code was touched. There are no deviations.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-24T19:57:45Z
- Tree: tree 9e0aedfa10029b901182741aaba1f38bc01dd463

## Audit note

PASS. Read by difference from the tree that failed: in the page, only the last sentence of section 4 changed, and it now names the login file's size, time and mode, as step 2 and baseline.json do; every other file carries the same content. F1 is answered: the narrative now credits the review with the notify entry and the Contractor with the approval entry, which is what the review comment and its summary show. The two shortened narrative sentences stay true: the manual places Codex titles in CC GUI and keeps PyCharm AI Chat as history, and the registry row and the docs index list the page and both parts. N1 is answered. The leaf's objective, scope, gates and amendments are unchanged. Both gates pass on a fresh copy, and the narrative is accurate.
