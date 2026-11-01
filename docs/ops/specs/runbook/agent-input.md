<!-- redact: public copy; source sha256 b0f98358e3333ae7a771aa3489d2075d4de03b022f072dabc8d05d103520024d; rules 8; mode history; words 5; sessions 0 whole, 0 truncated; host paths 0; decisions 0 -->
# Technical Specification: agent-input (the packet for a resident)

Asset: `Sessions/ops/src/runbook/agent-input.yaml` (`[PLACEHOLDER]` on 2026-10-30). Registry entry: `docs/ops/registry/runbook.md` (`RUNBOOK-02`). Spec written 2026-10-30 for Claude Shannon, adapted from the STELA runbook form (the file first held STELA's execution-decision spec, preserved in custody and in `Projects/STELA/docs/ops/specs/runbook/execution-decision.md`). Sources for the fields below: the Control root `CLAUDE.md` ("[words sha256=15b87514b499698e86a243b761548dee834aadb26e930877a64814e1d339cb42]", five steps), `Decisions/control-staff-routing-and-incident-closure.md`, and the Sessions block assignments in `storage/handoff/shannon.md`. Status: spec written 2026-10-30; the packet template asset is a placeholder.

## First Principles Rationale
A resident works only from what reaches its own conversation. Residents live in separate native containers, and a shared project root does not merge them. So every piece of work handed to a resident travels as a packet: a short, exact text that Kevin carries into that resident's chat. A routing decision is not delivery, and a file left in a room proves no delivery.

A packet has to stand alone. The resident receiving it may have been rotated, compacted or newly woken; it cannot ask the sender what was meant without another round trip through Kevin. So the packet names, in its own text, who owns the work, exactly what may be touched, whose authority allows it, and when to stop. A packet missing any of those is how one resident ends up writing a surface another resident holds, or running past a point Kevin meant to decide.

## Mechanics and Sequencing
1. **Who writes it.** The resident who owns the routing writes the packet: Shannon for Sessions team work; George for cross-room Control work. Kevin carries it. The writer of the packet is named on it, and is not presented as Kevin unless the words are his.
2. **The fields, in this order.** Each is required; "[words sha256=140bedbf9c3f6d56a9846d2ba7088798683f4da0c248231336e6a05679e4fdfe]" is written out when a field is empty.
   - **To:** the resident by `Role (Person)` and registry key. The registry, not the packet, says which body that is.
   - **From:** the packet's real author. Relayed words carry their real author; "[words sha256=b91136286b50c5be49bd3fdbd00648a98aded623894ebd9debdaa91ad844ca5c]" only for the author's own words.
   - **Owner:** the single writer of the work. One writer per surface; review grants no write authority.
   - **Scope:** the exact files or surfaces the owner may write, and that everything else is read-only. A list of paths, not a description.
   - **Authority:** whose decision this carries out, quoted with date (for example, "[words sha256=c8901a8c86493e73024c3f090295b66007038a44554458505052dbe09cff5686]"), and what still needs a further go (a hook, a timer, a registry change, a commit, a deletion, a live swap).
   - **Inputs:** the paths to read first, in order, beginning with the room's own instructions.
   - **Rules:** the house rules that apply, stated, not assumed: no session bodies read; no hook or timer wired; no registry change; no commit; no deletion; no contractions; deviations counted.
   - **Stop condition:** the deliverable, the time box ("[words sha256=427998eef293b10c9772cba8668ea2901a8e036273110ba99ff80159f551d2f9]"), and the point at which the owner stops and reports instead of continuing (a failed gate, an ambiguous authority, a surface another writer holds).
   - **Report:** where the result goes (for the Sessions team, the owner's own file in `storage/handoff/`), and what it contains: files written with sizes, what is real versus placeholder, tests run, deviations counted, and the release of the writer claim.
3. **Delivery.** Kevin pastes the packet into the resident's own chat. A packet written to a file is a draft until he does.
4. **Close.** The owner reports by the stop condition. Results that last are promoted from the team room to `archives/receipts/` or the office handoff.

[PLACEHOLDER: the paste-ready packet template in `ops/src/runbook/agent-input.yaml`, carrying the fields above as blanks to fill. Owner: Claude Shannon.]
[PLACEHOLDER: a packet check (every field present, scope given as paths, a stop condition with a time). Owner: Claude Shannon; nothing is built and none is required before the template exists.]

## Anecdotal Anchor
On 2026-10-29 a closing packet for Joy was written and left on Kevin's Desktop. It never reached her; her own earlier state note saved the day. The packet was correct and was never delivered. On 2026-10-30 the Sessions blocks ran on packets of this shape: one writer per file, the rules restated, a time to post by, and results in each member's own file. Each of the three blocks posted its result in the team room.

## Integrity Filter Warnings
- **A packet is not authority.** It carries Kevin's or George's decision; it cannot create one. A packet that claims approval the conversation does not show is refused by its recipient.
- **A packet is not delivery.** Only Kevin's paste into the resident's own chat delivers it.
- **Identity stays in the registry.** A packet names a resident by role, person and registry key, never by a session identifier frozen in prose.
- **No body content.** A packet never quotes session-body content, credentials or medical material.
- **One owner.** A packet that names two writers for one surface is not sent until one is chosen.
