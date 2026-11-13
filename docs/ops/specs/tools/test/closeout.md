# Technical Specification: test_closeout.py

Test: `Sessions/tools/test/test_closeout.py`. Tool:
`ops/lib/scripts/closeout.py`. Status: synthetic hook behavior suite; no live
body, registry, settings file, notification, or service is used.

## Purpose

Prove closeout's token reserve, current-reading behavior, session ownership,
failure handling, privacy, idempotency, and card rendering without operating
on a real resident.

## Invocation

Run `python3 -I -B tools/test/test_closeout.py` from the Sessions root.

## Inputs and Outputs

Each test creates synthetic provider bodies, a registry, window data, state,
and card template in a private temporary directory. The hook input is piped
to the tool as standard input. The suite asserts JSON context, silence, logs,
and exit behavior; the temporary directory is removed by the test fixture.

## Invariants and Failure Modes

Coverage includes the 50,000-token reserve across windows; repeated bands and
re-arming; current readings after compaction; own-transcript and registered
session gates; exit-zero failure behavior; unknown windows and notifications;
template refusal and substitution; malformed inputs and bounded runtime; who
runs a rotation, read from the registry's roles, with the Integrator's own left
to the Contractor the operator assigns and nobody named; and the tool's two
role names, with its words for that Contractor, against clauses 4.1.3 and
4.1.4 of the policy in the tree under test.
The installed hook and native delivery path are outside the suite.

## Not Covered

The suite cannot prove that a live session receives the card, that the operator
receives an actual notification, or that any hook/timer is installed. Those
remain separate deployment gates.
