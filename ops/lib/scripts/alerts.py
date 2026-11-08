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

Since 2026-11-05 it also writes a PRIVATE active panel, clinic-panel.json at
mode 0600 beside the alert state: one row per registered resident, keyed by
registry key, bound to exactly one live body or marked missing, ambiguous,
unknown or archived, with unregistered bodies, helpers and the archive counted
apart (W3). It carries no session id, patient label, path or body content, never
enters the public aggregate, and prints one closing PANEL line. The
aggregate, the state, the alert lines and the exit status are unchanged by it.
"""
from __future__ import annotations

import contextlib
import datetime
import importlib.util
import json
import os
import re
import sys
import tempfile
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
EXTRA_CODEX_ROOTS = None   # None: the working volume's Workbench sessions, from the host fingerprint at use
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
    extra = extra_codex_roots() if extra is None else extra
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


# --------------------------------------------------------------------------
# The active panel (W3, 2026-11-05): a PRIVATE projection beside the alert
# state, logs/clinic-panel.json at mode 0600, never part of the public
# aggregate. One row per registered resident, keyed by registry key, with its
# binding to exactly one live body or an explicit missing, ambiguous, unknown
# or archived; unregistered bodies and helpers, and the archive, are counted
# in their own inventories and never presented as resident health. A body is
# resolved by its file name only, as the health desk's
# measurement of 2026-11-05 did; never by the newest file or a working
# directory. The Codex ward does not scan the archive, so a registered session
# and the archive's count are read from the file names here, not from ward rows.
# Only a helper's test reads the session-meta record, as the popup's
# naming already does. The panel carries registry keys, ward names, verdicts, counts and
# ages; never a session id, a patient label, a path or body content.
# --------------------------------------------------------------------------
PANEL_NAME = "clinic-panel.json"      # beside STATE_FILE, so it follows wherever the state lives
PANEL_SCHEMA = "clinic-panel/1"
CLAUDE_PROJECTS = None                # the Claude live store; None is vitals.PROJECTS_ROOT
BINDINGS = ("one-live-body", "missing", "ambiguous", "unknown", "archived")
CLINIC_DOMAIN = ("clinic ward verdict (file size, media, compaction and carry, and context percentage "
                 "as each ward measures them)")
SIGNALS_NOT_JOINED = ("context pressure from the gauge", "scheduler operation", "product-source drift")


def _volume_root(name: str) -> Path:
    """One volume root from the room's private host fingerprint, read only where a path needs it. A missing or
    malformed file refuses this tool by name with exit 1 and names no value (fingerprint.py)."""
    path = Path(__file__).resolve().with_name("fingerprint.py")
    key = f"fingerprint@{path}"
    module = sys.modules.get(key)
    if module is None:
        spec = importlib.util.spec_from_file_location(key, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module   # the dataclass in it looks its module up here
        spec.loader.exec_module(module)
    return module.volume_root(Path(__file__).name, name)


def extra_codex_roots() -> list[Path]:
    """EXTRA_CODEX_ROOTS when a caller set it, else the Workbench sessions on the working volume."""
    if EXTRA_CODEX_ROOTS is not None:
        return EXTRA_CODEX_ROOTS
    return [_volume_root("working") / "VMs" / "Shared" / "Workbench" / "sessions"]


def _vitals():
    spec = importlib.util.spec_from_file_location("alerts_vitals", Path(__file__).resolve().with_name("vitals.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _age(path: Path, now: datetime.datetime) -> int | None:
    try:
        return max(0, int(now.timestamp() - path.stat().st_mtime))
    except OSError:
        return None


def body_index(codex_home: Path, extra: list, claude_projects: Path, room_name) -> tuple[dict, dict]:
    """Physical bodies by the label a ward report gives them: file names only, never content.
    Returns (codex: file name -> [(location, ward)], claude: "room / prefix" -> [(file name, ward)])."""
    codex = {}
    roots = [(codex_home / "sessions", "live", "codex-host-live")]
    roots += [(root, "live", "codex-vm-live") for root in extra]
    roots += [(codex_home / "archived_sessions", "archived", "codex-archive")]
    for root, location, ward in roots:
        if root.is_dir():
            for path in sorted(root.rglob("rollout-*.jsonl")):
                if path.is_file() and not path.is_symlink():
                    codex.setdefault(path.name, []).append((location, ward))
    claude = {}
    if claude_projects.is_dir():
        for path in sorted(claude_projects.glob("*/*.jsonl")):
            if path.is_file() and not path.is_symlink():
                claude.setdefault(f"{room_name(path.parent.name)} / {path.name[:20]}", []).append(
                    (path.name, "claude-live-store"))
    return codex, claude


def bodies_by_session(codex: dict, claude: dict) -> dict:
    """(provider, session id) -> the location of each body whose file name carries that id, from body_index."""
    found = {}
    for name, hits in codex.items():
        m = UUID.search(name)
        if m:
            found.setdefault(("codex", m.group(1)), []).extend(location for location, _ in hits)
    for hits in claude.values():
        for name, _ in hits:
            m = UUID.search(name)
            if m:
                found.setdefault(("claude", m.group(1)), []).append("live")
    return found


def classify_patient(pid: str, codex: dict, claude: dict) -> dict:
    """One patient: its provider, location (live, archived, missing, ambiguous) and native id. The id is
    used only in memory to bind the patient to the registry and never enters the panel."""
    provider, label = pid.split(":", 1)
    hits = codex.get(label, []) if provider == "codex" else claude.get(label, [])
    if len(hits) != 1:
        if provider == "codex":                  # the file name carries the whole id, found or not
            m = UUID.search(label)
            native = m.group(1) if m else None
        else:                                    # a Claude label carries only a prefix of it
            native = "prefix:" + label.rsplit(" / ", 1)[1] if " / " in label else None
        return {"provider": provider, "location": "ambiguous" if hits else "missing", "native": native, "ward": None}
    if provider == "codex":
        location, ward = hits[0]
        m = UUID.search(label)
    else:
        (name, ward), location = hits[0], "live"
        m = UUID.search(name)
    return {"provider": provider, "location": location, "native": m.group(1) if m else None, "ward": ward}


def build_panel(current: dict, reports: dict, registry_path: Path, now: datetime.datetime,
                codex_home: Path, extra: list, claude_projects: Path | None, home_meta=None) -> dict:
    """The panel object. reports maps provider -> (report path, rows parsed from it)."""
    evidence = [{"domain": f"clinic {provider} ward report", "age_seconds": _age(path, now), "rows": rows}
                for provider, (path, rows) in sorted(reports.items())]
    evidence.append({"domain": "resident registry", "age_seconds": _age(registry_path, now)})
    panel = {"schema": PANEL_SCHEMA, "generated_at": now.isoformat(timespec="seconds"), "evidence": evidence,
             "signals_not_joined": list(SIGNALS_NOT_JOINED)}
    try:
        identities = json.loads(registry_path.read_text(encoding="utf-8"))["identities"]
        if not isinstance(identities, list):
            raise TypeError
    except (OSError, ValueError, KeyError, TypeError):
        return {**panel, "status": "registry unavailable", "residents": {}, "inventories": None}
    rows = [r for r in identities if isinstance(r, dict) and isinstance(r.get("key"), str) and r["key"]]
    keys = [r["key"] for r in rows]
    vitals = _vitals()
    codex, claude = body_index(codex_home, extra, claude_projects or vitals.PROJECTS_ROOT, vitals.room_name)
    on_disk = bodies_by_session(codex, claude)
    bound = {}        # (provider, native) -> [(pid, location, ward)]
    for pid in sorted(current):
        c = classify_patient(pid, codex, claude)
        bound.setdefault((c["provider"], c["native"]), []).append((pid, c["location"], c["ward"]))
    binding_count = {}
    registered_natives = set()        # every row naming a session: an ambiguous row is still registered
    for r in rows:
        if isinstance(r.get("provider"), str) and isinstance(r.get("session_id"), str):
            pair = (r["provider"], r["session_id"])
            binding_count[pair] = binding_count.get(pair, 0) + 1
            if r["session_id"]:
                registered_natives.add(pair)
    residents = {}
    for r in rows:
        key, provider, native = r["key"], r.get("provider"), r.get("session_id")
        row = {"provider": provider if isinstance(provider, str) else None, "binding": "unknown", "verdict": None,
               "ward": None, "signals": {}}
        if keys.count(key) != 1:
            row["binding"], row["reason"] = "ambiguous", "the key appears in more than one registry row"
        elif provider not in reports:
            row["reason"] = "no clinic ward reads this provider"
        elif not isinstance(native, str) or not native:
            row["reason"] = "the registry row names no session"
        elif binding_count.get((provider, native), 0) != 1:
            row["binding"], row["reason"] = "ambiguous", "the session is bound to more than one registry row"
        elif reports[provider][1] == 0:
            row["reason"] = f"the {provider} ward report has no rows"
        else:
            hits = bound.get((provider, native), [])
            if provider == "claude":
                hits = hits + bound.get((provider, "prefix:" + native[:20]), [])
            live = [h for h in hits if h[1] == "live"]
            unresolved = [h for h in hits if h[1] in ("missing", "ambiguous")]
            disk = on_disk.get((provider, native), [])
            if len(live) == 1 and not unresolved:
                pid, _, ward = live[0]
                row.update(binding="one-live-body", verdict=current[pid], ward=ward)
                row["signals"]["clinic_verdict"] = {"value": current[pid], "domain": CLINIC_DOMAIN,
                                                    "evidence": f"clinic {provider} ward report",
                                                    "age_seconds": _age(reports[provider][0], now)}
            elif live or any(h[1] == "ambiguous" for h in unresolved) or len(disk) > 1:
                row["binding"], row["reason"] = "ambiguous", "more than one body or ward row carries this session"
            elif disk == ["archived"]:
                row["binding"], row["reason"] = "archived", "only an archived body carries this session"
            elif disk == ["live"]:             # never a verdict without a ward row, and not missing: a body exists
                row["reason"] = "one live body carries this session, but no ward row measures it"
            else:
                row["binding"] = "missing"
                row["reason"] = ("its ward row names a body that is not found" if unresolved else
                                 "no body is found under the live or archive roots")
        residents.setdefault(key, row)
    archived_names = [name for name, hits in codex.items() for location, _ in hits if location == "archived"]
    inventories = {"orphan_and_helper": {"unregistered": {}, "helper": {}},
                   "unresolved": {"missing": {}, "ambiguous": {}},
                   "lifecycle": {"archived": len(archived_names),
                                 "archived_registered": sum(1 for name in archived_names if (m := UUID.search(name))
                                                            and ("codex", m.group(1)) in registered_natives),
                                 "operator_recorded_retired": None}}

    def tally(bucket: dict, verdict: str) -> None:
        bucket[verdict] = bucket.get(verdict, 0) + 1

    for (provider, native), hits in bound.items():
        for pid, location, ward in hits:
            verdict = current[pid]
            if location in ("missing", "ambiguous"):
                tally(inventories["unresolved"][location], verdict)
            elif location == "live" and (provider, native) not in registered_natives:
                meta = (home_meta or codex_meta)(native) if provider == "codex" and native else {}
                source = meta.get("source") if isinstance(meta.get("source"), dict) else {}
                subagent = source.get("subagent") if isinstance(source.get("subagent"), dict) else {}
                spawn = subagent.get("thread_spawn") if isinstance(subagent.get("thread_spawn"), dict) else {}
                parent = meta.get("parent_thread_id") or spawn.get("parent_thread_id")
                tally(inventories["orphan_and_helper"]["helper" if parent else "unregistered"], verdict)
    counts = {b: sum(1 for r in residents.values() if r["binding"] == b) for b in BINDINGS}
    return {**panel, "status": "ok", "registered": len(residents), "active": len(residents) - counts["archived"],
            "bindings": counts, "residents": dict(sorted(residents.items())), "inventories": inventories}


def write_private(path: Path, data: bytes) -> None:
    """Replace path atomically at mode 0600."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix="." + path.name + ".")
    try:
        os.fchmod(fd, 0o600)
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
        os.close(fd)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.close(fd)
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def panel_line(panel: dict) -> str:
    """The one line for the rounds log; the rows stay in the private file. It starts with PANEL, so no
    pattern the wrapper reads can match it."""
    line = f"PANEL active panel, private ({PANEL_NAME}); generated {panel['generated_at']}; status {panel['status']}"
    if panel.get("residents") is None or panel.get("inventories") is None:
        return line
    b, inv = panel["bindings"], panel["inventories"]
    return (f"{line}; residents {panel['registered']}, active {panel['active']}: "
            + ", ".join(f"{k} {b[k]}" for k in BINDINGS)
            + "; not resident health: unregistered " + str(sum(inv["orphan_and_helper"]["unregistered"].values()))
            + ", helpers " + str(sum(inv["orphan_and_helper"]["helper"].values()))
            + ", unresolved " + str(sum(inv["unresolved"]["missing"].values())
                                    + sum(inv["unresolved"]["ambiguous"].values()))
            + f", archived {inv['lifecycle']['archived']}, archived registered {inv['lifecycle']['archived_registered']}")


def publish_panel(current: dict, codex_report: Path, claude_report: Path) -> None:
    """Build, write and print the panel. Any failure is printed and written as unavailable and changes
    nothing else: the state, the aggregate, the alert lines and the exit status are already settled."""
    now = datetime.datetime.now(datetime.timezone.utc)
    target = STATE_FILE.parent / PANEL_NAME
    try:
        reports = {"codex": (codex_report, sum(1 for p in current if p.startswith("codex:"))),
                   "claude": (claude_report, sum(1 for p in current if p.startswith("claude:")))}
        panel = build_panel(current, reports, REGISTRY, now, CODEX_HOME, extra_codex_roots(), CLAUDE_PROJECTS)
    except Exception as exc:
        panel = {"schema": PANEL_SCHEMA, "generated_at": now.isoformat(timespec="seconds"),
                 "status": f"unavailable ({exc.__class__.__name__})"}
    try:
        write_private(target, (json.dumps(panel, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    except OSError as exc:
        panel["status"] = f"{panel['status']}; not written ({exc.__class__.__name__})"
    print(panel_line(panel))


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
    publish_panel(current, Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
