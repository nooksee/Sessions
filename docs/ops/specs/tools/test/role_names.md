# Technical Specification: tools/test/test_role_names.py

Test file: `Sessions/tools/test/test_role_names.py`. Tool under test: none; the suite reads the tree itself. Registry entry: `docs/ops/registry/test.md` (`TEST-57`). Spec writer: the operator's outside writer (an outside Claude, not a resident), 2026-11-13, on the operator's direction. Status: 10 tests (measured 2026-11-13: 10 run at umask 0002, 0022 and 0077, in under 1 second).

## Purpose
Keep three role names out of the tree. The room's roles once carried three other names. The amendment that renamed the roles took those names out of the policy, the tools, the tests and the documents in one packet. This suite is what keeps them out: the required check runs it, so a change that brings one back does not land.

## Invocation
- Command, from the room root: `python3 -I -B tools/test/test_role_names.py`
- Required flags: none. Positional arguments: none (standard `unittest` arguments are accepted).
- Expected exit behavior: `0` when every test passes; `1` when any fails or errors.

## Inputs
- Every file git tracks or would add in the tree under test: `git ls-files` with the untracked files that are not ignored, so that a new file is read in a packet's worktree before it is committed. A tree without `.git` is walked, so a checkout and an export read alike. A failing git stops the test.
- `RoR.md` and everything under `archives/` are not read. A record is never rewritten (PoT 1.2.13), and a record keeps the names its event used (CONSTRAINTS C04).
- The names, as SHA-256 digests in the suite's own tables and never as text: a literal would be a hit on itself.
- Temporary trees with invented names, for the proofs of the cutting, the two rules and the two file routes.

## Outputs
- Writes only inside its own temporary directories, removed after each test.
- A failure prints a path and a line number, never the line. A hit in a file's own path is line 0.

## Invariants and failure modes

**The tree (4).** No file outside the records holds one of the names, in its text or in its own path; the list read is the tree, which is proved by five files that must be in it. The ledger still holds each of the three, which proves that the digests still match their names: a table that matched nothing would pass the first test and fail this one. The tables hold six distinct digests and no text, and the suite's own file is clean by its own rule. The ledger, the archives and bytecode folders are not read, and nothing else is spared.

**The rules, on invented names (3).** A line is cut into runs of letters and a whole run is compared, so a name is seen beside an apostrophe, a hyphen, an underscore or a digit, alone or as a plural, and is not seen glued inside a longer run. Two of the names are refused in any case of letters. The third is also the provider's own word for the author of a reply, which the transcript tools must use; it is refused only when it begins with a capital and continues in small letters, so its small and all-capital forms pass.

**The file routes (3).** In a temporary tree a planted line is found by path and line number through the walk and through git, and so is a file whose own name holds the name; through git a file not yet tracked is read, an ignored file is not, and a file deleted from the tree is passed over; a link is not followed, and a record is not read by either route. A tree whose `.git` is not a repository stops the test.

## What the suite does not prove
That a name built at run time, glued inside a longer run of letters, or written in another alphabet is absent. That the registry, a mind, a handoff or a body is free of the names: those are not tracked, and each has its own writer. That a record is free of them: the records keep them on purpose.
