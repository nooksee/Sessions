#!/usr/bin/env python3
"""Condense old Codex tool transcript rows in copied JSONL candidates.

Lane: session condensation and loader-limit reduction.

This script operates on copied lab artifacts. It does not edit production
sessions, rewrite source sessions, copy auth files, launch Codex, or promote
derivatives.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from collections import Counter, OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
LAB = ROOT / "Sessions" / "Lab" / "Tool-Transcript-Condensation"
EVIDENCE = ROOT / "Sessions" / "logs"


@dataclass
class RowRecord:
    line: int
    raw: str
    item: dict[str, Any] | None
    row_type: str
    response_index: int | None
    payload_type: str
    role: str
    call_id: str
    timestamp: str


@dataclass
class Unit:
    key: str
    row_indexes: list[int]
    first_line: int
    last_line: int
    classes: Counter[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Copied JSONL candidate to read.")
    parser.add_argument("--destination", help="Destination derivative JSONL. Default: lab path under Sessions/Lab.")
    parser.add_argument("--stamp", help="Stable stamp for repeatable output. Default: local timestamp.")
    parser.add_argument(
        "--target-response-items",
        type=int,
        default=14000,
        help="Practical response-item target for the derivative. Default: 14000.",
    )
    parser.add_argument(
        "--protect-last-response-items",
        type=int,
        default=6000,
        help="Preserve the latest N response items exactly. Default: 6000.",
    )
    parser.add_argument(
        "--receipt-group-size",
        type=int,
        default=500,
        help="Maximum removed response items represented by one receipt row. Default: 500.",
    )
    parser.add_argument(
        "--allow-reasoning-fallback",
        action="store_true",
        help="If paired function calls are insufficient, allow old reasoning rows to be condensed.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Measure only; do not write the derivative.")
    parser.add_argument("--write-evidence", action="store_true", help="Write evidence under Sessions/logs.")
    return parser.parse_args()


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_line(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def classify_payload(payload: Any) -> tuple[str, str, str]:
    if not isinstance(payload, dict):
        return "", "", ""
    payload_type = str(payload.get("type", "") or "")
    role = str(payload.get("role", "") or "")
    call_id = str(payload.get("call_id", "") or payload.get("id", "") or "")
    return payload_type, role, call_id


def read_rows(path: Path) -> tuple[list[RowRecord], dict[str, Any]]:
    records: list[RowRecord] = []
    response_index = 0
    parse_errors = 0
    first_parse_error: dict[str, Any] | None = None
    row_counts: Counter[str] = Counter()
    response_counts: Counter[str] = Counter()

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            item: dict[str, Any] | None = None
            row_type = "unparsed"
            payload_type = ""
            role = ""
            call_id = ""
            timestamp = ""
            current_response_index: int | None = None
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    item = parsed
                    row_type = str(item.get("type", "") or "")
                    timestamp = str(item.get("timestamp", "") or "")
                    if row_type == "response_item":
                        response_index += 1
                        current_response_index = response_index
                        payload_type, role, call_id = classify_payload(item.get("payload"))
                        response_counts[payload_type or "missing"] += 1
                else:
                    row_type = type(parsed).__name__
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                parse_errors += 1
                if first_parse_error is None:
                    first_parse_error = {"line": line_number, "error": str(exc)}

            row_counts[row_type or "missing"] += 1
            records.append(
                RowRecord(
                    line=line_number,
                    raw=raw,
                    item=item,
                    row_type=row_type,
                    response_index=current_response_index,
                    payload_type=payload_type,
                    role=role,
                    call_id=call_id,
                    timestamp=timestamp,
                )
            )

    summary: dict[str, Any] = {
        "rows": len(records),
        "parse_errors": parse_errors,
        "first_parse_error": first_parse_error,
        "response_item_rows": response_index,
        "row_counts": dict(sorted(row_counts.items())),
        "response_payload_types": dict(sorted(response_counts.items())),
    }
    return records, summary


def build_paired_function_units(records: list[RowRecord], eligible_response_cutoff: int) -> list[Unit]:
    by_call_id: OrderedDict[str, list[int]] = OrderedDict()
    for index, record in enumerate(records):
        if record.row_type != "response_item":
            continue
        if record.response_index is None or record.response_index > eligible_response_cutoff:
            continue
        if record.payload_type not in {"function_call", "function_call_output"}:
            continue
        if not record.call_id:
            continue
        by_call_id.setdefault(record.call_id, []).append(index)

    units: list[Unit] = []
    for call_id, indexes in by_call_id.items():
        classes = Counter(records[index].payload_type for index in indexes)
        if not {"function_call", "function_call_output"}.issubset(classes):
            continue
        line_numbers = [records[index].line for index in indexes]
        units.append(
            Unit(
                key=call_id,
                row_indexes=sorted(indexes),
                first_line=min(line_numbers),
                last_line=max(line_numbers),
                classes=classes,
            )
        )
    return sorted(units, key=lambda unit: unit.first_line)


def build_reasoning_units(records: list[RowRecord], eligible_response_cutoff: int) -> list[Unit]:
    units: list[Unit] = []
    for index, record in enumerate(records):
        if record.row_type != "response_item":
            continue
        if record.response_index is None or record.response_index > eligible_response_cutoff:
            continue
        if record.payload_type != "reasoning":
            continue
        units.append(
            Unit(
                key=f"reasoning:{record.line}",
                row_indexes=[index],
                first_line=record.line,
                last_line=record.line,
                classes=Counter({"reasoning": 1}),
            )
        )
    return units


def selected_net_reduction(selected_count: int, group_size: int) -> int:
    if selected_count <= 0:
        return 0
    return selected_count - math.ceil(selected_count / group_size)


def select_units(
    *,
    records: list[RowRecord],
    total_response_items: int,
    target_response_items: int,
    protect_last_response_items: int,
    receipt_group_size: int,
    allow_reasoning_fallback: bool,
) -> tuple[list[Unit], dict[str, Any]]:
    if target_response_items >= total_response_items:
        return [], {
            "required_net_reduction": 0,
            "eligible_response_cutoff": max(0, total_response_items - protect_last_response_items),
            "selection_status": "already_under_target",
        }

    eligible_response_cutoff = max(0, total_response_items - protect_last_response_items)
    required_net_reduction = total_response_items - target_response_items
    function_units = build_paired_function_units(records, eligible_response_cutoff)
    reasoning_units = build_reasoning_units(records, eligible_response_cutoff) if allow_reasoning_fallback else []
    candidate_units = function_units + reasoning_units
    candidate_units = sorted(candidate_units, key=lambda unit: unit.first_line)

    selected_units: list[Unit] = []
    selected_rows = 0
    for unit in candidate_units:
        selected_units.append(unit)
        selected_rows += len(unit.row_indexes)
        if selected_net_reduction(selected_rows, receipt_group_size) >= required_net_reduction:
            break

    net = selected_net_reduction(selected_rows, receipt_group_size)
    metadata = {
        "required_net_reduction": required_net_reduction,
        "eligible_response_cutoff": eligible_response_cutoff,
        "protect_last_response_items": protect_last_response_items,
        "receipt_group_size": receipt_group_size,
        "function_pair_units_available": len(function_units),
        "reasoning_units_available": len(reasoning_units),
        "selected_units": len(selected_units),
        "selected_response_rows": selected_rows,
        "estimated_receipt_rows": math.ceil(selected_rows / receipt_group_size) if selected_rows else 0,
        "estimated_net_reduction": net,
        "selection_status": "selected" if net >= required_net_reduction else "insufficient_eligible_rows",
    }
    return selected_units, metadata


def group_selected_rows(
    records: list[RowRecord],
    selected_units: list[Unit],
    receipt_group_size: int,
) -> list[dict[str, Any]]:
    selected_indexes: list[int] = []
    for unit in selected_units:
        selected_indexes.extend(unit.row_indexes)
    selected_indexes = sorted(set(selected_indexes))

    groups: list[dict[str, Any]] = []
    for offset in range(0, len(selected_indexes), receipt_group_size):
        indexes = selected_indexes[offset : offset + receipt_group_size]
        classes = Counter(records[index].payload_type for index in indexes)
        groups.append(
            {
                "group_index": len(groups) + 1,
                "row_indexes": indexes,
                "first_index": indexes[0],
                "last_index": indexes[-1],
                "first_line": records[indexes[0]].line,
                "last_line": records[indexes[-1]].line,
                "removed_response_rows": len(indexes),
                "classes": dict(sorted(classes.items())),
                "timestamp": records[indexes[0]].timestamp,
            }
        )
    return groups


def build_receipt_row(group: dict[str, Any], evidence_json: Path, stamp: str) -> dict[str, Any]:
    class_text = ", ".join(f"{key}={value}" for key, value in group["classes"].items())
    text = (
        "Session hygiene receipt: condensed "
        f"{group['removed_response_rows']} old tool-transcript response items from copied lab candidate. "
        f"Original source lines {group['first_line']}-{group['last_line']}. "
        f"Classes: {class_text}. "
        f"Evidence: {safe_relative(evidence_json)}. "
        "Production session edits: 0; source-session rewrites: 0; JSONL promotions: 0; "
        "automatic Codex launches: 0."
    )
    return {
        "timestamp": group.get("timestamp") or dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": text}],
            "phase": "commentary",
            "condensed_by": "Sessions/ops/lib/scripts/transcripts.py",
            "condensation_stamp": stamp,
        },
    }


def inspect_written_jsonl(path: Path) -> dict[str, Any]:
    rows = 0
    parse_errors = 0
    response_items = 0
    response_payload_types: Counter[str] = Counter()
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            rows += 1
            try:
                item = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                parse_errors += 1
                continue
            if isinstance(item, dict) and item.get("type") == "response_item":
                response_items += 1
                payload = item.get("payload")
                payload_type, role, _ = classify_payload(payload)
                if payload_type == "message":
                    response_payload_types[f"message:{role or 'missing'}"] += 1
                else:
                    response_payload_types[payload_type or "missing"] += 1
    return {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "rows": rows,
        "parse_errors": parse_errors,
        "response_item_rows": response_items,
        "response_payload_types": dict(sorted(response_payload_types.items())),
    }


def write_candidate(
    *,
    records: list[RowRecord],
    destination: Path,
    groups: list[dict[str, Any]],
    evidence_json: Path,
    stamp: str,
) -> None:
    first_index_to_group = {group["first_index"]: group for group in groups}
    selected_indexes = {index for group in groups for index in group["row_indexes"]}

    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for index, record in enumerate(records):
            group = first_index_to_group.get(index)
            if group:
                handle.write(json_line(build_receipt_row(group, evidence_json, stamp)))
            if index in selected_indexes:
                continue
            handle.write(record.raw)


def write_evidence(
    *,
    summary: dict[str, Any],
    groups: list[dict[str, Any]],
    stamp: str,
) -> dict[str, str]:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    json_path = EVIDENCE / f"codex-tool-transcript-condensation-{stamp}.json"
    summary_path = EVIDENCE / f"codex-tool-transcript-condensation-{stamp}-summary.txt"
    csv_path = EVIDENCE / f"codex-tool-transcript-condensation-{stamp}-groups.csv"

    summary_with_paths = dict(summary)
    summary_with_paths["evidence_paths"] = {
        "json": safe_relative(json_path),
        "summary": safe_relative(summary_path),
        "groups_csv": safe_relative(csv_path),
    }
    json_path.write_text(json.dumps(summary_with_paths, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "group_index",
                "first_line",
                "last_line",
                "removed_response_rows",
                "classes",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for group in groups:
            writer.writerow(
                {
                    "group_index": group["group_index"],
                    "first_line": group["first_line"],
                    "last_line": group["last_line"],
                    "removed_response_rows": group["removed_response_rows"],
                    "classes": json.dumps(group["classes"], sort_keys=True),
                }
            )

    output = summary.get("output") or {}
    selection = summary.get("selection") or {}
    lines = [
        "# Codex Tool Transcript Condensation",
        "",
        f"generated: {summary['generated']}",
        f"source: {summary['source']}",
        f"destination: {summary.get('destination', '')}",
        f"source_response_item_rows: {summary['source_scan']['response_item_rows']}",
        f"target_response_items: {summary['target_response_items']}",
        f"protect_last_response_items: {summary['protect_last_response_items']}",
        f"selected_response_rows: {selection.get('selected_response_rows', 0)}",
        f"receipt_rows_inserted: {len(groups)}",
        f"estimated_net_reduction: {selection.get('estimated_net_reduction', 0)}",
        f"selection_status: {selection.get('selection_status', '')}",
        f"output_response_item_rows: {output.get('response_item_rows', '')}",
        f"output_parse_errors: {output.get('parse_errors', '')}",
        "",
        "Safety counts:",
        "- production_session_edits: 0",
        "- source_session_rewrites: 0",
        "- jsonl_derivatives_promoted: 0",
        "- auth_file_copies: 0",
        "- automatic_codex_launches: 0",
        "- permanent_deletes: 0",
        "- protocol_deviations: 0",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "json": str(json_path),
        "summary": str(summary_path),
        "groups_csv": str(csv_path),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise SystemExit(f"Source not found: {source}")
    if ROOT not in source.parents:
        raise SystemExit("Refusing source outside repo Sessions lane. Copy the candidate into Sessions/Lab first.")

    stamp = args.stamp or now_stamp()
    run_root = LAB / stamp
    destination = Path(args.destination).expanduser().resolve() if args.destination else run_root / source.name
    if ROOT not in destination.parents:
        raise SystemExit("Refusing destination outside repo root.")
    if LAB not in destination.parents:
        raise SystemExit("Refusing destination outside Sessions/Lab/Tool-Transcript-Condensation.")
    if destination.exists() and not args.dry_run:
        raise SystemExit(f"Destination already exists: {destination}")

    source_stat = source.stat()
    records, source_scan = read_rows(source)
    if source_scan["parse_errors"]:
        raise SystemExit("Refusing condensation because source parse errors are nonzero.")

    selected_units, selection = select_units(
        records=records,
        total_response_items=source_scan["response_item_rows"],
        target_response_items=args.target_response_items,
        protect_last_response_items=args.protect_last_response_items,
        receipt_group_size=args.receipt_group_size,
        allow_reasoning_fallback=args.allow_reasoning_fallback,
    )
    if selection["selection_status"] == "insufficient_eligible_rows":
        if args.allow_reasoning_fallback:
            raise SystemExit("Insufficient eligible rows for target after tool-output and reasoning fallback selection.")
        raise SystemExit("Insufficient eligible rows for target. Retry with --allow-reasoning-fallback only in the lab.")

    groups = group_selected_rows(records, selected_units, args.receipt_group_size)
    evidence_json = EVIDENCE / f"codex-tool-transcript-condensation-{stamp}.json"

    output_scan: dict[str, Any] | None = None
    if not args.dry_run:
        write_candidate(records=records, destination=destination, groups=groups, evidence_json=evidence_json, stamp=stamp)
        output_scan = inspect_written_jsonl(destination)

    summary: dict[str, Any] = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "stamp": stamp,
        "source": str(source),
        "destination": str(destination) if not args.dry_run else "",
        "dry_run": args.dry_run,
        "source_bytes_at_scan_start": source_stat.st_size,
        "source_bytes_at_scan_end": source.stat().st_size,
        "source_changed_during_scan": (
            source_stat.st_size != source.stat().st_size
            or source_stat.st_mtime_ns != source.stat().st_mtime_ns
        ),
        "source_sha256": sha256_file(source),
        "source_scan": source_scan,
        "target_response_items": args.target_response_items,
        "protect_last_response_items": args.protect_last_response_items,
        "receipt_group_size": args.receipt_group_size,
        "allow_reasoning_fallback": args.allow_reasoning_fallback,
        "selection": selection,
        "receipt_rows_inserted": len(groups),
        "output": output_scan or {},
        "production_session_edits": 0,
        "source_session_rewrites": 0,
        "jsonl_derivatives_promoted": 0,
        "auth_file_copies": 0,
        "automatic_codex_launches": 0,
        "permanent_deletes": 0,
        "protocol_deviations": 0,
    }

    evidence_paths: dict[str, str] = {}
    if args.write_evidence:
        evidence_paths = write_evidence(summary=summary, groups=groups, stamp=stamp)
        summary["evidence_paths"] = evidence_paths
    return summary


def main() -> None:
    args = parse_args()
    summary = run(args)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
