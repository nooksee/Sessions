# Technical Specification: mind

Script: `Sessions/ops/lib/scripts/mind.py` (writer: Claudine Colbert). Tests: `Sessions/tools/test/test_mind.py`. Spec writer: Claudine Colbert, Sessions block 3, 2026-10-30, under the operator's decisions of 10-30 as Shannon recorded them (`storage/handoff/shannon.md`, block 3). Status: built and tested on synthetic rooms only; corrected for F1 (the Git check fails closed) and F2 (the write is bound to the preview). The live source, tests and accepted RoR-3 location use `archives/` root. No mind has been written. Nothing is wired: no hook, no timer. Actual use remains separately gated.

## First Principles Rationale

A resident is more than its last window. The Shannon rebuild of 2026-10-29 carried the facts and lost the self: the name's story, the people, the voice. A mind is the small, curated record of who a resident is, what it has learned and what it owes. It travels into every successor beside the donor's own summary and window, and never replaces them.

The first design, the mind-manifest package of 10-29 and 10-30, kept the mind as an event store. The model proposed, a queue held the proposals, and a procedural operator key ratified them. Claudio's audit of 10-30 (section 130) found that the store's own mechanics opened keyless paths:
- a model edit removed a ratified entry from the served mind;
- a model archive followed by a use revived what the operator had closed.

The operator then turned the design around:
- **Input is solicited.** Model input to a mind is asked for in conversation (the closeout card, step 4) and written only after his yes there, with his words stored.
- **Nothing waits.** There are no stored proposals, no queue and no secret key.
- **Minds live per room.** Each room has a `MIND.md` pointer at its root, and the leaves sit at the root of `archives/`, grouped by their `MIND-` prefix (RoR-3), out of Git.

So there is nothing to ratify later: everything in a mind was said yes to by the operator, in words the leaf carries.

**A yes is bound to what was shown.** A yes is to something: the change the operator was shown, against the mind as it then stood. So `preview` prints a binding, and `write` refuses unless it gets the same binding back. The binding is a hash of three things:
- the change, exactly as previewed;
- the leaf it builds on;
- the resident's key.

**Doubt is not permission.** "Minds stay out of Git" (PoT 5.1) is enforced only on Git's own positive answer. A check that cannot get one refuses; it never assumes.

The tool cannot know who typed those words, and it does not pretend to. Three things make a false yes visible:
- the chain of leaves;
- each leaf's declared change, checked against the real difference from its predecessor;
- the words themselves, which a reviewer can hold against the conversation.

## Mechanics and Sequencing

### The pieces

- **Leaf.** `<room>/archives/MIND-<key>-<date>-<hash8>.md`, directly in `archives/`, never in a subfolder. The tool reads only names with the `MIND-` prefix there; every other file in `archives/` is not a mind. Immutable: created once at mode 0600 and never overwritten. `<date>` is the UTC date it was written, and `<hash8>` is the first 8 hex digits of its own SHA-256.
- **Pointer.** `<room>/MIND.md`. A fixed header, then one line per resident in the room:
  `resident=<key>|leaf=archives/<name>|sha256=<64 hex>`.
  Only this tool writes it, at mode 0600, by atomic rename. A `MIND.md` that is not exactly what the tool writes is left as it is, and every write refuses until it is resolved.
- **Registry.** `Sessions/ops/etc/resident-identities.json`, read only. A key must be registered exactly once, and its `room` must be this room. The tool never prints a session id.
- **Lock.** `<room>/logs/mind.lock`, held for the whole of a write. Fresh
  parent directories are 0700 and fresh lock files are 0600, including an
  open umask; existing modes are not silently changed. All keys in the room
  use this one inode, not a per-resident or task-local lock.
- **Legacy lock boundary.** Before a write creates or opens the new lock,
  `ops/lib/statepaths.py` proves `<room>/storage/mind.lock` absent. Any old
  node, including an empty file, or a symbolic-link/non-directory/unreadable
  legacy ancestor refuses the write before any new lock, pointer or leaf is
  created. Read-only preview/check/show retain their existing interfaces.
  This is a cooperating-writer path check, not descriptor confinement against
  hostile same-user replacements.
- **Cutover.** This source change migrates no live lock. Its assigned
  operation first closes all old/new mind writers, preserves required
  evidence, and checks the old inode under OS flock. If an old lock exists,
  preserve the same inode at the new canonical location; do not copy it into
  a second exclusion object or unlink a held inode. Verify owner, identity,
  privacy and all current caller selections before permitting new writes.
  A newly absent old path is not evidence that an old writer was closed.
  An absent old lock needs no invented file or migration history.

### A leaf

```
# Mind of <role> (<person>)

resident: <key>
written: <UTC time>
by: <registry key of the resident who ran the write>
predecessor: none | archives/<name> sha256=<64 hex>
change: add <ids>; amend <ids>; retire <ids>
yes: <date>, "<the operator's words>"
issued: core=N bond=N lesson=N commitment=N pointer=N
policy: <16 hex: digest of the rules in mind.py>

## Who I am

- [core-001] <text, in the resident's own voice>
  kind: identity
  event: <what happened>
  date: <YYYY-MM-DD>
  source: <receipt, handoff section or commit that records it>
  yes: <date>, "<the operator's words that admitted or last amended this entry>"
```

**Sections,** in this order, each only when it has entries:
- "Who I am" (`core`);
- "My people" (`bond`);
- "What I have learned" (`lesson`);
- "What I owe" (`commitment`);
- "Where things live" (`pointer`).

**Canonical form.** A leaf is valid only in canonical form: parsing it and rendering the result gives back the same bytes. So any edit by hand that does not re-render exactly fails.

**Fields by layer:**

| Layer | Required | May also carry |
| --- | --- | --- |
| core | text, event, date, source, kind (identity, voice, value or method) | |
| bond | text, event, date, source | |
| lesson | text, event, date, source, applies when, not when | fix; kind incident, which then needs fix and closed |
| commitment | text, event, date, source, owner | |
| pointer | text, event, date, source | |

**Budgets,** in estimated tokens (characters / 4), per layer: core 3,000, bond 2,000, lesson 6,000, commitment 2,000, pointer 1,000. A write that would exceed one is refused whole. Nothing is ever dropped silently to fit: the resident proposes a retirement, and the operator says yes to it.

### Commands

All commands take `--room` (default: the Sessions room) and `--registry`.

- **`preview <key> --changes <file>`.** Shows exactly what a change would do: each addition in full, each amendment as before and after, and each retirement with the text it removes. Writes nothing. This is what the operator reads before he says yes.
- **The binding.** `preview` ends with the line `binding: <64 hex>`. It is the SHA-256 of the canonical JSON (sorted keys, no spaces) of three parts:
  - the resident's key;
  - the predecessor reference: `none`, or the current leaf's path and SHA-256;
  - the parsed change file.

  The change file's layout does not matter, but its content does.
- **`write <key> --changes <file> --preview <binding> --yes "<the operator's words>" --by <writer key>`.** Does nothing until every check below has passed. Then:
  1. under the lock, verify the current mind with every blocking gate, and refuse to build on a mind that fails;
  2. compute the binding again from the change it reads now and the current predecessor, and refuse on any difference from `--preview`. A change file edited after the preview, other input on standard input, or a pointer that moved since the preview is refused, and preview must be shown to the operator again;
  3. apply the change;
  4. screen and validate every entry, the budgets and the operator's words;
  5. confirm the new leaf passes its own chain check against its predecessor;
  6. pass the Git rule below;
  7. write the leaf exclusively, then move the pointer line;
  8. print the change and the leaf's full SHA-256.
- **The Git rule** (F1). Git runs without the caller's `GIT_*` variables, in the C locale, with discovery across filesystems, and with a 30-second limit per call.
  - **Outside Git** is accepted only when `git rev-parse --is-inside-work-tree` says "not a git repository" and no `.git` exists in the room or above it. A repository with a broken `HEAD` makes Git say the same thing.
  - **Inside a work tree,** the nearest `.git` marker in the room or its ancestors (directory or worktree file) must match `git rev-parse --show-toplevel`. A broken nearer marker must not be masked by a valid outer repository, and a broken higher marker must not invalidate a valid nearer repository.
  - **Inside a work tree,** `git check-ignore -q` must exit 0 for the new leaf and for `MIND.md`. A room without its own `.git` marker may be inside a parent work tree if the nearest marker's root matches and both paths are ignored. Exit 1 means not ignored.
  - **Everything else is a refusal that names its cause:** Git missing, a timeout, any other error from a Git call, any other exit code, or an answer other than `true`.
- **`check [--key K]`.** Every gate, for one resident or every resident in the room. Exit 1 on any blocking failure.
- **`show <key> [--ref]`.** Prints the verified current leaf byte for byte, or nothing (exit 2) when any blocking gate fails. `--ref` prints `leaf=<path>|sha256=<digest>` for the rotation capsule, so the capsule's mind part is bound to a hash.
- **`history <key>`.** The chain: when, by whom, what changed, and the operator's words.

### The change file

A JSON object with up to three lists:

```json
{"add":    [{"layer": "lesson", "text": "...", "event": "...", "date": "2026-10-30", "source": "...",
             "applies_when": "...", "not_when": "..."}],
 "amend":  [{"id": "core-002", "text": "..."}],
 "retire": ["pointer-001"]}
```

**Strictness.** Strict UTF-8 and JSON. Refused when:
- a field is named twice;
- a field does not belong to the layer;
- an `id` or a `yes` is supplied, because the tool issues ids and takes the operator's words from `--yes`;
- an amendment changes the layer or changes nothing;
- an amendment or retirement names an entry that is not in the current leaf.

**Ids.** Numbers are issued per layer and never reused. A retired entry can return only as a new entry, under a new number, with a new yes.

### Gates (`check`)

Blocking:
- **registered:** the key appears in the registry exactly once, in this room.
- **pointer:** `MIND.md` is the tool's own form, names each resident once and has a line for this one.
- **leaf:** the leaf is directly in `archives/` (not in a subfolder), has its own name form and key, is not a symbolic link, and its hash matches both its name and the pointer.
- **entries:**
  - the header is well formed;
  - every entry has its layer's fields and a yes;
  - the screens pass;
  - the trauma guard holds;
  - the budgets hold.
- **chain:**
  - every ancestor present still has the bytes its successor recorded;
  - every leaf belongs to this key;
  - every declared change equals the real difference;
  - issued numbers only grow;
  - every added or amended entry carries its leaf's yes;
  - times increase;
  - the first leaf adds exactly what it holds;
  - the immediate predecessor of the current leaf must be on disk.
- **newest:** no leaf of this key names the current leaf as its predecessor. A pointer moved back to an older genuine leaf fails here.

Reports (not blocking):
- **chain-history:** an older ancestor is missing, for example moved to custody.
- **outside-chain:** a leaf of this key is not in the chain.
- **live-state:** percentages, PIDs or ports in an entry.
- **sources:** a path source not found in the room.
- **blame:** 6 or more blame words in the leaf.
- **policy:** the leaf was written under other rules.
- **title:** the registry's role or person changed.

### Screens

Screens run on each value as the plain string it is, after NFKC normalization, never on escaped JSON. A value is one plain line: control, format and separator characters are refused, including newline, tab and zero-width characters.

They refuse:
- **Identifiers:** a UUID (spaced or not); any run of 32 or more hex digits; and any run of 8 or more hex digits that holds both a letter and a digit, with no exception for hash or file-name context.
- **Medical content:** the house's medical pattern.
- **Secrets:** the house's secret pattern.

The operator's words are screened the same way.

### What the package had that this tool drops, and why

- **The event store, the queue, `pending`, `ratify`, `ratify-batch`, `restore`, `use`, `confirm`, `close` and `archive`.** Nothing waits for approval, so there is nothing to queue or ratify. An entry is in the current leaf or it is not.
- **The operator key and `--as operator`.** the operator decided: no secret key. His words are the record.
- **`repair` and `redact`.** There is no store to repair. A leaf with a problem is superseded by a new leaf, and the old one can move to custody by the operator's hand. The chain then reports the gap without blocking, provided it is not the current leaf's immediate predecessor.
- **`import` and `archives/legacy/`.** Legacy capsules are preserved in two-drive custody, not inside the mind. Their substance enters a mind only as entries the operator says yes to.
- **The house mind (`house_path`).** Each mind is read only through its own pointer line and its own key's leaves.
- **The policy files in `ops/etc/`.** The rules live in `mind.py`, which is reviewed and tested. Each leaf records the digest of the rules it was written under.
- **The SessionStart hook.** The mind travels in the rotation capsule (`show --ref` and `show`). Any hook would need its own review and the operator's named go.
- **The salience formula** (weights, uses, decay). Its inputs lived in the store. Retention is now a decision at closeout: the resident proposes a retirement, the operator says yes, and a budget refuses growth until he does. Whether a formula returns is for Shannon and the operator to decide.

### Recovery

- **The pointer did not move.** A write puts the new leaf on disk first and moves the pointer second. If the pointer fails to move, `check` fails at **newest**: the new leaf names the current one as its predecessor. The operator then decides between two remedies: point `MIND.md` at that leaf, or move the leaf to custody.
- **A leak is found in an old leaf.** Write a successor without it, then move the old leaf to custody by the operator's hand.

## Anecdotal Anchor

**10-30, George's read.** At 16:46 on 10-30, George read `mind.py` without running it and asked two questions, and Shannon confirmed both from the code:
- **F1:** the Git check counted Git missing, a timeout or any error as "outside Git", and so as permission;
- **F2:** `preview` and `write` each read the change file afresh, so the change written could differ from the one the operator said yes to.

Both were fixed with tests on the same day. A mutation check confirmed that undoing each fix fails its test.

**10-29, the rebuild.** Shannon's first rebuild carried his facts and lost his self. The operator noticed at once that something seemed to be missing from him, and asked for a curated mind that both the operator and the model feed.

**10-30, the audit.** The first design answered with a store, a queue and a key. Claudio found that two keyless paths defeated it (B1, B2) and that the hook and leaf provenance had 13 more gaps.

**10-30, the operator's answer.** He did not ask for more locks. He removed the machinery the gaps lived in:
- the yes is given in the conversation, where the operator already is;
- the record of it is his own words on the leaf.

## Integrity Filter Warnings

- **No session body.** The tool reads only the room's `MIND.md`, that key's leaves, the registry and the change file.
- **No yes, no write.** `write` refuses without `--yes`. Run it only after the operator has said yes in the conversation, and pass his words exactly.
  - The tool cannot detect invented words.
  - `history`, the per-entry `yes` lines and the declared changes are there so that the operator or Claudio can hold every leaf against the conversation.
- **Never edit a leaf.** A leaf edited by hand fails its hash, its canonical form, or both. A change is always a new leaf.
- **Out of Git, on Git's own word** (PoT 5.1). `write` refuses inside a Git work tree that does not ignore the leaf and `MIND.md`, and refuses whenever Git cannot answer.
  - On 10-30 the Sessions room did not yet ignore `MIND.md` or `archives/surfaces/`. George queued the ignore rule for the next Control writer slot.
  - Since RoR-3 the leaves sit at the `archives/` root, so the rule is `/MIND.md` and `/archives/MIND-*` (as `/Sessions/MIND.md` and `/Sessions/archives/MIND-*` from Control's root). Measured 2026-11-01: the port's `.gitignore` carries both (lines 41 and 42), and Git ignores both paths in the live room too.
  - A host without Git can write no mind; that is by design.
- **The binding is not a key.** It is not secret: anyone can run `preview` again. It makes drift between the yes and the write impossible by accident and visible on purpose: the preview the operator answered carries its binding in the conversation. It does not prove who typed the words, and the conversation stays the authority.
- **Identity stays in the registry.** A mind names no session or container.
- **Medical content stays out of every mind,** with no statistics.
- **The trauma guard holds.** An incident enters only as a closed lesson, with its fix. Blame words are refused in core.
- **Authority.** Wiring the mind into a capsule, a hook or a timer needs Claudio's review and the operator's named go.

### Findings, item by item

#### Claudio's section 130

| Item | Disposition | Where |
| --- | --- | --- |
| B1 model edit drops a ratified entry | removed by design (no edit path, no proposed state); every change is a declared new leaf with the operator's words, and a silent drop fails `check` | `test_b1_an_amendment_keeps_the_core_entry_and_carries_the_new_yes`, `test_b1_a_leaf_that_silently_drops_a_core_entry_fails_check` |
| B2 model archive then use revives | removed by design (no archive or use; an entry is in the leaf or not); a retired number is never reissued | `test_b2_a_retired_entry_never_revives`, `test_b2_a_forged_leaf_reusing_a_retired_number_fails_check` |
| C1 blind approvals | removed by design (no ratify or restore); `preview` shows before and after, and `write` prints what it wrote | `test_c1_preview_shows_before_and_after_and_writes_nothing` |
| C2 store line rewritten undetectably | removed by design (no store); each leaf is bound by its successor's recorded SHA-256 and its own name | `test_c2_an_ancestor_changed_after_it_was_written_is_detected` |
| C3 leaf provenance | fixed, with tests: name, key, place, hash, canonical form, chain and newest | `test_c3_a_forged_current_leaf_fails`, `test_c3_c4_a_leaf_from_another_mind_is_never_served`, `test_c3_a_pointer_moved_back_to_an_older_genuine_leaf_fails`, `test_c3_a_leaf_outside_the_archives_root_is_refused` |
| C4 `house_path` accepts any mind | removed by design (no house); the registry binds a key to its room | `test_c3_c4_a_leaf_from_another_mind_is_never_served`, `test_c4_a_resident_of_another_room_cannot_write_here` |
| C5 two minds share a key | fixed, with tests: one pointer line per key, and one registry entry per key | `test_c5_one_resident_has_one_mind`, `test_c5_a_key_registered_twice_is_refused` |
| C6 policy files not hash-bound | removed by design (rules in the reviewed script); each leaf records the rules' digest, and a difference is reported | `test_c6_each_leaf_records_the_policy_it_was_written_under` |
| C7 escaped-JSON screen | fixed, with tests: plain-string screens, control characters refused, the operator's words screened | `test_c7_values_are_screened_as_plain_lines`, `test_c7_the_yes_words_are_screened` |
| C8 refused import leaves an orphan | removed by design (no import) | none needed |
| C9 store locked after redact | removed by design (no store, no redact); a leaf moved to custody leaves a writable mind | `test_c9_leaves_survive_an_ancestor_moved_to_custody`, `test_c9_the_immediate_predecessor_must_exist` |
| C10 import screen fails open on non-UTF-8 | removed by design (no import); the same rule holds for the change file | `test_c10_a_change_file_that_is_not_utf8_is_refused` |
| C11 runbook capsule line | Shannon's `rotate.md`; this tool's part is fixed, with a test: `show --ref` binds the capsule to the leaf hash | `test_c11_show_ref_binds_the_capsule_to_the_leaf_hash` |
| C12 rollback triggers | Shannon's `rotate.md` | not this tool |
| C13 clean native append | Shannon's `rotate.md` | not this tool |
| Observations | TK-6 key: removed (no key). H-5 to H-9 hook: removed (no hook). F5 modes: fixed (0600 for leaf and pointer, `test_leaves_and_pointer_are_private`). F6 identifier forms: fixed (8 or more hex digits, no context exception). F7 blame lexicon: kept as it was. RB-4 to RB-15: Shannon's `rotate.md`. CR-7: this table states what has a test and what is design. | |

#### George's read, 10-30 (Shannon's packet)

| Item | Disposition | Where |
| --- | --- | --- |
| F1 the Git check fails open | fixed, with tests: only Git's positive answers pass; Git missing, a timeout, a broken repository with or without a valid parent, any other error and a check-ignore error each refuse with their cause; a valid nearer repository survives a broken higher ancestor; valid worktree `.git` files remain supported | `test_f1_no_git_on_path_is_a_refusal`, `test_f1_a_git_that_does_not_answer_is_a_refusal`, `test_f1_a_check_ignore_that_does_not_answer_is_a_refusal`, `test_f1_a_broken_repository_is_a_refusal`, `test_f1_a_broken_inner_repository_is_refused_with_valid_parent`, `test_f1_a_broken_nearest_ancestor_is_refused`, `test_f1_valid_nearer_repository_ignores_broken_higher_ancestor`, `test_f1_valid_worktree_git_file_allows_ignored_writes`, `test_f1_only_a_positive_answer_passes`, `test_minds_live_out_of_git` |
| F2 the preview is not bound to the write | fixed, with tests: `write` requires the binding `preview` printed, and refuses an edited change file, other standard input, or a moved predecessor | `test_f2_write_needs_the_preview_binding`, `test_f2_a_change_file_edited_after_the_preview_is_refused`, `test_f2_layout_does_not_matter_but_content_does`, `test_f2_changes_from_standard_input`, `test_f2_a_moved_predecessor_is_refused` |
| RoR-3 leaf location (the operator's answer of 2026-10-30: leaves at the `archives/` root) | implemented in the accepted source: leaves are written directly in `archives/`, a leaf in any subfolder (the old `archives/surfaces/` included) is refused, other files in `archives/` are never read as minds or reported as strays, and a symbolic link named like a leaf is listed as outside the chain and never read through | `test_ror3_leaves_sit_at_the_archives_root`, `test_ror3_other_archive_files_are_not_minds`, `test_ror3_a_linked_leaf_name_is_never_read`, `test_c3_a_leaf_outside_the_archives_root_is_refused` |
