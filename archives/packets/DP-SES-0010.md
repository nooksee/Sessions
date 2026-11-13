# DP-SES-0010: Custody suite: no dependence on the machine's disk

- Packet: DP-SES-0010
- Branch: agent/dp-ses-0010-2026-11-13
- Base: commit 7cf4f36b9fa5bb99a467e84a429707d16ff4b556
- Opened: 2026-11-13T16:06:07Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claudine-colbert
- Orchestrator: jo-hamming
- Authority: RoR-25: a fault in a required gate's suite is mended by a packet

## Objective

The required check failed on main after DP-SES-0009 landed, on a runner whose temporary folder refuses direct reads: one test of the custody suite made a real direct read there. Make the suite independent of the machine: the test of naming a direct root proves which root is read directly without a real direct read; one new test makes the real direct read and is skipped with its reason printed where the folder allows none; one new test proves a failed direct read is refused with the reader's own reason and leaves nothing behind. The tool's refusal now carries the reader's last line, in the C locale. The change is the outside writer's patch storage/intake/DP-SES-custody.patch, applied whole. The Auditor here is acting, by the operator's word.

## Scope

- ops/lib/scripts/custody.py
- tools/test/test_custody.py
- docs/ops/specs/scripts/custody.md
- docs/ops/registry/test.md

## Gates

- custody
- role_names
- name_counts
- help
- template

## Results

- Closed: 2026-11-13T16:13:56Z
- Contractor: session-doctor
- Paths changed: 4
- Deviations: 0
- Tree: tree 333b1a8012aaa0db30f56962e9ed46441355b49e
- Gate: exit 0 in 1 s: tools/test/test_custody.py
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 2 s: tools/test/test_name_counts.py
- Gate: exit 0 in 2 s: ops/bin/help --test
- Gate: exit 0 in 8 s: ops/bin/template --test

## Narrative

The outside writer's patch from the intake folder was read whole and applied whole in the packet worktree; four files changed. The acting Auditor then failed the first tree on one finding: the new real-read test skipped on any refusal by the tool, so a reader with broken input flags passed with one skip. Reworked, in the one test only: the skip is now decided by a direct open with the reader's own flags and one aligned read of a file in that folder, made without the tool; only that refusal skips, with its error printed; otherwise the tool's digest is required. In scratch, with the reader's flags broken, the suite now fails. The skip path itself could not be run on this host, where no folder refuses direct reads. No custody root was read or written by this packet. The Integrator also carries the Contractor function here, and the Auditor of this packet is acting, by the operator's word.

## Audit

- Verdict: PASS
- Auditor: claudine-colbert
- Audited: 2026-11-13T16:15:11Z
- Tree: tree 333b1a8012aaa0db30f56962e9ed46441355b49e

## Audit note

Finding F1 of my first audit is closed. Against the tree I failed, one file changed, the custody suite, in the one test of F1 and one import; custody.py is byte-equal to the first close. The skip is now decided by the folder itself, an open with the reader's own flags and one aligned read made without the tool, and otherwise the tool's digest is required. Behind the room's barrier, at three umasks, on an ext4 folder and on a tmpfs one: the suite runs 29 tests OK. The mutant of my first audit, which breaks the reader's input flags, now fails the suite with an error on both folders at every umask, where before it passed with a skip. The skip path, which no folder on this host takes, I ran with a harness that refuses only direct opens, as the runner's folder does: the test skips and prints the folder's own error. The rest of the change stands as my first audit read it: the patch from intake applied whole, four paths, all in scope, the refusal text in custody.py sound. Verdict PASS.
