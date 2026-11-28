# Technical Specification: rounds

Script: `ops/lib/scripts/rounds.sh`. Tests: `tools/test/test_rounds.py`.
The room-owned wrapper collects Codex and Claude reports and writes its consolidated report and log.

## Mechanics and Sequencing

Resolve the room from the script location. Run telemetry.py and vitals.py, preserve both reports, then pass them to alerts.py. Append the summary and diff to the clinic log. Notify only on a new or worsened condition. Exit 2 for critical patient health, otherwise 0. SESSION_ROUNDS_NOTIFY=0 suppresses notifications for tests.

## Boundaries

No external detector is invoked and no drift state is written. The operator ended that binding in DP-SES-0024. This specification authorizes no service, timer or host change.
