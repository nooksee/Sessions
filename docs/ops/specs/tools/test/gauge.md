# Technical Specification: tools/test/test_gauge.py

Test file: `Sessions/tools/test/test_gauge.py` (writer: Claudine Colbert). Tool under test: `Sessions/ops/lib/scripts/gauge.py`. Tool spec: `docs/ops/specs/scripts/gauge.md`. Registry entry: `docs/ops/registry/test.md` (`TEST-01`). Spec written 2026-10-30 from a reading of the test file. Status: 21 of 21 passing at umask 0002, 0022 and 0077 on 2026-10-30.

## Purpose
Prove, on synthetic bodies only, that `gauge` reads the provider's own token figure for each registered resident, takes the window from the right authority, labels every state honestly, prints "unknown" rather than a guess, never reads message content into any output, and writes its ledger exactly as specified.

## Invocation
- Command, from the room root: `python3 -I -B tools/test/test_gauge.py`
- Required flags: none. Positional arguments: none (standard `unittest` arguments are accepted).
- Expected exit behavior:
  - `0` when all 21 tests pass.
  - `1` when any test fails or errors.
- Reviewers also run it at umask 0002, 0022 and 0077.

## Inputs
- `ops/lib/scripts/gauge.py`, run as a subprocess with `python3 -I -B`.
- A fresh temporary world per test (`World`, prefix `gauge-test-`): a registry, Claude, Codex (live and archived) and Copilot body roots, a one-row window table (`claude-opus-5-5`, 1,000,000), a status-line record, and a ledger path.
- A fixed clock: `--now 2026-10-30T16:00:00Z`.
- No real body, registry, ledger or spec is read.

## Outputs
- Stdout: `unittest` progress and a summary line (`Ran 21 tests`, `OK`).
- Writes only inside its own temporary directory, which is removed after each test.

## Invariants and failure modes
21 tests in four groups.

**Claude side (10).**
1. `test_latest_call_sum_and_table_window`: the newest call wins; tokens are input plus cache read plus cache creation, counted once per `message.id` across its rows (305,020 of 1,000,000 = 30.5 percent, `last observed`, age 1,800 seconds); the window source is the spec table.
2. `test_zero_usage_and_sidechain_rows_are_never_readings`: sidechain rows and `<synthetic>` zero-usage rows are skipped; the earlier genuine reading (400,000) stands.
3. `test_status_line_window_for_the_same_model`: with no table row, the status-line window for the same model is used and labeled as from the status line.
4. `test_unknown_window_is_printed_unknown_not_guessed`: a model with no reviewed window gives `window unknown`, percent empty, a reason naming the model, and "unknown" in the table.
5. `test_compaction_after_the_reading`: a compaction boundary after the reading gives `before compaction` with no percent, while keeping the token figure.
6. `test_spaced_json_from_a_rebuilt_body`: rows written with spaced separators (a rebuilt body) are still read.
7. `test_unterminated_final_line_is_ignored`: a torn final line is skipped; the last complete reading stands.
8. `test_a_quoted_boundary_in_content_is_not_a_compaction`: a compaction marker quoted inside message text is not a compaction.
9. `test_reading_found_deep_in_the_tail_and_unknown_beyond_the_bound`: a reading about 3.1 MB from the end is found; one beyond the 16,000,000-byte bound gives `unknown` with the bound named in the reason.
10. `test_content_is_never_printed_or_stored`: a planted secret marker in message content appears in 0 table outputs, 0 JSON outputs and 0 ledger lines.

**Codex side (5).**
11. `test_joe_method_model_from_the_preceding_turn_context`: the model comes from the nearest turn context before the token event, not a later one; the window comes from the same event (286,264 of 475,000 = 60.3 percent).
12. `test_compacted_row_after_the_reading_supersedes_without_parsing`: a `compacted` row after the reading gives `before compaction` with its time, and its replacement history is never printed.
13. `test_quoted_structure_in_a_message_is_ignored`: `compacted` and `token_count` quoted in a message do not count as structure.
14. `test_archived_body_is_labelled`: a body found only in the archived root is labeled `archived body`.
15. `test_live_preferred_over_archived_and_ambiguity_refused`: a live body is preferred over an archived one; two live bodies for one id give `unknown` with "refusing to choose".

**Copilot and registry (4).**
16. `test_copilot_usage_record`: `inputTokens` over `maxPromptTokens` (114,880 of 272,000 = 42.2 percent).
17. `test_copilot_compaction_after`: a Copilot compaction after the reading gives `before compaction`.
18. `test_missing_body_unknown_provider_and_bad_id`: a missing body, a provider with no reader, and a session id that is not a plain identifier (a path traversal attempt) each give a stated reason.
19. `test_tokens_above_the_window_are_invalid`: tokens above the window give `invalid`.

**Ledger (2).**
20. `test_one_line_per_resident_per_run_and_no_ledger_writes_nothing`: `--no-ledger` creates no ledger; two runs for two residents give exactly 4 lines, schema `gauge/1`, file mode 0600.
21. `test_unreadable_registry_measures_nothing`: an unreadable registry exits 2 and creates no ledger.

## Not covered
- The compaction matcher's margin (gauge.md O1: the boundary is found within the first 6 leading fields). [PLACEHOLDER: a pinning test for the Claude Code boundary row form, re-checked on each Claude Code upgrade. Owner: Claudine Colbert, as writer of gauge.py.]
- The real host roots and the VM-share Codex root: tests pass their own roots.
- Any timer or notification: none exists.

## Anecdotal Anchor
On 2026-10-30 this desk proposed rotating a resident because his body was 78 MB; his meter read 32 percent. The same day, gauge's first run found Claudine at 84.6 percent and Alan Codex at 73.3, past the line with nobody aware. These tests hold the meter to the provider's figure and to an honest "unknown".

## Related pointers
- Tool spec: `docs/ops/specs/scripts/gauge.md`.
- Script registry: `docs/ops/registry/scripts.md` (`SCRIPT-01`).
- Review: Claudio Freeman, section 131 (0 blockers; C1 window order, C2 the compacted state, C3 for closeout).
