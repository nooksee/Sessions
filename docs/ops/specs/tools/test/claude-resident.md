# Technical Specification: test_claude_resident.py

Tool: `ops/bin/claude-resident`. Test: `tools/test/test_claude_resident.py`.
Writer: Claudine Colbert. Registry entry: `docs/ops/registry/test.md` (`TEST-47`).
Scope: synthetic registries, rooms and notebooks only; the real provider is never executed, only a fake script.

## Purpose and invocation

Prove, on synthetic data, that the wrapper's dry run reaches each of six branches (the design's five, with a registered row split into this room and another room), attaches a notebook only for a registered row of this room, passes a registered row of another room through untouched, turns auto memory off in every other outcome, never blocks a launch, never executes anything in a dry run and never prints a registry value.

Run from the room root: `python3 -I -B tools/test/test_claude_resident.py`. Exit 0 when all 39 tests pass (two skip if `git` is not installed); 1 on any failure. Reviewers also run it at umask 0002, 0022 and 0077.

Each test builds a room with a registry at 0600 holding four rows (two Claude rows of this room, one Codex row, one Claude row of another room), each with an invented zero-block session, and one notebook folder at 0700 with a `MEMORY.md` at 0600 for the first key only. The wrapper runs as a subprocess with `python3 -I -B`, once directly through its interpreter line, and once in process for the error path.

## Proofs

Every dry run is checked for: exit 0 and an empty standard error; `mode` `dry-run` and `executed` false; `argv` equal to `<provider>` followed by the given arguments exactly; and no key, person, role, note or room of any row in the output, with a session present only as often as the arguments carry it.

1. `test_registered_attaches_the_notebook`: `--resume <id>`, `--resume=<id>`, `-r <id>`, `--session-id <id>`, `--session-id=<id>` and the same session named twice each attach the notebook, add no environment change, mark the route unproven and list nine unproven items.
2. `test_registered_without_a_usable_notebook_attaches_nothing`: a registered key of this room with no folder, a folder not 0700, an index not 0600, an index holding another key's projection marker, a malformed marker and a linked folder each give the registered branch with nothing attached and auto memory off.
3. `test_registered_elsewhere_passes_through_untouched`: a session held by one Claude row of another room gives the registered-elsewhere branch: no notebook, no environment change, no route, auto memory unchanged; a usable folder of that key in this room's home changes nothing.
4. `test_registered_needs_positive_git_exclusion`: inside a Git work tree that does not ignore the home, nothing is attached; once ignored, the notebook is attached. Skips if `git` is absent.
5. `test_unregistered_turns_auto_memory_off`: an unknown session, and a session held only by a Codex row.
6. `test_ambiguous_turns_auto_memory_off`: two different sessions in the arguments, and two Claude rows holding one session.
7. `test_new_turns_auto_memory_off`: no arguments, a prompt alone, `--continue`, `-c`, `--resume` with no value, `--resume` followed by a flag, `--fork-session`, and a session flag after the provider's own `--`.
8. `test_broken_registry_turns_auto_memory_off`: an absent registry, mode 0644, invalid JSON, a duplicate key, a row with an empty session, a key that is not a plain key, a linked registry and an identities value that is not a list; each also for a run that names no session.
9. `test_the_dry_run_executes_nothing_and_writes_nothing`: with a fake `claude` first on `PATH` that would leave a marker, two dry runs leave none and no settings folder; the output names that file as `provider`.
10. `test_a_malformed_wrapper_form_is_refused_and_echoes_nothing`: no arguments, a wrapper option without its value, an unknown option after `--dry-run`, and options with no `--` are each refused with exit 2, empty standard output, the usage line and no session echoed.
11. `test_the_wrapper_runs_directly`: the file is executable and its interpreter line runs it.
12. `test_an_explicit_registry_path_is_read`: `--registry` selects the registry read.
13. `test_an_unexpected_error_fails_closed_without_blocking`: in process, a failure while deciding gives the error outcome with auto memory off, exit 0 and the arguments still passed through.

The real form, with a fake provider script and a `PATH` that holds no real one:

14. `test_no_real_provider_is_reachable_from_this_suite`: the only `claude` on the suite's `PATH` is its tripwire; the module fails the suite if anything ran it.
15. `test_every_argument_stream_and_status_pass_through`: arguments with spaces, an empty one, a newline, `--` and shell characters arrive unchanged; standard input, output and error, the working directory and an exit status of 37 pass through.
16. `test_the_provider_inherits_no_ignored_signal_from_python`: the provider's ignored-signal mask equals that of a direct run.
17. `test_a_registered_launch_gets_the_route_and_nothing_else`: `--settings <file>` comes first and the arguments follow unchanged; no environment change; the file names the folder at 0600 in a 0700 folder; the notebook is untouched.
18. `test_the_settings_file_is_stable_and_replaced_only_when_it_differs`: a second launch keeps the same inode and time; wrong bytes or a wrong mode are replaced; no other file appears.
19. `test_a_settings_place_in_doubt_turns_memory_off_and_does_not_block`: a linked folder, a loose folder, a linked file, a folder holding the file's name and an absent `logs/` each give the same answer from the dry run and the launch: auto memory off, the arguments unchanged and the provider run; a linked file's target is untouched.
20. `test_the_dry_run_previews_a_folder_it_would_make_without_making_it`: an absent folder previews as attached and is not made; a `logs/` it cannot write in or a link in that place previews as nothing attached, and the launch agrees.
21. `test_the_launch_asks_again_if_the_place_changed_after_the_decision`: in process, a place that goes bad after the decision gives auto memory off, no file written and the provider still called.
22. `test_a_second_hard_link_is_replaced_even_with_the_right_bytes`: the file returns to one link and the other name keeps its bytes.
23. `test_a_settings_file_git_would_track_turns_memory_off`: a Git work tree that does not ignore `logs/` gives auto memory off; once ignored, the route returns. Skips if `git` is absent.
24. `test_a_failed_write_leaves_no_temporary_file_and_still_launches`: in process, a failed replace leaves the folder empty, auto memory off and the launch going.
25. `test_a_launch_that_carries_settings_gets_memory_off`: `--settings x`, `--settings=x` and either after other arguments each give auto memory off, no file written and the arguments unchanged; `--dry-run` states the reason.
26. `test_settings_after_the_providers_own_separator_is_not_a_settings_source`: the route is still given.
27. `test_registered_elsewhere_is_untouched`: the arguments are unchanged, an inherited switch stays as it was, whatever its value, and no file is written.
28. `test_every_other_branch_turns_memory_off_even_against_an_inherited_zero`: unregistered, new, continue, fork, ambiguous, another provider, no notebook and a broken registry.
29. `test_an_inherited_switch_is_left_on_an_attached_launch`: the route is given and the inherited value stays.
30. `test_an_error_before_the_exec_fails_closed_and_still_launches`: in process, a failure loading the mind tool or writing the file gives auto memory off with the provider still called.
31. `test_the_first_claude_on_path_runs_never_this_wrapper_or_a_relative_entry`: empty and relative entries and a link back to the wrapper are skipped; a `claude` in the working directory never runs.
32. `test_no_provider_is_stated_and_echoes_nothing`: an empty `PATH`, a named file that is not executable and the wrapper named as its own provider each exit 127 with no session echoed.
33. `test_a_provider_that_cannot_run_is_stated`: a bad interpreter exits 126.
34. `test_the_provider_option_is_used`: `--provider` wins with no `claude` on `PATH`.
35. `test_a_wrapper_may_be_reached_by_its_interpreter_line`: the real form runs through the interpreter line.
36. `test_the_bare_form_applies_the_defaults_and_passes_everything`: a copy of the wrapper in the synthetic room takes the plugin's argument shape, with the room's defaults, and gives the route or auto memory off.
37. `test_in_the_bare_form_every_argument_is_the_providers`: a later `--`, `--room`, `--registry`, `--provider` and `--dry-run` all reach the provider.
38. `test_a_first_argument_equal_to_a_wrapper_option_is_the_wrappers`: each is read as the wrapper's and refused with exit 2 when malformed; the provider does not run.
39. `test_the_explicit_form_keeps_a_separator_as_the_wrappers`: the first `--` is the wrapper's and a second reaches the provider.

**Mutation check, 2026-11-05.** Each guard was disabled in turn (25 mutations: `--dry-run` only, the `--` separator, unknown wrapper options, the session value, `--fork-session`, the provider's own `--`, two sessions named, Claude rows only, no match, several matches, the room, the registered-elsewhere run left untouched, the folder's private path, its Git rule, its markers, the registry's absence, regular file, mode, duplicate keys, row fields, plain keys and identities list, the auto-memory switch, the error path, and the key kept out of reasons); the suite caught 25 of 25.

## Not proved

- That any provider loads the attached folder, or obeys `CLAUDE_CODE_DISABLE_AUTO_MEMORY`: the tests run only a fake provider (the tool spec lists the native proof still needed).
- The plugin's real argument forms on every launch path.
- The real registry or the real notebook home: no test reads either.
