# Sessions Operations Manual (Command Console)

Owner: Claude Shannon, Integrator. Written 2026-10-30 at the operator's request for a help system and a manual, both taken from the STELA framework, by a workflow agent under Shannon's assignment. Framework: STELA's manual, the house convention, kept in the operator's Control tree and not in this repository; filled for this house. Map: `docs/ops/README.md`. Index: `docs/INDEX.md`.

Authority order:
- **Law:** `PoT.md` is the single Sessions constitution, below Control policy.
- **Operational requirements:** `ops/lib/manifests/CONSTRAINTS.md` names
  resident and worker obligations within PoT. Tool specifications remain the
  canonical behavior and parameter sources.
- **Context:** `ops/lib/manifests/CONTEXT.md` defines the read-in and points to
  each domain's source; it does not expand authorization.
- **Craft and mechanics:** this manual explains procedures; it neither
  restates nor overrides PoT or the contracts.
- **Identity:** `ops/etc/resident-identities.json` (the registry; private, not in this repository) wins over any prose, including this manual.
- **Behavior of a tool:** its spec in `docs/ops/specs/` wins over the summary here.
- **Decisions:** the operator decides; this manual records how his decisions are carried out.

Where a tool is not built yet, this manual says so with a `[PLACEHOLDER: ...]` line rather than describing behavior that does not exist.

---

## 0. Purpose

Sessions is the session-health office of the Control house. The operator runs about twenty-five long-lived AI residents (Claude Code, Codex and Copilot), one per room. Their context windows fill, and each must eventually move into a fresh body without losing who it is.

This room owns:
- **measurement:** how full each resident is, from the provider's own figures;
- **closeout:** telling a resident, from inside, that its time is near;
- **the mind:** the room's concepts, pointer first: ideas that stay true, written by the residents themselves;
- **rotation:** moving a resident into a fresh body the same way every time;
- **custody and receipts:** every donor preserved whole, every action receipted.

The resident bodies themselves (`~/.claude/projects/`, `~/.codex/sessions/`, `~/.copilot/session-state/`) are evidence, not canon. The repository is canon. When they disagree, the repository wins.

This manual is the operator console: what runs, in what order, who decides,
and where things live. Historical method prose is preserved as such;
current mechanics live here and in the tool specifications.

### Read-in and execution

Use `bash ops/bin/help read` for the maintained order. Follow CONTEXT X01,
then the applicable CONSTRAINTS clauses; read only task-authorized continuity
context, validated dependencies and the relevant specifications. Before a
state-changing step, resolve its authority, writer, target, evidence and
required custody. An affected stop does not halt unrelated authorized work.

Each resident maintains its own mapped handoff during assigned work. Use the
existing packet and receipt forms, record actual start/deadline and source
pins, and report actual state at the deadline. Promote durable results before
scratch closeout. Continuity operations follow their existing specifications:
measured closeout, verified custody,
destination-native successor, required go, closed-writer join, native
readback and operator acceptance. This sequence does not imply that an
unwritten runner or unwired hook exists. A Claude resident of this room runs
with auto memory off and wakes from the mind and its own handoff (CONTEXT X01).

---

## 1. People and Roles

| Who | Seat | Owns | Does not own |
| --- | --- | --- | --- |
| **The operator** | operator | objectives, priorities, authority, every yes and every go, final acceptance | implementation chores |
| **Claude Shannon** | Integrator (registry key `session-doctor`) | continuity, the Sessions room, the specs, coordination of the team, running rotations for other residents | his own rotation (Claudine runs it) |
| **Claudine Colbert** | Contractor | the tools she is assigned as sole writer (`gauge.py`, `mind.py`), and Shannon's rotation | a surface another writer holds |
| **Joe Codex** | Contractor | read-only measurement and the Codex side (methods, runway figures, Codex hooks) | any write without the operator's named go |
| **Jo Hamming** | Orchestrator (registry key `jo-hamming`; a Copilot resident, prompted only by the operator's paste; CONSTRAINTS C16) | staying in the loop from dispatch through closeout, and the ship station of every dispatch packet (section 1B): the commit of the audited tree, the push, the pull request, the required check, the exact-head merge, the proof that `main` equals origin, and the cleanup | content, review, acceptance, source, documents and records other than its own handoff; Git work is workflow, not authority, and any resident runs the station with a recorded fallback reason when the Orchestrator is not available |
| **Claudio Freeman** | independent reviewer and auditor (Control surfaces) | review before reliance, audit after change | implementation, repair or rollout writing on work he reviews |
| **The Auditor** (the operator's appointed seat; the registry names the holder) | independent reviewer and post-change auditor for this room's material work (PoT 4.1.9) | review before reliance, audit after change | implementation, repair or rollout writing on work it reviews |
| **George** | Control authority, desktop continuity and cross-project coordination | routing and the exact packet for cross-room work | the operator's acceptance |

Rules that hold for every seat:
- **One writer per surface.** Each file, live session and rollout has exactly one named writer at a time.
- **Git work is handed off.** A change reaches `main` only as one dispatch packet (section 1B). The Orchestrator runs its ship station; the Integrator, the writers and the Auditor do not commit, push, merge or pull as a routine. Any resident runs the station with a recorded fallback reason when the Orchestrator is not available. This is workflow, not authority (CONSTRAINTS C16 and C17).
- **The team room.** `storage/handoff/{shannon,claudine,joe}.md`. Each member writes only their own file. Results are promoted to `archives/receipts/` or the office handoff; the room itself is working notes.
- **A file proves no delivery.** A routing decision or a note in the team room is not delivery. The operator's paste is the fallback between chats, and the only route to a closed Claude chat and to a resident on Codex or on Copilot: such a resident does not listen or watch for messages unless the operator asks for it explicitly (RoR-30). Between separately governed rooms it stays the route until an acceptance names who may send, to whom and in what form. Claude residents of this room also reach one another by session message: such a message is information, grants nothing, and proves reading only by the receiver's own reply or record. On 2026-11-07 the operator accepted `codex queue` as a relay to the Contractor on Codex (Joe Codex) alone, with the Integrator and the Contractor on Claude (Claudine Colbert) as senders, by one line naming a path and a hash, through a tool at a reviewed hash. It was proved by one no-op send to one open chat, audited; what the chat displayed was not observed. That relay ended on 2026-11-13 with RoR-30 and is not used: no resident sends by it, and no relay or waiter runs towards a resident on Codex or on Copilot. What it showed stays true of any such route: a queued line starts a turn at that chat's settings whether or not anyone is watching, cannot be withdrawn, names a session and not a person as its sender, and is not the operator's word. The contract for these routes is an open item of the Central port, and this line gives way to it.
- **Attribution.** Relayed text is attributed to its real author; "verbatim" only for the author's own words.
- **House style.** No contractions. Deviations reported as counts.

The authority for who each resident is lives only in the registry. A resident checks its own body with `ops/lib/scripts/myself.py` and the identity lock with `ops/lib/scripts/identity.py`.

---

## 1A. The Four-Tool Loop

```
 registry (ops/etc/resident-identities.json): who each resident is
      |
      v
 [gauge]     reads each body's own API token count  -> logs/gauges/ledger.jsonl
      |      when 50,000 tokens remain before the 70 percent line
      v
 [closeout]  the card appears in the resident's own context; the resident parks work,
      |      writes its closing handoff, and writes any idea that stays true as a leaf
      v
 [mind]      a new leaf archives/mind/MIND-<date>-<NNN>.md, a pointer line in MIND.md,
      |      and a ledger line in logs/mind/ledger.jsonl; no approval
      v
 [rotate]    capsule + donor's own summary and window -> static gates -> custody (two tiers)
      |      -> the operator's go -> verified swap -> registry and binding -> labels -> receipt
      v
 [gauge]     the successor's first reading confirms the wake; the loop begins again
```

| Tool | Script | Spec | Tests | Implementation and installation |
| --- | --- | --- | --- | --- |
| gauge | `ops/lib/scripts/gauge.py` | `docs/ops/specs/scripts/gauge.md` | `tools/test/test_gauge.py` | built; see its specification for measurement behavior and installed scope |
| closeout | `ops/lib/scripts/closeout.py` | `docs/ops/specs/scripts/closeout.md` | `tools/test/test_closeout.py` | implemented and synthetically tested; current-hash review and native delivery proof precede installation (PoT 6.1.2) |
| notice (operator backstop) | `ops/lib/scripts/notice.py` | `docs/ops/specs/scripts/notice.md` | `tools/test/test_notice.py` | source integrated on `main` (PR #10, 2026-11-05) with the Independent Reviewer's source PASS and post-integration audit; unwired, live go pending the registry permission finding (F1) and George's activation; consumes one exact gauge row, submits an operator-only notice, never delivers resident context |
| mind | `ops/lib/scripts/mind.py` | `docs/ops/specs/scripts/mind.md` | `tools/test/test_mind.py` | built and tested on synthetic rooms; pointer-first index, concept leaves, ledger; residents write their own leaves |
| rotate | `ops/lib/scripts/rotate.py` | `docs/ops/specs/scripts/rotate.md` | `tools/test/test_rotate.py` | default synthetic phases 0 to 9 remain dry-run only; separate hash-gated disposable engine has private resumable checkpoints and external observer joins; no accepted live rotation or provider-load proof |

Registries: `docs/ops/registry/scripts.md`, `test.md`, `binaries.md`, `runbook.md`.

The diagram is the intended loop, not an installation report. `notice` is
an optional operator backstop to its closeout step, not another telemetry
reader or proof of native context injection. It receives one checked gauge
JSON row for an explicit key. `--dry-run` sends and writes nothing. Its
status `submitted` means only notifier success, not display or acceptance;
`unknown` is nonzero and never a clean reading. Host wiring remains George's
separately reviewed and named operation. See the notice specification for
private state, interruption limits and the exact CLI; no copy-and-run live
pipeline is implied by this source preparation.

## 1B. Dispatch Packets: How a Change Ships

A change reaches `main` only as one dispatch packet: one id, one branch, one pull request and one kept leaf. One packet is active in the room at a time. Each station is one command of `ops/lib/scripts/packet.py`, and each refuses when the station before it is not proved (CONSTRAINTS C17; spec `docs/ops/specs/scripts/packet.md`).

```
 [draft]   the Integrator fills storage/handoff/PACKET.md: title, Contractor, Auditor, Orchestrator,
    |      the authority cited, the objective, the exact scope, the gates
    v
 [open]    the Integrator, from clean main level with origin -> the id DP-SES-NNNN, the branch,
    |      the worktree var/tmp/packet/, and the contract in the leaf
    v
 [work]    the Contractor edits only in var/tmp/packet/, only in scope
    |
    v
 [close]   the Contractor: scope checked, gates run, results and the deviation count in the leaf
    |
    v
 [audit]   the Auditor, never the Contractor: PASS or FAIL, bound to the exact tree
    |
    v
 [ship]    the Orchestrator, on the operator's one paste: commit, push, pull request, required
           check, findings answered, merge by rebase, main level with origin, cleanup -> LANDED
```

A packet's leaf names, by registry key, who carries each of the four delivery functions (CONSTRAINTS C16 and C17; the Central Repository's PoT section 5). A function is work in one packet. It is not a seat: the seats of this room are in section 1.

| Function | Carried here by | Runs | Never |
| --- | --- | --- | --- |
| Integrator | the Integrator (PoT 4.1.3) | `draft`, `open`, `amend`, `restore`, `abandon` | commits, pushes or merges |
| Contractor | the resident the packet names for its work | edits in the worktree, then `close` | edits the room's own checkout, edits outside scope, or audits its own packet |
| Auditor | the Auditor | reads `diff`, then `audit --verdict pass` or `fail` | writes the work it audits |
| Orchestrator | the Orchestrator | `ship`, again until it prints `LANDED`; `abandon` once a branch is on origin | decides content, review or acceptance |
| Anyone | | `status`, `diff` | |

- **Start with status.** `python3 -I -B ops/lib/scripts/packet.py status` shows the room, the active packet, who carries its functions, what has changed and whose station is next. It is the first thing to run after wake, and the only thing a nudge between residents needs to say.
- **The leaf is the assignment.** The Contractor needs no other form for repository work: the objective, the exact scope, the authority and the gates are in the leaf. The resident packet (RUNBOOK-02) remains for work that changes no tracked file.
- **The room stays clean main.** Nobody edits tracked files in the room's own checkout; the work is in `var/tmp/packet/`. A file derived from a private source, such as the public ledger, is rendered into the worktree.
- **Working files are latest-wins and disposable.** The draft (`storage/handoff/PACKET.md`), the gate log (`storage/handoff/RESULTS.md`) and the worktree have fixed names; the newest replaces the last; none is committed.
- **The leaf is the one kept record.** `archives/packets/DP-SES-NNNN.md` holds the contract, the measured results and the verdict. It is public: it cites a decision by ledger number or digest and never quotes.
- **Board and ledger lines ride in the packet that causes them.** `NOW.md` and `RoR.md` are named in its scope; there is no pull request for a line alone.
- **The operator's part is one paste per packet,** to the Orchestrator: ship. Everything before it reaches a resident as other work does.
- **When a station refuses, it says what to do.** Only the tool writes a leaf: one edited by hand is refused, and `restore` puts back the leaf the tool last wrote. `abandon` keeps the work as a patch. The recovery table is in the spec.
- **The required check judges the same rules on GitHub.** A pull request that is not one valid packet does not merge, whoever opens it.
- **The field guide** is `docs/ops/specs/runbook/shipping.md`: the four functions and who carries them here, one packet from start to finish, the working agreements, and what each refusal means. Every resident who may carry a function reads it once, and again after a rotation.

## 1C. The Read-in: OPEN

Before a resident works, it runs `ops/bin/open`. The tool finds who is calling, prints the law on that caller's own screen, and records that it did (PoT 1.3.18). It is this room's form of STELA's `open`, changed for residents: it prints the text and not a pointer, and it prints a whole file of the law only when the caller's body has not been shown it as it now stands.

- **When.** After a wake, at the start of each shift, and again whenever `--check` says the OPEN is no longer good. An OPEN is good for one body, one text of the law and twelve hours, and only while it has shown the clauses of every function the open packet gives its holder. A landed amendment ends every OPEN. A packet that gives a resident a function its OPEN did not show ends that resident's OPEN; the next one shows that function.
- **What it shows.** The clauses that `CONTEXT.md` X04 lists for every reader, each under its heading of the law; the clauses for each delivery function the open packet's leaf gives the caller, or for all four when no open packet names the caller; what `packet.py status` says now; the newest ledger entry; the caller's fullness; two sections of the board; and five report lines to give the operator as they stand.
- **Who is shown which function.** The open packet's leaf decides, and nothing else does: not the registry, and not what a caller says of itself. Nobody types an identity or a function.
- **Parts.** A first OPEN is several parts, and an ordinary one is one or two. Run `--next` until the closing line says complete; only then is the OPEN recorded. A part that does not end with its own closing line was cut by the shell tool: stop and report it.
- **The intent** is one line saying what the shift is for. It is kept in the private record beside the trace.
- **The record** is one private line under `logs/open/`: who, when, which law by hash, which packet and functions, which clauses, the intent. `--roster` shows the operator who holds a good OPEN.
- **What it does not do yet.** No other tool requires an OPEN. That lock is a later packet, after every resident has made a first OPEN.
- **An unverified reader** is shown the common clauses and nothing is recorded; it says so and waits for the operator, as before.

The specification is `docs/ops/specs/binaries/open.md`.

---

## 2. Top Commands

Run from the room root, `<room>` (on a clone, the clone's root). Python runs isolated (`-I -B`) so that no bytecode is written beside the tools.

### Gauge (read the meters)
~~~bash
# Every registered resident, as a table; appends one ledger line per resident
python3 -I -B ops/lib/scripts/gauge.py

# Print only; append nothing to the ledger
python3 -I -B ops/lib/scripts/gauge.py --no-ledger

# One resident, machine-readable
python3 -I -B ops/lib/scripts/gauge.py --key session-doctor --json --no-ledger
~~~

### Mind (see section 5)
~~~bash
python3 -I -B ops/lib/scripts/mind.py show [--agent <key>]
python3 -I -B ops/lib/scripts/mind.py read <id>
python3 -I -B ops/lib/scripts/mind.py add --agent <key> --title "<title>" --body <file or ->
python3 -I -B ops/lib/scripts/mind.py add --agent <key> --title "<title>" --body <file> --supersedes <id>
python3 -I -B ops/lib/scripts/mind.py retire --agent <key> <id>
python3 -I -B ops/lib/scripts/mind.py check
~~~

### Open (see section 1C)
~~~bash
python3 -I -B ops/bin/open --intent "<what this shift is for>"   # begin the read-in; prints part 1
python3 -I -B ops/bin/open --next                                # the next part, until the closing line says complete
python3 -I -B ops/bin/open --check                               # is my OPEN still good
python3 -I -B ops/bin/open --roster                              # who in the room holds a good OPEN
~~~

### Packet (see section 1B)
~~~bash
python3 -I -B ops/lib/scripts/packet.py status
python3 -I -B ops/lib/scripts/packet.py draft        # the Integrator; then fill storage/handoff/PACKET.md
python3 -I -B ops/lib/scripts/packet.py open         # the Integrator
python3 -I -B ops/lib/scripts/packet.py amend --add <path> --reason "<why>"                  # the Integrator
python3 -I -B ops/lib/scripts/packet.py close --deviations <count> --narrative <file or ->   # the Contractor
python3 -I -B ops/lib/scripts/packet.py diff [stat or names]                                 # anyone: the exact change the audit binds
python3 -I -B ops/lib/scripts/packet.py audit --verdict <pass or fail> --note <file or ->    # the Auditor
python3 -I -B ops/lib/scripts/packet.py ship [--wait <seconds>] [--hold]                     # the Orchestrator, until LANDED
python3 -I -B ops/lib/scripts/packet.py restore                                              # the Integrator: put back a leaf edited by hand
python3 -I -B ops/lib/scripts/packet.py abandon --reason "<why>"                             # the Integrator
~~~

### Tests (synthetic data only; no real body, room or mind is touched)
~~~bash
python3 -I -B tools/test/test_gauge.py
python3 -I -B tools/test/test_mind.py
python3 -I -B tools/test/test_packet.py
~~~
Reviewers also run each suite at the host umasks 0002 and 0022 as well as 0077; a suite that passes only under one umask is not green.

### Closeout and rotate
`closeout.py` is an implemented hook entry point, not an interactive phase
runner; its specification defines JSON input and the staged validation route.
`rotate.py` implements synthetic dry-run phases 0 to 9. Each fixture stop
removes its temporary artifacts. Its separately selected slice-6 disposable
operation path has private persistent checkpoints and hash-bound per-action
go/proof inputs; the exact CLI and fields are in the rotate specification.
It starts no provider, changes no resident binding and proves no actual
native wake or operator acceptance merely by being integrated.
These facts do not authorize
hook wiring or a native canary (PoT 6.1.2, 6.1.5).

### Help and template (entry points; registry `docs/ops/registry/binaries.md`)
~~~bash
# The front door: read-in order, the loop, every tool with its spec's own status
ops/bin/help
ops/bin/help read          # the read-in order, checked
ops/bin/help specs         # every spec with its Status: line
ops/bin/help doctrine      # DOCTRINE.md section headings with line numbers
ops/bin/help term <text>   # search: specs first, then this manual, then docs/

# A new tool's skeleton (script, spec, test), all three or none; prints its registry row
ops/bin/template --dry-run <word>
ops/bin/template <word>
ops/bin/template --slot PURPOSE='one line' <word>   # a given slot replaces its placeholder
ops/bin/template --preserve-spec <word>             # preserve a reviewed regular spec; create only script and test

# A report from its form, every slot required (refusal lists the missing slots and what each holds)
ops/bin/template receipt                            # with no slots: refuses, listing the 17 slots a receipt needs
ops/bin/template receipt --slots-file my.slots --out archives/receipts/<resident>-rotation-<n>-<date>.md
ops/bin/template packet --slots-file packet.slots   # TO FROM RELAYED_BY OWNER SCOPE AUTHORITY SOURCES RULES STOP_CONDITION POST_TO
ops/bin/template closeout --slot PERCENT=65.2 --slot WINDOW=1,000,000 --slot READING_TIME='16:40 EDT' --slot "ROTATION_WRITER=Shannon's desk"
ops/bin/template source-change                       # lists the required source/configuration receipt fields
~~~
The forms live in `ops/src/` as `.tpl` files (the operator, 2026-10-30: the agent kept changing the form, or at times forgot it). A slots file holds `KEY=VALUE` lines. Report mode refuses a missing, unknown or empty slot, a `[PLACEHOLDER`, any `{{...}}` left in the output, and an existing `--out` file. Report forms are not tool names. The rotation `receipt` remains distinct from `source-change`, which records bounded source/configuration work, exact heads, validation, review, integration and rollback. Since 2026-11-12 a change to tracked files is recorded by its packet leaf, which the packet tool writes (section 1B); the `source-change` form remains for a configuration change that touches no tracked file.

The storage root is not an output directory. Only `storage/.gitignore`,
`storage/README.md` and the lane `.gitkeep` files are admitted; all case and
handoff payload stays ignored. Before a storage commit, verify the exact staged
path set rather than relying on ignore rules alone. Use `var/tmp/` for
disposable scratch.

Every spec carries a `Status:` line before its first section, so that `help` can show it. `ops/bin/help curriculum` remains a placeholder: closeout source exists, but the exact wake/closeout curriculum and rotate script are not complete.

---

## 3. Reading a Gauge

The meter already exists: after every working turn, the provider writes the exact token count into the resident's own body. `gauge` reads only that figure, from the end of the body, and never message content. Spec: `docs/ops/specs/scripts/gauge.md`.

### The columns
| Column | Meaning |
| --- | --- |
| resident | the registry key |
| model | the model of the newest genuine reading |
| tokens | the context in use at that reading (Claude: input plus cache read plus cache creation) |
| window | the model's window, from the body if the provider reports it, else the reviewed table in the spec, else the status-line record (shown as unverified), else unknown |
| percent | tokens over window; empty when either is unknown or the reading is no longer current |
| last observed | when the reading was written |
| age | how long ago that was |
| state | see below |
| note | the reason for anything unknown, and where the window came from |

### The states
| State | What it means | What to do |
| --- | --- | --- |
| `last observed` | a genuine current reading, with its age | trust the percent; an old age is not staleness, because context grows only on a working turn |
| `before compaction` | a compaction followed the reading; the figure is no longer current | wait for the next working turn |
| `compacted` | a compaction boundary with no reading after it | no current figure; wait |
| `archived body` | the body is in an archived root, not live | not a live reading; check the registry |
| `window unknown` | tokens are known, the window is not | do not guess; a window enters the spec table only with a source and a date |
| `invalid` | tokens above the window | investigate before acting |
| `unknown` | no reading could be established (body missing, ambiguous, beyond the 16,000,000-byte tail bound) | read the note |

### The lines
- **Closeout begins at a reserve:** 50,000 tokens before the 70 percent line, whatever the window (`closeout.md`; the operator may veto this rule). Computed from that rule:

| Window | 70 percent line | Closeout begins at |
| --- | --- | --- |
| 1,000,000 | 700,000 | 650,000 (65.0 percent) |
| 475,000 | 332,500 | 282,500 (about 59.5 percent) |
| 353,400 | 247,380 | 197,380 (about 55.9 percent) |
| 272,000 | 190,400 | 140,400 (about 51.6 percent) |
| 258,400 | 180,880 | 130,880 (about 50.6 percent) |

- **Rotation is due at 70 percent.**
- `gauge` itself only reports. A timer, and the notification the meter would trigger, each need the operator's separate go. A timer compares unrounded figures (649,960 of 1,000,000 prints as 65.0).

### Cautions
- **Bytes are not fullness.** A 78 MB body read 32 percent on 2026-10-30. Weigh tokens, never files.
- **An estimate is not a measurement.** A wake estimate made before a rotation is an estimate; the successor's first reading is the measurement.
- **The ledger is telemetry, not authority.** The source default is `logs/gauges/ledger.jsonl` (new files 0600, ignored by Git). The history moved here in place on 2026-11-04 with its inodes preserved (`archives/receipts/state-cutover-20261104.md`). A legacy `storage/gauges` would block default append; `--no-ledger` still prints a reading without writing. Explicit `--ledger` retains its selected-output interface, not migration authority. See the gauge specification and the map's bounded migration inventory.

---

## 4. Closeout

Spec: `docs/ops/specs/scripts/closeout.md`. Source and synthetic tests exist;
installation and native context delivery are separate acceptance steps. The
specification records the implementation boundary; PoT 6.1.2 governs wiring.

**Why.** A resident's end used to be noticed by someone else, late or never. Joy's closing packet of 2026-10-29 was left on the Desktop and never reached her. The closeout is built into the resident and triggered by its own measured state, not by anyone's memory.

**What it does, as designed:**
1. A `UserPromptSubmit` hook reads only the resident's own `transcript_path`, takes the newest reading the way `gauge` does, and divides by that model's window.
2. Above the reserve it prints nothing. At or beyond the reserve it adds one block to the resident's context: the measured figure and the closeout card. It repeats once per 5 points crossed, and re-arms after a compaction or rotation.
3. The operator receives a copy of the crossing as a notification.
4. Unknown readings print nothing to the resident; after 3 consecutive unknowns, the operator is notified once.
5. The hook is never in the way: it catches every error, always exits 0, and runs under a 5-second timeout.
6. Only registered sessions are covered; helpers, subagents and sidechains are always silent.

**The card, in order:**
1. Tell the operator plainly that the closeout has begun, with the figure.
2. Finish the current step if it is short; otherwise stop at a clean point. Start nothing new and material.
3. Write the closing handoff: work in flight, open promises, owners, first steps for the successor.
4. Write any idea learned that stays true as a leaf (`mind.py add`), and supersede or retire your own leaves that no longer hold. No approval is asked.
5. Tell the operator the resident is ready for rotation. Shannon's desk runs it; for Shannon himself, Claudine runs it.

**Codex and Copilot residents.** Codex CLI 0.166 documents the same hook (Joe Codex, `joe.md`); the PyCharm path is untested, so it is tried on one Codex resident before anyone relies on it. Until then, and for Copilot, the operator pastes the card.

The implementation and `tools/test/test_closeout.py` already exist. A native
delivery check and any hook, notification or timer installation follow the
separately reviewed exact operation (PoT 6.1.2, 6.1.5). The old staged runbook
does not reopen its expired live window.

---

## 5. The Mind

Spec: `docs/ops/specs/scripts/mind.md`. The design is the operator's, given on
2026-11-09.

**What a mind is.** The room's concepts: ideas that stay true, each one a
leaf. A concept, an abstraction, a method, a bond. Never the present: the
board, the ledger and the handoffs hold what is true now, dated and
replaced. A stale fact read as memory misleads with the authority of
something remembered, so the mind refuses it at the door.

**Pointers first.** The root `MIND.md` is an index and nothing else: one line
per live leaf, `- [<id>](archives/mind/<id>.md) <agent> — <title>`. A resident
reads it at wake with `mind.py show`, after its identity passes and before its
handoff, and opens a leaf with `mind.py read <id>` when the leaf bears on the
work. The tool serves only when its check passes; a refusal is reported, never
worked around. The room keeps the provider's auto memory off
(`.claude/settings.json`, `"autoMemoryEnabled": false`).

**Writing.** A registered resident writes its own leaves, at any time, with no
approval:
1. `mind.py add --agent <its key> --title "<one line>" --body <file or ->`.
   The tool gives the leaf its id, `MIND-<date>-<NNN>`, and records the write
   in the ledger.
2. When an idea changes, write the new form with `--supersedes <old id>`: the
   new line takes the old line's place, and the old leaf stays on disk,
   unserved.
3. When an idea no longer holds, `mind.py retire --agent <its key> <id>`.

A resident changes only its own leaves.

**What the screen refuses.** A date, a time, a word that dates the text
(today, currently, this week), a count or size, a path or file name, an
address, a pull request or version number, code or a command line, an
identifier, medical content and secrets. Say the idea instead of the fact.

**What the screen cannot refuse.** A rule of the room written down as if it
were an idea. A leaf states no rule (PoT 4.2.4): rules live in the policy and
its contracts, and a copy in a mind goes stale on the day the rule changes.
Where a leaf touches policy, cite the clause and write what you carry: the
habit, the method, the reason.

**Limits.** A title of at most 100 characters, a body of at most 2,000, and at
most 200 live leaves. A full index refuses a new leaf; supersede or retire one.

**Where it lives.** `MIND.md` at the room's root, the leaves under
`archives/mind/`, the ledger at `logs/mind/ledger.jsonl`: all mode 0600, all
out of Git (PoT 5.1.3), all backed by custody.

**Checking.** `mind.py check` runs every gate (legacy, index, out-of-git,
ledger, leaf, strays) and exits 1 on any blocking failure. A leaf whose bytes
no longer match its ledger line blocks the mind until its owner retires it.

---

## 6. Running a Rotation

Spec: `docs/ops/specs/scripts/rotate.md`. Status: synthetic phases 0 to 9
implemented, dry-run only. Each stop removes temporary fixture artifacts.
There is no production adapter or persistent recovery. Real rotations
still follow the spec by hand, phase by phase, and stop at each stop point.
No live rotation or provider-load proof.

**Roles.** the operator decides, opens the container, gives the go, accepts or does not. Exactly one writer, named before work starts and never the resident being moved. The donor closes well and never builds its own successor. The Auditor audits afterwards.

**Tiers, declared in writing before work starts.**
- **B, transplant (default):** the capsule plus the donor's compaction summary and a measured slice of its own window, word for word.
- **Capsule-only:** only when a window build fails to load, on the operator's go.
- **A, reseed:** a fresh session reads the handoff; only on the operator's explicit choice, recorded as Tier A and never called a rotation.

**The capsule, appended as text (never a path), in four parts:** registry header; the resident's own mind index lines, pointers only; the transition note; the first-turn line ("the room's status in a few lines, then speak as yourself").

**Phases (each ends at a stop point; the writer reports and does not run ahead):**

| Phase | What happens | Stop point |
| --- | --- | --- |
| 0 Trigger | gauge crosses the line; the closeout card has run; tier, donor, writer, destination and reading recorded | recorded in the handoff |
| 1 The donor closes well | closing handoff; any idea that stays true written as a leaf; the closing record names the mind index | record written |
| 2 The mind is ready | `mind check` passes; the index hash matches the closing record | gate passes |
| 3 The destination | the operator opens a fresh chat in the room; the writer labels it a spare at once and verifies room, working directory, no other owner, no process holding it | verified |
| 4 The window | measure the donor by the gauge method; cut at a genuine operator prompt; carry at least one exchange beyond procedure; record the reason | cut recorded |
| 5 Build and static gates | splice, re-identify by identity field, externalize media, append the capsule and a fresh plain label; run every static gate | all gates pass |
| 6 Custody and serve-safety | `launcher stop <key>` writes the hold; donor, pristine destination, successor, capsule, gates, media, registry and binding go to both tiers, checked against `SHA256SUMS` | both tiers verified |
| 6 to 7 the operator's go | the writer names container, room, size, custody hash and rollback, then waits; a go given at phase 0 does not count | the operator's go |
| 7 Install | verified swap (default) or the operator's `.NEW` swap (fallback); registry and binding switched; six identity checks agree; rollback on any failure | six checks agree |
| 8 Acceptance | `launcher serve <key>` (load test and hold release); first reply gives room status and speaks as itself; first gauge reading recorded; clean native append; then the operator's own acceptance | the operator states that he recognizes him, or her |
| 9 Close | receipt `archives/receipts/<resident>-rotation-<n>-<date>.md`; donor store entry removed or relabeled only after custody is verified in both tiers; the new resident reads its own leaves and confirms they still hold | receipt written |

Registry updates and rollback follow the canonical identity-registry privacy
contract in [the rotation specification](ops/specs/scripts/rotate.md). The
launcher roster/binding pair is a separate surface; no blanket file-mode
change follows from this procedure.

**Codex residents.** `ops/lib/scripts/rotation.py` does not carry the native compaction summary. A Codex rotation under this spec waits for a Codex-specific design and a loader test.

`rotate.py` implements synthetic dry-run phases 0 to 9. Each stop removes
its temporary fixture artifacts; no production adapter or persistent recovery exists.
There is no live rotation or provider-load proof.

---

## 7. Custody

Every donor is preserved whole. A rotation, a relabel or a removal never proceeds until custody is verified.

**Two tiers.**
- **Tier 1, canonical copy:** `<control>/Backup/Codex-Session-Preservation/<batch>/`, on the always-present internal drive.
- **Tier 2, redundant cold copy:** the same batch on a mounted hot-swap custody drive (interchangeable peers per `DOCTRINE.md` section 8).

**The batch.** One folder per operation, named for what and when (for example `central-donors-20261026/`, `claudio-spare-relabel-20261030/`), holding the files and a `SHA256SUMS` file. Verification is a fresh hash of every file in both tiers against `SHA256SUMS`, with tier 2 read directly from the drive, never assumed from the copy step.

**What goes into custody for a rotation:** the donor's closed copy, unmodified; the pristine destination; the successor; the capsule; the gate output; externalized media; the registry and launcher binding before the change.

**Drive health.** The map records that the tier-2 drive is failing and a replacement is pending. A tier-2 copy on a failing drive is still read back and hashed; a mismatch is a stop, not a warning.

[PLACEHOLDER: the current location of `PRESERVATION_MANIFEST.md` named in `DOCTRINE.md` section 8 (not found at the top two levels of `Backup/` on 2026-10-30), and the replacement tier-2 drive once the operator has it. Owner: Claude Shannon.]

The receipt for each operation names the exact custody paths and hashes. Permanent deletion is never the default.

---

## 8. Labels: Spares and Donors

The operator's policy, 2026-10-30: only the live, registered body carries the plain name `Role (Person)`. Every other body is visibly labeled on every surface:
- a pre-positioned or freshly opened destination: `<Role (Person)> - spare body, do not open`;
- a donor after rotation: `<Role (Person)> - donor, rotated <date>, do not resume`, unless the operator prefers removal from the list (his standing preference since 2026-10-29), after custody is verified.

**Where a label lives.**
- Claude: a `custom-title` and `agent-name` record appended to the session file.
- Codex in PyCharm: the chat title in the PyCharm workspace state, edited only while PyCharm is closed.
- Phone: the thread title record in the Codex state database.

Back up before every label edit. At cutover the plain name moves to the new body and the donor label to the old one. Current map: `archives/receipts/resident-label-map-20261030.md`.

**Why.** On 2026-10-29 the operator faced two identical entries and could not tell which was the live resident. A label makes the wrong body impossible to open by accident.

---

## 9. The Operator's Card

The operator's whole part in a rotation, in four words. Everything else is the writer's job.

```
1. DECIDE     Rotate now, at this tier (B unless you say otherwise).
2. CONTAINER  Open a fresh chat in the resident's room. Say nothing in it.
3. GO         When the writer names the container, size, custody hash and rollback, say go.
4. HELLO      Open the resident by its plain name and say hello. If it answers as itself, say "this is him" or "this is her"; if not, say no, and the writer rolls back.
```

Notes:
- **Decide** comes after the closeout card has run and the resident has said it is ready.
- **Container** is opened from the room's own root so the provider files it under that room. The writer labels it a spare at once.
- **Go** counts only when it is given for this replacement, after custody. A go given at the start does not count.
- **Hello** is two things: the load test (a correct first reply) and the operator's acceptance. A correct status alone is not acceptance.

---

## 10. Rules for New Files

Filing boundaries: PoT 1.1; filing mechanics: CONSTRAINTS C01. The map
(`docs/ops/README.md`) locates the lanes and current holds; it is not a second
source of law.

1. Use an existing base lane; other unmapped folders are legacy and are not extended absent assignment (CONSTRAINTS C01). The scratch lane is `var/tmp/`; from the project root, `mktemp -d "$PWD/var/tmp/<owner>-<operation>.XXXXXX"` allocates a unique task directory. The active case records that path and its owner/closeout condition.
2. One word per script, in `ops/lib/scripts/<word>.py`; a spec with the same name in `docs/ops/specs/scripts/<word>.md`, in STELA's sections (First Principles Rationale, Mechanics and Sequencing, Anecdotal Anchor, Integrity Filter Warnings); tests beside it in `tools/test/test_<word>.py`, with a test spec in `docs/ops/specs/tools/test/<word>.md`. `ops/bin/template <word>` writes the first three as skeletons.
3. Route incoming payloads to `storage/intake/` and working cases to `storage/active/` (PoT 1.1.4; CONSTRAINTS C01). Keep the storage root clear of new loose files. Operational source and documentation use `ops/`, `tools/` and `docs/` (PoT 1.1.1-1.1.3). Existing state consumers remain only under the bounded holds in the map; no permanent storage-state exception is implied. Clones, extraction trees and intermediates use owned `var/tmp/` scratch (PoT 1.1.13; CONSTRAINTS C01). Promote required results before scratch closeout (PoT 1.2.9); the retention pass classifies existing material separately.
4. A root file is a pointer, not a document.
5. Every new script, binary, test or runbook gets a row in its registry under `docs/ops/registry/`.

Also:
- The legacy scripts moved from `Scripts/` to `ops/lib/scripts/` on 2026-11-01, one word each with a spec (`docs/ops/specs/runbook/port.md`); the two frozen remains are under `archives/legacy/Scripts/`.
- `archives/legacy/Archived/`, `archives/legacy/Attic/`, `archives/legacy/Plans/` and `archives/legacy/Intake/` each get one review for the base or retirement. `Resident-Center/` and `Config/` left the room in block 7 for Control's frozen runtime custody.
- Raw session payload never enters Git.

---

## 11. Key Paths (Reference)

| Path | What |
| --- | --- |
| `ops/etc/resident-identities.json` | the registry: who each resident is (read only here) |
| `ops/lib/scripts/` | the tools |
| `ops/bin/` | entry points (`help`, `template`), adapted from STELA |
| `ops/src/` | templates and runbook assets |
| `docs/ops/specs/` | specs: `scripts/`, `binaries/`, `runbook/`, `tools/test/` |
| `docs/ops/registry/` | registries |
| `tools/test/` | tests |
| `logs/gauges/ledger.jsonl` | gauge default telemetry; the history moved here on 2026-11-04 (`archives/receipts/state-cutover-20261104.md`) |
| `<room>/logs/mind.lock` | shared mind-write lock, created by the first authorized write; no legacy lock existed at the cutover of 2026-11-04; no mind content change |
| `storage/handoff/` | team room (private working notes; ignored) |
| `storage/intake/`, `storage/active/` | incoming and named case payloads; only lane `.gitkeep` files admitted; no operational code trees |
| `var/tmp/<owner>-<operation>.<unique>/` | task scratch; allocate with `mktemp -d`, contents ignored |
| `var/tmp/packet/` | the one active dispatch packet's Git worktree; made by `open`, removed by `ship` or `abandon`; the room's own checkout stays on clean `main` |
| `storage/handoff/PACKET.md`, `storage/handoff/RESULTS.md` | the packet's draft and gate log; latest-wins, private, never committed |
| `archives/packets/` | one kept leaf per landed dispatch packet; public; written only by `packet.py` |
| `logs/packets/ledger.jsonl` | the packet tool's private ledger: one line per station, with each contract's digest |
| `logs/open/ledger.jsonl` | the read-in's private ledger: one line per complete OPEN, with the hashes of the law it showed |
| `MIND.md`, `archives/mind/`, `logs/mind/ledger.jsonl` | the mind: index, leaves and ledger (out of Git) |
| `archives/receipts/` | durable receipts; only explicitly admitted redacted copies are tracked |
| `Backup/Codex-Session-Preservation/<batch>/` (under `<control>`) | tier-1 custody |
| `storage/lab/` | the other residents' lab folders, in custody, kept until their owners say; `storage/candidates/` is in custody and gone; new ephemeral work uses `var/tmp/` |

---

## 12. Glossary

- **Resident:** a registered long-lived identity; room residents have this room as their registry room.
- **Worker:** an actor spawned by a resident through provider delegation, in-session or as a separate unregistered session. An unregistered session alone proves neither worker provenance nor disposal eligibility.
- **Body:** the session file the provider writes (Claude JSONL, Codex rollout, Copilot events).
- **Container:** the provider-native session a body belongs to; replaced at rotation.
- **Room:** the project root a resident works from; each room has one mind.
- **Registry:** `ops/etc/resident-identities.json`; the only authority for identity.
- **Window:** the model's context size in tokens.
- **Reading:** the provider's own token figure for one call, as `gauge` finds it.
- **Reserve:** the 50,000 tokens before the 70 percent line, where the closeout begins.
- **Closeout card:** the five steps a resident follows at its reserve.
- **Mind:** the room's concepts: a pointer index, `MIND.md`, and its leaves.
- **Leaf:** one immutable idea that stays true, with an id, an agent and a title.
- **Pointer:** one line of `MIND.md`, naming one live leaf.
- **Ledger:** `logs/mind/ledger.jsonl`, one line per write: id, agent, action, time, hash and size.
- **Donor:** the body being rotated out; never modified.
- **Destination:** the fresh native container selected for a successor.
- **Successor:** the new body built for the same resident.
- **Spare:** a prepared container not yet active; labeled as a spare.
- **Rotation:** changing bodies. **Compaction:** the provider's reduction of a body in place.
- **Binding:** the mapping from resident key to body. **Label:** the provider/editor display name.
- **Capsule:** the four-part orientation text appended to the successor.
- **Tier A, Tier B, capsule-only:** reseed, transplant, and the fallback (section 6).
- **Hold:** the launcher's stop record, kept from custody until acceptance.
- **Verified swap:** the writer's atomic install after the operator's go; the `.NEW` swap is the operator's fallback.
- **Custody:** two-tier, hash-verified preservation; see section 7.
- **Receipt:** the durable record of one action in `archives/receipts/`.
- **Writer:** the single named owner of a surface or operation.
- **Worker thread:** a provider-spawned helper session; not a resident (`DOCTRINE.md` section 1A).
- **Test:** synthetic execution. **Check:** read-only live or staged-layout inspection. **Native live validation:** the separately named native operation (CONSTRAINTS C07).
- **Role-directed body change:** an act on body bytes, container, binding, registry or label; native appends, compaction and supported rename are distinct.
- **Record:** a kept event account. **Maintained surface:** a surface deliberately kept current by its writer.
- **Rebuildable tool state:** not a kept record merely because it is called a ledger.
- **Block:** an operator-opened bounded work unit; the closeout card comes from its template.
- **Team:** the Integrator and the Contractors, identified through the registry.
- **Dispatch packet:** the one unit in which a change reaches `main`: one id, one branch, one pull request, one kept leaf (section 1B). Not the resident packet, which is a routing form.
- **Packet leaf:** `archives/packets/DP-SES-NNNN.md`, the kept record of one dispatch packet; a different thing from a leaf of the mind.
- **Delivery function:** one of the four kinds of work in a dispatch packet: Integrator, Contractor, Auditor, Orchestrator (PoT 4.1.11; CONSTRAINTS C16 and C17). The leaf names by registry key who carries each; a function is not a seat.
- **Station:** one step of a dispatch packet, one command run by the resident who carries its function: draft, open, close, audit, ship.
- **Packet gate:** the rules of a valid dispatch packet read from Git objects alone, run by the required check; a different thing from the single-writer gate.
- **OPEN:** a resident's read-in, made by `ops/bin/open`: the law shown on its own screen, with the clauses of the functions the open packet gives it, and recorded; good for one body, one text of the law, one shift and the functions it showed (section 1C). A different thing from the `open` station of a dispatch packet.
