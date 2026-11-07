# Technical Specification: tools/test/test_myself.py

Test file: `Sessions/tools/test/test_myself.py`. Tool under test: `Sessions/ops/lib/scripts/myself.py`. Tool spec: `docs/ops/specs/scripts/myself.md`. Registry entry: `docs/ops/registry/test.md` (`TEST-21`). Spec written 2026-11-05 by Claudine Colbert with the W3 window change; the suite was ported earlier and had no test spec. Status: 102 tests (count measured 2026-11-07; 57 on 2026-11-05, and the suite grew past this spec's count before this change).

## Purpose
Prove, on synthetic records only, that the self-check finds its caller from the native signal, compares it with the registry and fails closed on every unknown, and that its context-pressure leg reads the caller's own body through the gauge's reader and resolves a Claude window only from the gauge's reviewed table for the caller's own model.

## Invocation
- Command, from the room root: `python3 -I -B tools/test/test_myself.py`
- Required flags: none. Positional arguments: none (standard `unittest` arguments are accepted).
- Expected exit behavior: `0` when all 102 tests pass; `1` when any fails or errors.

## Inputs
- A `Fixture` per test: a synthetic room with a registry, roster and host bindings, a synthetic `/proc` tree for the caller's ancestry, a synthetic Codex or Claude body, a synthetic copy of the gauge's window table in the gauge spec's row form (`model=claude-fixture|window=1000|source=fixture table|observed=2026-08-09`), and a synthetic shared status-line record that the leg must ignore.
- Invented session identifiers, persons and roles. No real registry, body, record or provider is read.

## Outputs
- `unittest` progress and a summary line. Writes only inside each test's temporary directory.

## Invariants and failure modes
102 tests in 6 classes, by the file's own count: `ResidentSelfCheckTests` 27, `HeldResidentTests` 8, `SharedGaugePressureTests` 16, `WindowTableTests` 6, `NotebookRouteTests` 31, `OrientationAfterIdeNoticesTests` 14.
- `ResidentSelfCheckTests`: caller identification from the native signal and ancestry, registry, roster and binding agreement, orientation claims, coverage and fail-closed exits.
- `HeldResidentTests`: a registry-only resident held from the launcher: absent from the launcher passes; present in it, bound under another key, with non-private bindings, through a link, by alias, with a malformed collection or an unknown launcher value, it is a finding.
- `SharedGaugePressureTests`: the context-pressure leg agrees with the gauge's reader on the same synthetic bodies: ordinary readings, sidechains, zero usage, compaction before and after a fresh reading, incomplete rows, reader failure and repeated runs.
- `WindowTableTests` (W3, 2026-11-05):
  1. `test_a_model_in_the_table_resolves_with_provenance`: the leg passes with the table's window, reports the model, `tokens_source=caller-native-body` and `window_source=gauge spec table: fixture table, observed 2026-08-09`, names the table among its surfaces and never names the shared record.
  2. `test_a_model_absent_from_the_table_is_undetermined`: a table without the caller's model leaves the leg UNDETERMINED with the gauge's reason and the note that the shared record is not used.
  3. `test_the_shared_record_is_never_used`: a shared record naming another model, or the caller's model with another window, or absent, changes nothing; with the table lacking the model, a matching shared record does not supply a window.
  4. `test_a_pre_compaction_reading_stays_unknown`: a compaction boundary after the last reading leaves the leg UNDETERMINED.
  5. `test_an_unreadable_table_is_undetermined`: an absent table, one not in UTF-8, one with no rows and a folder in its place each leave the leg UNDETERMINED.
  6. `test_a_gauge_that_cannot_load_is_undetermined`: in process, a gauge that fails to load gives no window and names the cause.

- `NotebookRouteTests` (W5 Part C, 2026-11-07): the tenth leg. `test_every_combination_of_the_list_and_the_launch` runs the 12 cells of the spec's table, each with its stated reason, and `test_not_on_the_list_with_the_switch_is_never_a_pass` pins the silent loss, list or no list, with exit 1. The rest: no list as not wired; the route and the switch together; the switch's values read loosely, and a name that merely ends in it; `--settings` in its two forms, twice, as JSON, and after the launch's own `--`; the first token never read as an argument; the own route compared resolved; the `--bg` form naming no body as UNDETERMINED in each list state, and the form naming its session read like any launch; a worker's process naming no session passed over for its parent's; a Codex caller and a row of another room with nothing to judge, a broken list included; a row of this room through a link; an unreadable environment, a row naming no room, no identity, no room or wrapper configured, a wrapper absent, not Python, exiting as it loads or lacking a reader, and a registry row the reader cannot judge, each UNDETERMINED; a launch gone between two reads; a finding's log text, the newest row for this key among rows of another key, a null key and junk, an empty log, a linked log not followed and a log that is a pipe not waited on; a pass reading no log; no session or argument printed; nothing written; the live paths naming this room and its wrapper; importing the script loading no wrapper and `resolve_caller` never loading it; the bytecode setting kept and no bytecode written; and the real wrapper's reader being the one used.

Two tests of the removed shared-record path (its age and its future date) were removed with it, and the coverage test now removes the window table instead of the shared record.

**Mutation check, 2026-11-05.** Each new guard was disabled in turn (7 mutations: an absent model as unknown, no shared-record fallback, an unreadable table as unknown, the named table read, a gauge failure as unknown, the table as a surface, and the provenance reported); the suite caught 7 of 7.

## Not covered
- The live room: no test reads the real registry, body, table, shared record, wired list or decision log.
- Any real launch: the leg's reading of a real provider process is observed only at the wrapper's native wake.
- Whether the gauge's table rows are right: they are reviewed in the gauge's spec.
- Any threshold: the rotation line and the percentage formula are unchanged and not re-tested here.
