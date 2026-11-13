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

- Closed: 2026-11-13T18:45:18Z
- Contractor: session-doctor
- Paths changed: 7
- Deviations: 0
- Tree: tree a0130fe84597266635a04ba598df54453db94c6f
- Gate: exit 0 in 135 s: tools/test/test_packet.py
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 2 s: tools/test/test_name_counts.py
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 6 s: ops/bin/template --test

## Narrative

The outside writer's second reviews patch was applied whole and passed; the automatic reviewer then left two findings on the pull request, both right, and the writer's correction patch was applied whole on the closed tree. The acting Auditor failed that tree on one more finding of the same kind: the read of the pull request itself took an empty object, null, false or a list for a pull request that nobody was asked to review, said that 900 seconds had passed when no time had been read, and ended in a traceback on a list or a string. Reworked by the Contractor: that read now refuses any answer that is not an object holding something, by a helper beside the list helper, so the ship is refused and run again and the landing record says not read; and an opening time that cannot be read is said to be unread, not counted in seconds. The suite keeps its count; the new assertions stand in two tests that exist, and with the old read put back both fail. The Integrator also carries the Contractor function here, and the Auditor is the acting holder of RoR-29.

## Audit

- Verdict: PASS
- Auditor: claudine-colbert
- Audited: 2026-11-13T18:52:57Z
- Tree: tree a0130fe84597266635a04ba598df54453db94c6f

## Audit note

Finding G1 of my second audit is closed. Against the tree I failed, four files changed: packet.py, its suite and the two packet specifications. The pull request is now read through a helper that refuses any answer that is not an object holding something, so the ship is refused and run again, and the landing record says not read. A readable pull request whose opening time cannot be read is still taken as opened long ago, and the tool now says so instead of naming 900 seconds. Behind the room's barrier: my harness of the second audit, on this tree, now meets a refusal for each of the six malformed answers, while a readable one still waits for the asked reviewer; the suite runs 97 tests OK at umask 0002, 0022 and 0077; and three mutants are each caught by the tests named for them: the old read put back, an empty object let through, and the old message path restored. My earlier judgements stand: the two older reads belong in this packet, the landing record keeps the gate's one-page bound, and the packet's own landing line carries no reviews. One limit, not a finding: in the two older reads an element of a list that is not an object would end the ship in a traceback; that stops the merge, and it is older than this packet. Verdict PASS.
