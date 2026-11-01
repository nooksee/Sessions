#!/usr/bin/env bash
# Clinic rounds — one health pass over EVERY AI session, both wards:
#   - Codex rollouts  (telemetry.py: real token telemetry)
#   - Claude Code JSONLs (vitals.py: bytes + image bloat)
# Writes a consolidated report every run (full history in the log). Desktop
# notifications are EDGE-TRIGGERED via alerts.py: only a NEW flag
# or a WORSENED verdict pops a notification. A chronic, unchanged condition
# (e.g. a thread that is reviewed and accepted as "rotate-soon" forever)
# alerted once and then goes quiet — it does not re-notify every 15 minutes.
#
# Read-only against session files. Run by session-health-rounds.timer every
# 15 minutes, or by hand.
set -u

# The room is resolved from this file's own place, as gauge.py does:
# ops/lib/scripts/ sits three levels below the room, and logs/ is beside ops/.
SCRIPTS="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
EVID="$(cd "$SCRIPTS/../../.." && pwd)/logs"
PY="/usr/bin/python3"
STAMP="$(date '+%Y-%m-%d %H:%M:%S %Z')"
REPORT="$EVID/clinic-rounds-latest.txt"
LOG="$EVID/clinic-rounds.log"
CODEX_TXT="$EVID/.clinic-codex-raw.txt"
CLAUDE_TXT="$EVID/.clinic-claude-raw.txt"


# Desktop notifications are suppressed when SESSION_ROUNDS_NOTIFY=0. Tests
# exercise the fault paths repeatedly, and those paths are deliberately
# critical, so without this the suite fires a critical popup per case straight
# at the operator. A test that shouts at the person running it is a test that
# gets deleted.
notify() {
  [ "${SESSION_ROUNDS_NOTIFY:-1}" = "0" ] && return 0
  notify-send "$@" 2>/dev/null || true
}

mkdir -p "$EVID"

"$PY" "$SCRIPTS/telemetry.py" > "$CODEX_TXT" 2>&1
"$PY" "$SCRIPTS/vitals.py" > "$CLAUDE_TXT" 2>&1

{
  echo "# Clinic Rounds — $STAMP"
  echo
  echo "===== CODEX WARD ====="
  cat "$CODEX_TXT"
  echo
  echo "===== CLAUDE WARD ====="
  cat "$CLAUDE_TXT"
} > "$REPORT" 2>&1

DIFF_OUT="$("$PY" "$SCRIPTS/alerts.py" "$CODEX_TXT" "$CLAUDE_TXT")"
CHRONIC="$(echo "$DIFF_OUT" | head -1 | grep -oE 'chronic_flagged=[0-9]+' | cut -d= -f2)"
SHOULD_ALERT="$(echo "$DIFF_OUT" | grep -oE 'SHOULD_ALERT=[01]' | cut -d= -f2)"
ANY_CRITICAL="$(echo "$DIFF_OUT" | grep -oE 'ANY_CRITICAL=[01]' | cut -d= -f2)"

SUMMARY="clinic rounds: ${CHRONIC:-0} flagged (chronic+new), alert=${SHOULD_ALERT:-0}"
echo "$STAMP | $SUMMARY" >> "$LOG"
echo "$DIFF_OUT" | sed 's/^/    /' >> "$LOG"

# The popup speaks resident names: one SAY line per resident from the diff,
# Role (Person), with helper threads rolled up under their resident. The raw
# NEW and WORSE lines stay in the log as evidence. A diff without SAY lines,
# such as an older stub, falls back to the raw lines and the generic title.
if [ "${SHOULD_ALERT:-0}" = "1" ]; then
  CHANGES="$(echo "$DIFF_OUT" | sed -n 's/^[[:space:]]*SAY: //p')"
  [ -n "$CHANGES" ] || CHANGES="$(echo "$DIFF_OUT" | grep -E '^\s+(NEW|WORSE):' | sed 's/^\s*//')"
  HEADLINE="$(echo "$DIFF_OUT" | sed -n 's/^HEADLINE=//p' | head -1)"
  BODY="$CHANGES
See Sessions/logs/clinic-rounds-latest.txt"
  if [ "${ANY_CRITICAL:-0}" = "1" ]; then
    notify -u critical "🩺 ${HEADLINE:-Session clinic: CRITICAL}" "$BODY"
  else
    notify -u normal "🩺 ${HEADLINE:-Session clinic: new attention needed}" "$BODY"
  fi
fi

# A critical patient signal fails the run.
if [ "${ANY_CRITICAL:-0}" = "1" ]; then
  exit 2
fi
exit 0
