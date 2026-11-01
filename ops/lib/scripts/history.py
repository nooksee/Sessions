#!/usr/bin/env python3
"""Inspect Codex compacted-history rows without modifying session files."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "Sessions" / "logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", help="Explicit session JSONL to inspect.")
    parser.add_argument("--latest", action="store_true", help="Inspect the newest largest live session.")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--evidence-dir", default=str(EVIDENCE))
    parser.add_argument("--max-largest-items", type=int, default=40)
    parser.add_argument("--hash", action="store_true", help="Compute SHA-256 for the source session.")
    return parser.parse_args()


def is_session_file(path: Path) -> bool:
    name = path.name.lower()
    return path.is_file() and (name.endswith(".jsonl") or name.endswith(".jsonl.backup"))


def find_latest_session(codex_home: Path) -> Path:
    root = codex_home / "sessions"
    candidates = [path for path in root.rglob("*") if is_session_file(path)] if root.exists() else []
    if not candidates:
        raise SystemExit(f"No live session files found under {root}")
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.stat().st_size))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def content_metrics(content: Any) -> tuple[int, Counter[str], defaultdict[str, int]]:
    total = 0
    block_types: Counter[str] = Counter()
    block_bytes: defaultdict[str, int] = defaultdict(int)
    if isinstance(content, str):
        block_types["string"] += 1
        block_bytes["string"] += len(content.encode("utf-8"))
        return len(content.encode("utf-8")), block_types, block_bytes
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                block_type = str(block.get("type", "dict"))
                block_types[block_type] += 1
                block_bytes[block_type] += json_bytes(block)
                for key in ("text", "input", "output"):
                    value = block.get(key)
                    if isinstance(value, str):
                        total += len(value.encode("utf-8"))
            elif isinstance(block, str):
                block_types["string"] += 1
                string_bytes = len(block.encode("utf-8"))
                total += string_bytes
                block_bytes["string"] += string_bytes
            else:
                block_type = type(block).__name__
                block_types[block_type] += 1
                block_bytes[block_type] += json_bytes(block)
    return total, block_types, block_bytes


def classify_history_item(
    item: Any,
) -> tuple[str, str, int, Counter[str], defaultdict[str, int], str]:
    if not isinstance(item, dict):
        return "non_dict", type(item).__name__, 0, Counter(), defaultdict(int), ""
    item_type = str(item.get("type", ""))
    role = str(item.get("role", ""))
    text_bytes, block_types, block_bytes = content_metrics(item.get("content"))
    category = "history_other"
    if item_type == "message" and role:
        if role in {"system", "developer"}:
            category = "history_instruction"
        elif role == "user":
            category = "history_user"
        elif role == "assistant":
            category = "history_assistant"
        else:
            category = f"history_message_{role}"
    elif "tool" in item_type.lower() or "call" in item_type.lower():
        category = "history_tool_call"
    elif "output" in item_type.lower() or "result" in item_type.lower():
        category = "history_tool_output"
    reason = f"type={item_type or 'missing'} role={role or 'missing'}"
    return category, reason, text_bytes, block_types, block_bytes, item_type


def inspect(path: Path, max_largest_items: int) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    stat_start = path.stat()
    generated = dt.datetime.now().isoformat(timespec="seconds")
    line_count = 0
    parsed_lines = 0
    parse_errors = 0
    compacted_rows = 0
    compacted_bytes = 0
    message_bytes = 0
    replacement_history_bytes = 0
    replacement_history_items = 0
    empty_message_rows = 0
    payload_key_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    category_bytes: defaultdict[str, int] = defaultdict(int)
    category_text_bytes: defaultdict[str, int] = defaultdict(int)
    item_type_counts: Counter[str] = Counter()
    block_type_counts: Counter[str] = Counter()
    block_type_bytes: defaultdict[str, int] = defaultdict(int)
    largest_rows: list[dict[str, Any]] = []
    largest_items: list[dict[str, Any]] = []

    with path.open("rb") as handle:
        for raw in handle:
            line_count += 1
            raw_len = len(raw)
            try:
                row = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                parse_errors += 1
                continue
            parsed_lines += 1
            if not (isinstance(row, dict) and row.get("type") == "compacted"):
                continue

            compacted_rows += 1
            compacted_bytes += raw_len
            payload = row.get("payload")
            row_message_bytes = 0
            row_history_bytes = 0
            row_history_items = 0
            if isinstance(payload, dict):
                payload_key_counts.update(str(key) for key in payload.keys())
                message = payload.get("message")
                history = payload.get("replacement_history")
                row_message_bytes = json_bytes(message)
                row_history_bytes = json_bytes(history)
                message_bytes += row_message_bytes
                replacement_history_bytes += row_history_bytes
                if message == "":
                    empty_message_rows += 1
                if isinstance(history, list):
                    row_history_items = len(history)
                    replacement_history_items += row_history_items
                    for index, item in enumerate(history):
                        item_bytes = json_bytes(item)
                        category, reason, text_bytes, block_types, block_bytes, item_type = classify_history_item(item)
                        category_counts[category] += 1
                        category_bytes[category] += item_bytes
                        category_text_bytes[category] += text_bytes
                        if item_type:
                            item_type_counts[item_type] += 1
                        block_type_counts.update(block_types)
                        for block_type, bytes_value in block_bytes.items():
                            block_type_bytes[block_type] += bytes_value
                        largest_items.append(
                            {
                                "line_number": line_count,
                                "history_index": index,
                                "item_bytes": item_bytes,
                                "category": category,
                                "reason": reason,
                                "text_bytes": text_bytes,
                                "block_types": ";".join(
                                    f"{key}:{value}" for key, value in block_types.most_common(6)
                                ),
                                "block_bytes": ";".join(
                                    f"{key}:{value}"
                                    for key, value in sorted(
                                        block_bytes.items(),
                                        key=lambda item_pair: item_pair[1],
                                        reverse=True,
                                    )[:6]
                                ),
                            }
                        )
                        if len(largest_items) > max_largest_items * 4:
                            largest_items = sorted(
                                largest_items,
                                key=lambda item_row: int(item_row["item_bytes"]),
                                reverse=True,
                            )[:max_largest_items]

            largest_rows.append(
                {
                    "line_number": line_count,
                    "line_bytes": raw_len,
                    "payload_keys": ",".join(sorted(payload.keys())) if isinstance(payload, dict) else "",
                    "message_json_bytes": row_message_bytes,
                    "replacement_history_json_bytes": row_history_bytes,
                    "replacement_history_items": row_history_items,
                    "message_empty": row_message_bytes == 2,
                }
            )
            if len(largest_rows) > max_largest_items * 4:
                largest_rows = sorted(
                    largest_rows,
                    key=lambda row_item: int(row_item["line_bytes"]),
                    reverse=True,
                )[:max_largest_items]

    stat_end = path.stat()
    category_rows = []
    for category in sorted(category_counts, key=lambda key: category_bytes[key], reverse=True):
        bytes_value = category_bytes[category]
        category_rows.append(
            {
                "category": category,
                "count": category_counts[category],
                "item_bytes": bytes_value,
                "percent_of_replacement_history": round(
                    bytes_value / replacement_history_bytes * 100, 4
                )
                if replacement_history_bytes
                else 0,
                "text_bytes": category_text_bytes[category],
            }
        )

    largest_rows = sorted(largest_rows, key=lambda row_item: int(row_item["line_bytes"]), reverse=True)[
        :max_largest_items
    ]
    largest_items = sorted(largest_items, key=lambda item_row: int(item_row["item_bytes"]), reverse=True)[
        :max_largest_items
    ]
    summary = {
        "generated": generated,
        "session": str(path),
        "bytes": stat_end.st_size,
        "bytes_at_scan_start": stat_start.st_size,
        "bytes_at_scan_end": stat_end.st_size,
        "modified_at_scan_start": dt.datetime.fromtimestamp(stat_start.st_mtime).isoformat(timespec="seconds"),
        "modified_at_scan_end": dt.datetime.fromtimestamp(stat_end.st_mtime).isoformat(timespec="seconds"),
        "source_changed_during_scan": (
            stat_start.st_size != stat_end.st_size or stat_start.st_mtime_ns != stat_end.st_mtime_ns
        ),
        "line_count": line_count,
        "parsed_lines": parsed_lines,
        "parse_errors": parse_errors,
        "compacted_rows": compacted_rows,
        "compacted_bytes": compacted_bytes,
        "percent_of_file": round(compacted_bytes / stat_end.st_size * 100, 4) if stat_end.st_size else 0,
        "message_json_bytes": message_bytes,
        "replacement_history_json_bytes": replacement_history_bytes,
        "replacement_history_items": replacement_history_items,
        "empty_message_rows": empty_message_rows,
        "payload_key_counts": dict(payload_key_counts.most_common()),
        "category_rows": category_rows,
        "item_type_counts": dict(item_type_counts.most_common()),
        "block_type_counts": dict(block_type_counts.most_common()),
        "block_type_bytes": dict(
            sorted(block_type_bytes.items(), key=lambda item: item[1], reverse=True)
        ),
        "source_session_edits": 0,
        "raw_source_rewrites": 0,
        "jsonl_derivatives_promoted": 0,
        "active_session_reducer_authorized": False,
    }
    return summary, largest_rows, largest_items


def write_outputs(
    summary: dict[str, Any],
    largest_rows: list[dict[str, Any]],
    largest_items: list[dict[str, Any]],
    evidence_dir: Path,
) -> dict[str, Path]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = evidence_dir / f"codex-session-compacted-history-{stamp}.json"
    rows_path = evidence_dir / f"codex-session-compacted-history-rows-{stamp}.csv"
    items_path = evidence_dir / f"codex-session-compacted-history-largest-items-{stamp}.csv"
    summary_path = evidence_dir / f"codex-session-compacted-history-{stamp}-summary.txt"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with rows_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "line_number",
                "line_bytes",
                "payload_keys",
                "message_json_bytes",
                "replacement_history_json_bytes",
                "replacement_history_items",
                "message_empty",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(largest_rows)
    with items_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "line_number",
                "history_index",
                "item_bytes",
                "category",
                "reason",
                "text_bytes",
                "block_types",
                "block_bytes",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(largest_items)

    category_lines = "\n".join(
        (
            f"- {row['category']}: {row['item_bytes']} bytes, "
            f"{row['percent_of_replacement_history']}%, {row['count']} items"
        )
        for row in summary["category_rows"]
    ) or "- none"
    largest_line = largest_rows[0] if largest_rows else {}
    largest_item = largest_items[0] if largest_items else {}
    block_pressure_lines = "\n".join(
        f"- {key}: {value} bytes"
        for key, value in summary["block_type_bytes"].items()
    ) or "- none"
    text = f"""Codex Session Compacted History Inspection
generated: {summary['generated']}
session: {summary['session']}
bytes: {summary['bytes']}
line_count: {summary['line_count']}
parsed_lines: {summary['parsed_lines']}
parse_errors: {summary['parse_errors']}
source_changed_during_scan: {summary['source_changed_during_scan']}

Compacted history:
- compacted_rows: {summary['compacted_rows']}
- compacted_bytes: {summary['compacted_bytes']}
- percent_of_file: {summary['percent_of_file']}
- payload_keys: {summary['payload_key_counts']}
- empty_message_rows: {summary['empty_message_rows']}
- message_json_bytes: {summary['message_json_bytes']}
- replacement_history_json_bytes: {summary['replacement_history_json_bytes']}
- replacement_history_items: {summary['replacement_history_items']}

Largest compacted row:
- line_number: {largest_line.get('line_number', '')}
- line_bytes: {largest_line.get('line_bytes', '')}
- replacement_history_items: {largest_line.get('replacement_history_items', '')}
- replacement_history_json_bytes: {largest_line.get('replacement_history_json_bytes', '')}

Largest replacement-history item:
- line_number: {largest_item.get('line_number', '')}
- history_index: {largest_item.get('history_index', '')}
- item_bytes: {largest_item.get('item_bytes', '')}
- category: {largest_item.get('category', '')}
- reason: {largest_item.get('reason', '')}

Replacement-history item pressure:
{category_lines}

Replacement-history block byte pressure:
{block_pressure_lines}

Doctrine:
- source_session_edits: 0
- raw_source_rewrites: 0
- jsonl_derivatives_promoted: 0
- active_session_reducer_authorized: False
- compacted history remains untouchable until derivative sandbox proof exists.
"""
    summary_path.write_text(text, encoding="utf-8")

    for source, target in (
        (json_path, evidence_dir / "codex-session-compacted-history-current.json"),
        (rows_path, evidence_dir / "codex-session-compacted-history-rows-current.csv"),
        (items_path, evidence_dir / "codex-session-compacted-history-largest-items-current.csv"),
        (summary_path, evidence_dir / "codex-session-compacted-history-summary.txt"),
    ):
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "json": json_path,
        "rows": rows_path,
        "items": items_path,
        "summary": summary_path,
    }


def main() -> None:
    args = parse_args()
    if args.session:
        session = Path(args.session)
    elif args.latest:
        session = find_latest_session(Path(args.codex_home))
    else:
        raise SystemExit("Use --session PATH or --latest.")
    if not session.exists():
        raise SystemExit(f"Session not found: {session}")

    summary, largest_rows, largest_items = inspect(session, args.max_largest_items)
    if args.hash:
        summary["sha256"] = sha256_file(session)
    outputs = write_outputs(summary, largest_rows, largest_items, Path(args.evidence_dir))
    print(f"session: {session}")
    print(f"compacted_rows: {summary['compacted_rows']}")
    print(f"compacted_bytes: {summary['compacted_bytes']}")
    print(f"percent_of_file: {summary['percent_of_file']}")
    print(f"message_json_bytes: {summary['message_json_bytes']}")
    print(f"replacement_history_json_bytes: {summary['replacement_history_json_bytes']}")
    print(f"replacement_history_items: {summary['replacement_history_items']}")
    for label, path in outputs.items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
