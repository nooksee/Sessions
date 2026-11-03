# Technical Specification: test_rounds.py

Test: `Sessions/tools/test/test_rounds.py`. Tool: `ops/lib/scripts/rounds.sh`.
Status: three static/syntax checks; the wrapper is never executed.

## Purpose

Ensure the shell entry point remains present and syntactically valid, and
bind the preserved resident-center drift block to its registered text.

## Invocation

Run `python3 -I -B tools/test/test_rounds.py` from the Sessions root.

## Inputs and Outputs

The suite reads the tracked wrapper bytes and runs `bash -n`. It does not
invoke collectors, notifications, the drift detector, any service, or any
session-body reader. It writes no files.

## Invariants and Failure Modes

1. The wrapper exists.
2. Bash accepts its syntax.
3. The registered 6,489-byte drift suffix contains the detector and explicit
   fault handling and matches the expected 16-hex digest prefix.

## Not Covered

Runtime behavior, host paths, timers, notification behavior, or live health
data. Those require a separately authorized synthetic or operational test.
