#!/usr/bin/env python3
"""Resident Resource Governor — collector.

Runs as a Claude Code `statusLine` command. Claude Code hands it the session
telemetry JSON on stdin after each response, locally, costing zero API tokens.

Two jobs, in this order of importance:

1. Write a sanitized, identifier-free state file for Resident Center to read.
2. Print a short, genuinely useful status line for the operator.

SANITIZATION IS THE POINT, NOT A COURTESY. The payload Claude Code supplies
contains `session_id`, `transcript_path`, `cwd`, and the git repository owner
and name. None of that belongs in a file whose reason for existing is to be
displayed by another program. This mirrors the Session Clinic's public
aggregate contract: numbers and states leave, identity never does.

WHAT THIS DOES NOT DO. It observes. It does not purchase, upgrade, downgrade,
switch models, block launches, or change any account setting. Policy lives in
a separate operator-owned file and is advisory. The supported telemetry
carries plan *windows* only -- it does not expose usage-credit balance or
month-to-date credit spend, and this collector does not attempt to obtain
those by any other means.

Failure is silent by design: a status line that throws would be visible on
every turn and would teach the operator to ignore it. On any error the state
file is left alone and a minimal line is printed.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

SCHEMA_VERSION = 1
SESSIONS = Path(__file__).resolve().parents[3]   # the room, resolved as gauge.py does
STATE_PATH = Path(
    os.environ.get(
        "RESIDENT_RESOURCE_STATE",
        str(SESSIONS / "logs" / "resource-state.json"),
    )
)


def bar(pct: float, width: int = 10) -> str:
    filled = max(0, min(width, round(pct / 100 * width)))
    return "█" * filled + "░" * (width - filled)


def humanize(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    if hours >= 24:
        return f"{hours // 24}d{hours % 24}h"
    return f"{hours}h{rem // 60:02d}m" if hours else f"{rem // 60}m"


def sanitize(payload: dict, now: dt.datetime) -> dict:
    """Extract only what a display needs. Identity is dropped, not masked."""
    limits = payload.get("rate_limits") or {}
    windows: dict[str, dict] = {}
    for name in ("five_hour", "seven_day"):
        window = limits.get(name)
        if not isinstance(window, dict):
            continue
        used = window.get("used_percentage")
        resets_at = window.get("resets_at")
        entry: dict[str, object] = {}
        if isinstance(used, (int, float)):
            entry["used_percentage"] = round(float(used), 1)
        if isinstance(resets_at, (int, float)):
            entry["resets_at"] = int(resets_at)
            entry["resets_in_seconds"] = max(
                0, int(resets_at - now.timestamp())
            )
        if entry:
            windows[name] = entry

    context = payload.get("context_window") or {}
    model = payload.get("model") or {}
    cost = payload.get("cost") or {}
    effort = payload.get("effort") or {}

    state = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now.astimezone(dt.timezone.utc).isoformat(
            timespec="seconds"
        ),
        "source": "claude-code-statusline",
        "provider": "anthropic",
        "windows": windows,
        "model": {
            "id": model.get("id"),
            "display_name": model.get("display_name"),
            "effort": effort.get("level"),
            "thinking": bool((payload.get("thinking") or {}).get("enabled")),
            "fast_mode": bool(payload.get("fast_mode")),
        },
        "context": {
            "used_percentage": context.get("used_percentage"),
            "window_size": context.get("context_window_size"),
        },
        # Local, approximate, and explicitly labelled as such. This is what the
        # CLI estimates for this one session -- not an account balance, and it
        # must never be presented as one.
        "session_local_estimate": {
            "cost_usd": round(float(cost.get("total_cost_usd") or 0), 4),
            "duration_ms": cost.get("total_duration_ms"),
            "note": "local CLI estimate for this session only; not billing truth",
        },
        "cli_version": payload.get("version"),
    }
    return state


def render(state: dict) -> str:
    parts: list[str] = []
    model = state.get("model") or {}
    if model.get("display_name"):
        label = model["display_name"]
        if model.get("effort"):
            label += f"/{model['effort']}"
        parts.append(label)

    context = state.get("context") or {}
    if isinstance(context.get("used_percentage"), (int, float)):
        parts.append(f"ctx {context['used_percentage']:.0f}%")

    five = (state.get("windows") or {}).get("five_hour") or {}
    if isinstance(five.get("used_percentage"), (int, float)):
        pct = five["used_percentage"]
        chunk = f"5h {bar(pct)} {pct:.0f}%"
        if "resets_in_seconds" in five:
            chunk += f" ({humanize(five['resets_in_seconds'])})"
        parts.append(chunk)

    seven = (state.get("windows") or {}).get("seven_day") or {}
    if isinstance(seven.get("used_percentage"), (int, float)):
        parts.append(f"7d {seven['used_percentage']:.0f}%")

    return "  ".join(parts) if parts else "resource governor: no data"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print("resource governor: unreadable telemetry")
        return 0

    try:
        now = dt.datetime.now(dt.timezone.utc)
        state = sanitize(payload, now)
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        tmp.replace(STATE_PATH)  # atomic; a reader never sees a partial file
        print(render(state))
    except Exception:
        # Never let the status line become a source of noise.
        print("resource governor: collector error")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
