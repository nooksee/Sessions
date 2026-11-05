# Technical Specification: test_claude_resident.py

Tool: `ops/bin/claude-resident`. Test: `tools/test/test_claude_resident.py`.
Writer: Claudine Colbert. Registry entry: `docs/ops/registry/test.md` (`TEST-47`).
Scope: synthetic registries, rooms and notebooks only; the provider is never executed.

## Purpose and invocation

Prove, on synthetic data, that the wrapper's dry run reaches each of six branches (the design's five, with a registered row split into this room and another room), attaches a notebook only for a registered row of this room, passes a registered row of another room through untouched, turns auto memory off in every other outcome, never blocks a launch, never executes anything and never prints a registry value.

Run from the room root: `python3 -I -B tools/test/test_claude_resident.py`. Exit 0 when all 12 tests pass (one skips if `git` is not installed); 1 on any failure. Reviewers also run it at umask 0002, 0022 and 0077.

Each test builds a room with a registry at 0600 holding four rows (two Claude rows of this room, one Codex row, one Claude row of another room), each with an invented zero-block session, and one notebook folder at 0700 with a `MEMORY.md` at 0600 for the first key only. The wrapper runs as a subprocess with `python3 -I -B`, once directly through its interpreter line, and once in process for the error path.

## Proofs

Every run is checked for: exit 0 and an empty standard error; `mode` `dry-run` and `executed` false; `argv` equal to `<provider>` followed by the given arguments exactly; and no key, person, role, note or room of any row in the output, with a session present only as often as the arguments carry it.

1. `test_registered_attaches_the_notebook`: `--resume <id>`, `--resume=<id>`, `-r <id>`, `--session-id <id>`, `--session-id=<id>` and the same session named twice each attach the notebook, add no environment change, mark the route unproven and list five unproven items.
2. `test_registered_without_a_usable_notebook_attaches_nothing`: a registered key of this room with no folder, a folder not 0700, an index not 0600, an index holding another key's projection marker, a malformed marker and a linked folder each give the registered branch with nothing attached and auto memory off.
3. `test_registered_elsewhere_passes_through_untouched`: a session held by one Claude row of another room gives the registered-elsewhere branch: no notebook, no environment change, no route, auto memory unchanged; a usable folder of that key in this room's home changes nothing.
4. `test_registered_needs_positive_git_exclusion`: inside a Git work tree that does not ignore the home, nothing is attached; once ignored, the notebook is attached. Skips if `git` is absent.
5. `test_unregistered_turns_auto_memory_off`: an unknown session, and a session held only by a Codex row.
6. `test_ambiguous_turns_auto_memory_off`: two different sessions in the arguments, and two Claude rows holding one session.
7. `test_new_turns_auto_memory_off`: no arguments, a prompt alone, `--continue`, `-c`, `--resume` with no value, `--resume` followed by a flag, `--fork-session`, and a session flag after the provider's own `--`.
8. `test_broken_registry_turns_auto_memory_off`: an absent registry, mode 0644, invalid JSON, a duplicate key, a row with an empty session, a key that is not a plain key, a linked registry and an identities value that is not a list; each also for a run that names no session.
9. `test_only_dry_run_and_nothing_is_executed`: with a fake `claude` first on `PATH` that would leave a marker, two dry runs leave none; no arguments, no `--dry-run`, no `--`, a wrapper option without its value, an unknown wrapper option and another mode are each refused with exit 2, empty standard output, the usage line and no session echoed.
10. `test_the_wrapper_runs_directly`: the file is executable and its interpreter line runs it.
11. `test_an_explicit_registry_path_is_read`: `--registry` selects the registry read.
12. `test_an_unexpected_error_fails_closed_without_blocking`: in process, a failure while deciding gives the error outcome with auto memory off, exit 0 and the arguments still passed through.

**Mutation check, 2026-11-05.** Each guard was disabled in turn (25 mutations: `--dry-run` only, the `--` separator, unknown wrapper options, the session value, `--fork-session`, the provider's own `--`, two sessions named, Claude rows only, no match, several matches, the room, the registered-elsewhere run left untouched, the folder's private path, its Git rule, its markers, the registry's absence, regular file, mode, duplicate keys, row fields, plain keys and identities list, the auto-memory switch, the error path, and the key kept out of reasons); the suite caught 25 of 25.

## Not proved

- That any provider loads the attached folder, or obeys `CLAUDE_CODE_DISABLE_AUTO_MEMORY`: the wrapper prints its decision and executes nothing (the tool spec lists the native proof still needed).
- The plugin's real argument forms on every launch path.
- The real registry or the real notebook home: no test reads either.
