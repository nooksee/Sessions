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

- Closed: 2026-11-24T20:24:18Z
- Contractor: session-doctor
- Paths changed: 5
- Deviations: 0
- Tree: tree 85d609ca4b4fa44c3d73549b4173d63dcdc9f5b6
- Gate: exit 0 in 0 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: ops/bin/help --test

## Narrative

Spec, help and manual now describe the operator's prompts as they are used. RUNBOOK-05 section 4 names prompts.json as the master and the Prompt Library as its copy, and gives the cycle the operator agreed: export first into scratch, never into a folder of the room's checkout that Git does not ignore, since any file there that Git lists stops the next ship, as it did once that day; the master changes only by packet; a copy with the room's path is imported with Overwrite; a second export is compared prompt by prompt. Section 3 gains two facts measured in the plugin's own code: an exclamation mark in the chat input opens the list of prompts, and an import resolves a conflict by id with Skip, Overwrite or Duplicate. The manual's operator's card gains the four prompts, with when each is used and what comes back, and its closeout section names the Closeout card prompt for a Codex resident in CC GUI. help's curriculum mode, a placeholder since the port, now prints the wake sequence as the room's Claude instructions give it, the closeout and rotation sources with the fact that no closeout hook is installed for any provider, and the four prompts. A sixteenth self-test case holds the curriculum to the master: it must name every prompt in prompts.json and hold no placeholder. The case was checked to bite, in scratch copies, on the old curriculum and on a fifth prompt in the master. The help spec, its status line and the binaries registry row, which still said 14 of 14, now say 16 of 16; they and the manual's help note describe the built mode. In help, only the curriculum text, its menu row and the self-test changed; no setting, prompt or other tool changed. The audit found that the manual named only the packet station as a prompt that does more than report, and the Closeout card is a second; the manual now names both. The help curriculum names the handoff as the room instructions do, and the cycle names the folder Git does not ignore. There are no deviations.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-24T20:25:21Z
- Tree: tree 85d609ca4b4fa44c3d73549b4173d63dcdc9f5b6

## Audit note

PASS. Read by difference: the diff is byte-equal to the tree I failed last, and only the leaf's close time and narrative changed. F1 is answered: the narrative now says the help spec, its status line and the binaries registry row say 16 of 16, which each does, and that they and the manual's help note describe the built mode, which each does. N1 is taken: the narrative states the export rule as the page does. The shortened bite sentence makes the claim I reproduced. Every sentence of the narrative was checked against the diff, the manual, the spec, the registry and my own measurements, and is accurate. Both gates pass on a fresh copy.
