# DP-SES-0009: Sweep the old route out of four documents

- Packet: DP-SES-0009
- Branch: agent/dp-ses-0009-2026-11-13
- Base: commit 29faacbc03ed49c525a5cff3dbf6dc82f3cea1b6
- Opened: 2026-11-13T08:02:33Z
- Integrator: session-doctor
- Contractor: claudine-colbert
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: RoR-25

## Objective

Four documents still describe the route a change took before dispatch packets: the index, the manual, the start-here page and the repository runbook. Make each say that a change to tracked files travels as one dispatch packet and that its record is the packet leaf, without rewriting anything else in them. The change is the outside writer's patch storage/intake/DP-SES-0003-old-route-sweep.patch, which applies to main as it stands: apply it whole in the worktree, read it against each file, and correct only what the patch itself gets wrong.

## Scope

- docs/INDEX.md
- docs/MANUAL.md
- docs/START-HERE.md
- docs/ops/specs/runbook/repository.md

## Gates

- help
- template
- role_names
- name_counts

## Results

- Closed: 2026-11-13T08:04:04Z
- Contractor: claudine-colbert
- Paths changed: 4
- Deviations: 0
- Tree: tree e865f1bdcd5bc354a962af95eb5d7e6938bb8d54
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 3 s: ops/bin/template --test
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 2 s: tools/test/test_name_counts.py

## Narrative

I applied the outside writer's sweep patch from intake whole in the packet worktree and read each of its four hunks against its file on main. The index, the manual and the start-here page already said that a change ships as one dispatch packet, and the patch adds to each that the packet leaf is the record of a change to tracked files. The patch got one thing short against the objective: in the repository runbook it says that every change travels as one dispatch packet but not that the leaf is its record, so I added one sentence there saying that the change's record is the packet leaf under archives/packets. I rewrote nothing else in the four files; other old-route wording in them had already been swept by earlier packets. Deviations: none.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-13T08:05:06Z
- Tree: tree e865f1bdcd5bc354a962af95eb5d7e6938bb8d54

## Audit note

PASS. Three of the four paths equal the outside writer's sweep patch applied on the base, byte for byte. The fourth, the repository runbook, differs by one sentence of the Contractor's: the change's record is the packet leaf under archives. The patch had said every change travels as one packet but not where its record is, so the sentence completes the objective, as the leaf allows. Each file now says that a change to tracked files travels as one dispatch packet and that its record is the packet leaf. The manual keeps the source-change form for a configuration change that touches no tracked file, and its pointer to section 1B lands on the packet section. Every new statement matches the packet tool: it performs each Git step, never forces a push, and writes the leaf. Nothing else in the four files is rewritten.

The gates fit a document-only change. I ran all four again on an export of this exact tree: help, template, role names and name counts, each passing. The narrative counts no deviation and describes what the diff shows.
