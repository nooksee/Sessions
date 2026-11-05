# Technical Specification: test_rotate.py

Tool: `ops/lib/scripts/rotate.py` (`SCRIPT-04`).
Test: `tools/test/test_rotate.py` (`TEST-48`). Writer: Joe Codex.
Status: first slice integrated as PR #18. Second-slice synthetic source proof,
independent review pending; no native rotation or load claim.

## First Principles Rationale

The guided runner must stop where its implementation stops. A successful
metadata or mind gate must never become permission to install or launch a
successor. The W6 slices implement synthetic phases 0 to 5; only phase 5
constructs temporary fixture artifacts, removed before it returns.

## Mechanics and Sequencing

Run the tests with the configured interpreter and `-I -B tools/test/test_rotate.py` under
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
The second slice adds a bound spare/build plan, explicit unowned/fresh
metadata, process-observability refusal, a held-open private fixture file,
actual gauge extraction from invented Claude rows, an exact summary and
ordinary-user cut with a substantive reply, supplied wake-estimate provenance,
and actual successor/media construction. Every static predicate has negative
fixtures; gate results are real execution results, not constant success slots.
Tree snapshots check bytes, modes, inodes and mtimes rather than atime.

Refusal cases include missing/corrupt/duplicate/oversized JSON, bad or
archived/compacted counters, numeric booleans, changed evidence, unproved
closing/mind state, bad private modes, absolute/traversing/body paths,
symlinked files/parents/leaves, hardlinks and FIFOs. The tool's subprocess
entrypoint is forbidden during in-process tests; harmless CLI process
smokes invoke only the Python tool itself and its help. No provider,
notifier, launcher, custody command or real body is available to the tests.
Process fixtures model observable holders; one bounded smoke inspects only
the test process's descriptor for a synthetic file. Host-wide process
clearance is not inferred from that model. Temporary artifact privacy and
cleanup are checked after success, refusal, ordinary interruption and retry.
A pre-existing interrupted-stage directory remains untouched and blocks.
Codex build refusal is explicit because the accepted ingredient omits its
native compaction summary. No provider-parity claim follows.

## Anecdotal Anchor

The 2026-11-05 W6 assignment separates an executable dry-run preflight from
the still-unbuilt install/native-load workflow. The original rotate spec
and existing builders remain ingredients, not evidence of that workflow.

## Integrity Filter Warnings

Passing synthetic gates proves no real resident closed, no operator typed
an approval, no card reached native context and no provider loaded a body.
The fixture marker is a declaration, not hostile same-user confinement.
Phases 6 to 9, persistent recovery, custody, verified swap, rollback,
native append, first gauge and operator acceptance remain unimplemented.
The gate's 20-percent bound checks a hash-bound supplied wake estimate; it
does not implement a tokenizer or claim a measured native wake. Media files
and candidate bytes exist only while the synthetic build is being gated,
not as a durable custody package. A killed process's residual is never adopted.
Claudio independently reviews the frozen source; JoJo integrates it.
