#!/usr/bin/env python3
"""Analyze Codex session JSONL pressure without modifying session files."""

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
INVENTORY = ROOT / "Sessions" / "logs"
BLOAT_PATTERNS = (
    "progress",
    "replacement_history",
    "ui_state",
    "telemetry",
    "snapshot",
    "diff",
    "stdout",
    "stderr",
    "tool",
    "screenshot",
    "image",
    "attachment",
)
TYPE_KEYS = ("type", "event_type", "kind", "role", "source", "status")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", help="Explicit session JSONL or JSONL backup to analyze.")
    parser.add_argument("--latest", action="store_true", help="Analyze the largest newest session under CODEX_HOME sessions.")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--inventory-dir", default=str(INVENTORY))
    parser.add_argument("--max-largest-lines", type=int, default=25)
    parser.add_argument("--hash", action="store_true", help="Compute SHA-256 for the source session.")
    parser.add_argument(
        "--reducer-inventory",
        action="store_true",
        help="Write reducer policy inventory outputs with category percentages and reduce status.",
    )
    return parser.parse_args()


def is_session_file(path: Path) -> bool:
    name = path.name.lower()
    return path.is_file() and (name.endswith(".jsonl") or name.endswith(".jsonl.backup"))


def find_latest_session(codex_home: Path) -> Path:
    roots = [codex_home / "sessions", codex_home / "archived_sessions"]
    candidates: list[Path] = []
    for root in roots:
        if root.exists():
            candidates.extend(path for path in root.rglob("*") if is_session_file(path))
    if not candidates:
        raise SystemExit(f"No session files found under {codex_home}")
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.stat().st_size))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact_value(value: Any) -> str:
    if isinstance(value, str):
        return value[:120]
    if isinstance(value, (int, float, bool)) or value is None:
        return json.dumps(value)
    if isinstance(value, list):
        return f"list[{len(value)}]"
    if isinstance(value, dict):
        return f"dict[{len(value)}]"
    return type(value).__name__


def walk_keys(value: Any, prefix: str = "", depth: int = 0, max_depth: int = 4) -> list[str]:
    if depth > max_depth:
        return []
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            keys.append(name)
            keys.extend(walk_keys(child, name, depth + 1, max_depth))
    elif isinstance(value, list):
        for item in value[:3]:
            keys.extend(walk_keys(item, f"{prefix}[]", depth + 1, max_depth))
    return keys


def classify_bloat(keys: list[str], payload: Any) -> set[str]:
    text_keys = " ".join(keys).lower()
    found = {pattern for pattern in BLOAT_PATTERNS if pattern in text_keys}
    if isinstance(payload, dict):
        payload_type = " ".join(
            str(payload.get(key, ""))
            for key in TYPE_KEYS
            if payload.get(key) is not None
        ).lower()
        found.update(pattern for pattern in BLOAT_PATTERNS if pattern in payload_type)
    return found


def json_size(value: Any) -> int:
    return len(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def text_from_content_blocks(content: Any) -> tuple[int, Counter[str]]:
    total = 0
    block_types: Counter[str] = Counter()
    if isinstance(content, str):
        block_types["string"] += 1
        return len(content.encode("utf-8")), block_types
    if not isinstance(content, list):
        return 0, block_types
    for block in content:
        if isinstance(block, dict):
            block_type = str(block.get("type", "dict"))
            block_types[block_type] += 1
            for key in ("text", "input", "output"):
                value = block.get(key)
                if isinstance(value, str):
                    total += len(value.encode("utf-8"))
        elif isinstance(block, str):
            block_types["string"] += 1
            total += len(block.encode("utf-8"))
        else:
            block_types[type(block).__name__] += 1
    return total, block_types


def reducer_status_for_category(category: str) -> tuple[str, str, str]:
    table = {
        "session_structure": (
            "untouchable",
            "Codex loader and extension identity evidence.",
            "Preserve exactly.",
        ),
        "event_bookkeeping": (
            "untouchable_until_sandbox_proven",
            "Turn, progress, and lifecycle records may be loader-visible.",
            "Preserve in load candidates; summarize only in readable exports.",
        ),
        "compaction_history": (
            "untouchable_until_sandbox_proven",
            "Compacted rows dominate size but may be compatibility anchors.",
            "Measure first; never remove from load candidates without a sandbox receipt.",
        ),
        "instruction_context": (
            "mostly_untouchable",
            "Developer, system, skill, and environment instructions define behavior.",
            "Preserve recent and governing instructions; only dedupe copied boilerplate after proof.",
        ),
        "conversation_user": (
            "semantically_reducible",
            "User prose can often be distilled into decisions, constraints, facts, and open loops.",
            "Reduce prose only after extracting canonical facts and preserving explicit instructions.",
        ),
        "conversation_assistant": (
            "semantically_reducible",
            "Prose from the assistant often contains repeated reasoning, status reports, and summaries.",
            "Reduce to outcomes, commands, files changed, validation, and next state.",
        ),
        "tool_call": (
            "structure_preserve_payload_candidate",
            "Tool-call linkage may matter; arguments can be bulky.",
            "Preserve call structure; summarize or externalize large arguments only in copied candidates.",
        ),
        "tool_output": (
            "high_value_reducer_candidate",
            "Command output and tool results are often the highest safe reduction target.",
            "Replace large outputs with typed receipts, hashes, and external archived logs in candidates.",
        ),
        "image_or_attachment_payload": (
            "externalize_candidate",
            "Images and attachments are usually better represented by paths, hashes, and manifests.",
            "Externalize payloads; preserve references and provenance.",
        ),
        "other_response_item": (
            "measure_before_touch",
            "Response item subtype is not yet classified.",
            "Inventory first, then classify by observed schema.",
        ),
        "unknown": (
            "measure_before_touch",
            "Unknown schema cannot be safely reduced.",
            "Preserve until classified.",
        ),
        "unparsed": (
            "untouchable_error",
            "Invalid JSONL rows need repair evidence before any reduction.",
            "Do not reduce; report parse error.",
        ),
    }
    return table.get(category, table["unknown"])


def classify_reducer_row(payload: Any) -> tuple[str, str, Counter[str], int]:
    block_types: Counter[str] = Counter()
    text_bytes = 0
    if not isinstance(payload, dict):
        return "unknown", "non-dict row", block_types, text_bytes

    row_type = str(payload.get("type", ""))
    if row_type == "session_meta":
        return "session_structure", "session_meta", block_types, text_bytes
    if row_type == "turn_context":
        return "session_structure", "turn_context", block_types, text_bytes
    if row_type == "event_msg":
        return "event_bookkeeping", str(payload.get("payload", {}).get("type", "event_msg")), block_types, text_bytes
    if row_type == "compacted":
        return "compaction_history", "compacted", block_types, text_bytes

    if row_type != "response_item":
        return "unknown", row_type or "missing type", block_types, text_bytes

    inner = payload.get("payload")
    if not isinstance(inner, dict):
        return "other_response_item", "payload is not dict", block_types, text_bytes
    inner_type = str(inner.get("type", ""))
    role = str(inner.get("role", ""))
    text_bytes, block_types = text_from_content_blocks(inner.get("content"))
    block_name = ",".join(f"{key}:{value}" for key, value in block_types.most_common(4))

    if inner_type == "message":
        if any("image" in key.lower() or "attachment" in key.lower() for key in block_types):
            return (
                "image_or_attachment_payload",
                f"message role {role or 'missing'} {block_name}".strip(),
                block_types,
                text_bytes,
            )
        if role == "user":
            return "conversation_user", f"message role user {block_name}".strip(), block_types, text_bytes
        if role == "assistant":
            return "conversation_assistant", f"message role assistant {block_name}".strip(), block_types, text_bytes
        if role in {"developer", "system"}:
            return "instruction_context", f"message role {role} {block_name}".strip(), block_types, text_bytes
        return "other_response_item", f"message role {role or 'missing'}", block_types, text_bytes

    lower_type = inner_type.lower()
    type_and_keys = " ".join([lower_type, " ".join(str(key).lower() for key in inner.keys())])
    if "image" in type_and_keys or "attachment" in type_and_keys:
        return "image_or_attachment_payload", inner_type or "image-like response item", block_types, text_bytes
    if "output" in lower_type or "result" in lower_type:
        return "tool_output", inner_type or "tool output", block_types, text_bytes
    if "call" in lower_type or "tool" in lower_type or "function" in lower_type:
        return "tool_call", inner_type or "tool call", block_types, text_bytes
    return "other_response_item", inner_type or "response_item", block_types, text_bytes


def analyze(path: Path, max_largest_lines: int) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    stat = path.stat()
    line_count = 0
    parsed_lines = 0
    parse_errors = 0
    total_line_bytes = 0
    top_keys: Counter[str] = Counter()
    nested_keys: Counter[str] = Counter()
    type_values: Counter[str] = Counter()
    bloat_counts: Counter[str] = Counter()
    repeated_hashes: Counter[str] = Counter()
    size_by_type: defaultdict[str, int] = defaultdict(int)
    count_by_type: Counter[str] = Counter()
    largest: list[dict[str, Any]] = []
    parse_error_rows: list[dict[str, Any]] = []

    with path.open("rb") as handle:
        for raw in handle:
            line_count += 1
            size = len(raw)
            total_line_bytes += size
            digest = hashlib.sha1(raw).hexdigest()
            repeated_hashes[digest] += 1
            row_type = "unparsed"
            keys: list[str] = []
            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                parse_errors += 1
                if len(parse_error_rows) < 25:
                    parse_error_rows.append(
                        {
                            "line_number": line_count,
                            "line_bytes": size,
                            "error": str(exc),
                        }
                    )
                payload = None
            else:
                parsed_lines += 1
                if isinstance(payload, dict):
                    top_keys.update(str(key) for key in payload.keys())
                    keys = walk_keys(payload)
                    nested_keys.update(keys)
                    parts = []
                    for key in TYPE_KEYS:
                        value = payload.get(key)
                        if isinstance(value, str):
                            parts.append(f"{key}:{value}")
                    row_type = "|".join(parts) if parts else "dict"
                    type_values.update(parts)
                    bloat_counts.update(classify_bloat(keys, payload))
                else:
                    row_type = type(payload).__name__
            size_by_type[row_type] += size
            count_by_type[row_type] += 1
            largest.append(
                {
                    "line_number": line_count,
                    "line_bytes": size,
                    "row_type": row_type,
                    "top_keys": ",".join(keys[:12]),
                }
            )
            if len(largest) > max_largest_lines * 4:
                largest = sorted(largest, key=lambda row: int(row["line_bytes"]), reverse=True)[:max_largest_lines]

    largest = sorted(largest, key=lambda row: int(row["line_bytes"]), reverse=True)[:max_largest_lines]
    repeated_lines = sum(count for count in repeated_hashes.values() if count > 1)
    repeated_groups = sum(1 for count in repeated_hashes.values() if count > 1)
    type_rows = [
        {
            "row_type": key,
            "count": count_by_type[key],
            "bytes": size_by_type[key],
        }
        for key in sorted(count_by_type, key=lambda item: size_by_type[item], reverse=True)
    ]
    summary = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "session": str(path),
        "bytes": stat.st_size,
        "modified": dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "line_count": line_count,
        "parsed_lines": parsed_lines,
        "parse_errors": parse_errors,
        "total_line_bytes": total_line_bytes,
        "largest_line_bytes": largest[0]["line_bytes"] if largest else 0,
        "largest_line_number": largest[0]["line_number"] if largest else 0,
        "repeated_line_groups": repeated_groups,
        "repeated_line_instances": repeated_lines,
        "top_keys": dict(top_keys.most_common(30)),
        "nested_keys": dict(nested_keys.most_common(80)),
        "type_values": dict(type_values.most_common(40)),
        "bloat_signal_counts": dict(bloat_counts.most_common()),
        "source_session_edits": 0,
        "payload_moves": 0,
        "permanent_deletes": 0,
    }
    return summary, largest, type_rows + parse_error_rows


def analyze_reducer_inventory(path: Path, max_largest_lines: int) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    stat_start = path.stat()
    generated = dt.datetime.now().isoformat(timespec="seconds")
    line_count = 0
    parsed_lines = 0
    parse_errors = 0
    total_line_bytes = 0
    total_text_bytes = 0
    category_counts: Counter[str] = Counter()
    category_bytes: defaultdict[str, int] = defaultdict(int)
    category_text_bytes: defaultdict[str, int] = defaultdict(int)
    reason_counts: Counter[str] = Counter()
    content_block_counts: Counter[str] = Counter()
    response_payload_type_counts: Counter[str] = Counter()
    largest_rows: list[dict[str, Any]] = []
    parse_error_rows: list[dict[str, Any]] = []

    with path.open("rb") as handle:
        for raw in handle:
            line_count += 1
            line_bytes = len(raw)
            total_line_bytes += line_bytes
            category = "unparsed"
            reason = "parse error"
            text_bytes = 0
            block_types: Counter[str] = Counter()
            response_payload_type = ""
            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                parse_errors += 1
                if len(parse_error_rows) < 25:
                    parse_error_rows.append(
                        {
                            "line_number": line_count,
                            "line_bytes": line_bytes,
                            "category": category,
                            "error": str(exc),
                        }
                    )
                payload = None
            else:
                parsed_lines += 1
                category, reason, block_types, text_bytes = classify_reducer_row(payload)
                if isinstance(payload, dict) and payload.get("type") == "response_item":
                    inner = payload.get("payload")
                    if isinstance(inner, dict):
                        response_payload_type = str(inner.get("type", ""))
                        if response_payload_type:
                            response_payload_type_counts[response_payload_type] += 1

            category_counts[category] += 1
            category_bytes[category] += line_bytes
            category_text_bytes[category] += text_bytes
            total_text_bytes += text_bytes
            reason_counts[f"{category}: {reason}"] += 1
            content_block_counts.update(block_types)

            largest_rows.append(
                {
                    "line_number": line_count,
                    "line_bytes": line_bytes,
                    "category": category,
                    "reason": reason,
                    "response_payload_type": response_payload_type,
                    "text_bytes": text_bytes,
                    "reduce_status": reducer_status_for_category(category)[0],
                }
            )
            if len(largest_rows) > max_largest_lines * 4:
                largest_rows = sorted(largest_rows, key=lambda row: int(row["line_bytes"]), reverse=True)[
                    :max_largest_lines
                ]

    stat_end = path.stat()
    category_rows: list[dict[str, Any]] = []
    for category in sorted(category_counts, key=lambda item: category_bytes[item], reverse=True):
        reduce_status, rationale, first_action = reducer_status_for_category(category)
        bytes_value = category_bytes[category]
        text_value = category_text_bytes[category]
        category_rows.append(
            {
                "category": category,
                "count": category_counts[category],
                "bytes": bytes_value,
                "percent_of_file": round((bytes_value / total_line_bytes * 100), 4) if total_line_bytes else 0,
                "text_bytes": text_value,
                "percent_of_text_estimate": round((text_value / total_text_bytes * 100), 4) if total_text_bytes else 0,
                "reduce_status": reduce_status,
                "rationale": rationale,
                "first_action": first_action,
            }
        )

    largest_rows = sorted(largest_rows, key=lambda row: int(row["line_bytes"]), reverse=True)[:max_largest_lines]
    summary = {
        "generated": generated,
        "session": str(path),
        "bytes": stat_end.st_size,
        "bytes_at_scan_start": stat_start.st_size,
        "bytes_at_scan_end": stat_end.st_size,
        "modified_at_scan_start": dt.datetime.fromtimestamp(stat_start.st_mtime).isoformat(timespec="seconds"),
        "modified_at_scan_end": dt.datetime.fromtimestamp(stat_end.st_mtime).isoformat(timespec="seconds"),
        "source_changed_during_scan": (
            stat_start.st_size != stat_end.st_size
            or stat_start.st_mtime_ns != stat_end.st_mtime_ns
        ),
        "modified": dt.datetime.fromtimestamp(stat_end.st_mtime).isoformat(timespec="seconds"),
        "line_count": line_count,
        "parsed_lines": parsed_lines,
        "parse_errors": parse_errors,
        "total_line_bytes": total_line_bytes,
        "estimated_text_bytes": total_text_bytes,
        "category_rows": category_rows,
        "content_block_counts": dict(content_block_counts.most_common()),
        "response_payload_type_counts": dict(response_payload_type_counts.most_common()),
        "reason_counts": dict(reason_counts.most_common(80)),
        "parse_error_rows": parse_error_rows,
        "source_session_edits": 0,
        "raw_source_rewrites": 0,
        "auth_file_copies": 0,
        "dropbox_payload_moves": 0,
        "jsonl_derivatives_promoted": 0,
    }
    return summary, category_rows, largest_rows


def write_reducer_inventory(
    summary: dict[str, Any],
    category_rows: list[dict[str, Any]],
    largest_rows: list[dict[str, Any]],
    inventory_dir: Path,
) -> dict[str, Path]:
    inventory_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = inventory_dir / f"codex-session-reducer-inventory-{stamp}.json"
    category_path = inventory_dir / f"codex-session-reducer-category-pressure-{stamp}.csv"
    largest_path = inventory_dir / f"codex-session-reducer-largest-rows-{stamp}.csv"
    summary_path = inventory_dir / f"codex-session-reducer-inventory-{stamp}-summary.txt"

    json_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    json_path.write_text(json_text, encoding="utf-8")
    with category_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "category",
                "count",
                "bytes",
                "percent_of_file",
                "text_bytes",
                "percent_of_text_estimate",
                "reduce_status",
                "rationale",
                "first_action",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(category_rows)
    with largest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "line_number",
                "line_bytes",
                "category",
                "reason",
                "response_payload_type",
                "text_bytes",
                "reduce_status",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(largest_rows)

    category_lines = "\n".join(
        (
            f"- {row['category']}: {row['bytes']} bytes, "
            f"{row['percent_of_file']}%, {row['count']} rows, "
            f"status={row['reduce_status']}"
        )
        for row in category_rows
    )
    text = f"""Codex Session Reducer Inventory
generated: {summary['generated']}
session: {summary['session']}
bytes: {summary['bytes']}
modified: {summary['modified']}
line_count: {summary['line_count']}
parsed_lines: {summary['parsed_lines']}
parse_errors: {summary['parse_errors']}
estimated_text_bytes: {summary['estimated_text_bytes']}
source_session_edits: 0
raw_source_rewrites: 0
auth_file_copies: 0
dropbox_payload_moves: 0
jsonl_derivatives_promoted: 0

Category pressure:
{category_lines}
"""
    summary_path.write_text(text, encoding="utf-8")

    for source, target in (
        (json_path, inventory_dir / "codex-session-reducer-inventory-current.json"),
        (category_path, inventory_dir / "codex-session-reducer-category-pressure-current.csv"),
        (largest_path, inventory_dir / "codex-session-reducer-largest-rows-current.csv"),
        (summary_path, inventory_dir / "codex-session-reducer-inventory-summary.txt"),
    ):
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "json": json_path,
        "category": category_path,
        "largest": largest_path,
        "summary": summary_path,
    }


def write_outputs(summary: dict[str, Any], largest: list[dict[str, Any]], detail_rows: list[dict[str, Any]], inventory_dir: Path) -> dict[str, Path]:
    inventory_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = inventory_dir / f"codex-session-bloat-analysis-{stamp}.json"
    largest_path = inventory_dir / f"codex-session-bloat-largest-lines-{stamp}.csv"
    details_path = inventory_dir / f"codex-session-bloat-details-{stamp}.csv"
    summary_path = inventory_dir / f"codex-session-bloat-analysis-{stamp}-summary.txt"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    with largest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["line_number", "line_bytes", "row_type", "top_keys"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(largest)
    all_fields = sorted({key for row in detail_rows for key in row.keys()})
    with details_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=all_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(detail_rows)

    bloat_lines = "\n".join(
        f"- {key}: {value}"
        for key, value in summary["bloat_signal_counts"].items()
    ) or "- none"
    type_lines = "\n".join(
        f"- {row.get('row_type', row.get('error', 'unknown'))}: {row.get('count', '')} rows, {row.get('bytes', row.get('line_bytes', ''))} bytes"
        for row in detail_rows[:20]
    ) or "- none"
    text = f"""Codex Session Bloat Analysis
generated: {summary['generated']}
session: {summary['session']}
bytes: {summary['bytes']}
modified: {summary['modified']}
line_count: {summary['line_count']}
parsed_lines: {summary['parsed_lines']}
parse_errors: {summary['parse_errors']}
largest_line_number: {summary['largest_line_number']}
largest_line_bytes: {summary['largest_line_bytes']}
repeated_line_groups: {summary['repeated_line_groups']}
repeated_line_instances: {summary['repeated_line_instances']}
source_session_edits: 0
payload_moves: 0
permanent_deletes: 0

Likely bloat signals:
{bloat_lines}

Largest row-type pressure:
{type_lines}
"""
    summary_path.write_text(text, encoding="utf-8")
    for source, target in (
        (json_path, inventory_dir / "codex-session-bloat-analysis-current.json"),
        (largest_path, inventory_dir / "codex-session-bloat-largest-lines-current.csv"),
        (details_path, inventory_dir / "codex-session-bloat-details-current.csv"),
        (summary_path, inventory_dir / "codex-session-bloat-analysis-summary.txt"),
    ):
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "json": json_path,
        "largest": largest_path,
        "details": details_path,
        "summary": summary_path,
    }


def main() -> None:
    args = parse_args()
    if args.session:
        session = Path(args.session).expanduser().resolve()
    elif args.latest:
        session = find_latest_session(Path(args.codex_home).expanduser().resolve())
    else:
        raise SystemExit("Use --session PATH or --latest.")
    if not session.exists():
        raise SystemExit(f"Session does not exist: {session}")
    summary, largest, detail_rows = analyze(session, args.max_largest_lines)
    if args.hash:
        summary["sha256"] = sha256_file(session)
    outputs = write_outputs(summary, largest, detail_rows, Path(args.inventory_dir))
    reducer_outputs = None
    if args.reducer_inventory:
        reducer_summary, category_rows, largest_rows = analyze_reducer_inventory(session, args.max_largest_lines)
        if args.hash:
            reducer_summary["sha256"] = summary.get("sha256") or sha256_file(session)
        reducer_outputs = write_reducer_inventory(
            reducer_summary,
            category_rows,
            largest_rows,
            Path(args.inventory_dir),
        )
    print(f"session: {session}")
    print(f"bytes: {summary['bytes']}")
    print(f"line_count: {summary['line_count']}")
    print(f"parse_errors: {summary['parse_errors']}")
    print(f"summary: {outputs['summary']}")
    if reducer_outputs:
        print(f"reducer_summary: {reducer_outputs['summary']}")
    print("source_session_edits: 0")
    print("payload_moves: 0")
    print("permanent_deletes: 0")


if __name__ == "__main__":
    main()
