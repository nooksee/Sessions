# DP-SES-0013: Ledger and board: who listens for messages

- Packet: DP-SES-0013
- Branch: agent/dp-ses-0013-2026-11-13
- Base: commit abfdd202d1a54196025b3dd710823fe4bb3957ab
- Opened: 2026-11-13T19:19:53Z
- Integrator: session-doctor
- Contractor: session-doctor
- Auditor: claudine-colbert
- Orchestrator: jo-hamming
- Authority: The operator's direction of 2026-11-13, words digest a5b81c536df0a993, entered by this packet as RoR-30; the acting Auditor by RoR-29 and by his own word for this packet

## Objective

Enter one ledger entry, RoR-30, a standing direction: a resident on the Codex provider or on the Copilot provider does not listen or watch for messages unless the operator asks for it explicitly, and is reached by his paste; messages between residents on the Claude provider stay as they are for now, and a later packet will record them. Bring the board's routes line and its updated line into agreement with that, since the board still names a relay for the Contractor on Codex. Nothing else changes: no earlier ledger entry is reworded, and no hook, timer or setting is touched.

## Scope

- RoR.md
- NOW.md
- docs/MANUAL.md

## Gates

- ror_join
- help
- template
- role_names

## Amendments

- 2026-11-13T19:22:05Z session-doctor added docs/MANUAL.md: The acting Auditor's finding: the manual still names the relay to the Contractor on Codex as a live route; PoT 7.2 asks the dependent reader to change with RoR-30

## Results

- Closed: 2026-11-13T23:56:31Z
- Contractor: session-doctor
- Paths changed: 3
- Deviations: 1
- Tree: tree 2e41b4fb11bcfb9bf2810ba6adec09153ee3ffc9
- Gate: exit 0 in 2 s: tools/test/test_ror_join.py
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 4 s: ops/bin/template --test
- Gate: exit 0 in 0 s: tools/test/test_role_names.py

## Narrative

One entry appended to the ledger, RoR-30, a standing direction, rendered from its private source by the redaction tool; no earlier entry is touched. Two lines of the board and the manual's rule on delivery agree with it; the manual came into scope on the acting Auditor's first finding, when the Contractor's search had left it out, which is the one deviation counted. After the audit passed, the automatic reviewer found on the pull request that the entry stated no ending condition, which PoT 7.6 requires of a standing direction. The operator held the finding right and gave the condition in his own words: the direction stands until he ends it, or until it is made permanent by an amendment. Reworked: the entry's Act carries that condition, its Given and Words take in his second message, and its Record names a custody item that holds the two messages joined by one space and hashes to the published digest; the leaf's authority line still cites the digest of his first message, which is in custody as its own item. The Auditor is the acting holder of RoR-29, named for this packet by the operator.

## Audit

- Verdict: PASS
- Auditor: claudine-colbert
- Audited: 2026-11-13T23:57:12Z
- Tree: tree 2e41b4fb11bcfb9bf2810ba6adec09153ee3ffc9

## Audit note

Third audit, after a review finding on the pull request that the entry stated no ending condition, as PoT 7.6 asks. Against the tree I passed, only the new entry changed: its given, words, act and record now carry a second message of the operator, which I did not witness and take as relayed, and the act ends with the condition that the direction stands until the operator ends it or an amendment makes it permanent. Against main the ledger still loses no line. By hash only, without reading them, on each of the three custody disks: the two messages joined hash to the entry's new words digest; the first message alone still hashes to the digest that this leaf's authority line cites; and the live private source equals its new custody image. The authority line therefore stays verifiable, and the joined record contains the message it cites, so I do not hold that the contract must be opened again for it. The board and the manual are as I passed them. Verdict PASS.
