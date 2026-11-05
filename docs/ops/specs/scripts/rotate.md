# Technical Specification: rotate

Script: `Sessions/ops/lib/scripts/rotate.py` (to write; Claude residents first). Spec writer: Claude Shannon, 2026-10-30. It is ported from Claudine Colbert's runbook (`storage/candidates/mind-manifest-20261029/package/docs/ops/specs/runbook/transition.md`) and adds:
- Claudio Freeman's conditions C11 to C13 (`claudio.md` section 130);
- The operator's decisions of 2026-10-30, and the install decision Shannon made under his deferral.

Map: `docs/ops/README.md`.

Status: first source slice implemented 2026-11-05 by Joe Codex: synthetic,
read-only phase gates 0 to 2; phases 3 to 9 refuse. Independent source
review and integration pending. No live rotation or provider-load proof.

## First Principles Rationale

The operator, 2026-10-30: the rotation had never been formalized, and to him it always felt haphazard and awkward and was never carried out the same way twice. The craft existed in the Sessions doctrine: a native destination, a lineage capsule and the resident's own active window. But every rotation was assembled by hand from loose pieces, and the slips happened at the joins. In Joy's rotation 6, three of them came from hand-glued steps:
- a path passed where text was meant;
- an image pointer that led nowhere;
- a chmod in the wrong order.

`rotate` performs the same phases in the same order every time. It stops at fixed points, refuses on any failed gate, and drafts its own receipt. The art stays where it belongs, in where the window is cut and what the transition note says.

## Mechanics and Sequencing

### Implemented first slice: one dry-run stop at a time

The specification below describes the complete intended rotation. The first
source slice is deliberately smaller: it checks supplied synthetic evidence
for phases 0 to 2, rechecks earlier gates on each invocation, and stops after
the requested phase. Phases 3 to 9 return exit 2 with their named unmet
requirements before any input is read. They execute no builder, launcher,
custody, body, label, registry or installation operation. In particular, the
planned rollback below is not executable authority: donor handling must
follow CONSTRAINTS C09, not an unconditional donor restore.

Invocation uses the configured interpreter with `-I -B`:

```text
ops/lib/scripts/rotate.py --room SYNTHETIC_ROOM --key fixture-resident \
  --writer fixture-writer --destination INVENTED_SPARE --phase 2 \
  --gauge-row logs/gauge.json \
  --closeout-state logs/closeout/state.json \
  --closing-record storage/active/closing.json
```

`--phase` defaults to 0. `--dry-run` is the default and the only mode;
there is no apply mode. The room is mandatory, existing, 0700, owned by the
effective user, with no linked path components. It is not the source room.
It contains `.rotate-synthetic.json`, exactly
`{"schema":"rotate-synthetic/1","synthetic":true}`. This marker declares
fixture intent; it authenticates no operator and grants no live authority.
Registry bindings must use invented `0000`-prefix identifiers. No default
native store or real body is opened, and `.jsonl` input paths are refused.

All evidence paths are relative to this room, confined against parent/final
symlinks and `..`; regular 0600 owner files with one link are required.
The registry is `ops/etc/resident-identities.json`. JSON uses the existing
strict duplicate/nonfinite parser; input limits are 1 MiB, or 64 KiB for
the gauge snapshot, closing record, handoff/approval references and pointer.
Evidence is rechecked for content and identity changes before a successful
stop. Files, modes, locks and progress records are never written. Parents
above the private fixture root retain the trusted cooperating-writer bound;
this is not hostile same-user descriptor confinement.

0. **Trigger.** Reuse `notice.measurement`, which validates the gauge/1
   snapshot against the unique registry binding and calls the shared
   closeout pressure rule. Require a live-body, last-observed snapshot at
   the existing closeout.DUE line, using unrounded counters, not rounded
   display percent. The named writer must be a different registered key;
   the recipient's registry room must match. A declared, invented
   `--destination` must differ from every registered container. Its digest
   is reported, but no body is opened and native/spare admission remains
   unimplemented. Tier B is the only admitted tier in this slice.
   Claude and Codex metadata
   preflight are supported, not native rotation parity. Require the exact
   session's existing closeout state entry: matching key, integer band no
   greater than the snapshot band, and integer unknown=0. Preserve the
   snapshot reading/measuring times, age and window provenance. A pending
   `.state.*` sibling refuses without removal. This is
   recorded closeout-state evidence, not independent native-delivery proof.
1. **Donor closing checks.** Read the explicit `rotate-closing/1` record.
   It binds `key`, `writer`, tier `B`, the same hashed `binding` returned
   by notice, `destination_sha256`, and `gauge_sha256` / `closeout_sha256`
   to phase 0's exact bytes. `closed_at` is zoned and no earlier than the usage reading.
   `handoff` is a nonempty retained `{path, sha256}` reference. `mind`
   declares integer `proposed` from 0 to 3, `leaf_sha256`, and either
   `decision: none-proposed` with no approval (zero proposals), or
   `decision: approved-and-written` with a nonempty retained
   `approval: {path, sha256}` reference. Pending, missing and other
   dispositions refuse; neither a proposal nor this runner writes a mind.
   These are hash-bound declarations, not authenticated operator authorship.
2. **Mind readiness.** Invoke the existing `mind.py show KEY --ref`
   command path with the explicit synthetic room and registry; its existing
   verifier must pass. Read its exact leaf reference and verify its bytes
   against both the returned digest and the closing record. A newly proposed
   entry additionally needs a checked leaf written between the usage
   reading and `closed_at`; an older leaf cannot prove a new write. Reuse
   the mind tool's actual predecessor difference to check that the added
   and amended entry count equals the declared proposal count.
   Preflight pointer and archive leaf privacy before invoking show. No mind
   content, approval words, handoff text or native identifier is printed.

Exit 0 means only that the requested dry-run gate stopped successfully;
output lists `completed`, `next_phase` and `needs`, never whole-rotation
acceptance. A refusal or unsupported phase exits 2. Every output states
dry-run, zero writes, no native-load proof and no operator acceptance.
An interruption leaves no runner state to adopt: repeat the same phase
with unchanged evidence, or supply corrected evidence and recheck from 0.
There is no inferred persisted completion, automatic resume or journal.

Tests: `tools/test/test_rotate.py`; test contract:
`docs/ops/specs/tools/test/rotate.md`. The existing template generator
supplied the initial script/test skeleton while preserving this spec.

### Complete target workflow (phases 3 to 9 remain unimplemented)

**Roles.**
- **The operator:** chooses the tier, creates the destination container, gives the go, accepts or does not.
- **Writer:** exactly one, named before work starts, never the resident being moved. Builds, gates, takes custody, installs, writes the receipt.
- **Donor:** closes well; never builds its own successor.
- **Claudio:** the audit afterwards, read-only.

**Tiers, declared in writing before work starts.**
- **B, transplant:** the default. The capsule plus the donor's compaction summary and a measured slice of its own window, word for word.
- **Capsule-only:** only when a window build fails to load, on the operator's go.
- **A, reseed:** a fresh session reads the handoff. Only on the operator's explicit choice, recorded as Tier A and never called a rotation.

**The capsule.** It is appended as the orientation row, as text, never as a path, in four parts:
1. **Header,** from the registry: person, role, room, destination container.
2. **The mind:** the leaf named on this resident's line in the room's `MIND.md`, verbatim, its hash verified, its SHA-256 recorded in the receipt.
3. **Transition note,** written by the writer:
   - the window range not carried, and the handoff sections that cover it;
   - work in flight, the hold, the owners;
   - anything after the donor's last row.
4. **First turn:** "the room's status in a few lines, then speak as yourself."

The mind supplies part 2 only. Identifiers and live state belong in parts 1 and 3. The window always travels too; the mind is added to it and never replaces it. (C11: the capsule is assembled by `rotate` from these four parts. No mind command produces it.)

**Phases.** Each ends at a stop point; the writer reports and does not run ahead.

0. **Trigger.** The gauge reading crosses the resident's line, and the closeout card has run (`closeout.md`). The writer records the tier, donor, writer, destination and the gauge reading in the handoff.
1. **The donor closes well,** by the card:
   - a closing handoff;
   - up to three mind entries proposed in chat;
   - The operator's yes, after which `mind` writes the new leaf and moves the pointer.
2. **The mind is ready.** `mind check` passes, and the leaf hash matches the pointer.
3. **The destination.** the operator opens a fresh chat in the resident's room. The writer labels it `<Role (Person)> - spare body, do not open` at once. The writer then verifies:
   - the room and working directory are right;
   - the container is not registered to anyone else and carries no "old", "spare of another" or "do not resume" label;
   - no process holds it.
4. **The window.** Measure the donor from its own usage figures, by the gauge method. Choose the cut at a genuine operator prompt, so the measured wake estimate leaves the resident well inside its runway: a target of about 20 percent. Shannon's rebuild of 2026-10-29 woke at 32.8 percent, which spent a third of the window before the first word and brought his next closeout line within one heavy day. Carry at least one exchange with the operator beyond procedure. Record the reason for the cut.
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

6 to 7. **The operator's go,** for this replacement. The writer names the container, room, size and custody hash about to be replaced, and the rollback, then waits. A go given at phase 0 does not count.

7. **Install.**
   - **Default, the writer's verified swap:**
     - check that the destination still equals its custody copy and that no process or session record holds it;
     - write the successor beside it, hash it, rename it over atomically at mode 0600, and verify it;
     - switch the registry key and the launcher binding;
     - check that six things agree: registry id, binding id, body `sessionId`, binding root against body working directory, registry room, body label.
   - **Fallback, the operator's `.NEW` swap:** when a process still holds the file, or when the operator prefers it. The writer leaves `<id>.jsonl.NEW` beside the original; the operator closes the app and swaps it.
   - **Rollback (C12).** It runs on the operator's refusal, and also on any failed install step or failed load:
     - restore the pristine destination;
     - restore the registry and binding;
     - put the donor's store file back from custody;
     - keep the hold.

**Canonical identity-registry privacy.** Registry-value updates, creation,
replacement and restoration of `ops/etc/resident-identities.json` require
mode 0600, preserving its accepted uid and gid, regular single-link type
and no symbolic link in its path. This is distinct from the launcher roster
and binding pair. An in-place content update preserves the existing private
mode; a newly staged file must explicitly have 0600 before publication.
Verify both the staged object and the canonical postimage; do not rely on
umask or copy defaults. A preimage/postimage mismatch or unexpected
ownership, type, link count or path change stops the affected operation
instead of overwriting newer state. A separate metadata-only correction
names its own go, preimage and bounded inverse; it changes no registry values
and grants no enrollment, body-replacement or activation authority.

8. **Acceptance, in two parts.**
   - **Mechanical.** `launcher serve <key>`, which also releases the hold and is the load test. The first reply gives the room's status and then speaks as itself. Its first gauge reading is recorded beside the wake estimate. (C13) A clean native append: after that turn the body still parses, Claude Code's own new rows carry the new session id, and tool pairs match.
   - **The operator's.** the operator states that he recognizes her, or him, as the resident. A correct status alone is not acceptance.
9. **Close.**
   - Write the receipt `archives/receipts/<resident>-rotation-<n>-<date>.md`: tier, cut and reason, gates, custody, mind leaf hash, estimate against the measured wake, deviations counted, acceptance and its time.
   - Handle the donor's store entry. After its custody is verified by hash in both tiers, the entry is either relabeled "<Role (Person)> - donor, rotated <date>, do not resume" or removed from the list, as the operator prefers. His standing preference since 2026-10-29: removed. The custody copy is the donor of record.
   - The new resident confirms its mind entries.

**Codex residents** (Joe Codex, 2026-10-30): `ops/lib/scripts/rotation.py` carries messages after the last native compaction but not the compaction summary. A Codex rotation under this spec waits for a Codex-specific design and a loader test.

## Anecdotal Anchor

2026-10-29:
- the 19:12 rotation was Tier A run as a rotation, and woke as a resident the operator did not recognize as his doctor (his words, paraphrased);
- the 23:34 rebuild passed its gates but carried a briefing for a self, and the operator found that something was missing from it;
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
