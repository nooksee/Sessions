#!/usr/bin/env python3
"""Analyze Codex JSONL response-item pressure without rewriting sessions.

This is a loader-limit tool, not a byte-bloat tool. It answers which
`response_item` payload classes are pushing a copied candidate over the
observed Codex loader/API input ceiling.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "Sessions" / "logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, help="JSONL session or copied candidate to inspect.")
    parser.add_argument("--stamp", help="Stable evidence stamp. Default: local timestamp.")
    parser.add_argument("--max-input-items", type=int, default=16384)
    parser.add_argument("--target-margin", type=int, default=14000)
    parser.add_argument("--top-lines", type=int, default=50)
    parser.add_argument("--write-evidence", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def content_text_bytes(content: Any) -> tuple[int, Counter[str]]:
    text_bytes = 0
    block_types: Counter[str] = Counter()
    if isinstance(content, str):
        return len(content.encode("utf-8")), Counter({"string": 1})
    if not isinstance(content, list):
        return 0, block_types
    for block in content:
        if isinstance(block, str):
            text_bytes += len(block.encode("utf-8"))
            block_types["string"] += 1
        elif isinstance(block, dict):
            block_type = str(block.get("type", "dict"))
            block_types[block_type] += 1
            for key in ("text", "input", "output"):
                value = block.get(key)
                if isinstance(value, str):
                    text_bytes += len(value.encode("utf-8"))
        else:
            block_types[type(block).__name__] += 1
    return text_bytes, block_types


def response_class(payload: Any) -> tuple[str, str, int, Counter[str]]:
    if not isinstance(payload, dict):
        return "non_dict_payload", "missing", 0, Counter()

    payload_type = str(payload.get("type", "") or "missing")
    role = str(payload.get("role", "") or "missing")
    call_id = str(payload.get("call_id", "") or payload.get("id", "") or "")
    text_bytes, block_types = content_text_bytes(payload.get("content"))

    if payload_type == "message":
        block_label = ",".join(f"{key}:{value}" for key, value in block_types.most_common(4))
        return f"message:{role}", block_label or "message", text_bytes, block_types
    if payload_type in {"function_call", "custom_tool_call", "local_shell_call"}:
        name = str(payload.get("name", "") or payload.get("call_id", "") or "tool_call")
        return payload_type, name[:120], text_bytes, block_types
    if payload_type in {"function_call_output", "custom_tool_call_output", "local_shell_call_output"}:
        return payload_type, call_id[:120] or "tool_output", text_bytes, block_types
    if payload_type == "reasoning":
        summary = payload.get("summary")
        if isinstance(summary, list):
            return "reasoning", f"summary_items:{len(summary)}", text_bytes, block_types
        return "reasoning", "reasoning", text_bytes, block_types
    if "image" in payload_type.lower() or "attachment" in payload_type.lower():
        return "image_or_attachment", payload_type, text_bytes, block_types
    return payload_type, payload_type, text_bytes, block_types


def reduction_lane(row_class: str) -> tuple[str, str, str]:
    lanes = {
        "function_call_output": (
            "first_reducer_candidate",
            "Usually external command/tool output. Preserve recent outputs and replace older bulky outputs with receipts in copied candidates.",
            "Sandbox proof required before any candidate rewrite.",
        ),
        "function_call": (
            "linked_reducer_candidate",
            "Tool calls pair with outputs. Calls may be small but numerous; linkage must remain coherent.",
            "Collapse only with matching output strategy.",
        ),
        "custom_tool_call_output": (
            "first_reducer_candidate",
            "Developer-tool output can be archived as receipts when old and already represented in repo evidence.",
            "Sandbox proof required before any candidate rewrite.",
        ),
        "custom_tool_call": (
            "linked_reducer_candidate",
            "Developer-tool call structure may be loader-visible.",
            "Collapse only with matching output strategy.",
        ),
        "reasoning": (
            "strong_reducer_candidate",
            "Reasoning rows are numerous and usually not user-facing canon.",
            "Test removal or summary replacement in copied lab candidates only.",
        ),
        "message:assistant": (
            "semantic_reducer_candidate",
            "Prose from the assistant can be summarized into receipts, current state, files changed, and validation.",
            "Preserve recent visible continuity and repo-canonical summaries.",
        ),
        "message:user": (
            "preserve_or_careful_semantic_reducer",
            "User instructions and personal context are high-value.",
            "Extract facts and explicit instructions before any old-message condensation.",
        ),
        "message:system": (
            "preserve",
            "System instruction rows define behavior.",
            "Do not reduce.",
        ),
        "message:developer": (
            "preserve",
            "Developer instruction rows define behavior.",
            "Do not reduce.",
        ),
        "image_or_attachment": (
            "already_targeted_by_image_externalizer",
            "Image payloads are byte pressure and should already be externalized before row condensation.",
            "Use existing image externalizer only.",
        ),
    }
    return lanes.get(
        row_class,
        (
            "measure_before_touch",
            "This response item class has no approved reducer lane yet.",
            "Preserve until classified.",
        ),
    )


def analyze(path: Path, max_input_items: int, target_margin: int, top_lines: int) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    stat_start = path.stat()
    rows = 0
    parse_errors = 0
    response_items = 0
    first_over_limit: dict[str, Any] | None = None
    first_over_margin: dict[str, Any] | None = None
    row_counts: Counter[str] = Counter()
    row_bytes: defaultdict[str, int] = defaultdict(int)
    response_counts: Counter[str] = Counter()
    response_bytes: defaultdict[str, int] = defaultdict(int)
    response_text_bytes: defaultdict[str, int] = defaultdict(int)
    payload_type_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    block_counts: Counter[str] = Counter()
    largest_response_rows: list[dict[str, Any]] = []

    with path.open("rb") as handle:
        for raw in handle:
            rows += 1
            line_bytes = len(raw)
            try:
                item = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                parse_errors += 1
                row_type = "unparsed"
                row_counts[row_type] += 1
                row_bytes[row_type] += line_bytes
                continue

            if not isinstance(item, dict):
                row_type = type(item).__name__
                row_counts[row_type] += 1
                row_bytes[row_type] += line_bytes
                continue

            row_type = str(item.get("type", "missing") or "missing")
            row_counts[row_type] += 1
            row_bytes[row_type] += line_bytes

            if row_type != "response_item":
                continue

            response_items += 1
            payload = item.get("payload")
            row_class, reason, text_bytes, block_types = response_class(payload)
            response_counts[row_class] += 1
            response_bytes[row_class] += line_bytes
            response_text_bytes[row_class] += text_bytes
            reason_counts[f"{row_class}: {reason}"] += 1
            block_counts.update(block_types)

            if isinstance(payload, dict):
                payload_type_counts[str(payload.get("type", "missing") or "missing")] += 1

            if response_items == target_margin + 1:
                first_over_margin = {
                    "line": rows,
                    "response_item_prefix_count": response_items,
                    "row_class": row_class,
                    "reason": reason,
                }
            if response_items == max_input_items + 1:
                first_over_limit = {
                    "line": rows,
                    "response_item_prefix_count": response_items,
                    "row_class": row_class,
                    "reason": reason,
                }

            largest_response_rows.append(
                {
                    "line": rows,
                    "response_item_prefix_count": response_items,
                    "line_bytes": line_bytes,
                    "row_class": row_class,
                    "reason": reason,
                    "text_bytes": text_bytes,
                }
            )
            if len(largest_response_rows) > top_lines * 4:
                largest_response_rows = sorted(
                    largest_response_rows,
                    key=lambda row: int(row["line_bytes"]),
                    reverse=True,
                )[:top_lines]

    stat_end = path.stat()
    response_rows: list[dict[str, Any]] = []
    for row_class in sorted(response_counts, key=lambda key: response_counts[key], reverse=True):
        lane, rationale, first_action = reduction_lane(row_class)
        count = response_counts[row_class]
        bytes_value = response_bytes[row_class]
        response_rows.append(
            {
                "row_class": row_class,
                "count": count,
                "bytes": bytes_value,
                "text_bytes": response_text_bytes[row_class],
                "percent_of_response_items": round(count / response_items * 100, 4) if response_items else 0,
                "percent_of_file_bytes": round(bytes_value / stat_end.st_size * 100, 4) if stat_end.st_size else 0,
                "reduction_lane": lane,
                "rationale": rationale,
                "first_action": first_action,
            }
        )

    minimum_reduction_needed = max(0, response_items - max_input_items)
    margin_reduction_needed = max(0, response_items - target_margin)
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
        "row_type_counts": dict(row_counts.most_common()),
        "row_type_bytes": dict(sorted(row_bytes.items(), key=lambda item: item[1], reverse=True)),
        "response_item_rows": response_items,
        "max_input_items": max_input_items,
        "target_margin": target_margin,
        "minimum_reduction_needed": minimum_reduction_needed,
        "margin_reduction_needed": margin_reduction_needed,
        "first_response_item_over_target_margin": first_over_margin,
        "first_response_item_over_loader_limit": first_over_limit,
        "response_payload_type_counts": dict(payload_type_counts.most_common()),
        "response_class_rows": response_rows,
        "reason_counts": dict(reason_counts.most_common(80)),
        "content_block_counts": dict(block_counts.most_common()),
        "production_session_edits": 0,
        "source_session_rewrites": 0,
        "jsonl_derivatives_promoted": 0,
        "auth_file_copies": 0,
        "automatic_codex_launches": 0,
        "permanent_deletes": 0,
    }
    largest_response_rows = sorted(
        largest_response_rows,
        key=lambda row: int(row["line_bytes"]),
        reverse=True,
    )[:top_lines]
    return summary, response_rows, largest_response_rows


def write_evidence(summary: dict[str, Any], response_rows: list[dict[str, Any]], largest_rows: list[dict[str, Any]], stamp: str) -> dict[str, Path]:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    prefix = f"codex-session-response-item-pressure-{stamp}"
    json_path = EVIDENCE / f"{prefix}.json"
    summary_path = EVIDENCE / f"{prefix}-summary.txt"
    csv_path = EVIDENCE / f"{prefix}.csv"
    largest_path = EVIDENCE / f"{prefix}-largest-response-rows.csv"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "row_class",
                "count",
                "bytes",
                "text_bytes",
                "percent_of_response_items",
                "percent_of_file_bytes",
                "reduction_lane",
                "rationale",
                "first_action",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(response_rows)
    with largest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "line",
                "response_item_prefix_count",
                "line_bytes",
                "row_class",
                "reason",
                "text_bytes",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(largest_rows)

    class_lines = "\n".join(
        (
            f"- {row['row_class']}: {row['count']} rows, "
            f"{row['bytes']} bytes, lane={row['reduction_lane']}"
        )
        for row in response_rows
    )
    text = f"""Codex Session Response-Item Pressure
generated: {summary['generated']}
session: {summary['session']}
bytes: {summary['bytes']}
rows: {summary['rows']}
parse_errors: {summary['parse_errors']}
response_item_rows: {summary['response_item_rows']}
max_input_items: {summary['max_input_items']}
target_margin: {summary['target_margin']}
minimum_reduction_needed: {summary['minimum_reduction_needed']}
margin_reduction_needed: {summary['margin_reduction_needed']}
source_changed_during_scan: {summary['source_changed_during_scan']}
production_session_edits: 0
source_session_rewrites: 0
jsonl_derivatives_promoted: 0
auth_file_copies: 0
automatic_codex_launches: 0
permanent_deletes: 0

Response class pressure:
{class_lines}
"""
    summary_path.write_text(text, encoding="utf-8")
    return {
        "json": json_path,
        "summary": summary_path,
        "csv": csv_path,
        "largest": largest_path,
    }


def main() -> int:
    args = parse_args()
    path = Path(args.session).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"Session file not found: {path}")
    stamp = args.stamp or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    summary, response_rows, largest_rows = analyze(
        path,
        max_input_items=args.max_input_items,
        target_margin=args.target_margin,
        top_lines=args.top_lines,
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.write_evidence:
        paths = write_evidence(summary, response_rows, largest_rows, stamp)
        print("evidence:")
        for key, value in paths.items():
            print(f"{key}: {value}")
    return 0 if summary["parse_errors"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
