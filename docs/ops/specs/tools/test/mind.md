<!-- redact: public copy; source sha256 40e48c16b2576475ae746dce17ae2c9ce1184bcc1eba924bad83ce190ca9ebd4; rules 8; mode history; words 1; sessions 0 whole, 0 truncated; host paths 0; decisions 0 -->
# Technical Specification: tools/test/test_mind.py

Test file: `Sessions/tools/test/test_mind.py` (writer: Claudine Colbert). Tool under test: `Sessions/ops/lib/scripts/mind.py`. Tool spec: `docs/ops/specs/scripts/mind.md`. Registry entry: `docs/ops/registry/test.md` (`TEST-02`). Spec written 2026-10-30 from a reading of the test file. Status: 30 of 30 passing at umask 0002, 0022 and 0077 on 2026-10-30.

## Purpose
Prove, in synthetic rooms only, that `mind` writes a leaf only with Kevin's words and a registered writer, that every change is a declared new leaf in a verifiable chain, that a forged, moved or edited leaf is never served, and that each of Claudio Freeman's section 130 items the port fixes stays fixed. Each such item has a test named for it.

## Invocation
- Command, from the room root: `python3 -I -B tools/test/test_mind.py`
- Required flags: none. Positional arguments: none (standard `unittest` arguments are accepted).
- Expected exit behavior:
  - `0` when all 30 tests pass (one test skips if `git` is not installed).
  - `1` when any test fails or errors.
- Reviewers also run it at umask 0002, 0022 and 0077.

## Inputs
- `ops/lib/scripts/mind.py`, both imported (for its parser and renderer) and run as a subprocess with `python3 -I -B`.
- A fresh temporary room per test (`Room`): a room folder, a registry with two keys (`session-doctor`, `claudine-colbert`) whose session ids read `never-printed`, change files written beside it, and a clock that advances one minute per command.
- Three fixture entries: a core identity entry, a lesson and a commitment.
- No real room, registry, mind or body is read or written.

## Outputs
- Stdout: `unittest` progress and a summary line (`Ran 30 tests`, `OK`).
- Writes only inside its own temporary directory, which is removed after each test.
- Exit codes the tests assert on the tool: `0` success, `1` a failed `check`, `2` a refusal.

## Invariants and failure modes
30 tests.

**The basic loop (3).**
1. `test_write_check_show_round_trip`: write, check and show agree; `show` returns the leaf byte for byte; the leaf records Kevin's words, the writer, `predecessor: none` and the declared change.
2. `test_c11_show_ref_binds_the_capsule_to_the_leaf_hash`: `show --ref` prints `leaf=<path>|sha256=<digest>` matching the leaf.
3. `test_write_needs_kevins_words_and_a_registered_writer`: an empty yes, a bare "[words sha256=2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df]", or an unregistered `--by` is refused, and 0 files are written.

**Claudio's blockers (4).**
4. `test_b1_an_amendment_keeps_the_core_entry_and_carries_the_new_yes`: an amendment keeps the entry's number, carries the new yes, and shows in `history`.
5. `test_b1_a_leaf_that_silently_drops_a_core_entry_fails_check`: a planted leaf whose declared change differs from the real difference fails `check`, and `show` refuses it.
6. `test_b2_a_retired_entry_never_revives`: a retired entry cannot be amended; re-adding it issues a new number.
7. `test_b2_a_forged_leaf_reusing_a_retired_number_fails_check`: a planted leaf reusing a retired number fails `check`.

**Claudio's conditions (15).**
8. `test_c1_preview_shows_before_and_after_and_writes_nothing`: `preview` shows before and after and changes 0 files.
9. `test_c2_an_ancestor_changed_after_it_was_written_is_detected`: an ancestor edited after the fact fails its name hash.
10. `test_c3_a_forged_current_leaf_fails`: an edited current leaf with a re-pointed hash still fails its name hash.
11. `test_c3_c4_a_leaf_from_another_mind_is_never_served`: a pointer aimed at another resident's leaf fails `check`, and `show` prints nothing.
12. `test_c3_a_pointer_moved_back_to_an_older_genuine_leaf_fails`: a pointer moved back fails the newest gate.
13. `test_c3_a_leaf_outside_surfaces_is_refused`: a leaf outside `archives/surfaces/` is refused.
14. `test_c4_a_resident_of_another_room_cannot_write_here`: a key registered to another room is refused, and 0 files are written.
15. `test_c5_one_resident_has_one_mind`: a duplicated pointer line is refused by `check` and `write`.
16. `test_c5_a_key_registered_twice_is_refused`: a key registered twice is refused.
17. `test_c6_each_leaf_records_the_policy_it_was_written_under`: each leaf records the policy digest; a different digest is reported, not blocked.
18. `test_c7_values_are_screened_as_plain_lines`: newline, tab, zero-width characters, a UUID, a 16-digit hash, a secret pattern and a medical word are each refused, with 0 files written; the yes is screened too.
19. `test_c7_the_yes_words_are_screened`: a secret pattern in Kevin's words is refused.
20. `test_c9_leaves_survive_an_ancestor_moved_to_custody`: an older ancestor removed is reported as `chain-history`, and writing continues.
21. `test_c9_the_immediate_predecessor_must_exist`: a missing immediate predecessor fails `check`.
22. `test_c10_a_change_file_that_is_not_utf8_is_refused`: a non-UTF-8 change file and a field named twice are refused, with 0 files written.

**Rules the port keeps (8).**
23. `test_layer_rules_and_trauma_guard`: an incident without a fix, blame words in core, missing required fields, fields that do not belong to the layer, a supplied id or yes, and a bad date are each refused, with 0 files written.
24. `test_core_over_budget_is_refused_whole`: a write over the core budget is refused whole.
25. `test_amend_cannot_change_layer_or_change_nothing`: an amendment that changes the layer, or changes nothing, is refused.
26. `test_a_hand_written_pointer_is_left_as_it_is`: a `MIND.md` the tool did not write is refused and left byte for byte as it was.
27. `test_no_first_leaf_while_leaves_exist_without_a_pointer`: a new first leaf is refused while earlier leaves exist without a pointer line.
28. `test_a_reordered_leaf_is_not_canonical`: a leaf with reordered fields fails to parse.
29. `test_leaves_and_pointer_are_private`: leaf and pointer are mode 0600.
30. `test_minds_live_out_of_git`: inside a Git work tree that does not ignore `MIND.md` and `archives/surfaces/`, `write` is refused and creates neither; once ignored, it succeeds. Skips if `git` is absent.

## Not covered
- That the words passed to `--yes` are truly Kevin's: the tool cannot know, and the spec says so. The audit is the chain, the declared changes and the words held against the conversation.
- The Sessions room itself: no test writes a real mind, and none has been written.
- Any hook, timer or capsule wiring: none exists.

## Anecdotal Anchor
Claudio's audit of 2026-10-30 (section 130) found that the first design's store let a model edit drop a ratified entry and let an archive-then-use revive a closed one. Kevin removed the machinery those gaps lived in. These tests are the record that each gap stays closed: an item fixed by design has a test that tries the old path and is refused.

## Related pointers
- Tool spec: `docs/ops/specs/scripts/mind.md` (its last table maps each section 130 item to its test).
- Script registry: `docs/ops/registry/scripts.md` (`SCRIPT-03`).
- Rotation use: `docs/ops/specs/scripts/rotate.md` (capsule part 2, `show --ref`).
