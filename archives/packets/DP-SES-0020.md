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

- Closed: 2026-11-24T19:01:32Z
- Contractor: session-doctor
- Paths changed: 6
- Deviations: 0
- Tree: tree 2009a188a56e2aa8affc4f4c964dfa456c7e5bc6
- Gate: exit 0 in 0 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: ops/bin/help --test

## Narrative

Added docs/ops/specs/runbook/ccgui.md as RUNBOOK-05, a page for the CC GUI plugin, the operator's surface for the Codex residents. It records, panel by panel, each setting continuity relies on with its value, reason and owner; what the plugin was measured to do that bears on residents; and an eight-step re-check after an update that ends with one resident's identity check. On the operator's note, the working parts sit in the runbook home, ops/src/runbook/ccgui/, with one-word names under the page's one-word name: baseline.json, the values the re-check compares against, and prompts.json, the operator's four global prompts in the Prompt Library's export format, each keeping the saved prompt's id so that an import choosing Overwrite replaces it in place. The room is written in the map's convention and the operator is named by role. After the first PASS the operator found two faults. The page kept a private kit of tool state in storage, which PoT 1.1.4 excludes; it now names no kit and nothing is kept there. The prompts named the operator; they now name the role. The Wake check also asks for each check line that does not read PASS and for the path looked at when a handoff is absent, and Packet status gives the field guide's full path; the other two differ from the saved prompts only by the role. The second audit found an export time no clock gave, now the file's own write time, and a login check with no recorded values; baseline.json now holds the login file's size, time and mode, read by stat. The first audit's finding stays answered: the prompts are saved in the library, and the page names no export. The manual's label section now places Codex titles in CC GUI, keeping PyCharm AI Chat, removed the same day, as history. The runbook registry has a RUNBOOK-05 row, and the docs index lists the page and both parts. The scope was amended twice, for that folder and for the manual. No setting was changed and no code was touched. There are no deviations.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-24T19:02:25Z
- Tree: tree 2009a188a56e2aa8affc4f4c964dfa456c7e5bc6

## Audit note

PASS. Read by difference from the tree that failed: only the export time, the login entry and the note in baseline.json, and the wording of re-check step 2 changed. F1 is answered: the export time now equals the file's own write time to the second. F2 is answered: baseline.json records the login file's size, time and mode, and a stat of the file, which never opens it, gives the same values; step 2 now compares against them and says how they are replaced after a new login. Both gates pass on my copy, and the narrative is accurate. A note, not a condition: step 2 names the time and size, while the baseline also checks the mode.
