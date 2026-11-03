# Technical Specification: rounds

Script: `Sessions/ops/lib/scripts/rounds.sh`, a Bash wrapper. Test:
`tools/test/test_rounds.py`. Status: the scheduled clinic-rounds wrapper
collects the Codex and Claude reports, writes the consolidated report/log,
and separately checks Control's resident-center source-drift signal. This
spec records current behavior; it does not authorize service changes.

## First Principles Rationale

The wrapper joins existing read-only health collectors and edge-triggered
alerts. Resident-center source drift is a separate signal, not patient health,
and must not be presented as an aligned result when its detector fails or
returns a contradictory status tuple.

## Mechanics and Sequencing

1. Resolve the Sessions root from this script's location and use its private
   `logs/` directory. Run `telemetry.py` and `vitals.py`; preserve their output
   in the consolidated report.
2. Pass both collector outputs to `alerts.py`, append the summary and diff to
   the clinic log, and notify only on a new or worsened condition.
3. Run Control's registered drift detector independently. Accept only the
   contracted exit/state/severity/alert combinations. A missing or malformed
   summary is a critical detector fault, not success.
4. On detector fault, replace the drift-state records with explicit blocked
   evidence and log the bounded detector output. Do not repair either source.
5. Notifications can be disabled for synthetic tests with
   `SESSION_ROUNDS_NOTIFY=0`; production scheduling remains a Control-owned
   deployment surface.

## Anecdotal Anchor

The detector can fail while old state still says `aligned`. The wrapper
therefore converts missing fields, unexpected exit statuses, and contradictory
tuples to a fresh `blocked` state rather than leaving stale reassurance.

## Integrity Filter Warnings

- The script writes health output under `logs/` and is not a read-only process
  with respect to those artifacts.
- The drift detector is an external Control-owned dependency; do not copy it,
  mutate it, or infer its status when invocation fails.
- This spec describes code behavior only. It does not authorize wiring,
  timers, notifications, or service changes.
