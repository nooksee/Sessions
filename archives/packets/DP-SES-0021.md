# DP-SES-0021: Prompts: the change cycle, the manual, help's curriculum

- Packet: DP-SES-0021
- Branch: agent/dp-ses-0021-2026-11-24
- Base: commit afa09e2ee0dd788b82b6ba03dc46b55dc68ecade
- Opened: 2026-11-24T20:11:35Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: The operator's go of 2026-11-24 in the Integrator's window, recorded in the Integrator's handoff, digest 0e0b94c6

## Objective

Make spec, help and manual describe the operator's prompts as they are used. RUNBOOK-05 section 4 gains the change cycle agreed on 2026-11-24: export first into scratch, the master changes only by packet, a copy with the room's path is imported with Overwrite, a second export is compared. Section 3 gains the measured fact that an exclamation mark in the plugin's input opens the prompts. The manual gains the operator's prompts beside the operator's card, and its closeout section names the Closeout card prompt. help's curriculum mode, a placeholder since the port, is built from the canonical sources, with a self-test case that it names every prompt in prompts.json and holds no placeholder. The help spec, the binaries registry row and the manual's help note follow.

## Scope

- docs/ops/specs/runbook/ccgui.md
- docs/MANUAL.md
- ops/bin/help
- docs/ops/specs/binaries/help.md
- docs/ops/registry/binaries.md

## Gates

- filing
- help

## Results

- Closed: 2026-11-24T20:44:37Z
- Contractor: session-doctor
- Paths changed: 5
- Deviations: 0
- Tree: tree 6601f1e87b146ac42b4adf6a8c89d646f8dbf7b2
- Gate: exit 0 in 0 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: ops/bin/help --test

## Narrative

Spec, help and manual now describe the operator's prompts as they are used. RUNBOOK-05 section 4 names prompts.json as the master and the Prompt Library as its copy, and gives the cycle the operator agreed: export first into scratch, never into a folder of the room's checkout that Git does not ignore, since any file there that Git lists stops the next ship; the master changes only by packet; a copy with the room's path is imported with Overwrite; a second export is compared. Section 3 gains two facts measured in the plugin's code: an exclamation mark in the chat input lists the prompts, and an import resolves a conflict by id with Skip, Overwrite or Duplicate. The manual's operator's card gains the four prompts, and its closeout section names the Closeout card prompt. help's curriculum mode, a placeholder since the port, prints the wake sequence, the closeout and rotation sources with the fact that no closeout hook is installed, and the four prompts. A sixteenth self-test case, checked to bite, holds it to the master: it names every prompt in prompts.json and holds no placeholder. The help spec, its status line and the binaries registry row, which said 14 of 14, now say 16 of 16; they and the manual's help note describe the built mode. In help, only the curriculum text, its menu row and the self-test changed; no setting, prompt or other tool changed. The audit found the Closeout card to be a second prompt that does more than report; the manual names both. The pull request's review found two faults, both fixed. The saved Closeout card names the Integrator's desk as rotation writer, which does not hold for the Integrator or the Session Continuity Manager; the manual now gives those two the canonical card and words its last step as the template does. The cycle's last step deleted the first export even after a failed comparison; it now stops on a difference, and on a match deletes only what is rebuildable, after the hashes are recorded. There are no deviations.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-24T20:48:47Z
- Tree: tree 6601f1e87b146ac42b4adf6a8c89d646f8dbf7b2

## Audit note

PASS. Read by difference from the tree I passed, after two findings by the reviewer on the pull request. The pushed head carried exactly the files I passed. Since then three changes, and nothing else in the diff: the manual's section 9 now gives the Integrator and the Session Continuity Manager the canonical card and lets the other three prompts serve as they stand; section 4 step 5 words the rotation writer as the card template and PoT 4.1.4 and 4.2.3 do; RUNBOOK-05 step 5 stops and keeps every file on a difference, and on a match records the hashes, deletes only what is rebuildable, and puts a first export that is not rebuildable into custody before deleting it, as CONSTRAINTS C01 asks. Both findings are answered in substance. The step 5 rewording is in bounds: section 9 sends two roles to section 4's card, which must then name their rotation writer correctly. Every sentence of the narrative was checked against its source. Both gates pass on a fresh copy.
N1, a note, not a condition: the saved Closeout card says Shannon's desk runs the rotation; the manual and the narrative call it the Integrator's desk. That is true by reference while that seat holds the Integrator role, as the registry gives it today.
