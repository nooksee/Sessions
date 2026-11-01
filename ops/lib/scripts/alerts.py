#!/usr/bin/env python3
"""Edge-triggered alert layer for the clinic rounds report.

The two checker scripts (check_codex_token_health.py,
check_claude_session_health.py) are level-triggered: they report the CURRENT
verdict of every session on every run. Notifying on that raw output every
15 minutes means a chronic, already-reviewed condition (e.g. Addition sitting
at "rotate-soon" because it is 33 MB of real conversation) re-alerts forever.

This script parses both checkers' text reports, diffs each patient's verdict
against the last run (state file), and decides whether a DESKTOP alert is
warranted: only on a NEW flag or WORSENED severity. Unchanged/chronic flags
and improvements are logged but do not pop a notification.

Read-only against session files; only writes its own small state JSON.

Also publishes a small, VERSIONED, identifier-free aggregate
(clinic-aggregate.json) for external consumers (e.g. OSAI's status tray) that
must never retain a patient identifier, path, or title. `clinic-alert-state.json`
is this script's own internal working state (it does contain per-patient
identifiers as dict keys) and is not a stable public contract — external
consumers should read the aggregate instead. See
`Sessions/docs/clinic-aggregate-contract.md` for the schema.
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[3]   # the room, resolved as gauge.py does
STATE_FILE = SESSIONS / "logs" / "clinic-alert-state.json"
# The resident registry names each registered body as "Role (Person)". The
# desktop popup speaks those names; the state keys and the log keep the raw
# patient identifiers, so renaming never makes an old flag look new.
REGISTRY = SESSIONS / "ops" / "etc" / "resident-identities.json"
CODEX_HOME = Path.home() / ".codex"
# Every other root check_codex_token_health.py watches, so a helper flagged
# from there can still be named. The Workbench VM mounts this share.
EXTRA_CODEX_ROOTS = [Path("/media/nos4r2/user_vol/VMs/Shared/Workbench/sessions")]
AGGREGATE_FILE = SESSIONS / "logs" / "clinic-aggregate.json"
AGGREGATE_SCHEMA_VERSION = 1

# Severity order: higher = worse. no-telemetry is informational, not tracked.
SEVERITY = {
    "healthy": 0,
    "rotate-soon": 1,
    "treat-images": 1,
    # A treadmill session is losing history steadily rather than facing an
    # imminent failure. It ranks with rotate-soon: act, but it is not an
    # emergency.
    "compact-treadmill": 1,
    "CRITICAL": 2,
    "CRITICAL-window-exhausted": 2,
    # Retained so state files written before 2026-07-29 still compare cleanly.
    "CRITICAL-compact-treadmill": 2,
}

# Match the trailing session name without counting the columns before it. The
# table gained a carry column on 2026-07-29; a fixed-arity pattern silently
# stops matching every row when that happens, and the alerting goes quiet
# rather than loud.
CODEX_ROW = re.compile(r"^\s*\S+MB\s+.*?\s+(\S+)$")
CODEX_VERDICT = re.compile(r"^\s*verdict:\s*(\S+)")
# The Claude row is anchored on the verdict VOCABULARY, not on a column count.
#
# This pattern was fixed-arity until 2026-09-08 and had been silently wrong
# since 2026-08-05, when check_claude_session_health.py gained a `cmp` column.
# It then bound group(1) to `cmp` and group(2) to carry+verdict+label, so the
# recorded verdict for every Claude resident was a string like "2/5". That is
# not in SEVERITY, so the diff skipped the row entirely: for 34 days the Claude
# ward could not raise a new or worsened flag, and Home Advisor sat at CRITICAL
# without a single alert firing.
#
# The comment directly above CODEX_ROW warned of exactly this failure and
# CODEX_ROW was made arity-tolerant in response. This one was not, and it broke
# at the very next column addition. Counting columns is the defect; matching a
# value that must be a real verdict is the fix, because an unrecognised verdict
# now fails to match loudly instead of matching the wrong field quietly.
CLAUDE_ROW = re.compile(
    r"^\s*\S+MB\s+.*?\s+(" + "|".join(sorted(SEVERITY, key=len, reverse=True)) + r")\s+(\S.*)$"
)


def parse_codex(text: str) -> dict[str, str]:
    out = {}
    pending_name = None
    for line in text.splitlines():
        m = CODEX_ROW.match(line)
        if m:
            pending_name = m.group(1)
            continue
        m = CODEX_VERDICT.match(line)
        if m and pending_name:
            out[f"codex:{pending_name}"] = m.group(1)
            pending_name = None
    return out


def parse_claude(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        m = CLAUDE_ROW.match(line)
        if m:
            verdict, label = m.group(1), m.group(2).strip()
            out[f"claude:{label}"] = verdict
    return out


UUID = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl$")

# Plain words for the popup. The log keeps the verdict vocabulary itself.
PLAIN = {
    "healthy": "healthy",
    "rotate-soon": "needs rotation soon",
    "treat-images": "carrying heavy images",
    "compact-treadmill": "compacting repeatedly",
    "CRITICAL": "critical",
    "CRITICAL-window-exhausted": "critical, context window exhausted",
    "CRITICAL-compact-treadmill": "critical, compacting repeatedly",
}


def load_names(path: Path = None) -> dict[str, str]:
    """Map each registered session id to its "Role (Person)" name."""
    path = path or REGISTRY
    try:
        identities = json.loads(path.read_text())["identities"]
    except (OSError, ValueError, KeyError, TypeError):
        return {}
    names = {}
    for ident in identities:
        try:
            names[ident["session_id"]] = f"{ident['role']} ({ident['person']})"
        except (KeyError, TypeError):
            continue
    return names


def codex_meta(thread_id: str, home: Path = None, extra: list = None,
               _cache: dict = {}) -> dict:
    """First-line session_meta payload of a Codex thread, or {} when absent."""
    home = home or CODEX_HOME
    extra = EXTRA_CODEX_ROOTS if extra is None else extra
    key = (str(home), tuple(str(r) for r in extra), thread_id)
    if key not in _cache:
        meta = {}
        hits = sorted(home.glob(f"sessions/*/*/*/rollout-*-{thread_id}.jsonl"))
        hits += sorted(home.glob(f"archived_sessions/rollout-*-{thread_id}.jsonl"))
        for root in extra:
            if root.is_dir():
                hits += sorted(root.rglob(f"rollout-*-{thread_id}.jsonl"))
        for hit in hits[:1]:
            try:
                with hit.open(encoding="utf-8") as fh:
                    row = json.loads(fh.readline())
                meta = row.get("payload") or {}
            except (OSError, ValueError, AttributeError):
                meta = {}
        _cache[key] = meta if isinstance(meta, dict) else {}
    return _cache[key]


def describe(pid: str, names: dict, home: Path = None,
             extra: list = None) -> tuple[str, str | None]:
    """Name a patient for the popup: (resident name, helper nickname or None).

    A Codex helper thread names its parent in session_meta; parents are
    followed upward until a registered resident is reached. A Claude label
    carries the first 20 characters of the session id after " / ". Anything
    that does not resolve keeps its raw label.
    """
    if pid.startswith("codex:"):
        m = UUID.search(pid)
        if not m:
            return pid, None
        tid, nickname = m.group(1), None
        for _ in range(6):
            if tid in names:
                return names[tid], nickname
            meta = codex_meta(tid, home, extra)
            # Current rollouts carry the spawn record twice: at the payload's
            # top level and nested under source.subagent.thread_spawn, which
            # is the form inventory_worker_threads.py reads. Read either.
            spawn = ((meta.get("source") or {}).get("subagent") or {}).get("thread_spawn") \
                if isinstance(meta.get("source"), dict) else None
            spawn = spawn if isinstance(spawn, dict) else {}
            parent = meta.get("parent_thread_id") or spawn.get("parent_thread_id")
            if not parent:
                break
            if nickname is None:
                nickname = meta.get("agent_nickname") or spawn.get("agent_nickname") or "unnamed"
            tid = parent
        return pid, nickname
    if pid.startswith("claude:") and " / " in pid:
        prefix = pid.rsplit(" / ", 1)[1].strip()
        hits = [sid for sid in names if prefix and sid.startswith(prefix)]
        if len(hits) == 1:
            return names[hits[0]], None
    return pid, None


def build_alert(events: list, names: dict, home: Path = None) -> dict:
    """Decide the popup from (pid, verdict) events.

    Registered bodies always count. Helper threads roll up quietly under their
    resident and pop only when critical, so a resident's busy subagents do not
    page Kevin; every event still reaches the log.
    """
    quiet, critical = 0, False
    own = {}      # resident name -> its own verdicts, in event order
    helpers = {}  # resident name -> {verdict: [nicknames]}
    order = []    # resident names in first-seen order
    for pid, verdict in events:
        name, nickname = describe(pid, names, home)
        severe = SEVERITY.get(verdict, 0) >= 2
        if nickname is not None and not severe:
            quiet += 1
            continue
        if name not in order:
            order.append(name)
        if nickname is None:
            own.setdefault(name, []).append(verdict)
        else:
            helpers.setdefault(name, {}).setdefault(verdict, []).append(nickname)
        critical = critical or severe
    # One line per resident: its own verdicts first, then its helpers grouped
    # by verdict, so a resident and its helpers never repeat the name.
    lines = []
    for name in order:
        parts = [PLAIN.get(v, v) for v in dict.fromkeys(own.get(name, []))]
        for verdict, nicks in helpers.get(name, {}).items():
            label = "helper" if len(nicks) == 1 else "helpers"
            parts.append(f"{label} {', '.join(nicks)} {PLAIN.get(verdict, verdict)}")
        lines.append(f"{name}: {'; '.join(parts)}")
    popped = order
    distinct = list(dict.fromkeys(popped))
    if not distinct:
        headline = ""
    elif len(distinct) == 1:
        headline = f"Critical: {distinct[0]}" if critical else f"{distinct[0]} needs attention"
    else:
        headline = f"{'Critical: ' if critical else ''}{len(distinct)} residents need attention"
    return {"lines": lines, "headline": headline, "critical": critical,
            "alert": bool(lines), "quiet_helpers": quiet}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: clinic_alert_diff.py <codex_report.txt> <claude_report.txt>", file=sys.stderr)
        return 2
    codex_text = Path(sys.argv[1]).read_text()
    claude_text = Path(sys.argv[2]).read_text()

    current = {}
    current.update(parse_codex(codex_text))
    current.update(parse_claude(claude_text))

    prev = {}
    if STATE_FILE.exists():
        try:
            prev = json.loads(STATE_FILE.read_text())
        except Exception:
            prev = {}

    worsened = []
    new_flags = []
    resolved = []
    for pid, verdict in current.items():
        if verdict not in SEVERITY:
            continue  # no-telemetry etc: not alert-worthy
        prev_verdict = prev.get(pid)
        prev_sev = SEVERITY.get(prev_verdict, -1) if prev_verdict else -1
        cur_sev = SEVERITY[verdict]
        if prev_verdict is None and cur_sev > 0:
            new_flags.append((pid, verdict))
        # A verdict outside the vocabulary, such as no-telemetry, ranks -1 in
        # prev_sev. Comparing against it reported healthy as WORSE; a thread
        # worsens only when it rises above healthy and above its old tier.
        elif prev_verdict is not None and cur_sev > max(prev_sev, 0):
            worsened.append((pid, prev_verdict, verdict))

    for pid, prev_verdict in prev.items():
        if pid not in current:
            continue
        prev_sev = SEVERITY.get(prev_verdict, -1)
        cur_sev = SEVERITY.get(current[pid], -1)
        if prev_sev > 0 and cur_sev == 0:
            resolved.append((pid, prev_verdict))

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(current, indent=2, sort_keys=True))

    # Public, identifier-free aggregate — see AGGREGATE_SCHEMA_VERSION and the
    # contract doc. Counts only; never a session id, path, room name, or title.
    counts = {"healthy": 0, "no-telemetry": 0, "rotate-soon": 0,
              "treat-images": 0, "compact-treadmill": 0,
              "CRITICAL": 0, "CRITICAL-window-exhausted": 0,
              "CRITICAL-compact-treadmill": 0}
    for v in current.values():
        counts[v] = counts.get(v, 0) + 1
    # Deterministic worst-verdict. Several verdicts share a severity tier, so
    # picking by severity alone leaves the reported worst dependent on
    # iteration order -- the tray would flip its headline between rounds with
    # no underlying change. Resolve ties by an explicit priority instead.
    WORST_PRIORITY = (
        "CRITICAL",
        "CRITICAL-window-exhausted",
        "CRITICAL-compact-treadmill",
        "rotate-soon",
        "compact-treadmill",
        "treat-images",
        "healthy",
    )
    present = set(current.values())
    worst = next((v for v in WORST_PRIORITY if v in present), "healthy")
    critical = (
        counts["CRITICAL"]
        + counts["CRITICAL-window-exhausted"]
        + counts["CRITICAL-compact-treadmill"]
    )
    if critical:
        next_action = "rotate critical session(s) now"
    elif counts["rotate-soon"]:
        next_action = f"rotate {counts['rotate-soon']} session(s) soon"
    elif counts["compact-treadmill"]:
        next_action = (
            f"review {counts['compact-treadmill']} session(s) losing history to repeated compaction"
        )
    elif counts["treat-images"]:
        next_action = f"treat images on {counts['treat-images']} session(s)"
    else:
        next_action = "none"
    aggregate = {
        "schema_version": AGGREGATE_SCHEMA_VERSION,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "counts": counts,
        "worst_verdict": worst,
        "next_action": next_action,
    }
    AGGREGATE_FILE.write_text(json.dumps(aggregate, indent=2, sort_keys=True))

    alert_lines = []
    for pid, verdict in new_flags:
        alert_lines.append(f"NEW: {pid} -> {verdict}")
    for pid, pv, cv in worsened:
        alert_lines.append(f"WORSE: {pid} {pv} -> {cv}")
    for pid, pv in resolved:
        alert_lines.append(f"RESOLVED: {pid} {pv} -> healthy")

    chronic = sum(
        1
        for v in current.values()
        if v in (
            "rotate-soon",
            "treat-images",
            "compact-treadmill",
            "CRITICAL",
            "CRITICAL-window-exhausted",
            "CRITICAL-compact-treadmill",
        )
    )
    print(f"chronic_flagged={chronic} new={len(new_flags)} worsened={len(worsened)} resolved={len(resolved)}")
    for line in alert_lines:
        print("  " + line)

    events = [(pid, v) for pid, v in new_flags] + [(pid, cv) for pid, _, cv in worsened]
    alert = build_alert(events, load_names())
    for line in alert["lines"]:
        print("  SAY: " + line)
    print(f"QUIET_HELPERS={alert['quiet_helpers']}")
    print(f"HEADLINE={alert['headline']}")
    print(f"SHOULD_ALERT={'1' if alert['alert'] else '0'} ANY_CRITICAL={'1' if alert['critical'] else '0'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
