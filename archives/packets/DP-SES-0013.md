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

- Closed: 2026-11-13T19:22:16Z
- Contractor: session-doctor
- Paths changed: 3
- Deviations: 1
- Tree: tree e86c6ad5164cbafd75a3bc2c11c5246d7556c2d2
- Gate: exit 0 in 3 s: tools/test/test_ror_join.py
- Gate: exit 0 in 1 s: ops/bin/help --test
- Gate: exit 0 in 5 s: ops/bin/template --test
- Gate: exit 0 in 0 s: tools/test/test_role_names.py

## Narrative

One entry appended to the ledger, RoR-30, a standing direction, rendered from its private source by the redaction tool; no earlier entry is touched, and the words digest equals the hash of the custody item the entry names. Two lines of the board changed to agree with it. The acting Auditor failed the first tree on one finding: the manual still named the relay to the Contractor on Codex as a live route. Reworked: the scope was amended to take in the manual, whose rule on delivery now says that a resident on either other provider is reached by the operator's paste only, and that the relay of 2026-11-07 ended with RoR-30 and is not used; what that relay showed about queued lines is kept as true of any such route. A search of every tracked file outside the ledger and the archives finds no other reader that names the relay. The Contractor's first search had left the manual out; that is the one deviation counted. The Auditor is the acting holder of RoR-29, named for this packet by the operator.

## Audit

- Verdict: PASS
- Auditor: claudine-colbert
- Audited: 2026-11-13T19:22:49Z
- Tree: tree e86c6ad5164cbafd75a3bc2c11c5246d7556c2d2

## Audit note

The finding of my first audit is closed. The scope was amended, with its reason recorded, to take in the manual, and against the tree I failed only that file changed, in one line. Its rule on delivery now says that the operator's paste is the only route to a resident on Codex or on Copilot, who does not listen or watch for messages unless he asks, and that the relay of 2026-11-07 ended with the new entry and is not used; what that relay showed about queued lines is kept as true of any such route. A search of every tracked file outside the ledger and the archives finds no other reader that names the relay or a waiter towards another provider. The rest stands as my first audit read it: the ledger appended only, with every field of its form, the words digest matching the three custody copies, and the board in agreement. The entry's record field names the ledger, the board's routes line and this packet, whose leaf names all three paths; I do not hold that it must also name the manual, and it is left as written. Verdict PASS.
