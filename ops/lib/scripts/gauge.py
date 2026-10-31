#!/usr/bin/env python3
"""gauge: how full is each resident's context window, from the API's own figures.

For every resident in the registry, find its body and read only the latest
API usage figures from the end of the file. Never message content: a line is
parsed only when it carries usage or a compaction marker, and only these
fields are read from it: type, subtype, isSidechain, timestamp, and the
message's id, model and usage (or, for Codex, the token-count payload).

Prints resident, model, tokens used, window, percent, and the reading's time
and age. A figure the tool cannot establish is printed as "unknown", with the
reason, never guessed. Appends one line per resident to the ledger.

An idle resident's last reading is still its true number: context grows only
on a working turn, and every working turn writes a fresh reading. So the age
is shown and the reading is not called stale. A compaction after the reading
is different: the reading no longer describes the context, so it is shown as
"before compaction" and the percent is unknown until the next call.

Read-only on every body. Writes only the ledger (and nothing with --no-ledger).
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import json
import os
import re
import sys
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[3]
REGISTRY = SESSIONS / "Evidence" / "resident-identities.json"
LEDGER = SESSIONS / "storage" / "gauges" / "ledger.jsonl"
SPEC = SESSIONS / "docs" / "ops" / "specs" / "scripts" / "gauge.md"
RESOURCE_STATE = SESSIONS / "Evidence" / "resource-state.json"
CLAUDE_ROOT = Path.home() / ".claude" / "projects"
CODEX_LIVE = [Path.home() / ".codex" / "sessions", Path("/media/nos4r2/user_vol/VMs/Shared/Workbench/sessions")]
CODEX_ARCHIVED = [Path.home() / ".codex" / "archived_sessions"]
COPILOT_ROOT = Path.home() / ".copilot" / "session-state"
TAIL_START = 1 << 20          # first look at the last 1 MiB, then double
TAIL_LIMIT = 16_000_000       # never read more than this from the end (Joe Codex's bound)
SCHEMA = "gauge/1"
HEAD = 320                    # Codex and Copilot rows declare their type in the first bytes
SCALARS = rb'(?:"[A-Za-z_]+":\s?(?:-?\d+|"[^"\\]*"|true|false|null),\s?){0,6}'   # plain fields before "type", never nested
CODEX_TOKEN = re.compile(rb'^\{' + SCALARS + rb'"type":\s?"event_msg",\s?"payload":\s?\{"type":\s?"token_count"')
CODEX_CONTEXT = re.compile(rb'^\{' + SCALARS + rb'"type":\s?"turn_context"')
CODEX_COMPACTED = re.compile(rb'^\{' + SCALARS + rb'"type":\s?"compacted"')
HEAD_TIME = re.compile(rb'"timestamp":\s?"([^"]{10,40})"')
CLAUDE_BOUNDARY = b'"compact_boundary"'      # a prefilter only: content can carry the token too, so the line is parsed
                                             # and its top-level type and subtype decide
CLAUDE_ASSISTANT = re.compile(rb'"type":\s?"assistant"')
CLAUDE_USAGE = re.compile(rb'"usage":\s?\{')
COPILOT_USAGE = re.compile(rb'^\{"type":\s?"session\.usage_record"')
COPILOT_COMPACTED = re.compile(rb'^\{"type":\s?"session\.compaction_complete"')
WINDOW_ROW = re.compile(r"^\s*model=([^|\s]+)\|window=(\d+)\|source=([^|]+)\|observed=([^|\s]+)\s*$")


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def parse_time(value) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def age_text(seconds: float) -> str:
    seconds = max(0, int(seconds))
    if seconds < 90:
        return f"{seconds} s"
    if seconds < 90 * 60:
        return f"{round(seconds / 60)} min"
    if seconds < 36 * 3600:
        return f"{seconds / 3600:.1f} h"
    return f"{seconds / 86400:.1f} d"


# --------------------------------------------------------------------------
# Reading lines from the end of a body.
# --------------------------------------------------------------------------
def tail_lines(path: Path):
    """Yield (line_bytes, is_last_line) from the end of the file, newest first.

    Reads a growing window from the end; a partial first line of a window is
    never yielded unless the window reaches the start of the file. An
    unterminated final line (a write in progress) is skipped.
    """
    size = path.stat().st_size
    span = TAIL_START
    yielded = 0
    with path.open("rb") as fh:
        while True:
            start = max(0, size - span)
            fh.seek(start)
            chunk = fh.read(size - start)
            lines = chunk.split(b"\n")
            if not chunk.endswith(b"\n"):
                lines = lines[:-1]          # unterminated final line: in progress
            elif lines and lines[-1] == b"":
                lines = lines[:-1]
            if start > 0:
                lines = lines[1:]           # first line of the window may be cut
            fresh = lines[: len(lines) - yielded] if yielded else lines
            for line in reversed(fresh):
                yield line
            yielded = len(lines)
            if start == 0 or span >= TAIL_LIMIT:
                return
            span = min(span * 2, TAIL_LIMIT)


def load_json(line: bytes) -> dict | None:
    try:
        row = json.loads(line)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return None
    return row if isinstance(row, dict) else None


# --------------------------------------------------------------------------
# Claude: the newest main-chain assistant call with a nonzero usage sum.
# --------------------------------------------------------------------------
def read_claude(path: Path) -> dict:
    compaction_after = None
    for line in tail_lines(path):
        row = None
        if CLAUDE_BOUNDARY in line:          # order-independent (Claudio section 131, O1): find the token, parse
            row = load_json(line)            # the line in memory, and check the top-level type and subtype
            if row and row.get("type") == "system" and row.get("subtype") == "compact_boundary" \
                    and not row.get("isSidechain"):  # a side conversation compacting itself changes no resident state
                if compaction_after is None:
                    stamp = row.get("timestamp")
                    compaction_after = (stamp if isinstance(stamp, str) and len(stamp) <= 40 and parse_time(stamp)
                                        else "unknown time")   # bounded as the Codex and Copilot times are
                continue                     # a boundary row carries metadata, not a reading
        if not CLAUDE_USAGE.search(line) or not CLAUDE_ASSISTANT.search(line):
            continue                         # Claude rows put "type" after the message, so the row is parsed
                                             # in memory and only message.usage, model and id are read
        row = row if row is not None else load_json(line)
        if not row or row.get("type") != "assistant" or row.get("isSidechain"):
            continue
        message = row.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        parts = [usage.get(k) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")]
        if not all(isinstance(p, int) and p >= 0 for p in parts) or sum(parts) == 0:
            continue                         # zero-usage or synthetic rows are never readings
        return {"tokens": sum(parts), "model": message.get("model"), "reading_at": row.get("timestamp"),
                "call": message.get("id"), "compaction_after": compaction_after}
    return {"reason": f"no usage reading in the last {TAIL_LIMIT:,} bytes" + (" (compacted, no call since)" if compaction_after else ""),
            "compaction_after": compaction_after}


# --------------------------------------------------------------------------
# Codex: the newest token_count event. The window is reported by the API.
# --------------------------------------------------------------------------
def read_codex(path: Path) -> dict:
    """Joe Codex's method: the newest token_count event's last_token_usage.input_tokens over the
    same event's model_context_window; the model from the nearest turn_context before it; a
    compacted row after it supersedes it."""
    compaction_after = None
    found = None
    for line in tail_lines(path):
        head = line[:HEAD]
        if found is None:
            if CODEX_COMPACTED.match(head):
                if compaction_after is None:  # never parsed: replacement_history can hold content
                    stamp = HEAD_TIME.search(head)
                    compaction_after = stamp.group(1).decode("ascii", "replace") if stamp else "unknown time"
                continue
            if not CODEX_TOKEN.match(head):
                continue
            row = load_json(line)
            payload = (row or {}).get("payload") or {}
            info = payload.get("info") if payload.get("type") == "token_count" else None
            if not isinstance(info, dict):
                continue
            tokens = (info.get("last_token_usage") or {}).get("input_tokens")
            window = info.get("model_context_window")
            if not isinstance(tokens, int) or tokens <= 0:
                continue
            ok = isinstance(window, int) and window > 0
            found = {"tokens": tokens, "reading_at": row.get("timestamp"), "model": None,
                     "window": window if ok else None, "window_source": "model_context_window in the same event" if ok else None,
                     "compaction_after": compaction_after}
            continue
        if CODEX_CONTEXT.match(head):
            row = load_json(line)
            payload = (row or {}).get("payload") or {}
            if row and row.get("type") == "turn_context" and isinstance(payload.get("model"), str):
                found["model"] = payload["model"]
                break
    if found is None:
        return {"reason": f"no token_count reading in the last {TAIL_LIMIT:,} bytes", "compaction_after": compaction_after}
    if found["model"] is None:
        found["model_note"] = "no turn_context before the reading within the bound"
    return found


# --------------------------------------------------------------------------
# Copilot: the newest session.usage_record (values under data.usage).
# --------------------------------------------------------------------------
def read_copilot(path: Path) -> dict:
    compaction_after = None
    for line in tail_lines(path):
        if COPILOT_COMPACTED.match(line[:HEAD]):
            if compaction_after is None:
                stamp = HEAD_TIME.search(line[:2048])
                compaction_after = stamp.group(1).decode("ascii", "replace") if stamp else "unknown time"
            continue
        if not COPILOT_USAGE.match(line[:HEAD]):
            continue
        row = load_json(line)
        if not row or row.get("type") != "session.usage_record":
            continue
        usage = ((row.get("data") or {}).get("usage")) or {}
        tokens, window = usage.get("inputTokens"), usage.get("maxPromptTokens")
        if not isinstance(tokens, int) or tokens <= 0:
            continue
        ok = isinstance(window, int) and window > 0
        return {"tokens": tokens, "reading_at": row.get("timestamp"), "model": usage.get("model"),
                "window": window if ok else None, "window_source": "maxPromptTokens in the same record" if ok else None,
                "compaction_after": compaction_after}
    return {"reason": f"no session.usage_record in the last {TAIL_LIMIT:,} bytes", "compaction_after": compaction_after}


# --------------------------------------------------------------------------
# Windows, in order of authority (Claudio section 131, C1): the provider's own
# figure in the same record (Codex, Copilot); the reviewed table in the spec;
# only for a model the table lacks, Claude Code's status-line record, marked
# unverified (whichever session last ran it wrote it, with no session id).
# Else unknown.
# --------------------------------------------------------------------------
def window_table(spec: Path) -> dict[str, dict]:
    table = {}
    try:
        lines = spec.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return table
    for line in lines:
        m = WINDOW_ROW.match(line)
        if m:
            table[m.group(1)] = {"window": int(m.group(2)), "source": m.group(3).strip(), "observed": m.group(4)}
    return table


def statusline_window(resource_state: Path) -> tuple[str, int, str] | None:
    try:
        data = json.loads(resource_state.read_text(encoding="utf-8"))
        model = data["model"]["id"]
        window = data["context"]["window_size"]
        when = data["generated_at"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if isinstance(model, str) and isinstance(window, int) and window > 0:
        return model, window, when
    return None


def resolve_window(reading: dict, table: dict, statusline) -> None:
    if reading.get("window"):
        return
    model = reading.get("model")
    if not model:
        reading["window_reason"] = "the reading names no model"
        return
    row = table.get(model)
    same = statusline if statusline and statusline[0] == model else None
    if row:
        reading["window"], reading["window_source"] = row["window"], f"spec table: {row['source']}, observed {row['observed']}"
        if same and same[1] != row["window"]:
            reading["window_note"] = f"the status line (unverified) says {same[1]:,} for {model}; the table's {row['window']:,} is used"
        return
    if same:
        reading["window"], reading["window_source"] = same[1], f"Claude Code status line, unverified, observed {same[2]}"
        reading["window_note"] = "window unverified: from the status line; the table has no row for this model"
        return
    reading["window_reason"] = f"no reviewed window for {model}"


# --------------------------------------------------------------------------
# Finding bodies.
# --------------------------------------------------------------------------
def find_body(provider: str, session_id: str, claude_root: Path, codex_live: list[Path],
              codex_archived: list[Path], copilot_root: Path) -> tuple[Path | None, str, str]:
    """(body, location, reason). Location is live or archived; reason explains a None."""
    if not re.fullmatch(r"[0-9A-Za-z-]{8,64}", session_id or ""):
        return None, "", "the registry's session id is not a plain identifier"

    def pick(hits):
        hits = sorted({h for h in hits if h.is_file()})
        if len(hits) > 1:
            return None, f"{len(hits)} bodies match; refusing to choose"
        return (hits[0], "") if hits else (None, "body not found")

    if provider == "claude":
        body, why = pick(claude_root.glob(f"*/{session_id}.jsonl") if claude_root.is_dir() else [])
        return body, "live" if body else "", why
    if provider == "codex":
        for location, roots in (("live", codex_live), ("archived", codex_archived)):
            exact = re.compile(r"rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-" + re.escape(session_id) + r"\.jsonl")
            hits = [h for root in roots if root.is_dir() for h in root.rglob(f"rollout-*-{session_id}.jsonl")
                    if exact.fullmatch(h.name)]        # a partial id never matches as a suffix
            if hits:
                body, why = pick(hits)
                return body, location if body else "", why
        return None, "", "body not found"
    if provider == "copilot":
        body, why = pick([copilot_root / session_id / "events.jsonl"])
        return body, "live" if body else "", why
    return None, "", f"no reader for provider {provider} yet"


# --------------------------------------------------------------------------
# One measurement per resident.
# --------------------------------------------------------------------------
def measure(identity: dict, now: dt.datetime, table: dict, statusline, claude_root: Path, codex_live: list[Path],
            codex_archived: list[Path], copilot_root: Path) -> dict:
    out = {"schema": SCHEMA, "measured_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "key": identity.get("key"),
           "person": identity.get("person"), "provider": identity.get("provider"), "session_id": identity.get("session_id"),
           "model": None, "tokens": None, "window": None, "window_source": None, "percent": None,
           "reading_at": None, "age_seconds": None, "body": None, "state": "unknown", "reason": None}
    body, location, why = find_body(out["provider"], out["session_id"] or "", claude_root, codex_live, codex_archived, copilot_root)
    if body is None:
        out["reason"] = why
        return out
    out["body"] = location
    reader = {"claude": read_claude, "codex": read_codex, "copilot": read_copilot}[out["provider"]]
    try:
        reading = reader(body)
    except Exception as exc:                 # one bad body is one unknown row, never the end of the run
        out["reason"] = f"body unreadable: {getattr(exc, 'strerror', None) or exc.__class__.__name__}"
        return out
    if "tokens" not in reading:
        out["reason"] = reading["reason"]
        if reading.get("compaction_after"):
            out["state"] = "compacted"
        return out
    resolve_window(reading, table, statusline)
    out.update({k: reading.get(k) for k in ("model", "tokens", "window", "window_source", "reading_at")})
    when = parse_time(out["reading_at"])
    if when is not None:
        out["age_seconds"] = int((now - when).total_seconds())
    if reading.get("compaction_after"):
        out["state"] = "before compaction"
        out["reason"] = f"compacted at {reading['compaction_after']}; the next call gives the new figure"
        return out
    if not out["window"]:
        out["reason"] = reading.get("window_reason")
        out["state"] = "window unknown"
        return out
    if out["tokens"] > out["window"]:
        out["state"] = "invalid"
        out["reason"] = "tokens exceed the window; the window entry is wrong"
        return out
    out["percent"] = round(100.0 * out["tokens"] / out["window"], 1)
    out["state"] = "last observed" if location == "live" else "archived body"
    notes = (["archived body: not a live reading"] if location == "archived" else []) + \
        [reading[k] for k in ("model_note", "window_note") if reading.get(k)]
    out["reason"] = "; ".join(notes) or None
    return out


def append_ledger(ledger: Path, rows: list[dict]) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger.with_suffix(".lock"), "a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        data = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows).encode("utf-8")
        fd = os.open(ledger, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(fd, view):]
            os.fsync(fd)
        finally:
            os.close(fd)


def table_text(rows: list[dict], now: dt.datetime) -> str:
    def fmt_int(v):
        return f"{v:,}" if isinstance(v, int) else "unknown"
    lines = [f"gauge at {now.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}",
             f"{'resident':<26} {'model':<20} {'tokens':>11} {'window':>11} {'percent':>8}  {'last observed':<16} {'age':>8}  {'state':<17} note"]
    for r in sorted(rows, key=lambda r: (r["percent"] is None, -(r["percent"] or 0), r["key"] or "")):
        when = parse_time(r["reading_at"])
        read_at = when.astimezone().strftime("%m-%d %H:%M") if when else "unknown"
        age = age_text(r["age_seconds"]) if r["age_seconds"] is not None else "unknown"
        pct = f"{r['percent']:.1f}" if r["percent"] is not None else "unknown"
        note = r["reason"] or ""
        lines.append(f"{(r['key'] or '?'):<26} {(r['model'] or 'unknown')[:20]:<20} {fmt_int(r['tokens']):>11} "
                     f"{fmt_int(r['window']):>11} {pct:>8}  {read_at:<16} {age:>8}  {r['state']:<17} {note}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--ledger", type=Path, default=LEDGER)
    ap.add_argument("--spec", type=Path, default=SPEC, help="the spec holding the reviewed model-to-window table")
    ap.add_argument("--resource-state", type=Path, default=RESOURCE_STATE)
    ap.add_argument("--claude-root", type=Path, default=CLAUDE_ROOT)
    ap.add_argument("--codex-root", type=Path, action="append", help="live Codex root, repeatable; default: the host's")
    ap.add_argument("--codex-archived-root", type=Path, action="append", help="archived Codex root, repeatable")
    ap.add_argument("--copilot-root", type=Path, default=COPILOT_ROOT)
    ap.add_argument("--key", action="append", help="measure only these registry keys (repeatable)")
    ap.add_argument("--json", action="store_true", help="print JSON lines instead of the table")
    ap.add_argument("--no-ledger", action="store_true", help="print only; append nothing")
    ap.add_argument("--now", help="ISO time to measure ages against (tests)")
    args = ap.parse_args(argv)

    now = parse_time(args.now) if args.now else utc_now()
    try:
        identities = json.loads(args.registry.read_text(encoding="utf-8"))["identities"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"gauge: registry unreadable ({exc}); nothing measured", file=sys.stderr)
        return 2
    if args.key:
        identities = [i for i in identities if i.get("key") in set(args.key)]
    table = window_table(args.spec)
    statusline = statusline_window(args.resource_state)
    codex_live = args.codex_root or CODEX_LIVE
    codex_archived = args.codex_archived_root if args.codex_archived_root is not None else ([] if args.codex_root else CODEX_ARCHIVED)
    rows = [measure(i, now, table, statusline, args.claude_root, codex_live, codex_archived, args.copilot_root)
            for i in identities if isinstance(i, dict)]
    if args.json:
        sys.stdout.write("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    else:
        sys.stdout.write(table_text(rows, now))
    if not args.no_ledger:
        append_ledger(args.ledger, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
