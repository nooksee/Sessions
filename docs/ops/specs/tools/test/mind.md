# Technical Specification: tools/test/test_mind.py

Test file: `Sessions/tools/test/test_mind.py`. Tool under test: `Sessions/ops/lib/scripts/mind.py`. Tool spec: `docs/ops/specs/scripts/mind.md`. Registry entry: `docs/ops/registry/test.md` (`TEST-02`). Status: 47 tests (measured 2026-11-09: 47 run, 1 skipped as root, at umask 0002, 0022 and 0077).

## Purpose
Prove, in synthetic rooms only, that the mind is pointer first, holds concepts only, stays bounded, flows without approvals, keeps every leaf immutable and audited by its ledger line, and stays out of Git.

## Invocation
- Command, from the room root: `python3 -I -B tools/test/test_mind.py`
- Required flags: none. Positional arguments: none (standard `unittest` arguments are accepted).
- Expected exit behavior: `0` when every test passes; `1` when any fails or errors.
- Reviewers also run it at umask 0002, 0022 and 0077.

## Inputs
- `ops/lib/scripts/mind.py`, both imported and run as a subprocess with `python3 -I -B`.
- A fresh temporary room per test (`Room`): a registry with two keys (`session-doctor`, `claudine-colbert`) whose session ids are an invented UUID, leaf bodies written beside the room, and a clock that advances one minute per command.
- No real room, registry, mind or body is read or written.

## Outputs
- Writes only inside its own temporary directory, removed after each test.
- Exit codes the tests assert on the tool: `0` success, `1` a failed `check`, `2` a refusal.

## Invariants and failure modes

**The loop (6).** An empty room checks clean and shows nothing; add, show, read and check round trip; the index holds pointers only and the leaf carries its id, agent, time, title and supersedes line in canonical form; ids count up within a day across the room and are never reused; the ledger records each add and retire with the leaf's hash and size; a body can come from standard input.

**Concepts only (5).** Each kind the screen refuses is refused, by name and without echoing the text, and nothing is written; the title is screened too; abstractions, clause references and single digits pass; the limits hold at 100 and 2,000 characters and an empty body or a control character is refused; a full index refuses a new leaf but a superseding leaf still flows.

**Ownership and authority (5).** A superseding leaf takes the old line's place and the old leaf is no longer served; a resident cannot retire or supersede another's leaf; only a key registered exactly once to this room writes; no approval option exists and the chain commands (`preview`, `write`, `history`) are gone; retire takes the pointer out and keeps the leaf.

**Integrity (10).** A changed leaf fails the check and blocks `show` and `read` until its owner retires it; a hand-written index line is refused; an index line with no ledger record fails; the retired chain format is refused for writes and reads with a custody instruction; a leaf that fails a tightened screen is reported, not blocking; strays are reported; every file is 0600 and every directory 0700 even at umask 0; no output carries a session identifier; reading runs no Git and `check` does; the index, the leaves and the ledger stay out of Git, and `check` fails when the ignore rule is removed.

**The Git check fails closed (9).** No Git on the path, a Git that does not answer, a `check-ignore` that does not answer, a broken repository, a broken inner repository under a valid parent, and a broken nearest ancestor are each refusals; a valid nearer repository and a valid worktree allow ignored writes; only Git's positive answer passes.

**The legacy-state guard (4).** `ops/lib/statepaths.py` proves `storage/mind.lock` absent without creating or changing anything, refuses an existing node, refuses escaping paths before inspection, and treats a metadata error as not absent.

**The lock location (8).** A fresh write uses only the private `logs/mind.lock`; every kind of legacy lock node, an unsafe or unsearchable legacy parent, and a live legacy lock each block writes without being changed; a fresh process holds the exact shared lock inode; a reviewed relocation keeps the inode; a legacy lock does not block `check` or `show`.
