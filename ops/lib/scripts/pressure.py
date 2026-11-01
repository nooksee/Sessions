#!/usr/bin/env python3
"""Gate copied Codex JSONL candidates for compact/context pressure.

This is a deterministic proxy gate. It cannot prove that the hosted compact
service will accept a candidate, but it prevents repeating known bad shapes:
parse errors, weak response-item margin, excessive total bytes, and oversized
single rows.

Lane: session hygiene and VM load-test staging.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "Sessions" / "logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, help="Copied JSONL candidate to inspect.")
    parser.add_argument("--max-response-items", type=int, default=10000)
    parser.add_argument("--max-bytes", type=int, default=100_000_000)
    parser.add_argument("--max-largest-line-bytes", type=int, default=10_000_000)
    parser.add_argument("--stamp", help="Stable evidence stamp. Default: local timestamp.")
    parser.add_argument("--write-evidence", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_text_len(payload: Any) -> int:
    if not isinstance(payload, dict):
        return 0
    content = payload.get("content")
    if isinstance(content, str):
        return len(content)
    if not isinstance(content, list):
        return 0
    total = 0
    for block in content:
        if isinstance(block, str):
            total += len(block)
        elif isinstance(block, dict):
            for key in ("text", "input", "output"):
                value = block.get(key)
                if isinstance(value, str):
                    total += len(value)
    return total


def analyze(path: Path, max_response_items: int, max_bytes: int, max_largest_line_bytes: int) -> dict[str, Any]:
    rows = 0
    parse_errors = 0
    first_parse_error: dict[str, Any] | None = None
    response_items = 0
    compacted_rows = 0
    event_msg_rows = 0
    turn_context_rows = 0
    session_meta_rows = 0
    largest_line = {"line": 0, "bytes": 0}
    row_counts: Counter[str] = Counter()
    response_payload_types: Counter[str] = Counter()
    response_payload_bytes: Counter[str] = Counter()
    response_payload_text_chars: Counter[str] = Counter()

    stat_start = path.stat()
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
                if first_parse_error is None:
                    first_parse_error = {"line": rows, "error": str(exc)}
                continue

            if not isinstance(item, dict):
                row_counts[type(item).__name__] += 1
                continue
            row_type = str(item.get("type", "") or "missing")
            row_counts[row_type] += 1
            if row_type == "response_item":
                response_items += 1
                payload = item.get("payload")
                payload_type = "missing"
                if isinstance(payload, dict):
                    payload_type = str(payload.get("type", "") or "missing")
                response_payload_types[payload_type] += 1
                response_payload_bytes[payload_type] += line_bytes
                response_payload_text_chars[payload_type] += content_text_len(payload)
            elif row_type == "compacted":
                compacted_rows += 1
            elif row_type == "event_msg":
                event_msg_rows += 1
            elif row_type == "turn_context":
                turn_context_rows += 1
            elif row_type == "session_meta":
                session_meta_rows += 1

    stat_end = path.stat()
    byte_status = stat_end.st_size <= max_bytes
    response_status = response_items <= max_response_items
    largest_line_status = largest_line["bytes"] <= max_largest_line_bytes
    parse_status = parse_errors == 0
    gate_status = "pass" if all([parse_status, response_status, byte_status, largest_line_status]) else "fail"

    return {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "session": str(path),
        "sha256": sha256_file(path),
        "bytes": stat_end.st_size,
        "bytes_at_scan_start": stat_start.st_size,
        "bytes_at_scan_end": stat_end.st_size,
        "source_changed_during_scan": (
            stat_start.st_size != stat_end.st_size or stat_start.st_mtime_ns != stat_end.st_mtime_ns
        ),
        "rows": rows,
        "parse_errors": parse_errors,
        "first_parse_error": first_parse_error,
        "response_item_rows": response_items,
        "compacted_rows": compacted_rows,
        "event_msg_rows": event_msg_rows,
        "turn_context_rows": turn_context_rows,
        "session_meta_rows": session_meta_rows,
        "largest_line": largest_line,
        "max_response_items": max_response_items,
        "max_bytes": max_bytes,
        "max_largest_line_bytes": max_largest_line_bytes,
        "response_item_margin": max_response_items - response_items,
        "byte_margin": max_bytes - stat_end.st_size,
        "largest_line_margin": max_largest_line_bytes - largest_line["bytes"],
        "row_counts": dict(sorted(row_counts.items())),
        "response_payload_types": dict(sorted(response_payload_types.items())),
        "response_payload_bytes": dict(sorted(response_payload_bytes.items())),
        "response_payload_text_chars": dict(sorted(response_payload_text_chars.items())),
        "parse_status": "pass" if parse_status else "fail",
        "response_item_pressure_status": "pass" if response_status else "fail",
        "byte_pressure_status": "pass" if byte_status else "fail",
        "largest_line_pressure_status": "pass" if largest_line_status else "fail",
        "compact_context_pressure_status": gate_status,
        "production_session_edits": 0,
        "source_session_rewrites": 0,
        "jsonl_derivatives_promoted": 0,
        "auth_file_copies": 0,
        "automatic_codex_launches": 0,
        "permanent_deletes": 0,
    }


def write_evidence(summary: dict[str, Any], stamp: str) -> dict[str, str]:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    json_path = EVIDENCE / f"codex-compact-context-pressure-{stamp}.json"
    summary_path = EVIDENCE / f"codex-compact-context-pressure-{stamp}-summary.txt"
    csv_path = EVIDENCE / f"codex-compact-context-pressure-{stamp}.csv"

    summary_with_paths = dict(summary)
    summary_with_paths["evidence_files"] = {
        "json": str(json_path),
        "summary": str(summary_path),
        "csv": str(csv_path),
    }
    json_path.write_text(json.dumps(summary_with_paths, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "session",
                "bytes",
                "rows",
                "parse_errors",
                "response_item_rows",
                "largest_line_bytes",
                "compact_context_pressure_status",
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
                "response_item_rows": summary["response_item_rows"],
                "largest_line_bytes": summary["largest_line"]["bytes"],
                "compact_context_pressure_status": summary["compact_context_pressure_status"],
            }
        )

    lines = [
        "# Codex Compact Context Pressure Gate",
        "",
        f"generated: {summary['generated']}",
        f"session: {summary['session']}",
        f"bytes: {summary['bytes']}",
        f"rows: {summary['rows']}",
        f"parse_errors: {summary['parse_errors']}",
        f"response_item_rows: {summary['response_item_rows']}",
        f"response_item_margin: {summary['response_item_margin']}",
        f"largest_line_bytes: {summary['largest_line']['bytes']}",
        f"byte_pressure_status: {summary['byte_pressure_status']}",
        f"response_item_pressure_status: {summary['response_item_pressure_status']}",
        f"largest_line_pressure_status: {summary['largest_line_pressure_status']}",
        f"compact_context_pressure_status: {summary['compact_context_pressure_status']}",
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
    return {"json": str(json_path), "summary": str(summary_path), "csv": str(csv_path)}


def main() -> int:
    args = parse_args()
    path = Path(args.session).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise SystemExit(f"Session file not found: {path}")
    summary = analyze(path, args.max_response_items, args.max_bytes, args.max_largest_line_bytes)
    if args.write_evidence:
        stamp = args.stamp or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        summary["evidence_files"] = write_evidence(summary, stamp)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["compact_context_pressure_status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
