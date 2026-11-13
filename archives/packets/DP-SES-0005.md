# DP-SES-0005: Add OPEN: the read-in a resident runs before it works

- Packet: DP-SES-0005
- Branch: agent/dp-ses-0005-2026-11-13
- Base: commit 2ee9d55b295297a89ffc4fb115a3047ebcf77cb0
- Opened: 2026-11-13T03:03:58Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claude-bernard
- Orchestrator: jo-hamming
- Authority: The operator's direction of 2026-11-12 on the read-in, as he corrected it the same evening, entered by this packet as RoR-27

## Objective

Land the command ops/bin/open, the room's form of STELA's open: a resident runs it itself after every wake and at each shift. It finds the caller as the mind tool does and prints the law from main: the clauses the read-in table lists for every reader, and those of each delivery function the open packet's leaf gives the caller, or of all four when no open packet names the caller; a file of the law is printed whole when this body has not been shown it as it now stands. It records one private line. It lands as the command only: no other tool requires it yet. With it land its suite and specifications, the table as section X04 of the context manifest, its registry rows and pointers, the ledger entry and two board lines. The prepared patch storage/intake/DP-SES-open-2.patch is applied unchanged.

## Scope

- ops/bin/open
- docs/ops/specs/binaries/open.md
- tools/test/test_open.py
- docs/ops/specs/tools/test/open.md
- ops/lib/manifests/CONTEXT.md
- ops/bin/help
- docs/ops/specs/binaries/help.md
- docs/ops/registry/binaries.md
- docs/ops/registry/test.md
- docs/INDEX.md
- docs/MANUAL.md
- docs/ops/README.md
- README.md
- CLAUDE.md
- AGENTS.md
- RoR.md
- NOW.md

## Gates

- full

## Results

- Closed: 2026-11-13T03:13:58Z
- Contractor: session-doctor
- Paths changed: 17
- Deviations: 0
- Tree: tree 6859acde74bb7c2016dd47cb4be9ae797492d7b9
- Gate: exit 0 in 1 s: tools/test/test_alerts.py
- Gate: exit 0 in 0 s: tools/test/test_alerts_arity.py
- Gate: exit 0 in 0 s: tools/test/test_archive.py
- Gate: exit 0 in 0 s: tools/test/test_bloat.py
- Gate: exit 0 in 0 s: tools/test/test_capsule.py
- Gate: exit 0 in 0 s: tools/test/test_chamber.py
- Gate: exit 0 in 20 s: tools/test/test_closeout.py
- Gate: exit 0 in 0 s: tools/test/test_condense.py
- Gate: exit 0 in 0 s: tools/test/test_conflicts.py
- Gate: exit 0 in 2 s: tools/test/test_constitution.py
- Gate: exit 0 in 0 s: tools/test/test_custody.py
- Gate: exit 0 in 0 s: tools/test/test_dossier.py
- Gate: exit 0 in 0 s: tools/test/test_elide.py
- Gate: exit 0 in 0 s: tools/test/test_estimate.py
- Gate: exit 0 in 0 s: tools/test/test_filing.py
- Gate: exit 0 in 0 s: tools/test/test_fingerprint.py
- Gate: exit 0 in 0 s: tools/test/test_gate.py
- Gate: exit 0 in 5 s: tools/test/test_gauge.py
- Gate: exit 0 in 0 s: tools/test/test_history.py
- Gate: exit 0 in 3 s: tools/test/test_identity.py
- Gate: exit 0 in 0 s: tools/test/test_identity_held.py
- Gate: exit 0 in 0 s: tools/test/test_images.py
- Gate: exit 0 in 0 s: tools/test/test_inventory.py
- Gate: exit 0 in 0 s: tools/test/test_items.py
- Gate: exit 0 in 0 s: tools/test/test_janitor.py
- Gate: exit 0 in 0 s: tools/test/test_limits.py
- Gate: exit 0 in 0 s: tools/test/test_media.py
- Gate: exit 0 in 11 s: tools/test/test_mind.py
- Gate: exit 0 in 0 s: tools/test/test_miner.py
- Gate: exit 0 in 2 s: tools/test/test_myself.py
- Gate: exit 0 in 1 s: tools/test/test_name_counts.py
- Gate: exit 0 in 3 s: tools/test/test_notice.py
- Gate: exit 0 in 4 s: tools/test/test_open.py
- Gate: exit 0 in 38 s: tools/test/test_packet.py
- Gate: exit 0 in 4 s: tools/test/test_prepare.py
- Gate: exit 0 in 0 s: tools/test/test_pressure.py
- Gate: exit 0 in 0 s: tools/test/test_prime.py
- Gate: exit 0 in 1 s: tools/test/test_pycharm.py
- Gate: exit 0 in 11 s: tools/test/test_redact.py
- Gate: exit 0 in 0 s: tools/test/test_reid.py
- Gate: exit 0 in 0 s: tools/test/test_resources.py
- Gate: exit 0 in 0 s: tools/test/test_retention.py
- Gate: exit 0 in 1 s: tools/test/test_ror_join.py
- Gate: exit 0 in 451 s: tools/test/test_rotate.py
- Gate: exit 0 in 0 s: tools/test/test_rotation.py
- Gate: exit 0 in 0 s: tools/test/test_rounds.py
- Gate: exit 0 in 0 s: tools/test/test_sandbox.py
- Gate: exit 0 in 0 s: tools/test/test_successor.py
- Gate: exit 0 in 0 s: tools/test/test_tablet.py
- Gate: exit 0 in 0 s: tools/test/test_telemetry.py
- Gate: exit 0 in 0 s: tools/test/test_transcripts.py
- Gate: exit 0 in 0 s: tools/test/test_vitals.py
- Gate: exit 0 in 0 s: tools/test/test_watch.py
- Gate: exit 0 in 0 s: tools/test/test_workers.py
- Gate: exit 0 in 0 s: ops/bin/help --test
- Gate: exit 0 in 1 s: ops/bin/template --test

## Narrative

The command ops/bin/open lands with its suite of 76 tests, its two specifications, the read-in table as section X04 of the context manifest, its registry rows and the pointers to it. The patch its writer prepared is applied unchanged: fifteen paths, four of them new, and I altered nothing in them. The tool finds the caller, prints the clauses for every reader from main, and prints the clauses of each delivery function the open packet's leaf gives the caller, or of all four when no open packet names the caller. It shows and records; no other tool requires it yet. The ledger gains RoR-27, the operator's direction on the read-in as he corrected it the same evening; a first draft was withdrawn before it landed. The private source keeps what was first written under that number and carries the correction as an attributed addition, with the operator's words, the packet and the patch in custody on three disks; the public entry is rendered from the corrected fields by the redact tool and appended. Two board lines change: the Team line now names the four functions and where to start, and a read-in line is added; no other board line is touched. Not done: no first OPEN was made, since each resident makes its own after the landing, and the lock is a later packet. Deviations: none.

## Audit

- Verdict: PASS
- Auditor: claude-bernard
- Audited: 2026-11-13T03:16:39Z
- Tree: tree 6859acde74bb7c2016dd47cb4be9ae797492d7b9

## Audit note

PASS, read fresh. Fifteen paths equal the prepared patch applied on the base, byte for byte; the Manager's own are RoR-27 and two board lines. The command reads the law only from the Git objects of main, keeps the body as a digest in private files, records nothing for an unverified caller, and takes a function only from the open packet's leaf, all four when no open packet names the caller. Every count agrees with the suite: seventy-six tests, the seven groups exactly as the classes hold them.

On an export of this tree behind my masked runner the suite passes at umask 0022 and 0077. Of seven mutants of my own to the new logic, written before I read the tests, six were caught by name: always all four, none when none, no check of a missing function, a damaged leaf trusted, and either rule of the table dropped. RoR-27 is the corrected entry: its public fields equal the correction's lines in the private source, its Words digest is the correction's words, and the first text stays private with the correction attributed. The ledger only grows.

Two notes for a later packet, not conditions. First, matching the caller's key by substring breaks no test; the code compares exactly, and no key in the room contains another today, but one test with such a pair would prove it. Second, the open packet's leaf is taken when it parses, even if it is not the leaf the packet tool last wrote; treating such a leaf as unreadable, so that all four are shown, would close that.
