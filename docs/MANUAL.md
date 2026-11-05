# Sessions Operations Manual (Command Console)

Owner: Claude Shannon, Session Continuity Manager. Written 2026-10-30 at the operator's request for a help system and a manual, both taken from the STELA framework, by a workflow agent under Shannon's assignment. Framework: STELA's manual, the house convention, kept in the operator's Control tree and not in this repository; filled for this house. Map: `docs/ops/README.md`. Index: `docs/INDEX.md`.

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
- **minds:** the small curated record of who a resident is, written only with the operator's yes;
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
measured closeout, separately approved mind entries, verified custody,
destination-native successor, required go, closed-writer join, native
readback and operator acceptance. This sequence does not imply that an
unwritten runner, unwired hook or notebook integration exists.

---

## 1. People and Roles

| Who | Seat | Owns | Does not own |
| --- | --- | --- | --- |
| **The operator** | operator | objectives, priorities, authority, every yes and every go, final acceptance | implementation chores |
| **Claude Shannon** | Session Continuity Manager (registry key `session-doctor`) | continuity, the Sessions room, the specs, coordination of the team, running rotations for other residents | his own rotation (Claudine runs it) |
| **Claudine Colbert** | Assistant Session Continuity Manager | the tools she is assigned as sole writer (`gauge.py`, `mind.py`), and Shannon's rotation | a surface another writer holds |
| **Joe Codex** | Session Continuity Apprentice | read-only measurement and the Codex side (methods, runway figures, Codex hooks) | any write without the operator's named go |
| **Claudio Freeman** | independent reviewer and auditor (Control) | review before reliance, audit after change | implementation, repair or rollout writing on work he reviews |
| **George** | Control authority, desktop continuity and cross-project coordination | routing and the exact packet for cross-room work | the operator's acceptance |

Rules that hold for every seat:
- **One writer per surface.** Each file, live session and rollout has exactly one named writer at a time.
- **The team room.** `storage/handoff/{shannon,claudine,joe}.md`. Each member writes only their own file. Results are promoted to `archives/receipts/` or the office handoff; the room itself is working notes.
- **A file proves no delivery.** the operator relays between chats. A routing decision or a note in the team room is not delivery.
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
      |      writes its closing handoff, and proposes up to 3 mind entries in chat
      v
 the operator says yes, in conversation
      |
      v
 [mind]      writes a new leaf archives/MIND-<key>-<date>-<hash8>.md
      |      and moves the resident's line in the room's MIND.md
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
| mind | `ops/lib/scripts/mind.py` | `docs/ops/specs/scripts/mind.md` | `tools/test/test_mind.py` | built and tested on synthetic rooms; `project` writes a leaf copy into a named notebook folder (source only, no default home); actual use, a real notebook and the launch wrapper have separate acceptance |
| rotate | `ops/lib/scripts/rotate.py` (not written) | `docs/ops/specs/scripts/rotate.md` | none yet | spec only; rotations still run by hand, by the spec |

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

### Mind (read and check; writing needs the operator's yes first, see section 5)
~~~bash
python3 -I -B ops/lib/scripts/mind.py check
python3 -I -B ops/lib/scripts/mind.py show <key>
python3 -I -B ops/lib/scripts/mind.py show <key> --ref
python3 -I -B ops/lib/scripts/mind.py history <key>
python3 -I -B ops/lib/scripts/mind.py preview <key> --changes <file.json>
~~~

### Tests (synthetic data only; no real body, room or mind is touched)
~~~bash
python3 -I -B tools/test/test_gauge.py
python3 -I -B tools/test/test_mind.py
~~~
Reviewers also run each suite at the host umasks 0002 and 0022 as well as 0077; a suite that passes only under one umask is not green.

### Closeout and rotate
`closeout.py` is an implemented hook entry point, not an interactive phase
runner; its specification defines JSON input and the staged validation route.
`rotate.py` remains unimplemented. These facts do not authorize hook wiring
or a native canary (PoT 6.1.2, 6.1.5).

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
The forms live in `ops/src/` as `.tpl` files (the operator, 2026-10-30: the agent kept changing the form, or at times forgot it). A slots file holds `KEY=VALUE` lines. Report mode refuses a missing, unknown or empty slot, a `[PLACEHOLDER`, any `{{...}}` left in the output, and an existing `--out` file. Report forms are not tool names. The rotation `receipt` remains distinct from `source-change`, which records bounded source/configuration work, exact heads, validation, review, integration and rollback.

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
4. Propose up to three mind entries, in chat, for the operator's yes. Write nothing to the mind until he says yes.
5. Tell the operator the resident is ready for rotation. Shannon's desk runs it; for Shannon himself, Claudine runs it.

**Codex and Copilot residents.** Codex CLI 0.166 documents the same hook (Joe Codex, `joe.md`); the PyCharm path is untested, so it is tried on one Codex resident before anyone relies on it. Until then, and for Copilot, the operator pastes the card.

The implementation and `tools/test/test_closeout.py` already exist. A native
delivery check and any hook, notification or timer installation follow the
separately reviewed exact operation (PoT 6.1.2, 6.1.5). The old staged runbook
does not reopen its expired live window.

---

## 5. Writing a Mind

Spec: `docs/ops/specs/scripts/mind.md`. Source and synthetic tests exist;
current test results belong to their validation receipt, not a frozen count
here. The `project` command exists in source (W5 first slice): it copies a
verified leaf into a notebook folder the operator names; the operator must
first stop that notebook's writer, which the tool cannot detect. No notebook
home is chosen, no sealing or wrapper exists, and a projection is not proof
that a provider loaded it.

**What a mind is.** The small curated record of who a resident is, what it has learned and what it owes. It travels into every successor beside the donor's own summary and window, and never replaces them.

**How input arrives: solicited, in conversation.**
1. The closeout card (step 4), or the operator directly, asks the resident for up to three entries.
2. The resident proposes them in chat: layer, the text in its own voice, the event, the fix where one applies, where it does not apply, and a source that resolves.
3. The writer runs `preview` so that the operator reads exactly what would change: each addition in full, each amendment before and after, each retirement with the text it removes. Nothing is written.
4. **The operator says yes in the conversation.** Without his yes nothing is written.
5. The writer runs `write <key> --changes <file> --yes "<the operator's words>" --by <writer key>`, passing his words exactly as he said them. The tool refuses without them.
6. The tool writes a new immutable leaf and moves the resident's line in the room's `MIND.md`. It prints the change and the leaf's full SHA-256.

**What never happens.**
- No stored proposals, no queue, no secret key, nothing waiting for approval.
- No hand edits: a leaf is valid only in canonical form; a change is always a new leaf.
- No identifiers, live state, medical content or secrets in a mind; the screens refuse them.
- No blame in the core layer; an incident enters only as a closed lesson with its fix.
- Nothing is silently dropped to fit a budget; the resident proposes a retirement and the operator says yes to it.

**Where minds live.**
- Pointer: `<room>/MIND.md`, one line per resident in that room.
- Leaves: `<room>/archives/MIND-<key>-<date>-<hash8>.md`, mode 0600.
- Both are out of Git and backed by two-tier custody.

**Before a mind write.** Verify the target room ignores `MIND.md` and
`archives/MIND-*`; the tool checks that boundary and refuses exposure
(PoT 5.1.3). The archives-root leaf location is already implemented. A
historical missing-ignore observation is not a current permission gate.

**Checking.** `mind check` runs every gate (registered, pointer, leaf, entries, chain, newest) and exits 1 on any blocking failure. `mind show <key> --ref` binds the rotation capsule to the leaf hash.

---

## 6. Running a Rotation

Spec: `docs/ops/specs/scripts/rotate.md`. Status: spec only; `rotate.py` is not written, so each rotation follows the spec by hand, phase by phase, and stops at each stop point.

**Roles.** the operator decides, opens the container, gives the go, accepts or does not. Exactly one writer, named before work starts and never the resident being moved. The donor closes well and never builds its own successor. Claudio audits afterwards.

**Tiers, declared in writing before work starts.**
- **B, transplant (default):** the capsule plus the donor's compaction summary and a measured slice of its own window, word for word.
- **Capsule-only:** only when a window build fails to load, on the operator's go.
- **A, reseed:** a fresh session reads the handoff; only on the operator's explicit choice, recorded as Tier A and never called a rotation.

**The capsule, appended as text (never a path), in four parts:** registry header; the mind leaf, verbatim and hash-verified; the transition note; the first-turn line ("the room's status in a few lines, then speak as yourself").

**Phases (each ends at a stop point; the writer reports and does not run ahead):**

| Phase | What happens | Stop point |
| --- | --- | --- |
| 0 Trigger | gauge crosses the line; the closeout card has run; tier, donor, writer, destination and reading recorded | recorded in the handoff |
| 1 The donor closes well | closing handoff; up to three mind entries proposed; the operator's yes; `mind write` | leaf written |
| 2 The mind is ready | `mind check` passes; leaf hash matches the pointer | gate passes |
| 3 The destination | the operator opens a fresh chat in the room; the writer labels it a spare at once and verifies room, working directory, no other owner, no process holding it | verified |
| 4 The window | measure the donor by the gauge method; cut at a genuine operator prompt; carry at least one exchange beyond procedure; record the reason | cut recorded |
| 5 Build and static gates | splice, re-identify by identity field, externalize media, append the capsule and a fresh plain label; run every static gate | all gates pass |
| 6 Custody and serve-safety | `launcher stop <key>` writes the hold; donor, pristine destination, successor, capsule, gates, media, registry and binding go to both tiers, checked against `SHA256SUMS` | both tiers verified |
| 6 to 7 the operator's go | the writer names container, room, size, custody hash and rollback, then waits; a go given at phase 0 does not count | the operator's go |
| 7 Install | verified swap (default) or the operator's `.NEW` swap (fallback); registry and binding switched; six identity checks agree; rollback on any failure | six checks agree |
| 8 Acceptance | `launcher serve <key>` (load test and hold release); first reply gives room status and speaks as itself; first gauge reading recorded; clean native append; then the operator's own acceptance | the operator states that he recognizes him, or her |
| 9 Close | receipt `archives/receipts/<resident>-rotation-<n>-<date>.md`; donor store entry removed or relabeled only after custody is verified in both tiers; the new resident confirms its mind | receipt written |

Registry updates and rollback follow the canonical identity-registry privacy
contract in [the rotation specification](ops/specs/scripts/rotate.md). The
launcher roster/binding pair is a separate surface; no blanket file-mode
change follows from this procedure.

**Codex residents.** `ops/lib/scripts/rotation.py` does not carry the native compaction summary. A Codex rotation under this spec waits for a Codex-specific design and a loader test.

[PLACEHOLDER: `ops/lib/scripts/rotate.py` (Claude residents first), its tests and its test spec. Owner: Claude Shannon assigns the writer; Claudio reviews; ingredients are `splice_window.py` and the gates in `storage/candidates/joy-anne-rotation-20261030/` and `storage/candidates/shannon-rebuild-20261029/`.]

---

## 7. Custody

Every donor is preserved whole. A rotation, a relabel or a removal never proceeds until custody is verified.

**Two tiers.**
- **Tier 1, canonical copy:** `<control>/Backup/Codex-Session-Preservation/<batch>/`, on the always-present internal drive.
- **Tier 2, redundant cold copy:** the same batch on a mounted hot-swap drive (`hard_vol1` or `hard_vol2`, interchangeable peers per `DOCTRINE.md` section 8).

**The batch.** One folder per operation, named for what and when (for example `central-donors-20261026/`, `claudio-spare-relabel-20261030/`), holding the files and a `SHA256SUMS` file. Verification is a fresh hash of every file in both tiers against `SHA256SUMS`, with tier 2 read directly from the drive, never assumed from the copy step.

**What goes into custody for a rotation:** the donor's closed copy, unmodified; the pristine destination; the successor; the capsule; the gate output; externalized media; the registry and launcher binding before the change.

**Drive health.** The map records that `hard_vol2` is failing and a replacement is pending. A tier-2 copy on a failing drive is still read back and hashed; a mismatch is a stop, not a warning.

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
- **Decide** comes after the closeout card has run and the resident has said it is ready. The operator also says yes or no to any mind entries proposed at the closeout.
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
| `MIND.md`, `archives/MIND-*` | minds (out of Git) |
| `archives/receipts/` | durable receipts; only explicitly admitted redacted copies are tracked |
| `Backup/Codex-Session-Preservation/<batch>/` (under `<control>`) | tier-1 custody |
| `storage/lab/` | the other residents' lab folders, in custody, kept until their owners say; `storage/candidates/` is in custody and gone; new ephemeral work uses `var/tmp/` |

---

## 12. Glossary

- **Resident:** a registered long-lived identity; room residents have this room as their registry room.
- **Worker:** an actor spawned by a resident through provider delegation, in-session or as a separate unregistered session. An unregistered session alone proves neither worker provenance nor disposal eligibility.
- **Body:** the session file the provider writes (Claude JSONL, Codex rollout, Copilot events).
- **Container:** the provider-native session a body belongs to; replaced at rotation.
- **Room:** the project root a resident works from; minds live per room.
- **Registry:** `ops/etc/resident-identities.json`; the only authority for identity.
- **Window:** the model's context size in tokens.
- **Reading:** the provider's own token figure for one call, as `gauge` finds it.
- **Reserve:** the 50,000 tokens before the 70 percent line, where the closeout begins.
- **Closeout card:** the five steps a resident follows at its reserve.
- **Mind:** the curated record of a resident, as a chain of leaves.
- **Leaf:** one immutable version of a mind, named with its own hash.
- **Pointer:** the resident's line in the room's `MIND.md`.
- **Yes:** the operator's words, given in conversation, recorded on the leaf.
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
- **Team:** the Manager, Assistant and Apprentice, identified through the registry.
