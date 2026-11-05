# Technical Specification: test_rotate.py

Tool: `ops/lib/scripts/rotate.py` (`SCRIPT-04`).
Test: `tools/test/test_rotate.py` (`TEST-47`). Writer: Joe Codex.
Status: synthetic first-slice proof; independent review pending.

## First Principles Rationale

The guided runner must stop where its implementation stops. A successful
metadata or mind gate must never become permission to create, install or
launch a successor. The assigned W6 slice implements only phases 0 to 2.

## Mechanics and Sequencing

Run the 45 tests with the configured interpreter and `-I -B tools/test/test_rotate.py` under
umask 0002, 0022 and 0077. Every fixture lives in its own private temporary
room under this clone's `var/tmp/`; cleanup removes only that fixture.
Registries, gauge rows, closeout state, handoffs, approvals and mind entries
are invented. Fixture minds use the actual mind serializer and verifier.

The suite checks each implemented stop and each unsupported phase, with
no implicit advancement. It covers shared gauge/pressure validation,
unrounded due boundaries, age/provenance, exact session/key/band evidence,
writer separation, unique registry bindings, hash-bound closing records,
mind proposal disposition and retained approval, actual show --ref,
current leaf binding, interrupted retry, idempotence and late input change.
Tree snapshots check bytes, modes, inodes and mtimes rather than atime.

Refusal cases include missing/corrupt/duplicate/oversized JSON, bad or
archived/compacted counters, numeric booleans, changed evidence, unproved
closing/mind state, bad private modes, absolute/traversing/body paths,
symlinked files/parents/leaves, hardlinks and FIFOs. The tool's subprocess
entrypoint is forbidden during in-process tests; harmless CLI process
smokes invoke only the Python tool itself and its help. No provider,
notifier, launcher, custody command or real body is available to the tests.

## Anecdotal Anchor

The 2026-11-05 W6 assignment separates an executable dry-run preflight from
the still-unbuilt install/native-load workflow. The original rotate spec
and existing builders remain ingredients, not evidence of that workflow.

## Integrity Filter Warnings

Passing synthetic gates proves no real resident closed, no operator typed
an approval, no card reached native context and no provider loaded a body.
The fixture marker is a declaration, not hostile same-user confinement.
Phases 3 to 9, persistent recovery, custody, verified swap, rollback,
native append, first gauge and operator acceptance remain unimplemented.
Claudio independently reviews the frozen source; JoJo integrates it.
