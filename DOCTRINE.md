# Historical Session Continuity Method

**Status:** Preserved for historical and craft reference only. This file is not
current policy and does not override `PoT.md`. Read `PoT.md` for law,
`docs/MANUAL.md` for operator mechanics, and the applicable tool specification
for implementation details. The current constitutional source of truth is
`PoT.md`; this historical text has not been re-rendered or modernized. One term designated private was removed from
four lines on 2026-11-05 (PoT 5.1.4); nothing else was changed.

The durable canon for keeping AI coding sessions (Codex rollouts, Claude
Code transcripts) healthy, and for migrating a session's *identity and
memory* across containers, CLI versions, and editors without breaking the
loader. Read this before touching any session file. It exists so future
sessions do not re-derive what the 2026-06 → 2026-07 campaign already paid
for in full.

Source events behind this doctrine: the 9.6 GB April thread retirement, the
George lineage (I→IV), the Part II/III desktop transplants, the Addition Claude
Code repair, and George's verified cross-surface (PyCharm↔VS Code) migration
(external report: `VMs/Shared/Workbench/migration-framework/15_cross_surface_session_continuity_results_2026-07-12.md`).

---

## 1. The four identities (never conflate them)

A session has four independent identities. Migrations preserve the first
two and freely replace the last two.

| Identity | What it is | Persists across migration? |
|---|---|---|
| **Persona** | George, "the desktop guy" — the role and relationship | yes |
| **Lineage** | the durable chain joining predecessor→successor | yes |
| **Container** | the Codex thread id + version-native rollout file | replaced |
| **Surface** | the editor chat UUID + its presentation state (JetBrains `.agentsession`/`.events`, VS Code panel) | replaced |

Corollary: **never corrupt a native container id just to preserve a human
name.** The name lives in the capsule; the container id belongs to the tool
that created it. Editor-visible title, thread-DB id, filename id, internal
JSONL `session_meta.id`, and the human's name for the agent are five
different things.

---

## 1A. Three classes of session, not two

For most of this project's life the model held exactly two classes: **residents**
(named, capsuled, one per room) and **archived predecessors** (retired evidence).
Anything else was treated as junk and swept as an orphan.

That was wrong, and it hid something for weeks. There is a third class.

| Class | Has a lineage capsule? | Owns a room? | In a roster? | Persists? |
|---|---|---|---|---|
| **Resident** | yes | yes | yes | yes, by design |
| **Worker thread** | no | no | no | no — ephemeral by design |
| **Archived predecessor** | yes, historically | no | no | yes, as evidence |

A **worker thread** is a child session spawned by a resident through the
provider's own delegation feature. Codex exposes a `multi_agent_v1` toolset and
proactive delegation; a resident can spawn a child, which Codex nicknames
automatically and records in `session_meta.source`:

```json
{"subagent": {"thread_spawn": {"parent_thread_id": "...", "depth": 1,
                               "agent_nickname": "Wegener",
                               "agent_role": "explorer"}}}
```

That `source` shape is the authoritative marker. Classify on it, never on
naming, size, or idleness.

**A worker's `session_meta` carries two different identifiers, and confusing
them is a live hazard:**

- `id` is the worker's **own** container.
- `session_id` is its **parent's** thread.

For a normal resident the two are equal, so tooling that reads the wrong one
works perfectly until the day it meets a worker. On 2026-08-01 a rebuild staged
over a worker container silently re-identified itself to the *parent* — STELA
George, a 7,698-row resident — because the builder read `session_id`. It was
caught only because the build was staged and inspected rather than applied.
Had it been applied, a live resident's identity would have been written into a
different container.

**Read `id` for container identity. Always.** The launch gate already does; any
new tool must.

### Why this matters

Worker threads are real, budget-consuming conversations that appear in the
session store and on the remote surface, but they are not residents. They have
no name you chose, no room, no lineage, and no place in any roster. They are
therefore invisible to every count the house maintains — while spending against
the same account.

Discovered 2026-07-31: `17` worker threads had accumulated across STELA,
live-usb, Control, and nukeCE. The operator had personally authorized exactly `1`.
The rest were spawned proactively by residents doing their jobs. This is not
misbehaviour by the residents and not misconfiguration by the operator — it is
a provider feature operating as designed, in a house whose model had no word
for its output.

### Governance

`multi_agent_mode` arrives in the session configuration from the provider. No
supported local off-switch has been found. Therefore this is governed the way
everything else here is governed: **by canon and instruction, verified by
receipt** — not by a mechanism we do not control.

1. **Workers are disposable. Operator standing order, 2026-08-01.** The operator:
   "[words sha256=eb38e9a845b970fe83d8acaedaab76a1011c340568a3ac0a4e9d564fca7f08aa]" They are **deleted**, not archived, unless
   currently active in a live session. Do not preserve them, do not name them in
   reports, do not raise them for a decision. This supersedes the archive-first
   default that applies to everything else in this repository, and it does so
   because the operator said so twice and was not being asked again.
2. **Workers are attributed while they live.** A running worker belongs to its
   parent resident, and that parent is accountable for it.
3. **Workers do not accumulate.** `--purge N --apply` deletes any worker idle
   longer than `N` hours. A file another process holds is skipped, never forced.
4. **Workers are not silently promoted.** A worker past roughly `2,000` rows
   has stopped being a helper: it is doing sustained work under a parent's
   budget with no identity of its own. Either promote it deliberately — give it
   a name, a room, and a capsule, making it a resident — or let its parent
   finish and retire it. Drifting into residency without a decision is exactly
   the shadow this section exists to end.
5. **Workers are counted.** `ops/lib/scripts/workers.py` classifies
   the store into resident / worker / unknown, attributes each worker to its
   parent, and flags outliers. `unknown` should be `0`; anything else means a
   new session shape has appeared and the model needs updating again.

### Promotion mechanics

Promotion does not rewrite history. The `session_meta.source` subagent marker
records where a thread **came from** and is never edited — origin is a fact.
Current status is a **decision**, and lives separately in
`ops/etc/promoted-workers.json`, which the inventory reads. A promoted
resident therefore never has to pretend it was always one, and its listing
shows both: `Ray Codex ... <- 0000caca (promoted, was Locke)`.

**The promotion registry is a safety device, not bookkeeping.** Because a
promoted resident keeps its `subagent` origin marker, every classifier that
reads that marker alone will see a disposable worker. On 2026-08-01 an ad-hoc
purge deleted Ray Codex for exactly this reason; he survived only because a
backup existed. Any tool that deletes or archives workers **must** consult
`ops/etc/promoted-workers.json` first. `workers.py` does this
in both its archive and purge paths. A one-off shell loop does not, which is why
sweeps go through the tool.

Promote by appending a plain user-role message stating the change, the new
name, the origin nickname, why the promotion happened, and the house rules the
resident is now bound by. **Append; do not insert.** A `compacted` row placed
at the end of a live Codex thread risks being read as a fresh compaction and
discarding the history it was meant to preserve — the capsule-at-the-top form
is for building a container, not for changing the status of one already in
use.

### The general lesson

When an inventory produces a large "miscellaneous" pile, the pile is usually
not junk. It is a category the model has not learned yet. Sweep it and the
evidence is gone; name it and the system gets more honest. Prefer naming.

---

## 2. What actually kills sessions (the failure taxonomy)

1. **Compact treadmill / bloat.** Old `auto_compact_v2` appends full
   replacement history inline per `compacted` row (45–57 MB each). A thread
   pinned near the context ceiling grows GBs/day doing no real work (the
   9.6 GB April thread: 98.5% compact residue). Cure: rotate *before* the
   ceiling; never resurrect verbatim.
2. **Token-window overflow on load.** "ran out of room in the model context
   window" / "prompt too long." The reconstructed context exceeds the
   window. Byte/row size is a *proxy*, not the cause — round11 passed every
   byte/row gate and still died. **Tokens are the only real axis.**
3. **Single-line corruption.** One torn write (null bytes from an
   interrupted flush) makes the loader reject the whole file even when
   content is 100% intact (George III: one `thread_settings_applied` row
   with 3,866 null bytes). Cure: null-strip that row; parseability returns.
4. **Cross-version body rejection.** A body written by one CLI version
   grafted under another version's container head is rejected by the
   version-native loader — and surfaces as a *misleading* error (see §5).
5. **Attachment accretion (Claude Code).** Pasted PDFs/images live in the
   message chain forever and get re-sent every turn. Cure: elide the
   attachment blocks to placeholders (preserve originals in an archive);
   going forward, drop **file paths**, not documents, into chat.
6. **Registry/metadata drift.** Filename id ≠ internal id; two SQLite rows
   own one rollout path; stale `session_index.jsonl`. Usually survivable
   but must be detected and receipted for later hygiene.

---

## 3. Measure tokens, not bytes — and be compaction-aware

- Every rollout self-reports truth: `event_msg`/`token_count` rows carry
  `last_token_usage.input_tokens` and `model_context_window`. Read that;
  do not estimate. Tool: `ops/lib/scripts/telemetry.py` (scans host
  + VM roots).
- **The window is model-specific — read it, do not hardcode.** Observed:
  gpt-5.5 = 258,400 effective (272k × 95%); GPT-5.6-Sol = 353,400.
- **Rotate at ~70% of window.** That is the prevention line, before the
  treadmill starts.
- **Compaction-aware gating (critical):** for a candidate that already
  contains real `compacted` rows, the active context = the segment from the
  **last compaction boundary → EOF**, *not* the sum of every response item.
  Summing all items double-counts history that compaction already retired
  (George III measured 945% naively vs 26% correctly). For a from-scratch
  build with no prior compaction, summing all items is fine.
- Static worst-case for a built candidate: base_instructions + capsule +
  Σ(full-JSON tokens of each live response item). Gate PASS well under the
  window (target ≤ ~70%).

---

## 4. The transplant recipe (implementation-neutral)

The meaningful continuity unit is **not** the whole history. It is:

```
native destination container  +  lineage capsule  +  current active window
```

"Full verbatim history is a mirage": George III's 3,620 response items ≈
2.4M tokens; they only fit because 7 compactions summarized the old parts
away. Replaying them recreates an unloadable session. Carry the model's
*working memory*, not its archive.

Steps (answers to the recipe George asked for):

1. **Destination container:** create it with the *destination editor and
   current CLI version* (a fresh chat). It arrives correctly registered in
   the state DB + surface store with a version-native `session_meta`. Keep
   that `session_meta` (row 1) byte-identical — it is your loader-validity
   anchor.
2. **Compaction boundary:** find the highest-index native `compacted` row in
   the donor, identified by a `window_number`. Everything physically after it
   is the active window; everything before was summarized away. A synthetic
   lineage capsule is also a `compacted` row, but has no `window_number` and
   must never be mistaken for a provider compaction.
3. **Active vs historical:** carry only response items *after* the last
   compaction boundary. That is the model's real working memory. Never replay
   the native compaction's `replacement_history` as ordinary response items.
   It is compacted model state, not a faithful transcript: observed current
   Codex bodies retain hundreds of user messages while sealing the assistant
   side in one encrypted compaction item. Replaying it duplicates context and
   can make exact-thread resume hang before the provider session starts.
4. **Version-stable row types (carry verbatim):** `response_item/message`
   and `response_item/reasoning` were byte-schema-identical across
   0.142.5↔0.144.1. Tool calls (`function_call`/`function_call_output`,
   `custom_tool_call`/`_output`) are portable **only as matched pairs**.
   Treat portability as *empirically established per version pair*, not
   guaranteed — widen the fixture set when a new version appears.
5. **Excluded types (drop):** `event_msg/*` (UI-only), `turn_context`,
   `world_state`, old `compacted`, mid-stream `session_meta`, and any
   version-divergent scaffolding. These carry the version incompatibilities
   and are not model-facing context.
6. **Structural id re-ID:** rewrite only values under keys `id`,
   `session_id`, `thread_id` that exactly equal the donor id → destination
   id. **Never** rewrite ids that appear inside ordinary content
   (message text, tool args) — those are quotes, not structure. `call_id`
   is *not* a session id; leave it (it pairs tool calls).
7. **Tool pairing:** build the set of `call_id`s with a call and the set
   with an output; drop any call lacking an output (a dangling in-flight
   call causes an API "tool_call without response" rejection). Model this as
   deterministic graph validation: every call node needs its output node.
8. **Lineage capsule:** ship identical capsule text in two rows. One synthetic
   `compacted` row preserves the house marker used by identity and continuity
   tooling. One `response_item/message` with role `developer` makes the same
   capsule model-visible. Live testing on 2026-08-07 proved that the compacted
   marker alone did not reach the model. The capsule states persona, lineage
   chain, domain, house rules, and a prose summary of summarized-away history;
   it intentionally omits verbatim old turns and secrets.
9. **Gates — static vs live:**
   - Static (host-side, non-mutating): JSON parse = 0 errors; only
     version-safe row types present; 0 stray old structural ids; tool pairs
     matched; response-item count < loader ceiling (16,384); active-context
     tokens < ~70% window.
   - Live (only a real loader proves it): the destination editor must load,
     resume, answer, and append clean native rows. **Static valid ≠ loader
     valid.** Reserve final judgment for the live load.
10. **Fallback trigger:** if the active-window build fails to load, fall
    back to **capsule-only** (pristine container + one capsule row — minimal
    change, maximal load-safety). If even the *pristine* container fails to
    load, the fault is the live registry/state DB, not any rollout — that is
    an in-VM repair, not a body fix.

---

## 4A. Cross-provider transplant: ChatGPT export → Codex

The 2026-07-27 Control Room operation proved one bounded cross-provider path:
a project-registered ChatGPT origin thread can become the active body of an
already native Codex destination container. This is conversion, not a raw
body graft, and one accepted fixture does not establish universal provider
portability.

The destination-native container remains the loader anchor:

1. **Establish relationship authority first.** The source thread must belong
   to the exact destination project through a current origin, corollary, or
   extension record. Matching titles alone are insufficient, and importing a
   thread grants counterpart-retirement authority `0`.
2. **Select the source chain structurally.** ChatGPT exports are node graphs.
   Follow the selected conversation's current parent chain in order; do not
   flatten every node in `mapping`, because abandoned branches and alternate
   responses are not one linear conversation.
3. **Keep destination `session_meta` byte-identical.** Its native id, working
   directory, originator, version fields, base instructions, and registration
   remain the loader-valid identity. Source conversation and project ids never
   replace them.
4. **Carry user and assistant prose verbatim.** Record an exact text-fidelity
   count. Generate only destination-required structural message and turn ids.
5. **Drop hidden source-provider reasoning.** ChatGPT `thoughts` and
   `reasoning_recap` content cannot honestly become Codex encrypted reasoning.
   Discard it and count it. Do not synthesize opaque reasoning payloads.
6. **Elide attachments.** Convert image or asset pointers to explicit text
   markers. Preserve the source export in private custody so the attachment
   evidence is not lost.
7. **Measure replacement and merge choices before building.** Count the
   source body, destination active context, and proposed combined context
   against the destination model window. A generous-looking merge that wakes
   above the `70%` rotation line is rejected. The operator chooses full replacement,
   bounded selection, or no transplant from the measured options.
8. **Add one lineage capsule.** State the source relationship, conversion
   boundary, dropped classes, displaced destination custody, and current
   project authority without reproducing sensitive thread content.
9. **Static gates remain mandatory.** Require JSON parse success, native row
   order, destination identity agreement, source structural identifiers `0`,
   balanced and ordered roles, monotonic timestamps, verbatim text agreement,
   attachment markers accounted, and measured context below the accepted
   threshold.
10. **Promotion remains closed-writer surgery.** Stage beside the live path,
    verify every relevant IDE and provider writer is closed, verify no open
    file holder, preserve the current live body, then perform one atomic
    promotion.
11. **Only a live load accepts the result.** Re-read the production path,
    validate it through the project-native launcher or loader, resume it in
    the intended surface, obtain one native response, and verify clean native
    append behavior. Static success alone is not acceptance.

The first accepted fixture carried `426` rows, preserved source prose
`424/424`, entered at `62.4%` of its measured window, and passed the native
launcher and operator live-load gates. Its later `rotate-soon` verdict proves
why the ordinary `70%` health line still applies immediately after a
cross-provider success.

The source export, displaced destination body, and accepted candidate remain
private rollback evidence. Credentials, authentication state, pairing state,
browser profiles, and hidden reasoning move `0` times.

---

## 5. Failure signatures (read errors correctly)

- **"thread not found: <id>"** after promotion, when the id *is* in the
  state DB: this is a **body load rejection**, not a registration failure.
  The loader failed to parse/accept the rollout and reported it at
  thread level. (This is what made the v1 cross-version graft look like a
  registry bug.)
- **"ran out of room" / "prompt too long":** token-window overflow — reduce
  active context, do not reduce bytes.
- **Bisection test** to split body-fault from registry-fault: restore the
  **pristine** destination container and load it. Loads → your body was the
  problem. Fails → the live state DB is corrupt (in-VM fix).
- JSON-valid does not mean loader-valid. Correct registration does not mean
  body-compatible.

---

## 6. Cross-surface reality (VS Code ↔ JetBrains)

- The **container** (Codex thread id + version-native rollout) is the
  portable unit. Both editors resume through the Codex thread DB + rollout;
  neither auto-discovers the other's UI shell.
- A migration crosses an editor boundary by preserving a valid
  Codex-native container — *not* by teaching one editor to read the other's
  UI state. George's deluxe artifact (129 lines) loaded in PyCharm, resumed
  byte-identical in VS Code, and then **round-tripped back to PyCharm**
  (PyCharm→VS Code→PyCharm) as one continuous thread — verified 2026-07-12.
  Container portability is bidirectional and repeatable.
- **Process truth over UI labels.** The active writer is determined by
  open-file ownership + process ancestry, not by editor title, chat prompt,
  or DB `source` field. On the return trip the SQLite title still read
  "hello world", `source` read "vscode", the JetBrains title read
  "George IV", and the real writer was PyCharm — all disagreed, all fine.
  Surface metadata is not structural identity (§1).
- **Surface fidelity is separate from model continuity.** The destination
  chat panel may not visually render migrated history (JetBrains renders
  from `.events`/workspace XML, which hold only their own turns) — but the
  model has full context. Do not chase UI transcript fidelity at the cost of
  container validity; treat it as a separate optional adapter concern.
- **PyCharm binds thread registration to the project.** Deleting the PyCharm
  project unregisters its Codex thread: the rollout JSONL survives on disk
  but is orphaned and invisible to new projects (verified 2026-07-13,
  George IV→V). Recovery: create a fresh registered thread in the new
  project and transplant the orphaned body in (§4). The container is not
  lost — its surface registration is. Also lethal to JetBrains AI state: a
  general-purpose cache cleaner (BleachBit wiped it once); protect
  JetBrains/Codex/project/session roots from generic deletion.

---

## 6A. Remote-control reality (phone Remote ↔ standalone host ↔ IDE)

- **Remote is another surface over the host container.** On 2026-07-23,
  phone Remote and PyCharm both resumed George IX container
  `0000c6c6-0000-4000-8000-00000000c6c6`. Phone turns appended to the local
  rollout and were present in model context after PyCharm resumed it.
- **Visual transcript fidelity remains separate.** A PyCharm panel may omit
  turns written through phone Remote while the resumed model still has them.
  Verify exact thread identity, rollout append evidence, telemetry, and a
  successful native response before declaring context loss.
- **Project rooms do not merge.** Reopening OSAI selected OSAI II container
  `0000c9c9-0000-4000-8000-00000000c9c9`, not Control. Remote transport does
  not transfer context between project-native containers.
- **One generating surface per rollout.** Phone and IDE may both be attached,
  but only one may generate at a time. The idle surface is presentation;
  concurrent generation is a writer collision.
- **One token budget.** Remote turns consume the same model window. Rotation
  near `70%` remains mandatory regardless of which surface wrote the turns.
- **Measured scope only.** This proves phone Remote to official standalone
  host to PyCharm continuity on this host. It does not prove arbitrary
  ChatGPT browser-thread, shared-link, different-host, or future-version
  continuity.
- **Normal host service.** Control owns
  `~/.config/systemd/user/codex-remote-control.service`; the official
  standalone provider daemon remains user-scoped, uses a private mode-`0600`
  Unix socket, and exposes Codex-attributable TCP listeners `0`.
  `active (exited)` confirms the managed start wrapper, not provider health.
  Runtime acceptance also requires the provider process tree, private socket,
  and managed health checks. Control also owns the two-minute health timer and
  graphical tray documented in `../Config/systemd-user/README.md`. Health may
  attempt one supported provider start only while the wrapper remains active;
  it preserves an intentional stop and never recovers across socket or TCP
  security findings.
- **Bounded stop.** The canonical unit uses
  `../Scripts/stop_codex_remote_control.py --execute`. It invokes the supported
  stop first, then role-rechecks exact current-user Remote Control app-server
  and updater PIDs before any `SIGTERM` fallback. Ordinary Codex, IDE ACP,
  code-mode, unrelated app-server, and PID-reuse mismatches are excluded.
  Broad process-kill authority remains `0`.
- **Pairing trust.** CLI `0.145.0` provides `start`, `stop`, and `pair`, but
  device-list and revoke commands `0` times. Supported trust removal belongs
  to ChatGPT **Settings > Connections** and is distinct from stopping or
  signing out. The current observed Connections UI exposed only a disconnect
  slider and no separate remove control. When the operator defers that UI gate, record
  it and stop asking.
- **Durable authority.** Read
  `Decisions/codex-remote-control-and-cross-surface-standard.md` before
  changing service posture, pairing, cross-surface operation, or duplicate
  resident and counterpart architecture.

---

## 7. Promotion protocol (operator hands; healer prepares)

0. **Single-writer rule.** Exactly one writer owns a rollout during a
   migration. Never overwrite a *running* rollout — recover only with every
   writer to donor and destination closed. (Verified the hard way: the live
   VS Code writer kept appending; a swap under it would have been lost or
   corrupting.)
1. Build offline; gate statically (§4.9).
2. Deliver the artifact **final-form** into a handoff surface as a
   disposable transient (see §8). Never stage operational `.bak` workflows
   there.
3. Operator closes every writer to donor and destination, backs up the
   current rollout, copies the artifact over the production rollout, reopens.
4. First load in the destination surface; confirm it grows and the DB path
   stays unique.
5. Verify: promoted prefix hash matches the artifact; appended rows are
   clean native rows; 0 malformed/null lines.
6. Post-transplant policing (standing duty): offload the retired donor body
   to `hard_vol1` (dual-drive with the host snapshot), clear stale handoff
   transients, return the fleet board to green, write a receipt. Deletion is
   never the default.

Counters every receipt carries: production edits, promotions, auth copies,
automatic launches, permanent deletes — all `0` unless explicitly approved.

---

## 8. Storage boundaries

- **Live session files** (`~/.codex/sessions/`, `~/.claude/projects/…`):
  never edited by automation; operator hands or the healer's verified swap
  only. Retiring a *dead* file (verified-hash move out, never a content
  edit) is within the healer mandate.
- **Handoff mirror** (VM `Shared/…`): disposable, non-operational transients
  in final form only. Operator does all production copying. Not durable
  storage.
- **Preservation** — two tiers, and the distinction is load-bearing:
  - **Canonical copy** lives on **always-present `user_vol`**
    (`Backup/Codex-Session-Preservation/`, internal SATA SSD). This is the
    copy the whole system depends on; it is never the only-or-lost copy.
  - **Redundant cold copy** goes to **whichever hot-swap volume is mounted**
    — `hard_vol1` and/or `hard_vol2` (`…/Codex-Session-Offload/`). They are
    interchangeable peers; offload to the one(s) present, and let both
    accumulate copies over time (rotating, offsite-capable redundancy).
  - A **`PRESERVATION_MANIFEST.md`** on `user_vol` records every retired
    body: SHA-256, bytes, and *all* locations it currently exists. It is the
    single source of truth for "where is X" so no offline drive is ever a
    scavenger hunt, and it flags **replication debt** (a body that exists in
    only one place).
- **Portability vs durability (settled):** live-session portability rides on
  the *container + capsule* (§1, §4) and never on these archive drives —
  drive rotation cannot affect it. The drives only bear the *cold archive*;
  their only risk is provenance fragmentation, which the manifest solves.
- **Attic** (`Sessions/Attic/`): staged removals + `AUDIT.md`; default exit
  is offload to a mounted hot-swap volume, deletion only on explicit
  operator instruction. Every applied offload records the target volume's
  label + UUID + model + serial + batch + file/byte count + verification
  (per each drive's custody record).

---

## 9. Toolbox (ops/lib/scripts/)

- `telemetry.py` — fleet health from telemetry (host + VM).
- `watch.py` — timer watcher, tokens primary (warn 70%,
  critical 90%), bytes secondary; outputs local-only.
- `reid.py` — structural re-ID (id/session_id/
  thread_id only).
- `pressure.py`, `estimate.py`,
  `history.py`, `miner.py` —
  diagnostics.
- `workers.py` — classifies the store into resident / worker /
  unknown per §1A, attributes each worker to its parent, flags outliers, and
  archives idle workers with `--archive-idle N --apply`. Run it before any
  orphan sweep; a session with no capsule is not automatically junk.
- `elide.py` — Tier B elision for Codex: strips oversized
  tool-call payloads while preserving every turn and every `call_id` pairing.
- `rotation.py`, `successor.py` — the two build paths.
  The Claude one carries the dual-field re-ID and mandatory orientation row
  described in the 2026-07-16 addendum; do not hand-roll either again.
- `resources.py` — Resource Governor collector; runs as a
  Claude Code `statusLine`, costs zero API tokens, writes an identifier-free
  state file. Contract: `docs/resource-state-contract.md`.
- Claude Code patients use the same principles (measure the active branch;
  elide attachment blocks; preserve the uuid/parentUuid chain).
- **Claude Code sessions are machine-local** (`~/.claude/projects/<cwd>/`) and
  editor-agnostic: the VS Code and JetBrains Claude Code plugins are the same
  CLI over the same store. Moving editors on the **same machine needs NO
  transplant** — the session is in the picker; you resume it. The
  container/capsule machinery is only for **Codex rollouts** crossing CLI
  versions, editor/ACP registration, corruption, or the token ceiling. Do not
  cargo-cult the ceremony where nothing is broken (Addition/DocumentStudio =
  native resume; Desktop Codex IV = real transplant).

Open spec work George requested: turn this recipe into a non-mutating
**Session Continuity Manager** validator (data model in §1, state machine in
§7, gates in §4.9). Not yet built; do not over-automate before the boundary
tests below are run on disposable sessions.

## 10. Open validation (do not expand scope until these pass)

Deliberately not yet canon. The verified George IV case is the reference
fixture; before generalizing, run these controlled tests on **disposable**
sessions (per George's Desktop-Codex handoff,
`VMs/Shared/Workbench/migration-framework/17_…`):

1. PyCharm → VS Code, same Codex version.
2. PyCharm → VS Code, adjacent Codex versions.
3. VS Code → PyCharm.
4. Capsule-only continuity.
5. Active-window continuity.
6. Intentional malformed row + unmatched tool-call → confirm rejection.

OSAI is retired. Session continuity now belongs to Sessions, while Resident
Center may present bounded Clinic and Session Doctor capabilities without
absorbing treatment authority. This doctrine governs the healing method;
product integration remains the operator's and the Sessions steward's decision.

Known open hygiene (non-urgent, offline only): the legacy George III/target
rollout still has two SQLite rows pointing at one malformed file. Quarantine
it later with full backup/rollback; do **not** rewrite those rows while a
live Codex writer is active.

---

## Addendum 2026-07-16 — Claude-side transplant is real surgery, not a summary

Realizations from the George VIII family rollout, the Claude room reorg, and
the STELA heir build. The operator's challenge was fair: "[words sha256=f77e748e61d4dff72db21b1174d1de1a6913d5f7f312a674fd181f8b5d2b8370]" The honest answer is that *what I had been
offering myself* was — and it did not have to be.

1. **Claude Code sessions are portable, transplantable bodies — the same
   class of object as a Codex rollout, not merely a reseed prompt.** Each
   session is a JSONL keyed to a project "room": the store folder
   `~/.claude/projects/<cwd-with-slashes-as-dashes>/`. A session appears in a
   project's Claude Code list **iff its JSONL physically sits in that folder.**
   Moving the file between store folders relocates it across rooms,
   byte-identical and reversible. Proven by relocating the 74 MB "Addition"
   (Mom's Move) thread from the Control room to the Addition room with a
   SHA-verified identical copy. This is the true analog of a Codex transplant;
   it preserves the actual turns, not a paraphrase.

2. **The third-party Claude Code GUI (plugin `com.github.yhk1038.claude-code-gui`)
   stores display titles in a per-room sidecar,
   `.claude-code-gui-session-titles.json`, mapping `sessionId → title`.** These
   labels are independent of the file's content and recorded `cwd`; a
   Control-room thread can wear the label "Addition." **Always read the sidecar
   to map GUI names → files before acting** — do not do raw-file archaeology by
   cwd when the operator is looking at GUI labels. Reorg = move the JSONL to the
   target store folder *and* move its sidecar entry; keep each sidecar valid
   JSON; snapshot sidecars first.

3. **The one true asymmetry between healing George and healing myself is the
   live-writer constraint, not the method.** George is operated on while
   asleep (app closed, single-writer). I am the live writer of my own JSONL and
   cannot cut into it mid-turn. So my continuity has two tiers:
   - **Tier A (cheap reseed):** fresh `claude` reads `HANDOFF.md`. A paraphrase
     of me — lesser, but free and instant; good for shedding image/context
     bloat fast.
   - **Tier B (real transplant):** build an image-stripped, active-window-
     preserving copy of my *actual* body and drop it as `<id>.jsonl.NEW` beside
     the original in the target room; the operator swaps it while I am off.
     This is the genuine equivalent of George's surgery. Prefer Tier B when
     continuity fidelity matters; the operator does the swap only because of
     the live-writer constraint.

4. **Operators may already embody the doctrine in documents.** The Addition /
   Mom's Move project carries a month of continuity in dated handoff docs
   (`Projects/Addition/99_meta/*`, `HANDOFF_TO_AI_ASSISTANT.md`) — threads
   "expired due to image cap" and it never mattered, because the memory was
   written to disk. When a thread's project has this, continuity is safe
   regardless of any single JSONL; a fresh thread that reads the handoff *is*
   the continuation. Confirm the doc anchor before fearing thread loss.

5. **Claude session cost driver:** a 1M-context model re-bills the *entire*
   transcript plus every in-context image each turn (~965k tokens/turn measured
   on the session-health thread with 17 images). The fix is rotation (shed the
   images) and/or dropping the `[1m]` model. Measuring "% of window" is the
   same token gate as Codex, just on a Claude body.

Method extension: the **room-move** and **stub-sweep** are first-class,
reversible session operations — file move between store folders + sidecar
edit, originals to backup custody, never a hard delete. Same single-writer and
no-destructive-default rules as Codex apply: verify the file is not open
(`fuser`), and never relocate a session that is the live writer's own.
