# Technical Specification: mind

Script: `Sessions/ops/lib/scripts/mind.py`. Tests: `Sessions/tools/test/test_mind.py` (`TEST-02`). Design: the operator's, given on 2026-11-09: a root `MIND.md` that is pointers only, leaves in `archives/mind/` that hold concepts and abstractions, telemetry with an id and an agent id for every leaf, generous character limits, and no approvals on the operator's desk. Status: built and tested on synthetic rooms; the room's first leaf is written by a resident when it has one.

## First Principles Rationale

A mind that records the present goes stale within the hour, and a stale fact read as memory misleads the next reader with the authority of something remembered. So a leaf holds one idea that stays true: a concept, an abstraction, a method, a bond. The present belongs where it is dated and replaced: the board, the ledger and the handoffs.

**Pointers first.** A reader at wake loads only the index: one short line per leaf. It opens a leaf when the leaf bears on the work. The index stays small however many leaves are written, because superseded and retired leaves leave it.

**Refused at the door, not cleaned up later.** Drift is stopped by a screen at write time, not by review. A date, a time, a word that dates the text, a count or size, a path or file name, an address, a pull request or version number, code or a command line, an identifier, medical content and secrets are each refused, and the refusal names the kind, never the matched text.

**Bounded by construction.** A title is at most 100 characters and a body at most 2,000. The index holds at most 200 live leaves and is refused, never trimmed, when full; a superseding leaf still flows because it replaces a line. Nothing is ever dropped silently.

**Flow without approvals.** A registered resident writes, supersedes and retires its own leaves, and only as itself: `add` and `retire` bind `--agent` to the caller's own verified identity ("The caller", below). No preview or per-entry yes is asked. The ledger is the audit: every write is one line with the leaf's id, agent, time, SHA-256 and size.

**Immutable leaves.** A leaf is never edited. A change is a new leaf that supersedes the old one. A leaf whose bytes no longer match its ledger line is not served until its owner retires it.

**Out of Git.** The index, the leaves and the ledger never enter Git (PoT 5.1.3). A write proceeds only on Git's own positive answer that each path is ignored, or that the room is outside any repository.

## Mechanics and Sequencing

### The pieces

| Piece | Path | Written by | Mode |
| --- | --- | --- | --- |
| Index | `MIND.md` at the room root | the tool only, by atomic rename | 0600 |
| Leaves | `archives/mind/MIND-<date>-<NNN>.md` | the tool only, exclusive create | 0600 in a 0700 directory |
| Ledger | `logs/mind/ledger.jsonl` | the tool only, append | 0600 in a 0700 directory |
| Lock | `logs/mind.lock` | the tool only | 0600 |

Every directory the tool creates is created at mode 0700, one component at a time. The old lock path `storage/mind.lock` must be absent; its presence refuses every write and changes nothing (`ops/lib/statepaths.py`).

### The index

```
# Mind

Pointers only. Each line is one leaf: an idea a resident holds, never a fact about the present. Only the mind tool writes this file. Read a leaf with `mind.py read <id>`.

- [MIND-<date>-<NNN>](archives/mind/MIND-<date>-<NNN>.md) <agent> — <title>
```

The index is valid only in canonical form: the fixed head, then one pointer line per live leaf, each id once. A line added by hand fails the check.

### A leaf

```
---
id: MIND-<date>-<NNN>
agent: <registry key>
written: <UTC time>
title: <one line>
supersedes: none | MIND-<date>-<NNN>
---

<the idea, one or more paragraphs>
```

The id is the UTC date of the write and a three-digit number that counts up within that date across the whole room, never reused, including after a retirement. A leaf is valid only in canonical form.

### A ledger line

One JSON object per line, keys sorted: `action` (`add` or `retire`), `id`, `agent`, `time`, `sha256` and `bytes` of the leaf, and for `add`, `supersedes`.

### The caller

`add` and `retire` write only as the caller. Before anything else, before the screen, the lock or any read of the mind, each one:

1. resolves the caller with `myself.py`'s own `resolve_caller`, loaded by path from beside `mind.py`, on the same inputs `myself.py` uses: the process environment, `/proc`, the parent process, and the Codex writer-lock root. There is no second resolver;
2. refuses unless that resolution names exactly one native session with no signal problem;
3. refuses unless the room's canonical registry (`ops/etc/resident-identities.json` beside the tool) holds exactly one keyed row with that session and provider, as `myself.py`'s identity-registry leg matches it;
4. refuses unless that row's key is the `--agent` given.

It works alike for Claude and Codex residents, since `resolve_caller` reads both. Unverified, ambiguous or absent identity refuses, and the refusal never prints a session identifier. Outside the test seam, a `--registry` other than the canonical one refuses `add` and `retire`. `show`, `read` and `check` take no caller and stay open to any reader.

**A worker writes as its parent.** A subagent, workflow agent or background task runs inside its parent's session and carries its parent's signal, so the tool cannot tell it from its parent (PoT 3.5). A worker acts for its parent, and a leaf it writes is its parent's.

**The test seam.** `MIND_TEST_CALLER=<key>` in the environment declares the caller for a test, in place of steps 1 to 3. It is honoured only when all three conditions hold:

1. the registry is not the room's canonical one;
2. every registry session is a synthetic `0000` identifier, rotate's own convention;
3. the room is neither `mind.py`'s own room nor any room the canonical registry names.

A canonical registry that is absent names no room; one present but unreadable keeps the seam shut. Anywhere else, setting the variable refuses; it never falls back to the real route. No real room can meet those conditions, so the seam cannot be reached from the command line in a real room. `tools/test/test_mind.py` and `tools/test/test_rotate.py` use it.

### Commands

All take `--room` (default: this room), `--registry` (default: `ops/etc/resident-identities.json`) and `--now` (tests only).

- **`add --agent <key> --title <text> --body <file or -> [--supersedes <id>]`.** Binds the caller, screens the title and the body, takes the lock, checks the agent is registered exactly once to this room, refuses while a retired-format mind is present, checks Git, writes the leaf, appends the ledger line and rewrites the index. A superseding leaf takes the old line's place; only the agent's own live leaf can be superseded.
- **`retire --agent <key> <id>`.** Binds the caller, then takes the agent's own live leaf out of the index and appends the ledger line. The leaf stays on disk. Retire works on a leaf that fails its check, so an owner can always clear a blocked mind.
- **`show [--agent <key>]`.** Prints the verified index lines, all or one agent's. Refused while any blocking check fails.
- **`read <id>`.** Prints one live leaf byte for byte. Refused for a retired or superseded leaf, and while any blocking check fails.
- **`check`.** Prints every gate as `PASS`, `FAIL` or `REPORT`, then the count of blocking failures. Exit 0 with none, 1 with any.

Exit 2 is a refusal: the reason goes to standard error and nothing was written.

### Gates (`check`)

| Gate | Blocking | What it proves |
| --- | --- | --- |
| legacy | yes | no `archives/MIND-*.md` of the retired chain format sits at the archives root |
| index | yes | the index is canonical, holds at most 200 lines, and agrees with the ledger |
| out-of-git | yes | Git says the index, the leaves and the ledger are ignored, or the room is outside Git |
| ledger | yes | every ledger line is a mind record and no leaf is added twice |
| leaf | yes | each live leaf exists, is canonical, matches its index line, matches its ledger hash, is not retired, and its agent is registered once to this room |
| leaf | report | a leaf that no longer passes the current screen or limits; supersede or retire it |
| strays | report | files under `archives/mind/` that are neither live nor retired |

The verifier that `show`, `read` and `rotate.py` use reads files only and runs no program; only `check` and the writes ask Git.

### Screens

Applied to the title as one line and to the body as text, after Unicode NFKC normalization:

- control and invisible characters (a body may hold line breaks);
- identifiers: UUIDs and runs of hexadecimal digits;
- medical content and possible secrets;
- the concept screen: a date, a time, a word that dates the text, a count or size (any number of two or more digits standing alone, a percentage, a process number, a port), a path or file name, an address, a pull request, issue or version number, code or a command line.

A single digit and a dotted clause reference such as PoT 4.2.4 pass. The policy digest that `check` prints covers every limit and screen.

### Recovery

- A leaf that fails its hash, its format or its agent: its owner retires it, then writes the idea again as a new leaf.
- A retired-format mind (a `MIND.md` of `resident=` lines, or `archives/MIND-*.md` leaves at the archives root): the custody owner moves those files out of the room into custody. The tool never moves or deletes them.
- A full index: supersede or retire a leaf.

## Anecdotal Anchor

On 2026-11-09 the operator set aside the earlier designs, approved chains included, and gave this one in a single message: concepts and abstractions only, a pointer-first root `MIND.md`, leaves under `archives/`, telemetry with an id and an agent id for each leaf, character limits generous enough to hold an idea, and no approvals piled on his desk. He named the danger plainly: drift and sprawl, and continual reference to stale information. Every rule above answers one of those words.

## Integrity Filter Warnings

- **The binding is a cooperating-writer guard, not a file permission.** It stops the room's own tool from writing or retiring as another resident. A same-user process can still change the files directly; the ledger hashes and `check` are the audit that finds that. It cannot tell a worker from its parent (see "The caller"). Finding 1 of Claudio Freeman's read of PR #72 (his section 288) is what it answers: before it, the agent was only a key the caller named.
- The screen is a set of patterns. An idea phrased to slip past it is still a stale fact; readers treat a leaf as a lead, never as evidence.
- PoT 1.2.10, 4.1.7 and 4.2.4 were written for the approved chain and still say the operator decides mind entries and the resident proposes them for a recorded yes. The operator's design of 2026-11-09 decides them once, as a standing yes for every leaf written under this tool and its screen; the wording of those clauses is the operator's to amend under PoT 7.3. PoT 5.1.3, 5.1.4 and 5.1.5 are enforced as written.
