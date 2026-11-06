# Technical Specification: help

Binary: `Sessions/ops/bin/help` (Bash, no library). Self-test: `ops/bin/help --test`. Spec writer: a Claude subagent working for Claude Shannon, 2026-10-30, adapted from STELA's `ops/bin/help` and its spec (`Projects/STELA`). Status: built 2026-10-30, self-test 14 of 14 passing; read-only, wired to no hook and no timer. The Auditor reviews it before it is relied on. Map: `docs/ops/README.md`.

## First Principles Rationale

A resident who wakes in this room has to find, in the right order, who it is, what the room forbids, what is true now, and which tools exist. That knowledge is spread over eight files and a folder of specs. Read in the wrong order, or skipped, the room's own history shows what follows: a waking resident opens the first file it finds and treats whatever that file says as fact.

`help` is the front door. It prints the read-in order, the loop, and every tool with the status its own spec declares. Normal modes read and print. The bounded self-test uses an explicit `TMPDIR` or the room's `var/tmp/` and removes only its own fixture.

STELA's help solved the same problem for STELA: deterministic wayfinding, specs before narrative. Sessions keeps that shape and fills it with this room's canon.

## Mechanics and Sequencing

1. **Root.** The room is the directory that contains this `ops/bin` folder. The binary refuses unless that directory holds `AGENTS.md`, `PoT.md` and `docs/`, then works from it. It runs from any working directory. STELA's demand for a Git top level is dropped: Sessions is a subfolder of the Control repository.
2. **Arguments.** Zero or one, except `term`, which takes exactly one more. Anything else is refused.
3. **No argument: the menu.**
   - The read-in order:
     1. `AGENTS.md`
     2. `PoT.md`
     3. `ops/lib/manifests/CONTEXT.md`
     4. `ops/lib/manifests/CONSTRAINTS.md`
     5. `CLAUDE.md`
     6. `RoR.md`
     7. `NOW.md`
     8. `INDEX.md`
     9. `docs/ops/README.md`
     10. `docs/MANUAL.md`
   - The loop: gauge, closeout, the operator says yes, mind, rotate, gauge.
   - One row per tool, from the union of `docs/ops/specs/scripts/*.md` and `ops/lib/scripts/*.py`, with the same columns as `specs` below.
   - the two binaries, the help modes, and where things live (`storage/` working payload with only its declared skeleton admitted; `var/tmp/` task scratch under PoT 1.1.13; archives and custody kept; identity in `ops/etc/resident-identities.json`).
4. **`read`.** Checks the ten read-in files in order. For each: present or `MISSING`, its line count, and how many lines carry `[PLACEHOLDER`. Any missing file fails the command after the full list is printed.
5. **`specs`.** First the tool rows. For each word: spec yes or no, script yes or no, tests yes or no, and the first sentence after `Status:` in the spec's header (the text before its first `## ` section). A spec with no such line prints `[no Status: line before the first section]`. A script with no spec prints `[no spec: convention break]`. Then every other spec under `docs/ops/specs/`, grouped by folder, with its own status the same way.
6. **`doctrine`.** Prints each level-two heading of `DOCTRINE.md` with its line number. It is an index, never a summary. It fails when the file is missing or has no such heading.
7. **`term <text>`, or `<text>` alone.** A fixed-string search, any case, in three tiers printed in order:
   - the specs under `docs/ops/specs/`;
   - `docs/MANUAL.md`;
   - the rest of `docs/`.
   Files are searched in sorted order. Zero matches prints an explicit no-reference line and exits 0. The bare form is kept from STELA; `term` exists so that a mode word such as `specs` can itself be searched for.
8. **`curriculum`.** Not built. It prints a placeholder for the wake/closeout commands and accepted provider routes; closeout source exists but is not installed, and `rotate.py` is not written. It then points to the hand procedures (`CLAUDE.md` "ON WAKE", `HANDOFF.md`, `closeout.md`, `rotate.md`).
9. **`--test`.** Fourteen cases.
   - Three read-only passes over the live room: ten read-in entries; one row each for gauge, closeout, mind and rotate; a non-empty historical doctrine index.
   - Nine on a fixture room built under explicit `TMPDIR` or project-local `var/tmp/`: a missing read-in file fails; the placeholder manual is flagged; `Status:` is taken from the header only; a spec without one and a script without a spec are each reported; search is case-insensitive and keeps tier order; zero matches is reported; an empty term fails; doctrine without sections fails.
   - One through the binary itself, on the argument contract.
   - The menu.
   The fixture is removed when the test exits. Output is `OK: help self-test passed (14/14).`
10. **Colour.** Used only when standard output is a terminal, so captured output is plain text.

Dropped from STELA, each because its subject does not exist here:
- the `doctrine` index of `DOCTRINE.md`, which is historical and not current law;
- the curriculum of STELA commands (`open`, `dump`, `certify`, `bundle`, `prune`);
- the STELA command index;
- the telemetry leaves STELA's `common.sh` writes to `logs/` at the Git top level, which here would land in the Control root.

[PLACEHOLDER: a menu row and a `curriculum` sequence for each tool as it is built (closeout, rotate), owner Claude Shannon.]

## Anecdotal Anchor

`Sessions/CLAUDE.md` once carried the resident's session identifier as a literal. Between 2026-07-16 and 2026-09-08 it went two rotations stale while still reading as fact. It was the first file a waking resident opened, and it handed that resident the wrong body. That failure class produced the reversed STELA and nukeCE pairs. The lesson, in `CLAUDE.md` itself: a value that changes must not be frozen in prose. Ask the registry and the checkers instead.

`help` applies the same rule to wayfinding. Its menu points at the registry for identity. Its tool rows come from the files present and from each spec's own `Status:` line, so a tool's state is read where its writer declares it.

On 2026-10-30, the day it was built, `help specs` already showed two such facts:
- `rotate.md` has no `Status:` line;
- the `binaries`, `runbook` and `tools/test` specs copied from STELA declare none.

STELA's own anchor carries over as a design rule. A bolded heading once broke STELA's doctrine parser, which then printed later sections as doctrine. So `help` fails closed on missing structure rather than printing a fallback.

## Integrity Filter Warnings

- `help` refuses when its room lacks `AGENTS.md`, `PoT.md` or `docs/`, when given too many arguments, when `term` has no text, or when the search text is empty.
- `read` fails when any read-in file is missing. It still prints the whole list first, so one run shows every gap.
- `doctrine` fails on a missing `DOCTRINE.md` or one with no level-two heading. It never substitutes prose for doctrine.
- Status text is the spec writer's own sentence, cut at the first ". " and at 100 characters. `help` reports it and does not judge it. A spec whose status sits after its first section is reported as having none.
- Search with zero matches is an explicit report, not an inferred answer. Search covers `docs/` only. The root canon files are reached through `read`, not `term`. [PLACEHOLDER: whether `term` should also search the five root canon files, owner Claude Shannon.]
- Normal `help` modes write nothing, read no session body or registry JSON, and run no tool. The storage menu distinguishes the versioned skeleton from ignored payload. `--test` writes only its own unique fixture under explicit `TMPDIR` or project-local `var/tmp/` and removes only that fixture.
