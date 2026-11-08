#!/usr/bin/env python3
"""Report token health for Codex rollout JSONL files.

Reads the telemetry Codex itself writes into each rollout: the last
`event_msg`/`token_count` row carries `last_token_usage.input_tokens` and
`model_context_window`. That is the number auto-compact triggers on, so this
is a direct measurement, not a byte/row proxy.

Health axes per session:
- context_pct: last-turn input tokens vs model_context_window. The compact
  trigger fires at the window itself; sessions should rotate at ~70%.
- compact_thrash: count of `compacted` rollout rows and the bytes they hold.
  auto_compact_v2 appends the full replacement history inline, so a thrashing
  session grows by tens of MB per compact with no real work in between.
- file bytes and response_item rows (loader array ceiling remains 16,384).

Read-only. Never modifies session files.

Lane: session hygiene monitoring.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

TAIL_BYTES = 8_000_000


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


def default_roots() -> list[Path]:
    """The host's Codex sessions, and George's: the Workbench VM mounts this share as its sessions dir."""
    return [Path.home() / ".codex" / "sessions", _volume_root("working") / "VMs" / "Shared" / "Workbench" / "sessions"]

ROTATE_PCT = 70.0

# A session that keeps compacting is shedding working memory to stay under the
# window. Its context percentage goes DOWN each time it does so, which is why
# percentage alone cannot detect it -- the sickest sessions look like the
# healthiest ones. Count the compactions instead.
TREADMILL_COMPACTIONS = 8
# Of the messages on disk, the fraction still carried in the newest window.
# Low means most of the resident's history is no longer in front of it.
THIN_CARRY_RATIO = 0.40

# Match the row type regardless of JSON separator whitespace. Codex writes
# compact JSON; anything rebuilt through json.dumps defaults to spaced
# separators. Both are valid JSON and both load fine, so a byte scan that
# assumes one form silently counts zero against the other. This cost the
# clinic 2,561 invisible response items across 14 sessions before it was
# caught on 2026-07-29; five residents were reading as literally empty.
RE_TYPE_RESPONSE = re.compile(rb'"type"\s*:\s*"response_item"')
RE_TYPE_COMPACTED = re.compile(rb'"type"\s*:\s*"compacted"')
RE_PAYLOAD_MESSAGE = re.compile(rb'"type"\s*:\s*"message"')
HEAD_BYTES = 120


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Rollout JSONL files. Default: scan host + VM roots.")
    parser.add_argument("--root", default=None, help="Session root to scan when no paths given.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    return parser.parse_args()


def last_token_count(path: Path) -> dict[str, Any] | None:
    size = path.stat().st_size
    with path.open("rb") as handle:
        handle.seek(max(0, size - TAIL_BYTES))
        lines = handle.read().split(b"\n")
    for line in reversed(lines):
        if b'"token_count"' not in line:
            continue
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        info = (row.get("payload") or {}).get("info") or {}
        if info:
            return {"timestamp": row.get("timestamp"), **info}
    return None


def scan_structure(path: Path) -> dict[str, Any]:
    """Single streaming pass: row counts by type, compacted bytes, response items.

    Also records the byte offset of the last compaction row so the carry-forward
    ratio can be computed later with one seek, instead of a second full pass
    over files that reach tens of megabytes.
    """
    rows = 0
    response_items = 0
    message_rows = 0
    compacted_rows = 0
    compacted_bytes = 0
    last_compaction_offset: int | None = None
    offset = 0
    with path.open("rb") as handle:
        for line in handle:
            rows += 1
            head = line[:HEAD_BYTES]
            if RE_TYPE_RESPONSE.search(head):
                response_items += 1
                # Carry-forward compares like with like: messages against
                # messages. Counting tool calls, outputs, and reasoning in the
                # denominator would make every session look far more attrited
                # than it is.
                if RE_PAYLOAD_MESSAGE.search(head):
                    message_rows += 1
            elif RE_TYPE_COMPACTED.search(head):
                compacted_rows += 1
                compacted_bytes += len(line)
                last_compaction_offset = offset
            offset += len(line)
    return {
        "rows": rows,
        "response_item_rows": response_items,
        "message_rows": message_rows,
        "compacted_rows": compacted_rows,
        "compacted_bytes": compacted_bytes,
        "last_compaction_offset": last_compaction_offset,
    }


def carry_forward(path: Path, offset: int | None, message_rows: int) -> float | None:
    """Fraction of the session's messages still present in the newest window.

    A resident that has compacted repeatedly may be sitting at a comfortable
    context percentage precisely because most of its history is no longer in
    front of it. That is the state this measures.
    """
    if offset is None or not message_rows:
        return None
    try:
        with path.open("rb") as handle:
            handle.seek(offset)
            row = json.loads(handle.readline())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    history = (row.get("payload") or {}).get("replacement_history")
    if not isinstance(history, list):
        return None
    carried = sum(
        1 for item in history if isinstance(item, dict) and item.get("type") == "message"
    )
    return round(min(carried / message_rows, 1.0), 3)


def health(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    report: dict[str, Any] = {
        "session": str(path),
        "bytes": size,
        "mtime": dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
    }
    tc = last_token_count(path)
    if tc:
        last = tc.get("last_token_usage") or {}
        window = tc.get("model_context_window") or 0
        input_tokens = last.get("input_tokens") or 0
        report["last_turn_input_tokens"] = input_tokens
        report["model_context_window"] = window
        report["context_pct"] = round(100.0 * input_tokens / window, 1) if window else None
        report["token_count_at"] = tc.get("timestamp")
    else:
        report["last_turn_input_tokens"] = None
        report["model_context_window"] = None
        report["context_pct"] = None
    report.update(scan_structure(path))
    report["carry_forward_ratio"] = carry_forward(
        path,
        report.get("last_compaction_offset"),
        report["message_rows"],
    )
    pct = report["context_pct"]
    compactions = report["compacted_rows"]
    carry = report["carry_forward_ratio"]

    # Treadmill is judged on history loss, not on percentage. A session that
    # has compacted many times, or that carries only a thin slice of its own
    # history into the current window, is attrited even when its percentage
    # looks comfortable -- the low percentage is the symptom, not the health.
    on_treadmill = compactions >= TREADMILL_COMPACTIONS or (
        compactions >= 4 and carry is not None and carry < THIN_CARRY_RATIO
    )

    if pct is None:
        verdict = "no-telemetry"
    elif pct >= 90.0:
        verdict = "CRITICAL-window-exhausted"
    elif on_treadmill:
        verdict = "compact-treadmill"
    elif pct >= ROTATE_PCT:
        verdict = "rotate-soon"
    else:
        verdict = "healthy"
    if report["compacted_bytes"] > size * 0.5 and size > 100_000_000:
        verdict += "+compact-residue-dominant"
    report["verdict"] = verdict
    return report


def find_sessions(roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        if root.exists():
            found.extend(sorted(p for p in root.rglob("rollout-*.jsonl") if p.is_file()))
    return found


def main() -> int:
    args = parse_args()
    roots = [Path(args.root).expanduser()] if args.root else default_roots()
    paths = [Path(p).expanduser() for p in args.paths] or find_sessions(roots)
    reports = [health(p) for p in paths if p.is_file()]
    if args.json:
        print(json.dumps(reports, indent=2))
        return 0
    fmt = "{:>9}  {:>8}  {:>7}  {:>9}  {:>9}  {:>7}  {:>10}  {}"
    print(
        fmt.format(
            "size", "tokens", "ctx%", "resp_rows", "compacts", "carry", "compactMB", "session"
        )
    )
    for r in reports:
        carry = r.get("carry_forward_ratio")
        print(
            fmt.format(
                f"{r['bytes']/1e6:,.0f}MB",
                f"{(r['last_turn_input_tokens'] or 0)/1000:,.0f}k",
                f"{r['context_pct'] if r['context_pct'] is not None else '-'}",
                f"{r['response_item_rows']:,}",
                r["compacted_rows"],
                f"{carry:.0%}" if carry is not None else "-",
                f"{r['compacted_bytes']/1e6:,.1f}",
                os.path.basename(r["session"]),
            )
        )
        print(f"{'':9}  verdict: {r['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
