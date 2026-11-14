# DP-SES-0016: Ship: one reviewer named once in the landing record

- Packet: DP-SES-0016
- Branch: agent/dp-ses-0016-2026-11-14
- Base: commit c90df054c117fca0ac15f37f87a222770121a3d7
- Opened: 2026-11-14T01:12:56Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claudine-colbert
- Orchestrator: jo-hamming
- Authority: The operator's go of 2026-11-13 by his relay of his outside writer's page, digest 8764653152656b9a, its second part; the acting Auditor by RoR-29

## Objective

The landing record named one reviewer twice on DP-SES-0013, by the login on its finding and by the login on its review, and the second half was false. A reviewer is now one account, known by its account number and by its login only where no number is given, named once by the login on its review where it has one. The reviews and the general comments are read across every page, in the record and in the check for a running review, and an item that is no object is refused plainly. Per reviewer the record counts the findings answered without a change, by the mark of the code host on a finding whose line was changed afterwards; it is a pointer and stops nothing. A reviewer asked again on a later push is waited for from that request. The rule on unanswered findings is not touched.

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

- Closed: 2026-11-14T01:23:32Z
- Contractor: session-doctor
- Paths changed: 7
- Deviations: 0
- Tree: tree a1e74b6c913fb2806383ecd11967fdf4d113611f
- Gate: exit 0 in 170 s: tools/test/test_packet.py
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 2 s: tools/test/test_name_counts.py
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 4 s: ops/bin/template --test

## Narrative

Written by the Contractor from the second part of the outside writer's page; no patch came with it. The landing record now keys a reviewer by account number, and by login only where no number is given, and names it once by the login on its review; the pull request's own account is left out by its number too. One reader of every page, which refuses a page that is no list and an item that is no object, now serves the reviews, the general comments and the review comments, in the record and in the check for a running review. Per reviewer the record counts findings answered without a change, read from the comment's present line. A request is waited for 900 seconds from its own time, and from the opening where it has none. Five tests are new and one expectation of an older test follows the new count of findings without a change; the suite is 102 and ran whole and green in scratch before the packet opened. Run read-only against the real pull request 105, the new record is the text the writer's page names. Deliberate breakages of these changes were not run by the Contractor; that proof is left to the audit and said here so that it is not assumed. The Auditor is the acting holder of RoR-29.
During the audit the acting Auditor found that an object whose user is a string still ended in a traceback at the two readers that gate the merge. Mended in a second close: the one reader also refuses an item whose user is neither an object nor absent, and tests prove it in the record, in both gate readers and at the station.

## Audit

- Verdict: PASS
- Auditor: claudine-colbert
- Audited: 2026-11-14T01:39:47Z
- Tree: tree a1e74b6c913fb2806383ecd11967fdf4d113611f

## Audit note

I read the change whole against the seven items of the page, which is in custody under the cited digest. Read only against GitHub, the new record of pull request 105 is the page's text exactly. Behind the room's barrier the suite runs 102 tests OK at umask 0002, 0022 and 0077, and a nested user that is no object, which on the earlier tree ended in a traceback at both gate readers, is now refused plainly at every reader. Of ten mutants, nine are caught by the tests named for their items: number and owner by login, one page in the record and in the running check, unchecked items and users, no line mark, unanswered counted as unchanged, and request time ignored. The tenth, naming by the first login seen, survives as equivalent: the reviews are read first, so a reviewed account is first seen on its review. Two choices of the Contractor I accept as limits. The mark of a finding without a change is a null present line with the first line kept, as the page asks; a fix elsewhere in the file, or a finding on a whole file, would read as without a change, a pointer and never a judgement. A request with no time of its own is counted from the opening; team requests carry times in the events that are not read, and no team is asked in this repository. Verdict PASS.
