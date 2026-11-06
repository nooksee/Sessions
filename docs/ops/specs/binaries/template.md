# Technical Specification: template

Binary: `Sessions/ops/bin/template` (Bash, no library). Templates: `Sessions/ops/src/{scripts,docs,tests,reports}/*.tpl`, 11 files. Self-test: `ops/bin/template --test`. Spec writer: a Claude subagent working for Claude Shannon, 2026-10-30, adapted from STELA's `ops/bin/template`, its `factory` renderer and its `ops/src/**/*.tpl` form (`Projects/STELA`); rewritten the same day to render from template files instead of inline text. Status: built 2026-10-30; self-test covers all registered templates and the opt-in spec-preserving route. The Auditor reviews it before it is relied on. Map: `docs/ops/README.md`.

## First Principles Rationale

The operator, 2026-10-30, on why STELA keeps `.tpl` templates: the agent kept revising the form, and at times forgot it altogether, and the templates were his effort to make the form uniform and consistent and the reports better.

A form kept in an agent's memory drifts one use at a time: a receipt without its custody hashes, a packet without a stop condition, a closeout card reworded by whoever pasted it. A form kept in a file, with its required fields declared at the top, cannot be forgotten or quietly revised: the renderer refuses until every field is filled, and refuses anything it does not recognize.

The room has one convention for a tool (`docs/ops/README.md`, rules 1 and 2):
- one word;
- a script at `ops/lib/scripts/<word>.py`;
- a spec of the same name at `docs/ops/specs/scripts/<word>.md`, in STELA's five sections;
- tests beside it at `tools/test/test_<word>.py`;
- a row in `docs/ops/registry/scripts.md`.

`template` makes that convention the easiest path, and does the same for the three reports the continuity loop produces: the rotation receipt (`rotate.md`, phase 9), the packet for a resident (`agent-input.md`) and the closeout card (`closeout.md`).

STELA's `template` is a router to its `factory` and `manifest` backends. Sessions has no backends, so `template` renders itself, from STELA's template form: a front matter that declares the form, and a body with `{{SLOT}}` markers. It keeps STELA's discipline of a single entrypoint that fails explicitly and has no fallback path, and STELA's strict mode: no unresolved marker leaves the renderer.

## Mechanics and Sequencing

1. **Arguments.**
   - `template [--dry-run] [--root=DIR] [--preserve-spec] [SLOTS] <word>` writes a tool set.
   - `template receipt|packet|closeout|ror|custody|validation|source-change|readme [SLOTS] [--out PATH]` renders one report.
   - `template --test` runs the self-test; `template -h` prints usage.
   - `SLOTS` are `--slot KEY=VALUE` (also `--slot=KEY=VALUE`, repeatable) and at most one `--slots-file PATH`.
   An unknown option, a second name, a missing name, `--out` in tool-set mode, and `--dry-run`, `--root` or `--preserve-spec` in report mode are refused.
2. **The templates.** Each `.tpl` begins with a front matter between two `---` lines, then the body.
   - **`template_type`:** `tool` (the three tool-set files), `report` (receipt, packet, closeout, ror, custody, validation, source-change) or `docs` (readme).
   - **`template_id`:** the file's name in the form; `template` refuses a file whose type or id is not the one it expects.
   - **`template_version`:** a whole number.
   - **`requires_slots`:** the slots, one `  - SLOT` line each, in capitals, digits and `_`.
   - **`slot_notes`:** one `  SLOT: what it must hold` line for every required slot. A refusal prints these notes beside the missing slots, and tool-set mode turns them into placeholder text.
   - **`placeholder_owner`** (tool templates only): the owner named in each placeholder.
   - Other keys, such as `source`, are documentation.
   The grammar is a restricted YAML form, read line by line by `template`; all 11 files also parse as YAML. Every template must use each declared slot in its body and declare each slot its body uses; a template that does not is refused as a defect.

   | Type | File | Slots |
   | --- | --- | --- |
   | tool | `ops/src/scripts/script.py.tpl` | WORD, DATE, PURPOSE, READS_AND_WRITES |
   | tool | `ops/src/docs/spec.md.tpl` | WORD, DATE, SCRIPT_WRITER, SPEC_WRITER, FIRST_PRINCIPLES_RATIONALE, MECHANICS_AND_SEQUENCING, ANECDOTAL_ANCHOR, INTEGRITY_FILTER_WARNINGS |
   | tool | `ops/src/tests/test.py.tpl` | WORD, DATE, BEHAVIOR_TESTS |
   | report | `ops/src/reports/receipt.md.tpl` | RESIDENT, ROTATION, DATE, WRITER, AUTHORITY, TIER, DONOR, DESTINATION, CUT_AND_REASON, GATES, CUSTODY, MIND_LEAF, INSTALL, ESTIMATE_VS_MEASURED, DEVIATIONS, ACCEPTANCE, ROLLBACK (17, from `rotate.md` phase 9) |
   | report | `ops/src/reports/packet.md.tpl` | TO, FROM, RELAYED_BY, OWNER, SCOPE, AUTHORITY, SOURCES, RULES, STOP_CONDITION, POST_TO (10, from `agent-input.md`) |
   | report | `ops/src/reports/closeout.md.tpl` | PERCENT, WINDOW, READING_TIME, ROTATION_WRITER (4) |
   | report | `ops/src/reports/ror.md.tpl` | ENTRY, KIND, GIVEN, WORDS, ACT, RECORD, ENTERED_BY (7, one entry of the decision ledger `RoR.md`, PoT 1.2.10) |
   | report | `ops/src/reports/custody.md.tpl` | BATCH, DATE, WRITER, AUTHORITY, CONTENTS, TIER1, TIER2, VERIFICATION, EXCLUDED, COUNTS, DEVIATIONS (11, the receipt of a custody operation, PoT 5.3 and 6.4.5) |
   | report | `ops/src/reports/validation.md.tpl` | TEST, DATE, WRITER, AUTHORITY, SUBJECT, SETUP, STEPS, VERDICT, TEARDOWN, REVIEW, COUNTS, DEVIATIONS (12, the receipt of a live validation, PoT 6.1.5 and 6.4.5) |
   | report | `ops/src/reports/source-change.md.tpl` | CHANGE, DATE, WRITER, AUTHORITY, SCOPE, BASE, CANDIDATE, DIFF, VALIDATION, REVIEW, INTEGRATION, DEVIATIONS, ROLLBACK (13; bounded source/configuration change closeout) |
   | docs | `ops/src/docs/readme.md.tpl` | TITLE, OWNER, DATE, PURPOSE, STRUCTURE_POINTER, ENTRY_POINT, CONSTRAINTS, CANONICAL_POINTER (8, after STELA's `readme.md.tpl`) |

3. **Slots given.** `--slots-file` holds `KEY=VALUE` lines; blank lines and lines starting with `#` are skipped, and any other line that is not `KEY=VALUE` is refused with its line number. The value is everything after the first `=`, verbatim, on one line; a value with line breaks is given with `--slot`. Each of these is refused, and named:
   - a key that is not a slot name;
   - a slot given twice, in the file or on the command line;
   - an empty value ("none" is written out when a field is empty, as `agent-input.md` asks).
4. **Rendering.** One pass over the body: each `{{SLOT}}` is replaced by its value, and a value is never searched for markers itself, so one slot cannot fill another. Afterwards, any `{{...}}` left in the output, from a value that held one, is refused and named. Nothing is written until the render is clean.
5. **Report mode** (`receipt`, `packet`, `closeout`, `ror`, `custody`, `validation`, `source-change`, `readme`).
   - Every required slot must be given. Missing slots are listed, each with its note, with the count ("2 of 17 required slot(s) missing"); unknown slots are listed too; then it refuses, and renders nothing.
   - A value holding `[PLACEHOLDER` is refused: placeholders belong to tool skeletons only.
   - Output goes to standard output, or with `--out PATH` to that file. `--out` refuses an existing path, a link included, and a path whose folder does not exist (it creates no folder); it writes under `noclobber` and prints the path and byte count.
   - These four words are template types, so they are not available as tool names. `closeout` was already refused as a tool name, because its spec exists.
   - An output whose resolved parent is the room's storage root is refused
     before creation; use `storage/active/`, `storage/intake/` or an existing
     named case lane. Relative paths and symlink aliases are resolved with
     coreutils `realpath -m`. This is a trusted-writer path guard, not a
     hostile same-user filesystem sandbox.
   - The closeout card's single source is its template, `ops/src/reports/closeout.md.tpl` (PoT 1.2, SSOT); `closeout.md` points to it and carries no copy. Its slots are `PERCENT`, `WINDOW`, `READING_TIME` and `ROTATION_WRITER`, so each card names one writer: "5. Tell the operator you are ready for rotation. <ROTATION_WRITER> runs it." The self-test renders the card and refuses a second copy of it in the spec.
6. **Tool-set mode** (`<word>`).
   - **Name.** One lowercase word: letters `a` to `z` only, 2 to 32 of them.
   - **Root.** By default, the room that contains this `ops/bin` folder, which must hold `AGENTS.md` and `PoT.md`. With `--root=DIR`, an existing directory of any kind, for scratch trees and tests. Templates always come from this room's `ops/src`, whatever the root.
     A resolved root equal to or beneath this room's storage directory is
     refused, including aliases: operational code is not installed there.
     Each planned target is also resolved before any write, so a child
     source-directory alias cannot redirect generated code back into storage.
     Synthetic source trees in `var/tmp/` remain supported, as do unrelated
     directories whose names merely share the storage prefix.
   - **Refusals, all before any write.** Any target file existing, as a file or a link, unless the caller explicitly gives `--preserve-spec` and the existing spec is a regular non-link file. That route preserves the spec byte for byte and creates only the missing script and test; other existing targets still refuse. Without the option, any existing target refuses. A name `docs/ops/registry/scripts.md` already lists. A slot none of the three templates declares. `WORD` or `DATE` given: `template` sets those from the word and the clock.
   - **Placeholders.** Every slot not given is filled with `[PLACEHOLDER: <its note>, owner: <placeholder_owner>]`. This is the only mode that allows placeholders. A given slot replaces its placeholder in every file that uses it; a given `PURPOSE` also fills the registry row's purpose.
   - **Write.** All three are rendered first. It creates the three folders if they are absent, then writes each required file under `noclobber`. In preserve mode it leaves the existing spec untouched. A file that appears between the check and the write is not overwritten; the error says which earlier files were written.
   - **Dry run.** `--dry-run` runs every check and render, then prints each planned path with its byte count and template. In preserve mode it identifies the existing spec without printing a regenerated replacement. It writes nothing.
   - **The skeletons.** The script has the house shape of `gauge.py` and `mind.py` (docstring, `SESSIONS`, `build_parser`, `main`, `raise SystemExit(main())`) and the house rules as fixed text; until built it prints `refused: <word> is a skeleton; nothing is built` and exits 2. The spec has the title, a header line ending in `Status: skeleton generated by ops/bin/template on <date>; nothing built, nothing wired` (`help specs` reads it), and STELA's four sections. The test is standard library `unittest`, run as `python3 -I -B tools/test/test_<word>.py`, with three cases: the tool exists; the skeleton refuses with exit 2 (meant to fail once the tool is built); a skipped behaviour case.
7. **Registry row.** Printed after a tool set, never written, for the registry's writer.
   - **Columns.** It follows the registry's own `| ID |` header. Known columns are ID, Name, File Path, Status and Notes; any other column becomes `[PLACEHOLDER: <column>]`.
   - **ID.** One more than the highest `SCRIPT-NN` in the file.
   - **Status.** `skeleton`.
   - **Notes.** The spec and test paths, the date, and the purpose or a placeholder for it.
   - **No registry.** The row uses the Sessions form of 2026-10-30 (ID, Name, File Path, Status, Notes), with a placeholder ID.
8. **`--test`.** Eighteen cases in a unique temporary directory under an explicit `TMPDIR`, or the room's `var/tmp/` by default (PoT 1.1.13); only that fixture is removed:
   1. nine bad names refused, nothing written;
   2. a dry run writes nothing and shows three files;
   3. a real run writes exactly three files and prints a row;
   4. the spec has the five headings in order, and a `Status:` header;
   5. a second run refuses, names 3 of 3 files, and leaves them byte for byte;
   6. a spec written first refuses by default; `--preserve-spec` writes only script and test and proves the spec unchanged; missing spec refuses;
   7. registry numbering, a registered name refused, and a five-column header followed;
   8. the generated Python parses, and the generated test passes with one skip;
   9. everything generated, and every template, is plain ASCII;
   10. all 11 templates load: type, id, version, a note per slot, and body markers equal to `requires_slots`;
   11. every report type renders with all its slots: no marker, no placeholder, every value present; `--slot` and `--slots-file` give the same text, and `--out` writes exactly what standard output shows;
   12. a missing slot: a receipt without 2 slots is refused with both named and the count, and writes nothing; a closeout with none names all 4; an empty slot is refused;
   13. an unknown slot is refused and named in both modes; `WORD` given, a slot given twice, and a slots-file line without `=` are refused;
   14. an overwrite: `--out` refuses an existing file (left byte for byte), a dangling link (nothing created behind it) and a missing folder (none created);
   15. a leftover marker: a value holding another slot's marker, or `{{TODO}}`, is refused and named, in report and tool-set mode, and nothing is written;
   16. a report value holding `[PLACEHOLDER` is refused; in tool-set mode, given slots replace their placeholders (3 of 9 given), the rest stay placeholders, and `PURPOSE` reaches the registry row;
   17. the closeout card matches `closeout.md` lines 1 to 5, and step 5 renders the writer;
   18. option misuse is refused: `--out` in tool-set mode, `--dry-run` or `--root` in report mode.

   The directory is removed when the test exits. Output is `OK: template self-test passed (18/18).`
   Generated scripts expose `SCRATCH = SESSIONS / "var" / "tmp"`; script,
   specification and packet templates cite PoT 1.1.4 and 1.1.13 instead of
   sending arbitrary rebuildable intermediates into `storage/`. These forms
   affect newly generated artifacts; existing records are not regenerated.

Dropped from STELA:
- the `render` call form and STELA's template types (`agent`, `task`, `skill`, `dp`, `results`, `spec` and the stance types);
- the `factory` and `manifest` backends, `--non-strict`, and the `{{@include:...}}` directive;
- the `[TOKEN]` block form of a slots file (Sessions uses `KEY=VALUE` lines);
- the CCD front-matter keys `ff_target` and `ff_band`;
- the telemetry leaves STELA's `common.sh` writes to `logs/` at the Git top level, which here would land in the Control root.

[PLACEHOLDER: further template types (for example a binary under `ops/bin` with its spec under `docs/ops/specs/binaries`), and multi-line values in a slots file, owner Claude Shannon, when one is needed often enough.]
[PLACEHOLDER: a spec-first mode that adds only the missing files of a tool set, owner Claude Shannon, if the operator wants one.]

## Anecdotal Anchor

On 2026-10-30, the operator asked for the rotation to be formalized, because to him it always felt haphazard and awkward and was never carried out the same way twice (`rotate.md`). In Joy's rotation 6, three slips came from hand-glued joins:
- a path passed where text was meant;
- an image pointer that led nowhere;
- a chmod in the wrong order.

The same day, the room adopted STELA's convention, and its map lists 42 legacy scripts in `Scripts/` to be moved to `ops/lib/scripts/`, one word each, with a spec each, as each is next touched. That is 42 chances for the same kind of slip at the joins between script, spec, tests and registry. The day `template` was first built, `help specs` showed where hand assembly had already left gaps: `closeout` and `rotate` each have a spec and no script.

Later that day the operator explained STELA's templates: the agent kept changing the form, or at times forgot it. The rotation receipts in `archives/receipts/` show the same drift: Joy's rotation 6 receipt (`joy-anne-rotation-6-20261030.md`) is organized as Why, Close and custody, Build, Gates, Install, Rollback, Not done and Deviations, while `rotate.md` phase 9 asks for tier, cut and reason, gates, custody, mind leaf hash, estimate against the measured wake, deviations, acceptance and its time. `template receipt` holds every future receipt to the phase 9 list.

## Integrity Filter Warnings

- `template` refuses:
  - a name that is not one lowercase word of 2 to 32 letters;
  - any existing target file or `--out` path, a link included, and an `--out` folder that does not exist;
  - a name the registry already lists;
  - a missing, empty, unknown or twice-given slot, each named; `WORD` or `DATE` given in tool-set mode;
  - any `{{...}}` left in rendered output;
  - `[PLACEHOLDER` in a report;
  - a template that is malformed, is not the type and id expected, or whose body and `requires_slots` disagree;
  - a `--root` that is not a directory, and a default room without `AGENTS.md` and `PoT.md`;
  - unknown options, two names, or none, and an option used in the wrong mode.
- It never overwrites (checked first, then `noclobber` at the write), never deletes, never writes a registry, never commits, and wires no hook or timer.
- A rendered report is only as true as its slots. `template` checks that every field is present and filled; it does not check that a hash is right or a gate really passed. The writer stays answerable for every value.
- A template change is a form change. Editing a `.tpl` changes every future receipt, packet or card; it is done by the template's owner, Claude Shannon, and the self-test is run after it. Case 17 fails if the closeout card drifts from `closeout.md`.
- The registry row is text for the registry's writer, who owns that file. Its ID is computed from the registry as it stands at that moment. Two skeletons generated before either row is added receive the same ID; the registry writer resolves that.
- Every generated tool file is a skeleton that says so: the script refuses with exit 2, and the spec's `Status:` reads "skeleton". Nothing generated is fit to run until its writer replaces every `[PLACEHOLDER]` and the Auditor has reviewed it.
- `--test` writes only inside its own temporary directory and removes only that directory. It reads `docs/ops/specs/scripts/closeout.md` for case 17.
