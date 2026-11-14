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

- Closed: 2026-11-14T03:34:50Z
- Contractor: session-doctor
- Paths changed: 7
- Deviations: 1
- Tree: tree 04b2f2cdaa8422819d8e4f84ad072f5ee764b3cd
- Gate: exit 0 in 198 s: tools/test/test_packet.py
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 2 s: tools/test/test_name_counts.py
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 6 s: ops/bin/template --test

## Narrative

Written by the Contractor from the second part of the outside writer's page; no patch came with it. The landing record now keys a reviewer by account number, and by login only where no number is given, and names it once by the login on its review; the pull request's own account is left out by its number too. One reader of every page, which refuses a page that is no list and an item that is no object, now serves the reviews, the general comments and the review comments, in the record and in the check for a running review. Per reviewer the record counts findings answered without a change, read from the comment's present line. A request is waited for 900 seconds from its own time, and from the opening where it has none. Five tests are new and one expectation of an older test follows the new count of findings without a change; the suite is 102 and ran whole and green in scratch before the packet opened. Run read-only against the real pull request 105, the new record is the text the writer's page names. Deliberate breakages of these changes were not run by the Contractor; that proof is left to the audit and said here so that it is not assumed. The Auditor is the acting holder of RoR-29.
During the audit the acting Auditor found that an object whose user is a string still ended in a traceback at the two readers that gate the merge. Mended in a second close: the one reader also refuses an item whose user is neither an object nor absent, and tests prove it in the record, in both gate readers and at the station.
A third close, on a review finding on the pull request that is right: the suite's specification said that an item that is no object in the reviews stops the merge. The reviews are read only for the landing record, after the merge, where such an item gives a record that is not read; the sentence now says that, and keeps the promise of no merge for the comments and the review comments alone. That sentence was the Contractor's error and is the one deviation counted.

## Audit

- Verdict: PASS
- Auditor: claudine-colbert
- Audited: 2026-11-14T03:35:36Z
- Tree: tree 04b2f2cdaa8422819d8e4f84ad072f5ee764b3cd

## Audit note

Against the tree I passed, only one sentence of the suite's specification changed: the reviews are read only for the landing record, after the merge, so a malformed item there stops nothing. I confirmed it in the code: the reviews have one reader, called only at the landing. The code and the suite are byte-equal to the tree I passed, so my proof of it stands: 102 tests OK at three umasks behind the room's barrier, a nested user refused plainly at every reader, nine of ten mutants caught by name and the tenth equivalent, and the record of pull request 105 equal to the page's text. A correction to my earlier note, on a review finding that is right: I wrote the mark of item 6 the wrong way round. A finding whose present line is gone, with its first line kept, is one whose line was changed afterwards and is not counted; a finding that still has a present line is counted as answered without a change. My limit, restated: a fix made elsewhere in the file leaves the finding's line present, so it is counted as without a change, a pointer and never a judgement. A request with no time of its own is counted from the opening; team request times in the events are not read, and no team is asked in this repository. Verdict PASS.
