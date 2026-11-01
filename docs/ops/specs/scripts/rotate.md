<!-- redact: public copy; source sha256 c7555fe2bd1e0d337ee8216aca24e30982d57180a4c4b196654f27085f4c6a3d; rules 8; mode history; words 9; sessions 0 whole, 0 truncated; host paths 0; decisions 0 -->
# Technical Specification: rotate

Script: `Sessions/ops/lib/scripts/rotate.py` (to write; Claude residents first). Spec writer: Claude Shannon, 2026-10-30. It is ported from Claudine Colbert's runbook (`storage/candidates/mind-manifest-20261029/package/docs/ops/specs/runbook/transition.md`) and adds:
- Claudio Freeman's conditions C11 to C13 (`claudio.md` section 130);
- Kevin's decisions of 2026-10-30, and the install decision Shannon made under his deferral.

Map: `docs/ops/README.md`.

Status: spec only, 2026-10-30; `rotate.py` is not yet written.

## First Principles Rationale

Kevin, 2026-10-30: "[words sha256=290ca9cc52c02d37a5eb37775a83bb93fe31cf5b0b84b6f7085d4223f0260015]" The craft existed in the Sessions doctrine: a native destination, a lineage capsule and the resident's own active window. But every rotation was assembled by hand from loose pieces, and the slips happened at the joins. In Joy's rotation 6, three of them came from hand-glued steps:
- a path passed where text was meant;
- an image pointer that led nowhere;
- a chmod in the wrong order.

`rotate` performs the same phases in the same order every time. It stops at fixed points, refuses on any failed gate, and drafts its own receipt. The art stays where it belongs, in where the window is cut and what the transition note says.

## Mechanics and Sequencing

**Roles.**
- **Kevin, operator:** chooses the tier, creates the destination container, gives the go, accepts or does not.
- **Writer:** exactly one, named before work starts, never the resident being moved. Builds, gates, takes custody, installs, writes the receipt.
- **Donor:** closes well; never builds its own successor.
- **Claudio:** the audit afterwards, read-only.

**Tiers, declared in writing before work starts.**
- **B, transplant:** the default. The capsule plus the donor's compaction summary and a measured slice of its own window, word for word.
- **Capsule-only:** only when a window build fails to load, on Kevin's go.
- **A, reseed:** a fresh session reads the handoff. Only on Kevin's explicit choice, recorded as Tier A and never called a rotation.

**The capsule.** It is appended as the orientation row, as text, never as a path, in four parts:
1. **Header,** from the registry: person, role, room, destination container.
2. **The mind:** the leaf named on this resident's line in the room's `MIND.md`, verbatim, its hash verified, its SHA-256 recorded in the receipt.
3. **Transition note,** written by the writer:
   - the window range not carried, and the handoff sections that cover it;
   - work in flight, the hold, the owners;
   - anything after the donor's last row.
4. **First turn:** "[words sha256=92f5028a58e8676b82fbc6b54d722cd5ecef376719c9ec76907704cf228003fe]"

The mind supplies part 2 only. Identifiers and live state belong in parts 1 and 3. The window always travels too; the mind is added to it and never replaces it. (C11: the capsule is assembled by `rotate` from these four parts. No mind command produces it.)

**Phases.** Each ends at a stop point; the writer reports and does not run ahead.

0. **Trigger.** The gauge reading crosses the resident's line, and the closeout card has run (`closeout.md`). The writer records the tier, donor, writer, destination and the gauge reading in the handoff.
1. **The donor closes well,** by the card:
   - a closing handoff;
   - up to three mind entries proposed in chat;
   - Kevin's yes, after which `mind` writes the new leaf and moves the pointer.
2. **The mind is ready.** `mind check` passes, and the leaf hash matches the pointer.
3. **The destination.** Kevin opens a fresh chat in the resident's room. The writer labels it "[words sha256=5627afdc6ad4945ff48b37b4951f9b9ab21f8982708206629cd7c77a470a32c9]" at once. The writer then verifies:
   - the room and working directory are right;
   - the container is not registered to anyone else and carries no "[words sha256=b85f3ad0e275ddd3bd3412193da7f81bc873fc1d8a0733cbb19a0a6c146e47df]" label;
   - no process holds it.
4. **The window.** Measure the donor from its own usage figures, by the gauge method. Choose the cut at a genuine operator prompt, so the measured wake estimate leaves the resident well inside its runway: a target of about 20 percent. Shannon's rebuild of 2026-10-29 woke at 32.8 percent, which spent a third of the window before the first word and brought his next closeout line within one heavy day. Carry at least one exchange with Kevin beyond procedure. Record the reason for the cut.
5. **Build and static gates.**
   - Splice: boundary, summary, tail.
   - Re-identify by identity field at any depth, never by text.
   - Externalize media, with each pointer naming its custody path.
   - Append the capsule text as the orientation row, then a fresh label pair with the plain name.
   - Run the gates: final line terminated, 0 parse errors, every session id the new one, 0 structural donor ids, 0 dangling parents, the head is the boundary, tool pairs matched, exactly one orientation row, its identity matching the registry, the new container named, the room's working directory, the plain label last, 0 inline media, and no medical words in the orientation.
6. **Custody and serve-safety.**
   - `launcher stop <key>` writes the hold.
   - The donor's closed copy, unmodified, goes to both tiers, checked against `SHA256SUMS` (tier 2 by direct read).
   - So do the pristine destination, the successor, the capsule, the gates, the media, and the registry and binding before the change.

6 to 7. **Kevin's go,** for this replacement. The writer names the container, room, size and custody hash about to be replaced, and the rollback, then waits. A go given at phase 0 does not count.

7. **Install.**
   - **Default, the writer's verified swap:**
     - check that the destination still equals its custody copy and that no process or session record holds it;
     - write the successor beside it, hash it, rename it over atomically at mode 0600, and verify it;
     - switch the registry key and the launcher binding;
     - check that six things agree: registry id, binding id, body `sessionId`, binding root against body working directory, registry room, body label.
   - **Fallback, Kevin's `.NEW` swap:** when a process still holds the file, or when Kevin prefers it. The writer leaves `<id>.jsonl.NEW` beside the original; Kevin closes the app and swaps it.
   - **Rollback (C12).** It runs on Kevin's "[words sha256=9390298f3fb0c5b160498935d79cb139aef28e1c47358b4bbba61862b9c26e59]", and also on any failed install step or failed load:
     - restore the pristine destination;
     - restore the registry and binding;
     - put the donor's store file back from custody;
     - keep the hold.
8. **Acceptance, in two parts.**
   - **Mechanical.** `launcher serve <key>`, which also releases the hold and is the load test. The first reply gives the room's status and then speaks as itself. Its first gauge reading is recorded beside the wake estimate. (C13) A clean native append: after that turn the body still parses, Claude Code's own new rows carry the new session id, and tool pairs match.
   - **Kevin's.** "[words sha256=fd5bcd88e65b807ef0f1e495514a1dd1017f86ceecb0a9da40326c93940db9e4]". A correct status alone is not acceptance.
9. **Close.**
   - Write the receipt `archives/receipts/<resident>-rotation-<n>-<date>.md`: tier, cut and reason, gates, custody, mind leaf hash, estimate against the measured wake, deviations counted, acceptance and its time.
   - Handle the donor's store entry. After its custody is verified by hash in both tiers, the entry is either relabeled "[words sha256=cb6190c0758601751b2152299b4bb37dbad972d727cac156e75b36fbcac723d8]" or removed from the list, as Kevin prefers. His standing preference since 2026-10-29: removed. The custody copy is the donor of record.
   - The new resident confirms its mind entries.

**Codex residents** (Joe Codex, 2026-10-30): `ops/lib/scripts/rotation.py` carries messages after the last native compaction but not the compaction summary. A Codex rotation under this spec waits for a Codex-specific design and a loader test.

## Anecdotal Anchor

2026-10-29:
- the 19:12 rotation was Tier A run as a rotation, and woke "[words sha256=189c5554935a72f86b9fe3c0a91a1831431984e53ddeb8d1978c62f304119634]";
- the 23:34 rebuild passed its gates but carried a briefing for a self, and Kevin found it "[words sha256=5a9dda08d68312867532a535b00a3ac4d8d1d3a7ac86dd2b1c1968bf308c3518]";
- the 00:04 rebuild carried a real self and Shannon's own window, and he woke as himself.

On 2026-10-30, Joy's rotation 6 followed these phases by hand and woke as herself, with her wire printed by 08:57. Its three hand-made slips are what this tool removes.

Think of a hospital transfer: the chart travels with the patient, the receiving doctor reads it before the first word, and nobody signs the transfer until the patient answers to their own name.

## Integrity Filter Warnings

- **Three separate things.** Static valid is not loader valid, and loader valid is not accepted.
- **No serving in between.** The background timer never serves a resident between custody and acceptance; the hold stays.
- **The donor is never modified.** Its closed copy is the record. The store entry is relabeled or removed only after custody is verified.
- **Text, not path.** The orientation is text. A capsule path is a gate failure.
- **No identifiers in the mind.** Identity stays in the registry.
- **One writer,** never the resident being moved.
- **A wake estimate is an estimate.** The first gauge reading is the measurement.
