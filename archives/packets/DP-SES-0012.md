# DP-SES-0012: Ship: wait for an asked reviewer, name the reviews

- Packet: DP-SES-0012
- Branch: agent/dp-ses-0012-2026-11-13
- Base: commit 207412d0a17b3fc2b8bb564142f52679dc3e066a
- Opened: 2026-11-13T17:25:12Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claudine-colbert
- Orchestrator: jo-hamming
- Authority: RoR-24 (nothing merges with a review finding open); the acting Auditor by RoR-29

## Objective

The ship station already rests the head, waits while a reviewer says it is running, and refuses to merge over an unanswered review comment. Add two things. First, a reviewer that was asked is waited for: read from the pull request's own events in order, known by account number, for at most 900 seconds from the opening, and events that cannot be read stop no landing. Second, the landing names the reviews: the landed line, the ledger line and the landing proof carry who reviewed, each count of findings and how many stand unanswered, and any reviewer asked and silent. Nothing else of the review rule changes. The change is the outside writer's patch storage/intake/DP-SES-reviews-2.patch, applied whole.

## Scope

- ops/lib/scripts/packet.py
- tools/test/test_packet.py
- docs/ops/specs/scripts/packet.md
- docs/ops/specs/tools/test/packet.md
- docs/ops/specs/runbook/shipping.md
- docs/ops/registry/test.md
- docs/INDEX.md

## Gates

- packet
- role_names
- name_counts
- help
- template

## Results

- Closed: 2026-11-13T17:28:16Z
- Contractor: session-doctor
- Paths changed: 7
- Deviations: 0
- Tree: tree d385d4679dc69eccac5ccb0c57f8c1234ff49d5e
- Gate: exit 0 in 166 s: tools/test/test_packet.py
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 2 s: tools/test/test_name_counts.py
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 6 s: ops/bin/template --test

## Narrative

The outside writer's second reviews patch from the intake folder was read whole and applied whole in the packet worktree with one apply; seven files changed and nothing else. The first reviews patch was never in the room and is not used. The ship station now waits, for at most 900 seconds from the opening, for a reviewer the pull request's events show was asked, and the landing line, the ledger line and the landing proof name who reviewed and what each left. This packet is shipped by the tool that stands on main, so its own landing line carries no reviews; the next packet's does. The Integrator also carries the Contractor function here, and the Auditor is the acting holder of RoR-29.

## Audit

- Verdict: PASS
- Auditor: claudine-colbert
- Audited: 2026-11-13T17:42:53Z
- Tree: tree d385d4679dc69eccac5ccb0c57f8c1234ff49d5e

## Audit note

I read the change whole: it equals the intake patch, seven paths, all in scope, and the documents say what the code does. Behind the room's barrier the packet suite runs 97 tests OK at umask 0002, 0022 and 0077. Six mutants of the new behaviour were each caught by the test named for it: no wait for an asked reviewer, a wait without end, a reviewer known by name instead of account number, unreadable events stopping the landing, a dropped count of unanswered findings, and the reviewers asked before the head has rested. The landing record is always bound before the LANDED line, since every path that skips it raises first. Two limits, neither a finding. The landing record reads the reviews and the issue comments from one page of 100 each; the existing check of a running reviewer reads issue comments from one page too, so the record keeps the gate's own bound, and only a pull request with more than 100 of either could name fewer reviewers than it had; reading every page in both belongs to a later packet. This packet ships by the tool on main, so its own landing line carries no reviews, as its narrative says. Verdict PASS.
