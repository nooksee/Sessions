# DP-SES-0017: Custody: the tool makes its own direct read

- Packet: DP-SES-0017
- Branch: agent/dp-ses-0017-2026-11-14
- Base: commit 72a3c9cb3865d9e9fa530f1c4d94401001f68c25
- Opened: 2026-11-14T03:47:02Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claudine-colbert
- Orchestrator: jo-hamming
- Authority: The operator's go of 2026-11-13 by his relay of his outside writer's page, digest 8764653152656b9a, its third part; the acting Auditor by RoR-29

## Objective

The custody tool handed its direct read to whichever dd the machine has, and one kind of dd fails every direct read; two required checks failed on it. The tool now makes the direct read itself, with the same two flags, direct and no access-time update, and calls no other program. It reads a megabyte at a time into an aligned buffer; a read that comes back short is the end of the file and no read is asked after it; what was read must be the whole file by its size; a refused read carries the system's own reason and leaves nothing behind. Tests cover seven file sizes and prove that both flags are asked for. The one real direct read stays behind the probe of the folder. What the direct option means and which roots it names are not touched.

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

- Closed: 2026-11-14T03:47:29Z
- Contractor: session-doctor
- Paths changed: 4
- Deviations: 0
- Tree: tree fc7ec17c73502348fe39a586dd4486267858a063
- Gate: exit 0 in 1 s: tools/test/test_custody.py
- Gate: exit 0 in 0 s: tools/test/test_role_names.py
- Gate: exit 0 in 2 s: tools/test/test_name_counts.py
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 4 s: ops/bin/template --test

## Narrative

Written by the Contractor from the third part of the outside writer's page; no patch came with it. The custody tool no longer calls another program for its direct read: it opens the copy with the direct flag and without an access-time update, reads a megabyte at a time into a page-aligned buffer, takes a short read as the end of the file and asks for none after it, requires the whole file by its size, and refuses with the system's own reason. The suite is 31 tests. Two are new: one proves at seven file sizes, with the direct flag taken off at the open so that it runs on any machine, that the digest is right and that no read follows a short one; one proves that both flags are asked for and that no program is there to be called. The test of a failed read now proves the system's reason for a missing file, for a folder that allows no direct read and for a medium that fails under the read, a refusal when the file ends before its size, and that nothing is left behind. In scratch, before the packet opened, five deliberate breakages were each caught: no direct flag, no access-time flag, a read after a short read, no whole-file check, no system reason. The one real direct read stays behind the probe of the folder. No custody root was read or written by the suite. The Auditor is the acting holder of RoR-29.

## Audit

- Verdict: PASS
- Auditor: claudine-colbert
- Audited: 2026-11-14T03:49:51Z
- Tree: tree fc7ec17c73502348fe39a586dd4486267858a063

## Audit note

I read the change whole against the eight items of the page's third part. The tool now reads the copy itself, with the direct flag and no access-time update, a megabyte at a time into a page-aligned buffer; a short read ends the file, the bytes read must equal the size, and a refusal carries the system's own reason. Behind the room's barrier the suite runs 31 tests OK at three umasks, on an ext4 folder and on a tmpfs one. Of seven mutants, one per item and two that break only a real direct read, all are caught on ext4: no direct flag, no access-time flag, a read after a short read, no whole-file check, no system reason, a block that is not whole, and an unaligned buffer. On tmpfs the unaligned buffer passes, since that filesystem accepts it: only the one real read behind the probe proves alignment, and only on a filesystem that enforces it, as the gate's folder here does. That is a limit, not a finding; a test of the buffer's own address would close it. Read only, by hash, the tool's direct digest equals the plain one for three files of one batch on each of the three real roots, two of ext4 and one of ntfs3. As before, the access-time flag is refused for a file the caller does not own; the custody copies are the operator's own. Verdict PASS.
