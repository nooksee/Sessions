# Technical Specification: tools/test/test_mind.py

Test file: `Sessions/tools/test/test_mind.py` (writer: Claudine Colbert). Tool under test: `Sessions/ops/lib/scripts/mind.py`. Tool spec: `docs/ops/specs/scripts/mind.md`. Registry entry: `docs/ops/registry/test.md` (`TEST-02`). Spec written 2026-10-30 and updated for the retained RoR-3 and F1/F2 regressions, then for the W5 projection, sealing and seal-field slices (2026-11-05). Status: 92 tests in the current suite (measured 2026-11-05: 92 passed at umask 0002, 0022 and 0077); rerun at those umasks for measured results.

## Purpose
Prove, in synthetic rooms only, that `mind` writes a leaf only with the operator's words and a registered writer, that every change is a declared new leaf in a verifiable chain, that a forged, moved or edited leaf is never served, and that each of Claudio Freeman's section 130 items the port fixes stays fixed. Each such item has a test named for it.

## Invocation
- Command, from the room root: `python3 -I -B tools/test/test_mind.py`
- Required flags: none. Positional arguments: none (standard `unittest` arguments are accepted).
- Expected exit behavior:
  - `0` when all 65 tests pass (four tests skip if `git` is not installed).
  - `1` when any test fails or errors.
- Reviewers also run it at umask 0002, 0022 and 0077.

## Inputs
- `ops/lib/scripts/mind.py`, both imported (for its parser and renderer) and run as a subprocess with `python3 -I -B`.
- A fresh temporary room per test (`Room`): a room folder, a registry with two keys (`session-doctor`, `claudine-colbert`) whose session ids read `never-printed`, change files written beside it, and a clock that advances one minute per command.
- Three fixture entries: a core identity entry, a lesson and a commitment.
- No real room, registry, mind or body is read or written.

## Outputs
- Stdout: `unittest` progress and a summary line (`Ran 93 tests`, `OK`).
- Writes only inside its own temporary directory, which is removed after each test.
- Exit codes the tests assert on the tool: `0` success, `1` a failed `check`, `2` a refusal.

## Invariants and failure modes
65 tests. The 43 numbered below, the 6 retired-notebook tests listed after them, and 16 tests of the legacy-state guard, the lock location and the nearest-Git rule (B1) that this list does not yet itemize; the base suite at d7e9ae51 measured 59.

**The basic loop (3).**
1. `test_write_check_show_round_trip`: write, check and show agree; `show` returns the leaf byte for byte; the leaf records the operator's words, the writer, `predecessor: none` and the declared change.
2. `test_c11_show_ref_binds_the_capsule_to_the_leaf_hash`: `show --ref` prints `leaf=<path>|sha256=<digest>` matching the leaf.
3. `test_write_needs_kevins_words_and_a_registered_writer`: an empty yes, a bare "ok", or an unregistered `--by` is refused, and 0 files are written.

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
13. `test_c3_a_leaf_outside_the_archives_root_is_refused`: a leaf outside the current archives-root layout is refused.
14. `test_c4_a_resident_of_another_room_cannot_write_here`: a key registered to another room is refused, and 0 files are written.
15. `test_c5_one_resident_has_one_mind`: a duplicated pointer line is refused by `check` and `write`.
16. `test_c5_a_key_registered_twice_is_refused`: a key registered twice is refused.
17. `test_c6_each_leaf_records_the_policy_it_was_written_under`: each leaf records the policy digest; a different digest is reported, not blocked.
18. `test_c7_values_are_screened_as_plain_lines`: newline, tab, zero-width characters, a UUID, a 16-digit hash, a secret pattern and a medical word are each refused, with 0 files written; the yes is screened too.
19. `test_c7_the_yes_words_are_screened`: a secret pattern in the operator's words is refused.
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
30. `test_minds_live_out_of_git`: inside a Git work tree that does not ignore `MIND.md` and `archives/MIND-*`, `write` is refused and creates neither; once ignored, it succeeds. Skips if `git` is absent.

**Archives-root and authorization regressions (13).**
31. `test_ror3_leaves_sit_at_the_archives_root`: new leaves use the accepted archives-root location.
32. `test_ror3_other_archive_files_are_not_minds`: unrelated archive files are not parsed as leaves.
33. `test_ror3_a_linked_leaf_name_is_never_read`: a linked leaf is refused.
34. `test_f1_no_git_on_path_is_a_refusal`: inability to find Git fails closed.
35. `test_f1_a_git_that_does_not_answer_is_a_refusal`: a failed Git command refuses.
36. `test_f1_a_check_ignore_that_does_not_answer_is_a_refusal`: failed ignore inspection refuses.
37. `test_f1_a_broken_repository_is_a_refusal`: a malformed repository is not treated as safe.
38. `test_f1_only_a_positive_answer_passes`: only a positive ignore result admits a mind write.
39. `test_f2_write_needs_the_preview_binding`: write requires the reviewed preview binding.
40. `test_f2_a_change_file_edited_after_the_preview_is_refused`: post-preview edits invalidate approval.
41. `test_f2_layout_does_not_matter_but_content_does`: equivalent layout is accepted; changed content is not.
42. `test_f2_changes_from_standard_input`: the supported stdin route is covered.
43. `test_f2_a_moved_predecessor_is_refused`: a moved predecessor invalidates the binding.

**The retired notebook (6, class `RetiredNotebookTests`).** The notebook classes of W5 (`ProjectTests`, `SealTests`, `SealFieldTests`, 34 tests) were removed with the notebook on 2026-11-09; Git history keeps them. What remains proves the retirement leaves every mind readable:
- `test_a_version_1_leaf_of_the_real_shape_still_passes`: a first leaf shaped like a real one, written under the policy before version 2 (`a92a7c3f6a3b6112`), is canonical, version 1, passes `check` with its policy reported and no seal gate, is served by `show`, and takes a new version 1 leaf after it.
- `test_the_binding_is_the_plain_body`: the binding equals the three-part body's digest, and `binding_of` takes no seal.
- `test_a_version_2_leaf_is_read_and_served_and_its_seal_is_not_checked`: a version 2 leaf whose seal is not on disk passes `check` with no seal gate, is served byte for byte, takes a version 1 leaf after it, and `history` prints its notebook line on its own row only.
- `test_a_version_2_header_is_canonical_and_checked`: a `notebook:` line out of place, a `format:` line after or before it, and an empty `notebook:` value are refused by the parser; a reference of another form, another resident, a disagreeing digest or a bad date fails the entries gate.
- `test_the_policy_digest_still_covers_the_leaf_formats`: the digest differs from the one before version 2, and changes when the formats change.
- `test_the_notebook_commands_and_options_are_gone`: `project`, `seal`, `unseal`, `check --notebook` and `preview --seal` are refused as usage errors, and the module has none of their functions.

## Not covered
- That the words passed to `--yes` are truly the operator's: the tool cannot know, and the spec says so. The audit is the chain, the declared changes and the words held against the conversation.
- The Sessions room itself: no test reads or writes a real mind.
- Any hook, timer or capsule wiring: none exists.
- Whether a real version 2 leaf exists on the host: the operator's preconditions read `archives/` for one before the retirement is pulled.

## Anecdotal Anchor
Claudio's audit of 2026-10-30 (section 130) found that the first design's store let a model edit drop a ratified entry and let an archive-then-use revive a closed one. The operator removed the machinery those gaps lived in. These tests are the record that each gap stays closed: an item fixed by design has a test that tries the old path and is refused.

## Related pointers
- Tool spec: `docs/ops/specs/scripts/mind.md` (its last table maps each section 130 item to its test).
- Script registry: `docs/ops/registry/scripts.md` (`SCRIPT-03`).
- Rotation use: `docs/ops/specs/scripts/rotate.md` (capsule part 2, `show --ref`).
