# Technical Specification: test_rounds.py

Test: `Sessions/tools/test/test_rounds.py`. Tool: `ops/lib/scripts/rounds.sh`.
Status: three static/syntax checks; the wrapper is never executed.

## Purpose

Ensure the shell entry point remains present and syntactically valid, and
pin local reporting and absence of any external drift dependency.

## Invocation

Run `python3 -I -B tools/test/test_rounds.py` from the Sessions root.

## Inputs and Outputs

The suite reads the tracked wrapper bytes and runs `bash -n`. It does not
invoke collectors, notifications, the drift detector, any service, or any
session-body reader. It writes no files.

## Invariants and Failure Modes

1. The wrapper exists.
2. Bash accepts its syntax.
3. The wrapper retains local collectors and reporting, contains no drift
   detector or state, and exits on patient health alone.

## Not Covered

Runtime behavior, host paths, timers, notification behavior, or live health
data. Those require a separately authorized synthetic or operational test.
