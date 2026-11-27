# DP-SES-0023: Board after the parent move; two notes on the prompts

- Packet: DP-SES-0023
- Branch: agent/dp-ses-0023-2026-11-27
- Base: commit 84ad4ac47a0865e7ee18ad15ee8de31471eb8625
- Opened: 2026-11-27T18:30:23Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: The operator's word of 2026-11-27 in the Integrator's window, kept in the Integrator's handoff, digest df9b763b

## Objective

The parent folder was reorganised from 2026-11-26, and the board described the state before it. The board is corrected as measured on 2026-11-27: the custody line sets the measured places of the three roots beside the rulings; one open line records that seven room folders moved and that registry rows keep an old path until a rewire; the open line on Control's rounds timer says what was measured. Other lines stay. Two notes owed from DP-SES-0022 are paid: the manual's sentence on pasting names Compaction prep and its one limit for a Copilot resident (the review comment on pull request 114, made after its merge), and the plugin page says the saved Closeout card is a second text kept by hand, not a rendering of the canonical card (a note in the Auditor's audit of that packet).

## Scope

- NOW.md
- docs/MANUAL.md
- docs/ops/specs/runbook/ccgui.md

## Gates

- filing
- help

## Results

- Closed: 2026-11-27T18:30:25Z
- Contractor: session-doctor
- Paths changed: 3
- Deviations: 3
- Tree: tree 818c31984974bf49d47eca941cceac05bb62fa73
- Gate: exit 0 in 0 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: ops/bin/help --test

## Narrative

NOW.md, the board. The Custody line sets the rulings of 2026-11-08 and 2026-11-11, three roots on three disks, beside what was measured on 2026-11-27: the folder that was the user_vol root is on hard_vol1, so two disks hold the three, and a ruling is awaited. One new Open line: the parent was reorganised from 2026-11-26, seven room folders moved under projects, one was renamed, and registry rows keep a room's old path until its residents are rewired. The Open line on Control's rounds timer keeps its work order and says what was measured: not installed, its log last written 2026-11-15, and rounds.sh names a Control detector whose folder is gone. A blank line went, so the board keeps 40 lines, the longest 200 characters. Routes is unchanged.

docs/MANUAL.md, section 9. The sentence on pasting names Compaction prep and one limit: the fullness readers of myself.py are for Claude and Codex bodies, so a Copilot resident's context pressure line cannot carry a measured figure. Read in the code, not run as a Copilot resident.

docs/ops/specs/runbook/ccgui.md, section 4. One paragraph: the saved Closeout card is a second text kept by hand, the three differences from the template that matter, and that nothing renders it.

One read-only worker pre-read the first wording and refuted it in nine places. It also read two unchanged board lines as stale: other desks' lines, not re-measured here.

Deviations 3. First deviation: the Contractor changed directory into the worktree once to run a gate, and made no edit that way. Second deviation: the first objective claimed more than was measured, so the packet was abandoned and reopened. Third deviation: the first authority line gave the hash of the Integrator's handoff where the digest of the operator's words belongs, so it was abandoned and reopened again on the Auditor's finding.

Not here: the manual, the map and the custody spec still describe the ruled custody arrangement; the plugin page still names the earlier version.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-27T18:31:43Z
- Tree: tree 818c31984974bf49d47eca941cceac05bb62fa73

## Audit note

PASS. Read by difference: the diff is byte-equal to the tree I failed, and only the leaf changed, its open and close times, its authority line, its count and its narrative. F1 is answered: the operator's words are now kept in the Integrator's handoff, and that kept text hashes to the digest the authority line gives; the words ask for the house to be put in order, which this board correction serves. The ledger shows the second abandon with its reason, the reopen and the close on the same tree. F2 is answered: the narrative counts three deviations and names each in its own clause, the third being the first authority line. The rest of the narrative is as I checked it before. Both gates pass on a fresh copy.
