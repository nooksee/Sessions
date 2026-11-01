#!/usr/bin/env python3
"""Watch Codex sessions and emit operator-visible warnings.

Primary axis (2026-07-04): token pressure. Each rollout self-reports its
last-turn context usage in `event_msg`/`token_count` rows
(`last_token_usage.input_tokens` vs `model_context_window`). Auto-compact
fires at the window; the rotation doctrine warns at 70% and flags critical
at 90% (the compact treadmill).

Secondary axis: file bytes. auto_compact_v2 appends full replacement
history per compact, so runaway file growth is a thrash symptom even when
token pressure looks stable.

Read-only. Outputs are local evidence only (not tracked by git).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_SESSIONS_ROOTS = [
    Path("/home/nos4r2/.codex/sessions"),
    # George's home: the Workbench VM mounts this share as its sessions dir.
    Path("/media/nos4r2/user_vol/VMs/Shared/Workbench/sessions"),
]
SESSIONS = Path(__file__).resolve().parents[3]   # the room, resolved as gauge.py does
DEFAULT_EVIDENCE_DIR = SESSIONS / "logs"
DEFAULT_WARN_BYTES = 500_000_000
DEFAULT_CRITICAL_BYTES = 1_000_000_000
DEFAULT_WARN_CONTEXT_PCT = 70.0
DEFAULT_CRITICAL_CONTEXT_PCT = 90.0
TOKEN_TAIL_BYTES = 8_000_000

_SEVERITY = {"ok": 0, "warning": 1, "critical": 2}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def human_bytes(size: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{size} B"


def classify_bytes(size: int, warn_bytes: int, critical_bytes: int) -> str:
    if size >= critical_bytes:
        return "critical"
    if size >= warn_bytes:
        return "warning"
    return "ok"


def classify_context(pct: float | None, warn_pct: float, critical_pct: float) -> str:
    if pct is None:
        return "ok"
    if pct >= critical_pct:
        return "critical"
    if pct >= warn_pct:
        return "warning"
    return "ok"


def read_session_id(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            first_line = handle.readline()
        if not first_line:
            return ""
        data = json.loads(first_line)
        if not isinstance(data, dict):
            return ""
        payload = data.get("payload", {})
        if isinstance(payload, dict) and payload.get("id"):
            return str(payload["id"])
        if data.get("id"):
            return str(data["id"])
    except Exception as exc:  # pragma: no cover - receipt value only
        return f"unreadable:{type(exc).__name__}"
    return ""


def read_token_telemetry(path: Path) -> dict[str, object]:
    """Last token_count event from the file tail: the number auto-compact acts on."""
    empty = {"last_turn_input_tokens": None, "model_context_window": None, "context_pct": None}
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            handle.seek(max(0, size - TOKEN_TAIL_BYTES))
            lines = handle.read().split(b"\n")
    except OSError:
        return empty
    for line in reversed(lines):
        if b'"token_count"' not in line:
            continue
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        info = (row.get("payload") or {}).get("info") or {}
        last = info.get("last_token_usage") or {}
        window = info.get("model_context_window") or 0
        input_tokens = last.get("input_tokens") or 0
        if not window:
            continue
        return {
            "last_turn_input_tokens": input_tokens,
            "model_context_window": window,
            "context_pct": round(100.0 * input_tokens / window, 1),
        }
    return empty


def scan_sessions(roots: list[Path], args: argparse.Namespace) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    paths: list[Path] = []
    for root in roots:
        if root.exists():
            paths.extend(sorted(root.rglob("*.jsonl")))
    for path in paths:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        telemetry = read_token_telemetry(path)
        byte_status = classify_bytes(size, args.warn_bytes, args.critical_bytes)
        token_status = classify_context(
            telemetry["context_pct"], args.warn_context_pct, args.critical_context_pct
        )
        status = max(byte_status, token_status, key=lambda s: _SEVERITY[s])
        records.append(
            {
                "path": str(path),
                "bytes": size,
                "human_bytes": human_bytes(size),
                "byte_status": byte_status,
                "token_status": token_status,
                "status": status,
                "session_id": read_session_id(path),
                **telemetry,
            }
        )
    records.sort(
        key=lambda r: (_SEVERITY[str(r["status"])], r["context_pct"] or 0.0, int(r["bytes"])),
        reverse=True,
    )
    return records


def build_result(records: list[dict[str, object]], args: argparse.Namespace) -> dict[str, object]:
    critical_count = sum(1 for record in records if record["status"] == "critical")
    warning_count = sum(1 for record in records if record["status"] == "warning")
    overall_status = "critical" if critical_count else "warning" if warning_count else "ok"
    return {
        "generated_at": utc_now(),
        "sessions_root": ", ".join(str(r) for r in args.sessions_root),
        "warn_bytes": args.warn_bytes,
        "critical_bytes": args.critical_bytes,
        "warn_context_pct": args.warn_context_pct,
        "critical_context_pct": args.critical_context_pct,
        "overall_status": overall_status,
        "session_count": len(records),
        "warning_count": warning_count,
        "critical_count": critical_count,
        "top": records[: args.top],
        "safety_counters": {
            "production_session_edits": 0,
            "jsonl_promotions": 0,
            "automatic_codex_launches": 0,
        },
    }


def write_outputs(result: dict[str, object], evidence_dir: Path) -> tuple[Path, Path]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    json_path = evidence_dir / "codex-session-size-watch-current.json"
    summary_path = evidence_dir / "codex-session-size-watch-summary.txt"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "Codex session watch (tokens primary, bytes secondary)",
        f"generated_at: {result['generated_at']}",
        f"sessions_root: {result['sessions_root']}",
        f"warn_context_pct: {result['warn_context_pct']}",
        f"critical_context_pct: {result['critical_context_pct']}",
        f"warn_bytes: {result['warn_bytes']}",
        f"critical_bytes: {result['critical_bytes']}",
        f"overall_status: {result['overall_status']}",
        f"session_count: {result['session_count']}",
        f"warning_count: {result['warning_count']}",
        f"critical_count: {result['critical_count']}",
        "safety.production_session_edits: 0",
        "safety.jsonl_promotions: 0",
        "safety.automatic_codex_launches: 0",
        "",
        "Top sessions:",
    ]
    for index, record in enumerate(result["top"], start=1):
        pct = record["context_pct"]
        tokens = record["last_turn_input_tokens"]
        ctx = f"ctx={pct}% ({tokens:,} tok)" if pct is not None else "ctx=n/a"
        lines.append(
            f"{index}. {record['status']} {ctx} {record['human_bytes']} "
            f"{record['session_id']} {record['path']}"
        )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, summary_path


def send_notification(result: dict[str, object]) -> None:
    if result["overall_status"] == "ok":
        return
    notify_send = shutil.which("notify-send")
    if not notify_send:
        return
    top = result.get("top") or []
    lead = top[0] if top else {}
    title = "Codex session watch warning"
    if result["overall_status"] == "critical":
        title = "Codex session watch critical"
    pct = lead.get("context_pct")
    body = (
        f"context={pct if pct is not None else 'n/a'}% "
        f"(rotate at {result['warn_context_pct']}%) "
        f"largest={lead.get('human_bytes', 'unknown')}"
    )
    subprocess.run([notify_send, title, body], check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only Codex session watcher (tokens + bytes).")
    parser.add_argument(
        "--sessions-root",
        type=Path,
        action="append",
        default=None,
        help="Session root to scan; repeatable. Default: host + Workbench VM share.",
    )
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR)
    parser.add_argument("--warn-bytes", type=int, default=DEFAULT_WARN_BYTES)
    parser.add_argument("--critical-bytes", type=int, default=DEFAULT_CRITICAL_BYTES)
    parser.add_argument("--warn-context-pct", type=float, default=DEFAULT_WARN_CONTEXT_PCT)
    parser.add_argument("--critical-context-pct", type=float, default=DEFAULT_CRITICAL_CONTEXT_PCT)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--fail-on-critical", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.sessions_root:
        args.sessions_root = DEFAULT_SESSIONS_ROOTS
    records = scan_sessions(args.sessions_root, args)
    result = build_result(records, args)
    _json_path, summary_path = write_outputs(result, Path(args.evidence_dir))
    if args.notify:
        send_notification(result)
    print(summary_path)
    if args.fail_on_critical and result["critical_count"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
