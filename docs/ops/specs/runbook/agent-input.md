# Technical Specification: agent-input (the packet for a resident)

Asset: `Sessions/ops/src/runbook/agents/agent-input.yaml`. Registry entry: `docs/ops/registry/runbook.md` (`RUNBOOK-02`). Spec written 2026-10-30 for Claude Shannon, adapted from the STELA runbook form (the file first held STELA's execution-decision spec, preserved in custody and in `Projects/STELA/docs/ops/specs/runbook/execution-decision.md`). Sources for the fields below: the Control root `CLAUDE.md` ("Before writing", five steps), `Decisions/control-staff-routing-and-incident-closure.md`, and the Sessions block assignments in `storage/handoff/shannon.md`. Status: the fill-in packet form is maintained; it does not deliver a packet or create authority.

## First Principles Rationale
A resident works only from what reaches its own conversation. Residents live in separate native containers, and a shared project root does not merge them. So every piece of work handed to a resident travels as a packet: a short, exact text that Kevin carries into that resident's chat. A routing decision is not delivery, and a file left in a room proves no delivery.

A packet has to stand alone. The resident receiving it may have been rotated, compacted or newly woken; it cannot ask the sender what was meant without another round trip through Kevin. So the packet names, in its own text, who owns the work, exactly what may be touched, whose authority allows it, and when to stop. A packet missing any of those is how one resident ends up writing a surface another resident holds, or running past a point Kevin meant to decide.

## Mechanics and Sequencing
1. **Who writes it.** The resident who owns the routing writes the packet: Shannon for Sessions team work; George for cross-room Control work. Kevin carries it. The writer of the packet is named on it, and is not presented as Kevin unless the words are his.
2. **The fields, in this order.** Each is required; "none" is written out when a field is empty.
   - **To:** the resident by `Role (Person)` and registry key. The registry, not the packet, says which body that is.
   - **From:** the packet's real author. Relayed words carry their real author; "verbatim" only for the author's own words.
   - **Owner:** the single writer of the work. One writer per surface; review grants no write authority.
   - **Scope:** the exact files or surfaces the owner may write, and that everything else is read-only. A list of paths, not a description.
   - **Authority:** whose decision this carries out, quoted with date (for example, "Kevin, 2026-10-30: ..."), and what still needs a further go (a hook, a timer, a registry change, a commit, a deletion, a live swap).
   - **Inputs:** the paths to read first, in order, beginning with the room's own instructions.
   - **Rules:** the house rules that apply, stated, not assumed: no session bodies read; no hook or timer wired; no registry change; no commit; no deletion; no contractions; deviations counted.
   - **Stop condition:** the deliverable, the time box ("post by HH:MM"), and the point at which the owner stops and reports instead of continuing (a failed gate, an ambiguous authority, a surface another writer holds).
   - **Report:** where the result goes (for the Sessions team, the owner's own file in `storage/handoff/`), and what it contains: files written with sizes, what is real versus placeholder, tests run, deviations counted, and the release of the writer claim.
3. **Delivery.** Kevin pastes the packet into the resident's own chat. A packet written to a file is a draft until he does.
4. **Close.** The owner reports by the stop condition. Results that last are promoted from the team room to `archives/receipts/` or the office handoff.

The fill-in fields are in `ops/src/runbook/agents/agent-input.yaml`. No
automated packet validator is provided; the owner checks the required fields
against this specification before Kevin delivers the packet.

## Anecdotal Anchor
On 2026-10-29 a closing packet for Joy was written and left on Kevin's Desktop. It never reached her; her own earlier state note saved the day. The packet was correct and was never delivered. On 2026-10-30 the Sessions blocks ran on packets of this shape: one writer per file, the rules restated, a time to post by, and results in each member's own file. Each of the three blocks posted its result in the team room.

## Integrity Filter Warnings
- **A packet is not authority.** It carries Kevin's or George's decision; it cannot create one. A packet that claims approval the conversation does not show is refused by its recipient.
- **A packet is not delivery.** Only Kevin's paste into the resident's own chat delivers it.
- **Identity stays in the registry.** A packet names a resident by role, person and registry key, never by a session identifier frozen in prose.
- **No body content.** A packet never quotes session-body content, credentials or medical material.
- **One owner.** A packet that names two writers for one surface is not sent until one is chosen.
