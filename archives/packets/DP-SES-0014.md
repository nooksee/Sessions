# DP-SES-0014: Required check: time limit from 10 to 15 minutes

- Packet: DP-SES-0014
- Branch: agent/dp-ses-0014-2026-11-14
- Base: commit 6eb22d8cd8ed4b2d2dcec99ee78c820dffa56f64
- Opened: 2026-11-14T00:12:34Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claudine-colbert
- Orchestrator: jo-hamming
- Authority: The operator's named go of 2026-11-12, words digest 584b1f08, repeated by his word of 2026-11-13; the acting Auditor by RoR-29 and by his word for this packet

## Objective

Raise the time limit of the required check from 10 minutes to 15, in the one line of the workflow that sets it. The check runs every suite, and its recent runs took between about 6 and 11 minutes from start to end as the code host reports them, so a slow runner can end a sound pull request at the limit. Nothing else in the workflow changes: not its steps, its triggers, its name or the name of the required check. No suite and no document states the limit, so no other path changes.

## Scope

- .github/workflows/sessions-gates.yml

## Gates

- packet
- help
- template

## Results

- Closed: 2026-11-14T00:15:03Z
- Contractor: session-doctor
- Paths changed: 1
- Deviations: 0
- Tree: tree 735c14b352d4b7c4d1175e6773474453c29e8a5c
- Gate: exit 0 in 135 s: tools/test/test_packet.py
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 5 s: ops/bin/template --test

## Narrative

One line of the workflow changed: the job's time limit is 15 minutes where it was 10. Nothing else in the workflow changes, and the required check keeps its name. A search of every tracked file outside the ledger and the archives finds no suite and no current document that states the limit; one dated review under the documents folder mentions ten minutes as a past measurement and is left as the record it is. The operator gave his named go for this on 2026-11-12 and repeated it on 2026-11-13. The Integrator also carries the Contractor function here; the Auditor is the acting holder of RoR-29, named for this packet by the operator.

## Audit

- Verdict: PASS
- Auditor: claudine-colbert
- Audited: 2026-11-14T00:16:22Z
- Tree: tree 735c14b352d4b7c4d1175e6773474453c29e8a5c

## Audit note

I read the change whole: one line of the required check's workflow, its time limit from 10 minutes to 15, and nothing else in the file. This is a change to automation, so PoT 6.1.2 asks an independent review and a named go: this audit is the review, and the go's words are in custody on each of the three disks, hashing to the digest the authority line cites, which I checked by hash only. From the code host, read only: of the last 100 runs of the check, none was ended by its limit; the job's own time, which is what the limit bounds, reached 8.4 minutes, and the last ten successful runs took 7.8 to 8.4, close to the old limit; from creation to end, queue included, they took up to 11.1, which is the upper figure the objective gives. No tracked file states the limit as current; the dated review that mentions ten minutes is a record, and the other mentions of ten minutes are about other things. Whether the host's sign-in may push a change to a workflow file is not tested here and is met at the ship. Verdict PASS.
