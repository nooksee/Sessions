#!/usr/bin/env python3
"""Validate copied Codex JSONL candidates against observed loader limits.

This script is read-only with respect to the session being inspected. It does
not edit live sessions, promote derivatives, copy auth files, or launch Codex.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "Sessions" / "logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, help="JSONL session candidate to validate.")
    parser.add_argument(
        "--max-input-items",
        type=int,
        default=16384,
        help="Observed maximum API input item count. Default: 16384.",
    )
    parser.add_argument("--stamp", help="Stable evidence stamp. Default: local timestamp.")
    parser.add_argument("--write-evidence", action="store_true", help="Write evidence files under Sessions/logs.")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_preview(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    payload = value.get("payload")
    if not isinstance(payload, dict):
        return ""
    content = payload.get("content")
    if isinstance(content, str):
        return content.replace("\n", " ")[:240]
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict):
            for key in ("text", "input", "output"):
                item = block.get(key)
                if isinstance(item, str):
                    parts.append(item.replace("\n", " ")[:120])
                    break
            else:
                block_type = block.get("type")
                if isinstance(block_type, str):
                    parts.append(block_type[:120])
        elif isinstance(block, str):
            parts.append(block.replace("\n", " ")[:120])
    return " | ".join(parts)[:240]


def validate(path: Path, max_input_items: int) -> dict[str, Any]:
    stat_start = path.stat()
    rows = 0
    parse_errors = 0
    response_items = 0
    event_rows = 0
    compacted_rows = 0
    turn_context_rows = 0
    session_meta_rows = 0
    first_response_item_over_limit: dict[str, Any] | None = None
    first_message_after_limit: dict[str, Any] | None = None
    largest_line = {"line": 0, "bytes": 0}
    response_payload_types: dict[str, int] = {}

    with path.open("rb") as handle:
        for raw in handle:
            rows += 1
            line_bytes = len(raw)
            if line_bytes > largest_line["bytes"]:
                largest_line = {"line": rows, "bytes": line_bytes}
            try:
                item = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                parse_errors += 1
                if parse_errors == 1:
                    first_parse_error = {"line": rows, "error": str(exc)}
                continue

            if not isinstance(item, dict):
                continue
            row_type = item.get("type")
            if row_type == "response_item":
                response_items += 1
                payload = item.get("payload")
                payload_type = ""
                role = ""
                if isinstance(payload, dict):
                    payload_type = str(payload.get("type", ""))
                    role = str(payload.get("role", ""))
                    response_payload_types[payload_type or "<missing>"] = (
                        response_payload_types.get(payload_type or "<missing>", 0) + 1
                    )
                if response_items == max_input_items + 1:
                    first_response_item_over_limit = {
                        "line": rows,
                        "response_item_prefix_count": response_items,
                        "payload_type": payload_type,
                        "role": role,
                        "preview": text_preview(item),
                    }
                if (
                    first_message_after_limit is None
                    and response_items > max_input_items
                    and payload_type == "message"
                ):
                    first_message_after_limit = {
                        "line": rows,
                        "response_item_prefix_count": response_items,
                        "role": role,
                        "preview": text_preview(item),
                    }
            elif row_type == "event_msg":
                event_rows += 1
            elif row_type == "compacted":
                compacted_rows += 1
            elif row_type == "turn_context":
                turn_context_rows += 1
            elif row_type == "session_meta":
                session_meta_rows += 1

    stat_end = path.stat()
    over_limit_by = max(0, response_items - max_input_items)
    status = "pass" if parse_errors == 0 and response_items <= max_input_items else "fail"
    summary: dict[str, Any] = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "session": str(path),
        "bytes": stat_end.st_size,
        "bytes_at_scan_start": stat_start.st_size,
        "bytes_at_scan_end": stat_end.st_size,
        "source_changed_during_scan": (
            stat_start.st_size != stat_end.st_size
            or stat_start.st_mtime_ns != stat_end.st_mtime_ns
        ),
        "sha256": sha256_file(path),
        "rows": rows,
        "parse_errors": parse_errors,
        "max_input_items": max_input_items,
        "response_item_rows": response_items,
        "response_item_rows_over_limit": over_limit_by,
        "event_msg_rows": event_rows,
        "compacted_rows": compacted_rows,
        "turn_context_rows": turn_context_rows,
        "session_meta_rows": session_meta_rows,
        "largest_line": largest_line,
        "response_payload_types": dict(sorted(response_payload_types.items())),
        "first_response_item_over_limit": first_response_item_over_limit,
        "first_message_after_limit": first_message_after_limit,
        "loader_limit_status": status,
        "production_session_edits": 0,
        "source_session_rewrites": 0,
        "jsonl_derivatives_promoted": 0,
        "auth_file_copies": 0,
        "automatic_codex_launches": 0,
        "permanent_deletes": 0,
    }
    if parse_errors:
        summary["first_parse_error"] = first_parse_error
    return summary


def write_evidence(summary: dict[str, Any], stamp: str) -> dict[str, str]:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    json_path = EVIDENCE / f"codex-session-loader-limit-validation-{stamp}.json"
    summary_path = EVIDENCE / f"codex-session-loader-limit-validation-{stamp}-summary.txt"
    csv_path = EVIDENCE / f"codex-session-loader-limit-validation-{stamp}.csv"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "session",
                "bytes",
                "rows",
                "parse_errors",
                "max_input_items",
                "response_item_rows",
                "response_item_rows_over_limit",
                "loader_limit_status",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(
            {
                "session": summary["session"],
                "bytes": summary["bytes"],
                "rows": summary["rows"],
                "parse_errors": summary["parse_errors"],
                "max_input_items": summary["max_input_items"],
                "response_item_rows": summary["response_item_rows"],
                "response_item_rows_over_limit": summary["response_item_rows_over_limit"],
                "loader_limit_status": summary["loader_limit_status"],
            }
        )

    first_over = summary.get("first_response_item_over_limit") or {}
    first_message = summary.get("first_message_after_limit") or {}
    lines = [
        "# Codex Session Loader-Limit Validation",
        "",
        f"generated: {summary['generated']}",
        f"session: {summary['session']}",
        f"bytes: {summary['bytes']}",
        f"rows: {summary['rows']}",
        f"parse_errors: {summary['parse_errors']}",
        f"max_input_items: {summary['max_input_items']}",
        f"response_item_rows: {summary['response_item_rows']}",
        f"response_item_rows_over_limit: {summary['response_item_rows_over_limit']}",
        f"loader_limit_status: {summary['loader_limit_status']}",
        "",
        "First response item over limit:",
        f"- line: {first_over.get('line', '')}",
        f"- response_item_prefix_count: {first_over.get('response_item_prefix_count', '')}",
        f"- payload_type: {first_over.get('payload_type', '')}",
        f"- role: {first_over.get('role', '')}",
        "",
        "First message after limit:",
        f"- line: {first_message.get('line', '')}",
        f"- response_item_prefix_count: {first_message.get('response_item_prefix_count', '')}",
        f"- role: {first_message.get('role', '')}",
        "",
        "Safety counts:",
        "- production_session_edits: 0",
        "- source_session_rewrites: 0",
        "- jsonl_derivatives_promoted: 0",
        "- auth_file_copies: 0",
        "- automatic_codex_launches: 0",
        "- permanent_deletes: 0",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "json": str(json_path),
        "summary": str(summary_path),
        "csv": str(csv_path),
    }


def main() -> int:
    args = parse_args()
    session = Path(args.session).expanduser().resolve()
    if not session.exists() or not session.is_file():
        raise SystemExit(f"Session file not found: {session}")
    summary = validate(session, args.max_input_items)
    if args.write_evidence:
        stamp = args.stamp or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        summary["evidence_files"] = write_evidence(summary, stamp)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["loader_limit_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
