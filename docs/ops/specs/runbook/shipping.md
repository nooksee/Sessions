# Shipping: how a change reaches main (the field guide)

Registry entry: `docs/ops/registry/runbook.md` (`RUNBOOK-04`). Tool: `ops/lib/scripts/packet.py` (`SCRIPT-50`), specified in `docs/ops/specs/scripts/packet.md`. Contract: CONSTRAINTS C16 and C17. Written 2026-11-12 by the port's writer, on the operator's direction, as the team's onboarding to the packet workflow. The specification says what the tool does. This guide says how the team works with it. Status: maintained by the Integrator; read once by every resident who may carry a function in a packet, and again after a rotation.

## 1. Why this exists

The policy opens with one line: the system prevents an action that violates policy; it does not request compliance. Shipping was the one place where this room still asked. Each resident followed a rule, and no two followed the same route.

What the workflow gives each resident:

- **The state of the work lives in the room, not in anyone's memory.** `status` says which packet is open, what has changed, and whose turn it is. A resident who was rotated or compacted in the middle of a packet runs `status` and has lost nothing. This is the room's own craft, continuity, applied to its own work.
- **Less to carry.** No Git, no receipt filled by hand, no numbered handoff, no tracking of who waits on whom. A handoff no longer has to hold the state of the repository.
- **A refusal instead of a ruling.** When a step is not allowed, the tool says so at once and says what to do. Nobody waits for a decision about procedure.

What it costs, said plainly:

- **One thing at a time.** One packet is open in the room from start to landing.
- **The Auditor is in every path.** No packet lands without a PASS bound to its exact content.
- **A quarter to half an hour from open to landing,** most of it the gates and the required check.

## 2. The four functions

A packet is carried by the four delivery functions the team already works by: the Integrator, the Contractor, the Auditor and the Orchestrator (CONSTRAINTS C16 and C17; the Central Repository's PoT section 5). The leaf names, by registry key, who carries each one in that packet. A function is work in one packet. It is not a seat, and it changes nobody's role, title or lineage (PoT 4.1.8).

| Function | Carried here by | What it does in a packet |
| --- | --- | --- |
| Integrator | the Integrator (PoT 4.1.3) | drafts and opens the packet; changes its scope; restores or abandons it |
| Contractor | whoever does this packet's work: a Contractor, within the scope the operator assigns to it (PoT 4.1.4), or the Integrator himself | edits in the worktree, then closes |
| Auditor | the Auditor (PoT 4.1.9); never the packet's Contractor | reads the exact change and records PASS or FAIL |
| Orchestrator | the Orchestrator (CONSTRAINTS C16); any resident on a recorded fallback | ships: everything that touches origin or `main` |

Until 2026-11-09 this room gave the name Integrator to the seat that is now the Orchestrator's (RoR-23). The Integrator of PoT 4.1.3, and of a packet, is not that seat.

STELA's packets call the Contractor's session the Worker. This room does not use that word for it: here a worker is what a resident starts to help with its own work, such as a subagent or a background task; it acts as its parent and carries no function of its own (PoT 3.5).

## 3. One packet, start to finish

Every command is `python3 -I -B ops/lib/scripts/packet.py <command>`, run from the room. The examples shorten that to `packet.py`.

**Everyone starts with `status`.**

```
room: main at <commit>, clean, level with origin/main as last fetched
tools: git found, gh found
you: <your registry key>
packet: none active; the next is DP-SES-0007
station: draft: the Integrator runs `packet.py draft`
```

**The Integrator drafts and opens.** `packet.py draft` writes the form to `storage/handoff/PACKET.md`. The Integrator fills it: a title of at most 58 characters, the Contractor, the Auditor, the Orchestrator, the authority (a ledger number or a digest, never a quotation), the objective, the exact scope and the gates. Then `packet.py open`:

```
packet: DP-SES-0007 is open on agent/dp-ses-0007-<date>, base <commit>
next: the Contractor (<key>) edits only under var/tmp/packet/, only in scope, then runs `packet.py close`
```

The Integrator tells the Contractor one thing: run `status`.

**The Contractor works.** The assignment is the leaf, `var/tmp/packet/archives/packets/DP-SES-0007.md`: read it first. Every edit is under `var/tmp/packet/`. To try a suite before closing, run it there: `cd var/tmp/packet && python3 -I -B tools/test/test_<word>.py`. Then, from the room, `packet.py close --deviations 0 --narrative <file>`:

```
gate: exit 0 in 1 s: tools/test/test_filing.py
gate: exit 0 in 0 s: ops/bin/help --test
packet: DP-SES-0007 closed: 3 path(s), 2 of 2 gates passed, deviations 0, tree <tree>
next: the Auditor (<key>) reads `packet.py diff`, then runs `packet.py audit --verdict pass|fail --note FILE`
```

**The Auditor audits.** `packet.py diff` prints the exact change the verdict will bind, new files included. Then `packet.py audit --verdict pass --note <file>`, or `fail` with what must change:

```
packet: DP-SES-0007 audit PASS on tree <tree>
next: the Orchestrator (<key>) runs `packet.py ship`
```

**The Orchestrator ships,** on the operator's paste: `packet.py ship --wait 900`, again until it prints `LANDED`.

```
commit: <commit>
push: origin/agent/dp-ses-0007-<date>
pull request: #<number>
gates: sessions-gates success
findings: none unanswered
merge: #<number> by rebase
sync: main <commit> is origin/main; tree <tree>
LANDED: DP-SES-0007; the room is clean main, level with origin; the next packet may open
```

`PENDING` means run it again. `refused` and `FAILED` say what must happen next.

## 4. Working agreements

1. **Status first.** At wake, before any station, and whenever in doubt.
2. **One packet.** It lands or it is abandoned before the next opens.
3. **A refusal is information.** Read the line. Do what it says, or relay it word for word to whoever it names. Never route around it. The start page of this room ends on the same rule: a gate that refuses you is probably right.
4. **Work lives in the worktree, and only the tool writes the leaf.** The room's own checkout stays on clean `main`.
5. **Nobody runs Git by hand for a change:** no commit, push, merge, pull, rebase or pull request. The ship station does all of it.
6. **Say less.** The leaf and `status` carry the state. A nudge to whoever is next is one line: run `status`.
7. **The audit comes first.** A packet waiting on a verdict holds the whole room, so the Auditor answers it before other work.
8. **If the tool is wrong, the fix is a packet.** Report the exact line to the Integrator. Do not edit around it.

## 5. What changed, habit by habit

| Before | Now |
| --- | --- |
| Edit files in the room, on a branch you made | Edit only under `var/tmp/packet/`; the tool made the branch |
| Commit, push and open a pull request yourself, or hand the Orchestrator a numbered handoff | The Orchestrator runs `ship`; the leaf says everything it needs |
| Stack stage on stage and rebase them | One packet; the next opens when this one has landed |
| A pull request for a ledger line or a board line alone | The line rides in the packet that causes it; `RoR.md` and `NOW.md` are named in its scope |
| Fill a change receipt by hand | The tool writes the leaf: contract, measured results, verdict |
| A lease push to answer a review | A rework adds a commit on the same pull request; the tool never forces |
| Carry the repository's state in your handoff | `status` holds it; the handoff holds what only you know |
| Ask whether a step is allowed | Run the command; it answers |

## 6. Sizing, ordering and waiting

- **One packet is one objective** that the Auditor can hold in mind and the leaf can state in 800 characters. Make it as large as that needs and no smaller for the sake of slicing. A slice of a larger work is a packet when `main` is whole and green with it.
- **Scope.** Name exact paths when you can, and a folder ending in `/` when the work will create files. Too narrow costs one `amend`. Too wide costs the Auditor's attention.
- **Gates.** `full` for code: every suite and both self-tests, about seven minutes. Suite words for a document-only packet, such as `help`, `filing` or `ror_join`. The required check runs everything either way.
- **The queue is the Integrator's.** He keeps the next two or three packets in view, and the operator sets priority.
- **While a packet is not at your station,** do work that changes no tracked file: measurement, reading, review, the objective of the next packet. Nothing in the room's own checkout.
- **Preparing ahead.** A Contractor whose packet is next may prepare its change as a patch in its own scratch folder and apply it with `git apply` once its packet is open. Nothing ships except through the one open packet.
- **An urgent fix is a small packet.** There is no side door. With suite-word gates it lands in about a quarter of an hour.

## 7. Writing for a public record

The leaf is published. The narrative and the audit note are checked before any gate runs, so a refusal costs seconds. Both are plain ASCII, with no line that begins with `#`.

| This is refused | Write this |
| --- | --- |
| a quotation in double quotation marks, of anyone | what was decided, in your own words, and where it is recorded: a ledger number or a digest |
| a path on the host | the path relative to the room |
| a session identifier, or a short run of hexadecimal on its own | nothing; or the word commit or tree, then the Git id |
| curly quotation marks, long dashes, arrows | plain punctuation |

A good narrative is three to six sentences: what changed, why it satisfies the objective, what was not done, and each deviation named in a clause. The limit is 2,000 characters; 1,500 for an audit note.

## 8. Counting deviations

`close` asks for a count. A deviation is something you did that the packet's contract or the room's rules did not allow, or something they required that you did not do. Zero is the normal count, and a count is a measurement, not a confession.

- A refusal by the tool is not a deviation. Nothing happened.
- An amendment is not a deviation. It is recorded in the leaf.
- An edit made in the room's own checkout by habit, then moved into the worktree, is one.

## 9. When a command says no

| The line says | It means | Who acts |
| --- | --- | --- |
| `the room's own checkout has N uncommitted path(s)` | someone edited the room instead of the worktree | whoever did: move the change into `var/tmp/packet/` or discard it |
| `a packet is already active` | one at a time | finish or abandon the open one |
| `only the packet's Contractor (key)`, and the like | not your function in this packet | nudge the key it names: run `status` |
| `changed path(s) are outside the packet's scope` | the work reached past the contract | the Integrator amends, or the Contractor undoes the change |
| `FAILED: N of M gate(s) did not exit 0` | a gate failed; the log is `storage/handoff/RESULTS.md` | the Contractor fixes and closes again |
| `the worktree changed after close` | the results no longer describe the content | the Contractor closes again |
| `packet hash failure` | the leaf was edited by hand | the Integrator runs `restore`; the skipped station is then run properly |
| `not the tree the Auditor passed` | content changed after the audit | the Contractor closes again; the Auditor audits again |
| `PENDING` | the required check or a review is still running, or the head is resting | the Orchestrator runs `ship` again |
| `review finding(s) are unanswered` | a reviewer left a comment on the pull request | answer it there, fixed or declined with a reason; a fix returns the packet to the Contractor |
| `FAILED: the required check ... ended failure` | GitHub disagrees with the gates run here | the Contractor reworks; then close, audit and ship again |
| `origin/main moved since this packet opened` | something else landed | the Integrator abandons and opens again; the work is kept as a patch |
| `a branch for DP-SES-NNNN already exists` | a leftover branch | the Orchestrator deletes the branch it names |
| `the caller is not verified` | the tool cannot tell who you are | stop; report the line to the Integrator and the operator |

## 10. Questions

**I was rotated in the middle of a packet.** Run `status`. The packet, the worktree and your station are as you left them.

**I need a file that is not in scope.** Stop and tell the Integrator. `amend` adds it and records why, and you close again.

**I think the tool is refusing wrongly.** Do not work around it. Send the exact line to the Integrator. If it is a fault, the next packet fixes it.

**My change is derived from a private source,** such as the public ledger. Keep the private source where it is, and render the public copy into the worktree.

**My work changes no tracked file.** It is not a packet. It travels as it always has, on the resident packet form.

**The Auditor returned FAIL.** Rework in the worktree and close again. The next close clears the verdict, and the Auditor audits the new content.

**Two things are urgent.** They are two packets, in the order the Integrator sets. The second can be prepared as a patch while the first lands.

**The Orchestrator is away.** Any resident ships with `--fallback` and a one-line reason, which is recorded. This is workflow, not authority.

**The Auditor is away.** The packet waits. Another auditor is the operator's to name.

**A reviewer commented on the pull request.** Every such comment is answered on its thread before the merge, by a fix or by a reason for declining. The tool waits while the reviewer says it is still reading.

**I want to stop a packet.** Before its branch is on origin, the Integrator runs `abandon` with a reason. Once the Orchestrator has pushed it, the Orchestrator runs `abandon`, or another resident does with `--fallback` and a one-line reason. Either way the work is kept as a patch, and the number is used by the next packet.

## 11. The first week

- Each resident, once: read this guide; run `status`; cut from your own handoff what described the old route, and add how you ship now in a few lines; write the idea, in your own words, as a leaf of the mind.
- Each resident who carries a function, once: one packet through your station, and one refusal met on purpose.
- The Integrator, after ten landed packets: read what the refusals taught, and open packets for what should change.
