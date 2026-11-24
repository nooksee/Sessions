# DP-SES-0022: Prompts: seat and key in place of a name; Compaction prep

- Packet: DP-SES-0022
- Branch: agent/dp-ses-0022-2026-11-24
- Base: commit e7aae8c8725166346bea08f312ff4012a88438ea
- Opened: 2026-11-24T22:45:21Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: The operator's word of 2026-11-24 in the Integrator's window, recorded in the Integrator's handoff, digest 00ff5b5b

## Objective

The master prompts named a person by surname alone: as the sender in Identity check, Wake check and Packet status, and as the desk that runs a rotation in the Closeout card. Kept text names seats and keys, not persons: a name does not address one seat, and by the operator's account a name-only relay confused a resident on 2026-11-23. Those three prompts now name their sender by seat and registry key, and the Closeout card names the desk the same way. Compaction prep, the prompt the operator saved on 2026-11-24 for a resident to prepare before a compaction he has chosen, joins the master under the id his library gave it, and help's curriculum names it. RUNBOOK-05 states how a prompt is worded, and the page, manual, index, registry row, baseline and help spec stop counting the prompts.

## Scope

- ops/src/runbook/ccgui/prompts.json
- ops/src/runbook/ccgui/baseline.json
- docs/ops/specs/runbook/ccgui.md
- docs/MANUAL.md
- docs/INDEX.md
- docs/ops/registry/runbook.md
- ops/bin/help
- docs/ops/specs/binaries/help.md

## Gates

- filing
- help

## Results

- Closed: 2026-11-24T22:45:32Z
- Contractor: session-doctor
- Paths changed: 8
- Deviations: 0
- Tree: tree 82feb27211474caa267daf6cfb9450a49a5b6b94
- Gate: exit 0 in 0 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: ops/bin/help --test

## Narrative

The master prompts named a person by surname alone: as the sender in Identity check, Wake check and Packet status, and as the desk that runs a rotation in the Closeout card. The operator's standard is that kept text names seats and keys, not persons; a name does not address one seat, and by his account a name-only relay confused a resident the day before. In ops/src/runbook/ccgui/prompts.json those three prompts now name the sender as the Session Continuity Manager with the registry key, and the Closeout card names that seat's desk by key. The canonical card's template gives that writer as the Integrator's desk; the saved prompt uses seat and key because it serves residents of rooms that have an Integrator of their own. Compaction prep joins the master as a fifth prompt, under the id and creation time the operator's library gave it when he saved it: the resident stops at a clean point, updates its own handoff noting that the operator chose compaction, reports its context pressure line and says it is ready. It names no sender. With the room's path in place of the placeholder, its text equals the saved prompt. help's curriculum names it, as self-test case 16 requires; the self-test passes 16 of 16. RUNBOOK-05 section 4 lists the five by name and states how a prompt is worded. The manual's table gains the new prompt, its sentence on exceptions counts three, and it states the same wording rule. The page, the manual, the index, the registry row, the baseline and the help spec no longer count the prompts. The export time in the master is the clock time of the write. No setting changed, and no tool behaviour beyond help's curriculum text. The operator's library holds the four older wordings until he imports the copy made from this tree. The packet was opened three times: read-only workers checked each claim before any close, and the objective was corrected twice on what they and the Contractor found. There are no deviations.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-24T22:49:55Z
- Tree: tree 82feb27211474caa267daf6cfb9450a49a5b6b94

## Audit note

PASS. Read whole: the leaf, the diff and the source of each claim. The authority digest matches the operator's recorded words. In the master, the four older prompts differ from the base only by the stated wording, the sender named by seat and registry key and the Closeout card's desk by key; no prompt names a person, and all five name the operator by role. Compaction prep carries the id, name and creation time of the operator's saved prompt, and with the room's path in place its text equals the saved one. The export time equals the file's own write time. The registry gives the STELA and Personal rooms an Integrator each, so the reason for the card's departure from the template holds. No count of the prompts remains in the tree. The ledger shows two abandons, each with its reason, before the one close, as the field guide allows. Both gates pass on a fresh copy, and case 16 fails when the new curriculum line is removed. Every sentence of the narrative was checked against its source.
Notes, not conditions. N1: the closeout spec gives the card one source, the template; the saved prompt is a kept variant whose last step now departs from the template by design, so a later change to the template does not reach it. N2: the manual's sentence on pasting names three prompts and is silent on Compaction prep.
