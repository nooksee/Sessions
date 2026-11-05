# Technical Specification: tools/test/test_mind.py

Test file: `Sessions/tools/test/test_mind.py` (writer: Claudine Colbert). Tool under test: `Sessions/ops/lib/scripts/mind.py`. Tool spec: `docs/ops/specs/scripts/mind.md`. Registry entry: `docs/ops/registry/test.md` (`TEST-02`). Spec written 2026-10-30 and updated for the retained RoR-3 and F1/F2 regressions, then for the W5 projection, sealing and seal-field slices (2026-11-05). Status: 92 tests in the current suite (measured 2026-11-05: 92 passed at umask 0002, 0022 and 0077); rerun at those umasks for measured results.

## Purpose
Prove, in synthetic rooms only, that `mind` writes a leaf only with the operator's words and a registered writer, that every change is a declared new leaf in a verifiable chain, that a forged, moved or edited leaf is never served, and that each of Claudio Freeman's section 130 items the port fixes stays fixed. Each such item has a test named for it.

## Invocation
- Command, from the room root: `python3 -I -B tools/test/test_mind.py`
- Required flags: none. Positional arguments: none (standard `unittest` arguments are accepted).
- Expected exit behavior:
  - `0` when all 92 tests pass (four tests skip if `git` is not installed).
  - `1` when any test fails or errors.
- Reviewers also run it at umask 0002, 0022 and 0077.

## Inputs
- `ops/lib/scripts/mind.py`, both imported (for its parser and renderer) and run as a subprocess with `python3 -I -B`.
- A fresh temporary room per test (`Room`): a room folder, a registry with two keys (`session-doctor`, `claudine-colbert`) whose session ids read `never-printed`, change files written beside it, and a clock that advances one minute per command.
- Three fixture entries: a core identity entry, a lesson and a commitment.
- No real room, registry, mind or body is read or written.

## Outputs
- Stdout: `unittest` progress and a summary line (`Ran 92 tests`, `OK`).
- Writes only inside its own temporary directory, which is removed after each test.
- Exit codes the tests assert on the tool: `0` success, `1` a failed `check`, `2` a refusal.

## Invariants and failure modes
92 tests. The 43 numbered below, the 10 projection, 15 sealing and 8 seal-field tests listed after them, and 16 tests of the legacy-state guard, the lock location and the nearest-Git rule (B1) that this list does not yet itemize; the base suite at d7e9ae51 measured 59.

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

**Notebook projection, W5 first slice (10, class `ProjectTests`).** Each uses its own synthetic notebook folder (0700) with a one-line `MEMORY.md` (0600).
- `test_w5_project_puts_one_block_at_the_top_and_keeps_every_other_byte`: the block is the leaf verbatim between its two markers, at the top; the earlier bytes follow unchanged; the index stays 0600; the room's leaf and pointer are unchanged; output says the copy is not evidence of loading and prints no session id.
- `test_w5_project_creates_the_index_in_a_named_empty_notebook`: with no `MEMORY.md`, the index is created holding the block alone, at 0600.
- `test_w5_project_is_idempotent_and_follows_a_new_leaf`: a second run reports unchanged and writes nothing; after a new leaf the block is replaced and the tail kept.
- `test_w5_project_has_no_default_notebook`: no `--notebook`, a blank one, or an absent folder is refused, and no folder is created.
- `test_w5_project_refuses_unsafe_notebook_paths`: a linked ancestor, a linked notebook folder, a folder not 0700, an index not 0600, an index with two hard links, a linked index and a file in place of the folder are each refused; the link target is untouched.
- `test_w5_project_refuses_wrong_duplicate_malformed_and_misplaced_markers`: another key's block, a duplicated block, a malformed marker, an end without a begin, a block below the top and a CRLF marker are each refused with the index byte for byte as it was.
- `test_w5_an_edited_block_is_reported_and_replaced`: a hand-edited block is reported as edited and replaced by the leaf, never trusted.
- `test_w5_an_unverified_mind_is_never_projected_and_nothing_is_locked`: no pointer line, a forged leaf, or an unregistered key is refused; a refusal before the lock creates no `logs/`.
- `test_w5_oversize_is_refused_never_truncated`: a mind whose block exceeds 200 lines is refused whole.
- `test_w5_project_needs_positive_git_exclusion`: a notebook inside a Git work tree that does not ignore `MEMORY.md` is refused; once ignored, it is projected. Skips if `git` is absent.

**Notebook seals and the two check gates, W5 second slice (15, class `SealTests`).** Each uses a synthetic notebook folder (0700) holding `MEMORY.md`, a topic file and a subfolder with one file (0600). Hostile seals are built in the test with a correct name hash, as a forger would build them.
- `test_w5_seal_writes_once_binding_key_and_hash`: the seal is named for the key, the UTC date and its own hash, mode 0600, opens with `SEAL.json` and `notebook`, and its manifest names the key and every member; a repeat is reported unchanged with one file; a changed notebook gives a second seal and the first stays byte for byte.
- `test_w5_seal_never_overwrites_other_bytes`: a seal name holding other bytes is refused and left as it is.
- `test_w5_seal_refuses_links_specials_hard_links_and_an_unregistered_key`: a linked member, a pipe, a file with two hard links, an unregistered key, a folder not 0700, a blank or missing `--notebook` are each refused; no seal is written and no lock is created.
- `test_w5_seal_needs_positive_git_exclusion`: in a room inside a Git work tree that does not ignore the seal, it is refused; once ignored, it is written. Skips if `git` is absent.
- `test_w5_unseal_restores_byte_for_byte_into_an_absent_folder`: every file comes back byte for byte, folders 0700 and files 0600, and no staging folder is left.
- `test_w5_unseal_fills_an_empty_folder_and_replaces_only_with_replace`: an empty folder is filled; a non-empty one is refused without `--replace`; with it, the seal takes the name and the earlier folder is kept beside it with its bytes.
- `test_w5_unseal_checks_fixity_before_extracting`: one flipped bit in the seal is refused on its name hash; no target and no staging folder exist afterwards.
- `test_w5_unseal_refuses_hostile_members_without_extracting`: an absolute member, a `..` escape, a symbolic link, a hard link, a character device, a pipe, a foreign owner, a member outside `notebook/`, a member before its folder, a manifest of another key, a manifest hash that does not match and a manifest that omits a member are each refused, and nothing is extracted.
- `test_w5_unseal_binds_the_key`: a seal of one key is refused for another by its name; renamed to the other key, it is refused by its manifest; a malformed name is refused.
- `test_w5_unseal_refuses_unsafe_targets`: a linked parent, a linked target, a target not 0700 and an absent parent are each refused.
- `test_w5_unseal_needs_positive_git_exclusion`: a target inside a Git work tree that does not ignore it is refused; once ignored, it is restored. Skips if `git` is absent.
- `test_w5_a_staged_tree_must_equal_the_seal`: the staged-tree comparison rejects other bytes, another mode and an extra file.
- `test_w5_a_bad_staged_write_never_takes_the_name`: in process, a staged write that loses a byte is caught by the comparison; the target never appears and the staging folder is removed.
- `test_w5_check_seal_gate`: no seals passes; a valid seal passes; a seal with one changed byte fails `check` (exit 1) while `show` still serves the mind; a garbled `NOTEBOOK-` name is reported at room level.
- `test_w5_check_projection_gate`: no projection fails; a fresh projection passes; a hand-edited block fails; a newer leaf not yet projected fails as stale; `--notebook` without `--key` is refused.

Each guard of this slice was disabled in turn (26 mutations: links, specials, hard links, overwrite, preflight before the lock, registration, fixity, escape, special members, ownership, manifest key, member hash, member count, folder order, `--replace`, the staged comparison, keeping the earlier folder, the name's key, the target's parent and privacy, both Git rules and both gates, and `--notebook` without `--key`); the suite caught 26 of 26.

**Leaf format 2, the seal in the leaf, W5 third slice (8, class `SealFieldTests`).** Synthetic rooms and notebooks; the operator's words are invented.
- `test_w5_a_version_1_leaf_of_the_real_shape_still_passes`: a first leaf shaped like a real one (three lessons, two of them closed incidents with fixes, written under the policy before this slice, `a92a7c3f6a3b6112`) parses and renders byte for byte as version 1, passes `check` with `policy` reported and not failed and `leaf-seal` passing, is served by `show` byte for byte, has no notebook in `history`, and takes a version 2 successor.
- `test_w5_the_binding_without_a_seal_is_unchanged`: without a seal the binding equals the old three-part body's digest; with one it differs.
- `test_w5_write_with_a_seal_records_a_version_2_leaf`: the `notebook:` line follows `policy` with the seal's path and full SHA-256; the leaf is version 2, canonical and 0600; `check` passes `leaf-seal`; `show` prints the line; a later write without a seal is version 1; `history` marks only the sealed leaf.
- `test_w5_preview_shows_the_seal_and_the_binding_covers_it`: preview shows the line and names the seal in its instruction; the binding differs from the one without a seal; a write with another seal, with none, or with a binding previewed without the seal is refused, and the pointer does not move.
- `test_w5_write_refuses_a_seal_it_cannot_trust`: a seal not on disk, another key's seal, a malformed name, a seal at 0644, a linked seal, a seal with one flipped bit and a seal renamed to another key are each refused, and the pointer does not move.
- `test_w5_check_gate_for_the_leaf_seal`: a named seal moved away is reported under `seal-history`, with exit 0; a changed seal fails `leaf-seal`; a leaf whose recorded digest differs from the seal's after the first 8 digits fails it too.
- `test_w5_a_version_2_header_is_canonical_and_checked`: a `notebook:` line out of place, a `format:` line after or before it, and an empty `notebook:` value are refused by the parser; a reference that is not a seal path, one of another resident, one whose name and digest disagree, and one with an impossible date each fail the header check.
- `test_w5_the_policy_digest_covers_the_leaf_formats`: the digest differs from the one before this slice, and changes again when the formats change.

Each new guard of this slice was disabled in turn (18 mutations: parsing and rendering version 2, the reference's form, key, digest prefix and date, the binding's seal, the seal's verification and its 0600 mode, the line in the leaf, custody as a report, a bad seal as a failure, the full digest, the gate's blocking, the history line, the policy's formats, and preview's line and instruction); the suite caught 18 of 18.

## Not covered
- That the words passed to `--yes` are truly the operator's: the tool cannot know, and the spec says so. The audit is the chain, the declared changes and the words held against the conversation.
- The Sessions room itself: no test reads or writes a real mind, notebook or seal.
- Any hook, timer or capsule wiring: none exists.
- That a provider loads the projected block: projection source is not evidence of loading; that needs its own native proof.
- A real notebook or its home, a real seal or unseal, and the launch wrapper: none is touched or built here.
- A seal-only leaf, with no change to the entries: not possible (the tool spec says why).
- Whether a provider writes the notebook during a seal or unseal: the tool cannot detect its writer; the seam is the operator's.

## Anecdotal Anchor
Claudio's audit of 2026-10-30 (section 130) found that the first design's store let a model edit drop a ratified entry and let an archive-then-use revive a closed one. The operator removed the machinery those gaps lived in. These tests are the record that each gap stays closed: an item fixed by design has a test that tries the old path and is refused.

## Related pointers
- Tool spec: `docs/ops/specs/scripts/mind.md` (its last table maps each section 130 item to its test).
- Script registry: `docs/ops/registry/scripts.md` (`SCRIPT-03`).
- Rotation use: `docs/ops/specs/scripts/rotate.md` (capsule part 2, `show --ref`).
