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

# ---------------------------------------------------------------------------
# Resident Center source drift — a SEPARATE signal.
#
# This is not patient health. It says nothing about any session, it never
# enters clinic-aggregate.json, and it keeps its own private state so the two
# signals cannot mask one another. It answers one question: has the frozen
# Sessions runtime custody diverged from the product repository that now holds
# source authority?
#
# Edge-triggered like the Clinic: it notifies on a state transition and then
# stays quiet. product-ahead is normal, because the source authority advancing
# is the expected direction of travel. Donor mutation, both sides changing, and
# a blocked comparison are critical. It repairs nothing.
# ---------------------------------------------------------------------------
# The detector's exit status is evidence, not noise. A crash, a truncated
# summary, or a missing field means the comparison did not happen, and a
# comparison that did not happen is not an "aligned" result. Every one of those
# is forced to critical here rather than defaulting quietly to normal.
DRIFT_OUT="$("$PY" "/media/nos4r2/user_vol/Sessions/Scripts/check_resident_center_drift.py" --write-state --quiet 2>&1)"
DRIFT_RC=$?
DRIFT_STATE="$(printf '%s\n' "$DRIFT_OUT" | grep -oE '\bSTATE=[a-z-]+' | tail -1 | cut -d= -f2)"
DRIFT_SEV="$(printf '%s\n' "$DRIFT_OUT" | grep -oE '\bSEVERITY=[a-z]+' | tail -1 | cut -d= -f2)"
DRIFT_ALERT="$(printf '%s\n' "$DRIFT_OUT" | grep -oE '\bSHOULD_ALERT=[01]' | tail -1 | cut -d= -f2)"

DRIFT_FAULT=""
case "$DRIFT_RC" in
  0|1|2) : ;;
  *) DRIFT_FAULT="detector exited $DRIFT_RC, outside the contracted 0, 1, or 2" ;;
esac
if [ -z "$DRIFT_STATE" ] || [ -z "$DRIFT_SEV" ] || [ -z "$DRIFT_ALERT" ]; then
  DRIFT_FAULT="${DRIFT_FAULT:+$DRIFT_FAULT; }detector summary missing STATE, SEVERITY, or SHOULD_ALERT"
fi
# The full tuple is contracted, not just the exit code. Each state implies one
# severity, and an alert may only be 0 or 1; anything else means the detector
# and the wrapper disagree about what happened, and a disagreement is not a
# result. aligned additionally must never request an alert.
if [ -z "$DRIFT_FAULT" ]; then
  case "$DRIFT_ALERT" in 0|1) : ;; *) DRIFT_FAULT="SHOULD_ALERT='$DRIFT_ALERT' is not 0 or 1" ;; esac
fi
if [ -z "$DRIFT_FAULT" ]; then
  case "$DRIFT_RC:$DRIFT_STATE:$DRIFT_SEV" in
    0:aligned:normal)          [ "$DRIFT_ALERT" = "0" ] || DRIFT_FAULT="aligned requested an alert" ;;
    # Added 2026-09-08. A registered convergence is a completed,
    # operator-authorized path transition: the live donor and the accepted
    # product ref both hold the exact registered target hash, mode, and
    # size. It exits 0 like aligned because nothing is outstanding, but it
    # stays a distinct state because the frozen tree genuinely no longer
    # matches RC-1 and a reader must be able to see that. Unlike aligned it
    # may alert once, on the transition itself.
    0:registered-converged:normal) : ;;
    1:product-ahead:normal)    : ;;
    1:donor-mutated:critical)  : ;;
    1:both-changed:critical)   : ;;
    2:blocked:critical)        : ;;
    *) DRIFT_FAULT="contradictory detector tuple rc=$DRIFT_RC state='$DRIFT_STATE' severity='$DRIFT_SEV'" ;;
  esac
fi

if [ -n "$DRIFT_FAULT" ]; then
  DRIFT_STATE="blocked"; DRIFT_SEV="critical"; DRIFT_ALERT=1
  echo "$STAMP | resident-center drift: DETECTOR FAULT — $DRIFT_FAULT" >> "$LOG"
  printf '%s\n' "$DRIFT_OUT" | tail -20 | sed 's/^/    /' >> "$LOG"
  # Replace the state file. A fault leaves whatever the last successful run
  # wrote, and a stale "aligned" is exactly the reassurance nobody should get
  # from a detector that just failed.
  "$PY" - "/media/nos4r2/user_vol/Sessions/Evidence" "$DRIFT_FAULT" "$DRIFT_RC" <<'FAULT'
import json, os, sys, tempfile, datetime as dt
evid, fault, rc = sys.argv[1], sys.argv[2], sys.argv[3]
now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
payload = {"schema_version": 2, "signal": "resident-center-source-drift",
           "generated_at": now, "state": "blocked", "severity": "critical",
           "blocked_reason": f"detector fault: {fault}", "detector_exit_status": int(rc)
           if rc.lstrip('-').isdigit() else rc,
           "evidence_is_detector_fault": True, "findings": [], "counts": {},
           "convergence": [], "repairs_performed": 0}
for name, body in (("resident-center-drift-state.json", payload),
                   ("resident-center-drift-alert-state.json",
                    {"state": "blocked", "severity": "critical", "generated_at": now})):
    target = os.path.join(evid, name)
    fh = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=evid,
                                     prefix="." + name + ".", delete=False)
    json.dump(body, fh, indent=2, sort_keys=True); fh.write("\n")
    fh.flush(); os.fsync(fh.fileno()); fh.close()
    os.replace(fh.name, target)
FAULT
fi

echo "$STAMP | resident-center drift: ${DRIFT_STATE:-unknown} (${DRIFT_SEV:-unknown}) rc=${DRIFT_RC}" >> "$LOG"

if [ "${DRIFT_ALERT:-0}" = "1" ]; then
  if [ "${DRIFT_SEV:-normal}" = "critical" ]; then
    notify -u critical "📦 Resident Center: source drift" \
      "State ${DRIFT_STATE}. The frozen Sessions runtime and the product source authority disagree. See Sessions/Evidence/resident-center-drift-state.json"
  elif [ "${DRIFT_STATE:-}" = "registered-converged" ]; then
    # A completed registered convergence has both sides equal at the
    # registered target; "product ahead" would be false (PR #64 review).
    notify -u normal "📦 Resident Center: registered convergence complete" \
      "The registered transition is complete: the frozen Sessions runtime and the product source authority both hold the registered target. Nothing is outstanding. See Sessions/Evidence/resident-center-drift-state.json"
  elif [ "${DRIFT_STATE:-}" = "product-ahead" ]; then
    notify -u normal "📦 Resident Center: product ahead" \
      "The product repository has advanced beyond the frozen Sessions runtime. See Sessions/Evidence/resident-center-drift-state.json"
  else
    notify -u normal "📦 Resident Center: drift state ${DRIFT_STATE:-unknown}" \
      "See Sessions/Evidence/resident-center-drift-state.json"
  fi
fi

DRIFT_CRITICAL=0
[ "${DRIFT_SEV:-normal}" = "critical" ] && DRIFT_CRITICAL=1

# Either signal failing loudly fails the run; neither is folded into the other.
if [ "${ANY_CRITICAL:-0}" = "1" ] || [ "$DRIFT_CRITICAL" = "1" ]; then
  exit 2
fi
exit 0
