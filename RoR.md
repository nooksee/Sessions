<!-- redact: public copy; source sha256 d16ac7dfccc180778d0aa4018f51d75917d0403317b9e18b2883acbd35dde412; rules 8; mode record; words 22; sessions 0 whole, 0 truncated; host paths 2; decisions 4 -->
# RoR: the decision ledger of the Sessions room

This is the room's decision ledger (PoT 1.2.10, 1.3.2). Each entry records one operator decision, standing direction, exception, acting holder, or anomaly that needs a decision: the operator's exact words, when they were given, the act they authorize, and a pointer to the record of that act.

Entries are appended only, generated from `ops/src/reports/ror.md.tpl` (`ops/bin/template ror`), numbered permanently, and never reworded. A correction is a new entry that cites the one it corrects (PoT 1.2.13).

### RoR-1: ratification

- **Given:** 2026-10-30, in conversation with the Session Continuity Manager; received shortly before the entry time below, which is the nearest clock read (the message carries no timestamp of its own)
- **Words:** "[words sha256=ff067bcbbbe3b817e8c5f83436e63b1f4788a67d79b082b9a1ef52608a000e44]"
- **Act:** Ratification and adoption of Sessions/PoT.md, the exact text with sha256 388546477dd9f01f2997d38976f5b6f9fd87f13e3697562687e9340e8766af94, under PoT 7.1. It opens the conforming programme of PoT 7.2. It was given while a blocker-only check of this text (workflow run wf_97f499ac-088) was still running; any blocker it reports is brought to the operator as an amendment under PoT 7.3, and the text in force stays this one until then.
- **Record:** archives/pot/PoT-38854647.md, a write-once snapshot of the ratified text, sha256 388546477dd9f01f2997d38976f5b6f9fd87f13e3697562687e9340e8766af94
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-30 17:56:55 EDT

### RoR-2: anomaly

- **Given:** 2026-10-30, in conversation with the Session Continuity Manager; received shortly before the entry time below, which is the nearest clock read
- **Words:** "[words sha256=9d4a4fdb078a9a534d0298c06e1e8bf82a818a69e52a56ed9716d9b0831dd686]"
- **Act:** Anomaly, counted: 3 deviations from PoT 1.1.11 by the Session Continuity Manager, who created the one-file folders archives/drafts/, archives/pot/ and storage/pot/ where a base folder already fit. Correction: both archive snapshots were moved to the archives/ root by copy, hash verification and unlink (PoT 1.2.9), and both folders removed. This entry corrects the Record line of RoR-1 (PoT 1.2.13): the ratified text's snapshot is now archives/PoT-38854647.md, with the same sha256. The opening words 'totally approve' answered the Amendment 1 plan then in progress; they are not a ratification of Amendment 1, which follows PoT 7.3.
- **Record:** archives/PoT-38854647.md, sha256 388546477dd9f01f2997d38976f5b6f9fd87f13e3697562687e9340e8766af94; archives/PoT-draft-v0-de5d6c0c.md, sha256 de5d6c0c508baa024549ad2dc3ec4726f8302b4e47289cc2383a9589a1f9e674
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-30 18:25:55 EDT

### RoR-3: decision

- **Given:** 2026-10-30, as an answer the operator selected in a question dialog from the Session Continuity Manager; the selection arrived shortly before the entry time below, which is the nearest clock read
- **Words:** "[words sha256=7c32e7542846c7b8785a5ee06389070bf2b956984a1a1de03bcf940050345275]"
- **Act:** Answer to the question: where should mind leaves live? The operator chose the archives/ root over archives/surfaces/ (PoT 1.1.11): leaves are archives/MIND-<key>-<date>-<hash8>.md, grouped by their MIND- prefix, and the Git ignore rule matches that prefix. The mind tool's writer changes its leaf location, specification and tests before the ignore rule lands through Control's writer process; no mind leaf exists yet.
- **Record:** storage/handoff/claudine.md section 6 (the condition this answers); the change to ops/lib/scripts/mind.py and docs/ops/specs/scripts/mind.md, when made, is that tool's own record
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-30 22:04:47 EDT

### RoR-4: decision

- **Given:** 2026-10-30, as an answer the operator selected in a question dialog from the Session Continuity Manager; the selection arrived shortly before the entry time below, which is the nearest clock read
- **Words:** "[words sha256=e651ceb1c97eb69d6a900f99f6aefbd709218510af0b0c53d0ac85573221625c]"
- **Act:** Answer to the question: the default install method for a rotation. The operator chose that PoT name the writer's verified swap as lawful (the body file replaced atomically while no client holds it and while it still equals its custody copy), with the operator's .NEW swap kept as the fallback. Carried into PoT Amendment 1 as a new rule in 5.2; the rotation specification already makes the verified swap its default.
- **Record:** storage/handoff/claudine.md section 6 (the condition this answers); docs/ops/specs/scripts/rotate.md phase 7
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-30 22:04:47 EDT

### RoR-5: decision

- **Given:** 2026-10-30, as an answer the operator selected in a question dialog from the Session Continuity Manager; the selection arrived shortly before the entry time below, which is the nearest clock read
- **Words:** "[words sha256=b53b4fc369b9358bfa77bf4ce5abc0e7e400b1a82696fb85bbc3ff1a3def6cf1]"
- **Act:** Compaction instead of rotation (PoT 5.2.6) for Assistant Session Continuity Manager (Claudine Colbert, claudine-colbert), the Control desktop continuity manager (George Friend, george-x) and Session Continuity Apprentice (Joe Codex, joe-codex), now. Each first brings its own handoff current; the operator runs the compaction in each one's own client.
- **Record:** storage/handoff/claudine.md section 9 (the proposal with the readings: Claudine 63.6, George 82.5, Joe 80.3, measured by gauge, last observed 23:00 to 23:39)
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-30 23:51:00 EDT

### RoR-6: decision

- **Given:** 2026-10-30, as an answer the operator selected in a question dialog from the Session Continuity Manager; the selection arrived shortly before the entry time below, which is the nearest clock read
- **Words:** "[words sha256=c97a444aaa3f71d0d3bc00d15b5227d8431e51b0f6c236fb1ef7586e48d9b237]"
- **Act:** A hash-verified custody copy of the day's untracked canon (PoT.md, RoR.md, ops/, tools/, docs/, archives/, the day's untracked Receipts/ and the team room storage/handoff/), tonight, by the Session Continuity Manager, to both custody tiers, with hard_vol2 counted only on a direct-read verify (PoT 5.3.3). Nothing is moved or deleted.
- **Record:** the custody receipt for this copy, when written
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-30 23:51:00 EDT

### RoR-7: decision

- **Given:** 2026-10-30, as an answer the operator selected in a question dialog from the Session Continuity Manager; the selection arrived shortly before the entry time below, which is the nearest clock read
- **Words:** "[words sha256=8a7adbce0a68cbd30601e51e6a9735d95d69c2637bde758a56c313c74c5a8bcc]"
- **Act:** The first live test of the closeout hook, on a disposable thread that is never a resident, is to run tonight, against the Session Continuity Manager's recommendation of tomorrow. Its prerequisites stand unchanged: the runbook and fixtures, the independent review of the frozen code and of the hook wiring (PoT 6.1.2, 6.1.3), and the operator's named go naming the folder, the settings file, the command and the frozen hashes (PoT 6.1.1).
- **Record:** storage/handoff/claudine.md section 9 (the proposal with the readings: Claudine 63.6, George 82.5, Joe 80.3, measured by gauge, last observed 23:00 to 23:39)
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-30 23:51:00 EDT

### RoR-8: anomaly

- **Given:** 2026-10-30, in conversation with the Session Continuity Manager, shortly before the entry time below
- **Words:** "[words sha256=03f91e4b26cf8775d29c3a85e9d6f3fe077c598843598ef58ff006a2ea4c5211]"
- **Act:** Anomaly, counted 1: in a side conversation the operator addressed the Assistant (claudine-colbert) as the Session Continuity Manager, and the Assistant answered in the first person across many turns, accepting a direction ('your role is the lead') before correcting the address in its last answer. The labels and the registry were correct (measured at 23:46); the failure was the missing correction of a misaddress. Proposed remedy, for a later amendment: a resident addressed as another resident says so at once, before acting on what was said. Also recorded: compaction under RoR-5 now waits for the operator's reboot.
- **Record:** [host path 1] is chugging sputtering.txt (the operator's export of a side conversation with the Assistant, sha256 5471d9ef4de0d789)
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-30 23:54:46 EDT

### RoR-9: standing direction

- **Given:** 2026-10-30, in the side conversation recorded in RoR-8 (operator's own words, quoted from the export)
- **Words:** "[words sha256=cc566b3f8010e020a61b1d57a27964b576cbf3f8d01d40607eb261eee502265d]"
- **Act:** Standing directions, scope the Sessions room and its tools, ending only when carried into the constitution by amendment (PoT 7.6): (1) all authority runs from the operator; (2) roles are pre-eminent: code, specifications and templates name roles, the registry alone maps roles to residents, records keep the historical holder, labels keep plain names; (3) the domain owner leads its own initiative, other executive staff contribute under its packets, and the Control desktop continuity manager keeps a veto and authority to push back. To be proposed as Amendment 2, with the misaddress rule of RoR-8.
- **Record:** [host path 1] is chugging sputtering.txt (the operator's export of a side conversation with the Assistant, sha256 5471d9ef4de0d789)
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-30 23:54:46 EDT

### RoR-10: decision

- **Given:** 2026-10-30, in conversation with the Session Continuity Manager, shortly before the entry time below
- **Words:** "[words sha256=c1486c57c1a8414d4fac2fcee1d494ebed2312b202ec83914f3bec115d044f56]"
- **Act:** Answer to the question: who leads the Sessions series. The lead is the Session Continuity Manager; every direction in the side conversation of RoR-8, except its last turn, was meant for that role. The Assistant's section 9 coordination proposal and its acceptance of the lead are superseded; the Assistant remains lead writer of gauge, closeout and mind and the live-test operator. The words 'she can be the experiment' are recorded but not acted on: making a resident the subject of a live test is a named act that needs its own plan, review and named go (PoT 6.1.1, 6.1.2).
- **Record:** RoR-8 and RoR-9; storage/handoff/claudine.md section 9
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-30 23:59:19 EDT

### RoR-11: direction

- **Given:** 2026-10-31, in conversation with the Session Continuity Manager, shortly before the entry time below, after the reboot and the compactions of RoR-5
- **Words:** "[words sha256=cac20d3202838584ac9ec8fbabe331b1cb234fe683dab01235bb84a613404cc5]"
- **Act:** The block Live test 1 now ends at 01:15 EDT, 30 minutes after the direction, instead of 02:00. On the coordinator's reading, the live run itself is not in this block: after Claudio's PASS it needs the operator's named go and about 45 minutes of prompts typed by the operator, more than the block holds, so under the plan's stop condition it moves to the next block. Within the 30 minutes the members prepare: the runbook and the test folder (Claudine), the review of the frozen code and of whatever runbook has arrived (Claudio), the review of Amendment 1 revision 4 and a measurement method (Joe), and the two Control readings or the time they will come (George, by request). The prerequisites of RoR-7 stand. A further direction from the operator overrides this reading.
- **Record:** storage/handoff/shannon.md, "Block plan: Live test 1, revision 2"
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-10-31 00:42:51 EDT

### RoR-12: ratification

- **Given:** 2026-11-01, in conversation with the Session Continuity Manager, shortly before the entry time below, after the team reviews (Claudine section 7, Joe) and the Independent Reviewer's PASS on the changed lines (claudio.md section 135, 01:59:57 EST)
- **Words:** "[words sha256=28a275997a14ecfcfcacee25c1f741afdadaee66bdb0bd42163125ea716d5b8b]"
- **Act:** Amendment 1 revision 4 is applied under 7.3: PoT.md is now the reviewed text, sha256 ef2e16c0e3baa2312247d349d2b336365d29b82c2c9123451af9c2537b63efed, snapshotted write-once as archives/PoT-ef2e16c0.md. The superseded text 388546477dd9f01f2997d38976f5b6f9fd87f13e3697562687e9340e8766af94 remains as archives/PoT-38854647.md. Applied by the Session Continuity Manager (7.3). The Independent Reviewer audits the applied text next (7.3); the port candidate Amendment 3 rebases on this text.
- **Record:** PoT.md; archives/PoT-ef2e16c0.md; storage/PoT-amendment-1-delta.diff (the full delta since b853f7d0); claudio.md section 135; storage/handoff/claudine.md section 7; storage/handoff/joe.md
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-11-01 02:13:53 EST

### RoR-13: standing direction

- **Given:** 2026-11-02 02:05:52 EST, in conversation with the Session Continuity Manager (the session body's row at 07:05:52 UTC), as the operator left the desk
- **Words:** "[words sha256=e3d2276e79b4a9c49133becaa2a5993c44c4bb41f1ee22d4f5a2ec6d77bffcc5]"
- **Act:** A pocket authorization in two parts. (a) The ratification of PoT Amendment 2 revision 4, sha256 5b93c454f93e7651e7cb91c834cd84dec8f948f25c22781c8a6ad92a037c1289, given in advance and conditioned on the reviews ("[words sha256=743bfcbb3d8133a077b058546b02186f36de66ce03a1d0875caafaa4475975dc]"): it takes effect when the team's reviews (Assistant, Apprentice) and the Independent Reviewer's review of that exact revision are posted without a blocker, and the Session Continuity Manager then applies it under 7.3 without a further sentence; a revision at any other hash is not covered. (b) Other matters concerning the completion of the root-level directory structure in the STELA shape: block 7 (the frozen runtime's relocation to Control-Runtime; the Scripts/, Config/ and Resident-Center/ lanes leaving the room; the door's pointer switch to the landed identity tools), each act still gated by the Independent Reviewer's PASS on its exact heads and by its own receipt, which names this entry as its authority and the heads, hashes and window a go would have named. Not covered: ratifying any other law (Amendment 3 waits for its own hash-bound sentence); the public gate's irreversible acts (the rewritten history's push, the route choice, a repository's deletion, the visibility switch). Ends when block 7 closes with the Independent Reviewer's audit, or when the operator returns and says otherwise, whichever is first. The planned process altered: 6.1.2's named go for each act, with the operator present. The reasoning: the operator is away and asked for speed; the gates that make a go safe (the review of the exact heads, the receipt, the rollback) are kept, and only his presence at the moment of each act is waived; the bounds above are the Session Continuity Manager's reading of his words, so that a blanket sentence does not become blanket authority.
- **Record:** This entry; the receipts of each act taken under it, each citing RoR-13; storage/handoff/shannon.md, block 9, at sha256 ef6d480498a36e259ffa9aac0b5eee451b48965ad420bcdbf4ad9d2dba48ca91 when this entry was rendered
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-11-02 02:09:47 EST

### RoR-14: ratification

- **Given:** 2026-11-02 02:05:52 EST, in advance, inside the pocket authorization of RoR-13, conditioned on the reviews ("[words sha256=743bfcbb3d8133a077b058546b02186f36de66ce03a1d0875caafaa4475975dc]"); effective 2026-11-02 02:10:00 EST, when the Independent Reviewer's PASS (claudio.md section 169) joined the Assistant's (claudine.md section 34, 02:05:50 EST) and the Apprentice's (joe.md, 02:02:43 EST), each on revision 4 at this hash
- **Words:** "[words sha256=419734d7c8e837d44b97285d119b4335f83a66b903bc001dc97c61df5e03d5ac]"
- **Act:** Amendment 2 revision 4 is applied under 7.3: PoT.md is now the reviewed text, sha256 5b93c454f93e7651e7cb91c834cd84dec8f948f25c22781c8a6ad92a037c1289, snapshotted write-once as archives/PoT-5b93c454.md; the superseded text ef2e16c0e3baa2312247d349d2b336365d29b82c2c9123451af9c2537b63efed remains as archives/PoT-ef2e16c0.md. The 7.1 in force at the moment of ratification (ef2e16c0) governs this adoption, so this entry carries the operator's words here; from this entry on, the ledger's source is archives/RoR-words.md and RoR.md is its derived copy (1.2.10 and 1.3.2 as amended). The conforming programme's first item (7.2): the custody copy and the source file first, then the first render of the public ledger, and the rendering of every tracked file that carries the operator's words, measured at this tip by the Assistant (claudine.md section 34): 20 files, 49 spans, 12 of them Markdown (this ledger, three receipts, eight maintained documents) and 8 code, template or test files to classify first, by the redact tool at its passed head (PR #9, under revision by the Assistant); until that render those files are out of rule by this entry and the repository stays private. RoR-9 stands; no clause of it ends; 4.1.8 carries its pre-eminence clause into law. Applied by the Session Continuity Manager (7.3); the Independent Reviewer audits the applied text next (7.3). Amendment 3 rebases on this text.
- **Record:** PoT.md; archives/PoT-5b93c454.md; storage/PoT-amendment-2.diff (sha256 57ed03c0dc89d6edb032f7e1000a1b34dc4ed48c4f0a88906e7c3b1af5a3bc3e); storage/PoT-amendment-2-notes.md; claudine.md sections 31 to 34; joe.md, the reviews of revisions 1 to 4; claudio.md sections 164 to 169; RoR-13
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-11-02 02:13:01 EST

### RoR-15: standing direction

- **Given:** 2026-11-02 02:51:23 EST, in conversation with the Session Continuity Manager (the session body's row at 2026-11-02T07:51:23.151Z), after the plan passed (claudio.md section 176, 02:34:44 EST)
- **Words:** "[words sha256=a40ea377e7b9e57d926185ad746c5d41817a3d007ff31389742b89ddca4ee1f6]"
- **Act:** The public gate, as the plan of part 3 (storage/handoff/shannon.md, revisions 2 to 7, passed by the Independent Reviewer in claudio.md sections 166 to 176) states it, under route B with the repository name nooksee/sessions kept: the rewrite of the history in a scratch clone; the old repository renamed and kept private; a new nooksee/sessions pushed from the rewritten history; the old repository deleted after the Independent Reviewer's post-push audit; protection and scanning; the visibility switch last. Each of these steps runs only after the Independent Reviewer's PASS on its exact inputs, named by hash (the rewritten head, the bundle in custody, the scans), and its receipt cites this entry and that PASS. Not covered: any step the passed plan does not name, any change to the plan itself (a blocker that alters it returns to the operator), any other repository. Ends when the visibility switch is done and the Independent Reviewer's audit of it closes, or when the operator says otherwise. The planned process altered: 6.1.2's named go for each irreversible act, replaced for this programme by one go bounded by the reviewer's PASS on exact hashes. The reasoning: the operator directed that he not be asked for a signature act by act (his words of the same minute, kept in this source); the gates that make each act safe are kept, and only the repetition of the request is removed. The route and the name were decided by the Session Continuity Manager under the operator's deferral of 2026-11-01, with the Independent Reviewer's concurrence (section 167), and are named in the words.
- **Record:** This entry; storage/handoff/shannon.md, block 9 and the plan's revisions 2 to 7; claudio.md sections 166 to 176; the receipts of each step, each citing RoR-15
- **Entered by:** Session Continuity Manager (Claude Shannon), registry key session-doctor, at 2026-11-02 02:51:54 EST, in the ledger's source archives/RoR-words.md (1.3.2); RoR.md receives it only by the render

- **Correction to RoR-15, by its writer (2026-11-02 02:52:04 EST):** the Act says the operator's words about signatures are "[words sha256=0d50ad7ec1bb51bebc6c2b20fa291bc6dcb44a25f173f7f6721c379fecac6ed5]"; they were not entered with it. They were given at 02:49:22 EST on 2026-11-02 (the session body's row at 2026-11-02T07:49:22.254Z): "[words sha256=9adf45980192e4a9d3e668e595970b7279896247257eb87cebf8e77ba9e4d8bd]". The entry above is left as written (1.2.13).

### RoR-16: operator-directed filing amendment and bounded process exception

- **Given:** 2026-11-03 in conversation with Joe Codex; the operator message has no supplied timestamp, so the entry clock below is the nearest recorded write time
- **Words:** "[words sha256=b00282bccaa0549566854ddae3ddaa63cb2c2283c3a3fdc5ea6f2d37f283a15d]"
- **Act:** Apply the immediate project-local scratch filing update now, without the normal PoT 7.3 pre-application amendment sequence for this named act. The applied PoT SHA-256 is 5a2a17a92cbae0e2d8a187869d04aaf6ee36142c31d04e2b5cbceb7f34d48877. Scope: owned active cases in storage; owner/operation-scoped scratch and its closeout in var/tmp; current filing pointers and retired Evidence/Receipts numbers; supporting instructions, factories and self-test scratch defaults. The existing A3 filing payload is incorporated; accession A4 is not. The exception ends when this exact filing update and its record are applied; PoT 7.3 remains unchanged for future amendments. It waives no privacy, retention, custody, native-body, host/service or protected Git requirement. Joe is the named source writer for this policy/default correction; JoJo retains Git integration. No independent review of Joe's own work is claimed.
- **Record:** PoT.md and archives/PoT-5a2a17a9.md, sha256 5a2a17a92cbae0e2d8a187869d04aaf6ee36142c31d04e2b5cbceb7f34d48877; private act receipt archives/receipts/var-tmp-policy-20261103.md. Pre-change law and both ledger preimages were copied to two external custody tiers and all six copies passed direct-read hash verification before this entry.
- **Entered by:** Session Continuity Apprentice (Joe Codex), registry key joe-codex, as Kevin's named writer for this exact act, at 2026-11-03 01:07:00 EST (-0500) / 2026-11-03 06:07:00 UTC

### RoR-17: operator-directed single-source alignment and gate

- **Given:** Kevin's direct finish-line instruction, received 2026-11-03; no operator timestamp was supplied
- **Words:** "[words sha256=6cd97026509801d7f00af3e2a1e090893fd06cdd0182f3a5c9bb2d45cfc8a038]"
- **Act:** Decision: Operator. Scope: PoT.md. Target policy SHA-256: 457fe85955dad98675e2ed5f6c7a4a5ca409c3b598c7221ef45cd8509c2f04cb. Implement the directed constitutional alignment and exact-base/head authorization gate; do not reinstate the superseded Amendment 3 permission loop.
- **Record:** PoT.md; archives/PoT-457fe859.md; archives/PoT-authority-457fe859.md; private words source archives/RoR-words.md; Words SHA-256: 6cd97026509801d7f00af3e2a1e090893fd06cdd0182f3a5c9bb2d45cfc8a038
- **Entered by:** Chief Repository Operations Officer (JoJo Git), registry key jojo-git, at 2026-11-03 02:00:20 EST (-0500)

### RoR-18: ratification of reviewed foundational policy and connected readers

- **Given:** 2026-11-04T12:12:26-05:00, first observed current operator instruction; utterance time was not supplied. Effective only on actual recorded application, not a backdated event.
- **Words:** "[words sha256=b1b34b0d43225bac58b69bcb05c87867e1ff84f18b687b9cb48dd3f5052ae67c]"
- **Act:** Decision: Operator. Scope: PoT.md. Target policy SHA-256: 2dc41d8754189cbb52d65bca4bc387ba508eedf1cd2156f2e62f408b86eb21e7. Apply the exact reviewed foundational policy and its eleven-path reader wiring under the current named instruction. The target/hash attribution is the operation writer's explicit binding of the current direction, not a quotation of a hash typed by the operator. No native, host-service or operational-state change is part of this adoption.
- **Record:** PoT.md; archives/PoT-2dc41d87.md; archives/PoT-authority-2dc41d87.md; private words source archives/RoR-words.md; Words SHA-256: b1b34b0d43225bac58b69bcb05c87867e1ff84f18b687b9cb48dd3f5052ae67c
- **Entered by:** Session Continuity Apprentice (Joe Codex), joe-codex; prepared 2026-11-04T12:21:17-0500; actual application recorded in operation receipt

- **Correction to RoR-14, by its writer (2026-11-04 16:30:03 EST):** the Record field names storage/PoT-amendment-2.diff and storage/PoT-amendment-2-notes.md; on 2026-11-04 at 14:27:34 EST the Apprentice moved those files, with the candidate storage/PoT-amendment-2.md, to archives/working-records/20261102-policy-a2/ by copy, hash verification and unlink, on the Session Continuity Manager's written consent (shannon.md, block 10 close), because a record's cited evidence does not live in the disposable lane (1.1.4, 1.1.5). The candidate's bytes are the law snapshot archives/PoT-5b93c454.md. The entry above is left as written (1.2.13); RoR.md shows this note at its next render.

**Correction, by the Assistant Session Continuity Manager (Claudine Colbert), 2026-11-04 22:26:08 EST.** In this record, PR #9 refers to the nooksee/sessions repository as it stood before its history rewrite of 2026-11-04. Each such pull request's title, body, comments and reviews are in the custody export of batch sessions-prerewrite-20261104, and the map from each number to its export entry is in archives/receipts/history-rewrite-20261104.md, the rewrite receipt.
