# Technical Specification: test_rotate.py

Tool: `ops/lib/scripts/rotate.py` (`SCRIPT-04`).
Test: `tools/test/test_rotate.py` (`TEST-48`). Writer: Joe Codex.
Status: synthetic phases 0 to 9 implemented, dry-run only. No native rotation,
persistent recovery or provider-load claim.

## First Principles Rationale

The guided runner must stop where its implementation stops. A successful
metadata or mind gate must never become permission to install or launch a
successor. The accepted first two W6 slices implement synthetic phases 0 to 5.
The third slice adds disposable phases 6 to 9, not a native adapter or an
accepted real rotation.
Temporary fixture artifacts are removed before return in every write phase.

## Mechanics and Sequencing

Run the tests with the configured interpreter and `-I -B tools/test/test_rotate.py` under
umask 0002, 0022 and 0077. Every fixture lives in its own private temporary
room under this clone's `var/tmp/`; cleanup removes only that fixture.
Registries, gauge rows, closeout state, handoffs, approvals and mind entries
are invented. Fixture minds use the actual mind serializer and verifier.

The suite checks each implemented stop and each later phase's evidence refusal, with
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

The suite has 222 tests: the first two slices' 115 (92 plus 23
distinct C1 tests from the section 276 gap table) and 107 third-slice tests.
The original C1 tests are paired with one single-clause or
property omission in the author's retained mutation table, not a whole
require-call skip. The new test names identify those exact cases:

| Gap | Test method, with the common test_c1_ prefix |
| --- | --- |
| Capsule mind from actual show --ref leaf | capsule_mind_is_verbatim_actual_show_ref_leaf |
| First turn and four-part order | capsule_first_turn_and_four_part_order |
| Staging inside the synthetic room before creation | staging_is_created_inside_the_synthetic_room |
| Required, hash-bound and recorded cut reason | cut_reason_is_required_hash_bound_and_recorded |
| Last of two boundaries | window_uses_the_last_of_two_boundaries |
| Exactly one summary | two_summaries_are_not_exactly_one |
| Estimate schema | estimate_schema_is_checked_independently |
| Estimate donor digest | estimate_binds_the_exact_donor_hash |
| Estimate cut row | estimate_binds_the_selected_cut |
| Estimate model window | estimate_window_matches_the_reading |
| Nonblank estimate method | estimate_method_cannot_be_blank |
| Metadata prompt exclusion | metadata_user_row_is_not_a_prompt |
| Sidechain prompt exclusion | sidechain_user_row_is_not_a_prompt |
| Summary prompt exclusion | summary_user_row_is_not_a_prompt |
| Nonempty tool-result prompt exclusion | nonempty_tool_result_is_not_a_prompt |
| Empty prompt exclusion | empty_user_content_is_not_a_prompt |
| Injected prompt exclusion | injected_user_content_is_not_a_prompt |
| Cut-start prompt independently checked | cut_start_must_itself_be_a_user_prompt |
| Exchange prompt independently checked | exchange_row_must_itself_be_a_user_prompt |
| Cut/exchange ordering | exchange_cannot_precede_the_selected_cut |
| Plan bound to closing-record digest | build_plan_binds_the_closing_record_hash |
| Exact identity on every row | every_row_needs_the_exact_session_identity |
| No build object after a late refusal | late_failure_never_leaks_a_completed_build_object |

Refusal cases include missing/corrupt/duplicate/oversized JSON, bad or
archived/compacted counters, numeric booleans, changed evidence, unproved
closing/mind state, bad private modes, absolute/traversing/body paths,
symlinked files/parents/leaves, hardlinks and FIFOs. The tool's subprocess
entrypoint is forbidden during first/second-slice in-process tests; harmless CLI process
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
Native phases 6 to 9, persistent recovery, physical custody, production swap
and rollback, native append, first native gauge and real operator acceptance
remain unimplemented.
The gate's 20-percent bound checks a hash-bound supplied wake estimate; it
does not implement a tokenizer or claim a measured native wake. Media files
and candidate bytes exist only during the synthetic invocation, including
later model phases, not as durable custody. A killed process's residual is never adopted.
The Auditor independently reviews the frozen source; the Apprentice integrates it.

## Third-slice coverage and limits

The 107 third-slice tests comprise 95 install/recovery cases and 12 focused private
staging/swap cases. Each stop is tested with later evidence absent where it
must not be read. Inputs are snapshotted before/after; only temporary runtime
and custody copies may change. No host process table is read in phases 6 to 9;
their explicit process model is mandatory.

The review follow-up adds nine test methods and strengthens the existing
swap, seed-owner, wake-claim, receipt-authority and staging checks. It covers
equivalent relative holder spellings in both model lists; custody root and
member privacy after creation; custody rereading before rollback; unchanged
other registry rows; the post-append six-way check; the phase-8 stop with
close-only fields absent; and input checks before swap and close. Call and
unlink observations distinguish refusal before an act from refusal after it.
The equal serve/go timestamp boundary is allowed and tested explicitly.

Coverage includes two directly read custody roots and all manifest members;
wrong inventory, manifests and bytes; exact preimages and spare work hidden
behind fresh metadata; post-custody go and each target field; six independent
join predicates, including body cwd versus binding root; `.NEW` without a
registry switch or run-ahead; staging/postimages and accepted uid/gid;
stale/replaced targets, links and hardlinks; failure before/after publication,
declined go/load/recognition, interruption, hold reassertion/readback,
absent-donor go and conflicting newer bytes. Named refusals and final safety
outcomes are checked. Overlapping guards use isolated synthetic metadata or
dependency faults where needed.

Append cases bind every identity, role, parent and tool pair. Wake tokens,
model and time come from the existing reader and match a separately validated
snapshot; estimate, reading and recognition stay separate. The receipt test
invokes only the fixed existing Bash template command with a minimal
environment, verifies the actual form and measured fields, and checks that
only the disposable donor entry is unlinked after custody. No provider,
notifier, launcher, host store or real custody command is available.

The retained author mutation table replaces single Boolean clauses, expected
mapping fields and named workflow acts in disposable in-memory source
modules; it never edits frozen source. Each row names its mutation, original
clause, selected tests, failures/errors and source digest. Baseline and final
unmutated tests must pass. Results and survivors are reported, not inferred
from a whole-require count. A staging mutant is checked before it can create
any directory outside its synthetic room.

This proves model swaps, model recovery and fixture recognition, not physical
drive independence, native load/append, semantic identity readback, operator
authorship, durable recovery or a real rotation. The model's `.NEW` does not
survive return; no later invocation adopts it. The existing rotate-spare/1
and rotate-estimate/1 schemas remain unchanged.
