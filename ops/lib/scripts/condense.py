#!/usr/bin/env python3
"""Condense old Codex compacted-history rows in copied JSONL candidates.

Lane: session byte-pressure reduction.

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
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
LAB = ROOT / "Sessions" / "Lab" / "Compacted-History-Condensation"
EVIDENCE = ROOT / "Sessions" / "logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Copied JSONL candidate to read.")
    parser.add_argument("--destination", help="Destination derivative JSONL. Default: lab path under Sessions/Lab.")
    parser.add_argument("--stamp", help="Stable stamp for repeatable output. Default: local timestamp.")
    parser.add_argument(
        "--keep-latest-compacted",
        type=int,
        default=32,
        help="Preserve the latest N compacted rows exactly. Default: 32.",
    )
    parser.add_argument(
        "--receipt-group-size",
        type=int,
        default=50,
        help="Maximum condensed compacted rows represented by one receipt row. Default: 50.",
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


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def json_line(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def read_rows(path: Path) -> tuple[list[str], list[dict[str, Any] | None], dict[str, Any]]:
    raw_rows: list[str] = []
    parsed_rows: list[dict[str, Any] | None] = []
    parse_errors = 0
    compacted_indexes: list[int] = []
    compacted_bytes = 0
    largest_line = {"line": 0, "bytes": 0}
    row_counts: dict[str, int] = {}
    row_bytes: dict[str, int] = {}

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, raw in enumerate(handle, 1):
            raw_rows.append(raw)
            raw_len = len(raw.encode("utf-8"))
            if raw_len > largest_line["bytes"]:
                largest_line = {"line": line_number, "bytes": raw_len}
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parse_errors += 1
                parsed_rows.append(None)
                row_type = "unparsed"
            else:
                parsed_rows.append(parsed if isinstance(parsed, dict) else None)
                row_type = str(parsed.get("type", "") or "missing") if isinstance(parsed, dict) else type(parsed).__name__
                if row_type == "compacted":
                    compacted_indexes.append(len(raw_rows) - 1)
                    compacted_bytes += raw_len
            row_counts[row_type] = row_counts.get(row_type, 0) + 1
            row_bytes[row_type] = row_bytes.get(row_type, 0) + raw_len

    summary = {
        "rows": len(raw_rows),
        "parse_errors": parse_errors,
        "compacted_rows": len(compacted_indexes),
        "compacted_bytes": compacted_bytes,
        "largest_line": largest_line,
        "row_counts": dict(sorted(row_counts.items())),
        "row_bytes": dict(sorted(row_bytes.items())),
        "compacted_indexes": compacted_indexes,
    }
    return raw_rows, parsed_rows, summary


def build_groups(indexes: list[int], raw_rows: list[str], group_size: int) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for offset in range(0, len(indexes), group_size):
        group_indexes = indexes[offset : offset + group_size]
        original_bytes = sum(len(raw_rows[index].encode("utf-8")) for index in group_indexes)
        groups.append(
            {
                "group_index": len(groups) + 1,
                "row_indexes": group_indexes,
                "first_line": group_indexes[0] + 1,
                "last_line": group_indexes[-1] + 1,
                "condensed_rows": len(group_indexes),
                "original_bytes": original_bytes,
            }
        )
    return groups


def build_receipt_row(group: dict[str, Any], evidence_json: Path, stamp: str) -> dict[str, Any]:
    message = (
        "Session hygiene receipt: condensed "
        f"{group['condensed_rows']} old compacted-history rows from copied lab candidate. "
        f"Original source lines {group['first_line']}-{group['last_line']}. "
        f"Original bytes represented: {group['original_bytes']}. "
        f"Evidence: {safe_relative(evidence_json)}. "
        "Production session edits: 0; source-session rewrites: 0; JSONL promotions: 0; "
        "automatic Codex launches: 0."
    )
    return {
        "timestamp": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
        "type": "compacted",
        "payload": {
            "message": message,
            "replacement_history": [],
            "condensed_by": "Sessions/ops/lib/scripts/condense.py",
            "condensation_stamp": stamp,
        },
    }


def inspect_written_jsonl(path: Path) -> dict[str, Any]:
    rows = 0
    parse_errors = 0
    compacted_rows = 0
    largest_line = {"line": 0, "bytes": 0}
    with path.open("rb") as handle:
        for line_number, raw in enumerate(handle, 1):
            rows += 1
            raw_len = len(raw)
            if raw_len > largest_line["bytes"]:
                largest_line = {"line": line_number, "bytes": raw_len}
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                parse_errors += 1
                continue
            if isinstance(parsed, dict) and parsed.get("type") == "compacted":
                compacted_rows += 1
    return {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "rows": rows,
        "parse_errors": parse_errors,
        "compacted_rows": compacted_rows,
        "largest_line": largest_line,
    }


def write_candidate(
    raw_rows: list[str],
    groups: list[dict[str, Any]],
    destination: Path,
    evidence_json: Path,
    stamp: str,
) -> None:
    first_index_to_group = {group["row_indexes"][0]: group for group in groups}
    selected_indexes = {index for group in groups for index in group["row_indexes"]}
    destination.parent.mkdir(parents=True, exist_ok=False)
    with destination.open("w", encoding="utf-8") as handle:
        for index, raw in enumerate(raw_rows):
            group = first_index_to_group.get(index)
            if group:
                handle.write(json_line(build_receipt_row(group, evidence_json, stamp)))
            if index in selected_indexes:
                continue
            handle.write(raw)


def write_evidence(summary: dict[str, Any], groups: list[dict[str, Any]], stamp: str) -> dict[str, str]:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    json_path = EVIDENCE / f"codex-compacted-history-condensation-{stamp}.json"
    csv_path = EVIDENCE / f"codex-compacted-history-condensation-{stamp}-groups.csv"
    summary_path = EVIDENCE / f"codex-compacted-history-condensation-{stamp}-summary.txt"

    summary_with_paths = dict(summary)
    summary_with_paths["evidence_paths"] = {
        "json": safe_relative(json_path),
        "groups_csv": safe_relative(csv_path),
        "summary": safe_relative(summary_path),
    }
    json_path.write_text(json.dumps(summary_with_paths, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["group_index", "first_line", "last_line", "condensed_rows", "original_bytes"],
            lineterminator="\n",
        )
        writer.writeheader()
        for group in groups:
            writer.writerow({key: group[key] for key in writer.fieldnames})

    output = summary.get("output") or {}
    source_scan = summary.get("source_scan") or {}
    lines = [
        "# Codex Compacted-History Condensation",
        "",
        f"generated: {summary['generated']}",
        f"source: {summary['source']}",
        f"destination: {summary.get('destination', '')}",
        f"source_compacted_rows: {source_scan.get('compacted_rows', '')}",
        f"keep_latest_compacted: {summary['keep_latest_compacted']}",
        f"condensed_compacted_rows: {summary['condensed_compacted_rows']}",
        f"receipt_rows_inserted: {summary['receipt_rows_inserted']}",
        f"output_bytes: {output.get('bytes', '')}",
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
        "groups_csv": str(csv_path),
        "summary": str(summary_path),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise SystemExit(f"Source not found: {source}")
    if ROOT not in source.parents:
        raise SystemExit("Refusing source outside repo Sessions lane. Copy the candidate into Sessions/Lab first.")

    stamp = args.stamp or now_stamp()
    destination = Path(args.destination).expanduser().resolve() if args.destination else LAB / stamp / source.name
    if ROOT not in destination.parents:
        raise SystemExit("Refusing destination outside repo root.")
    if LAB not in destination.parents:
        raise SystemExit("Refusing destination outside Sessions/Lab/Compacted-History-Condensation.")
    if destination.exists() and not args.dry_run:
        raise SystemExit(f"Destination already exists: {destination}")

    source_stat = source.stat()
    raw_rows, _parsed_rows, source_scan = read_rows(source)
    if source_scan["parse_errors"]:
        raise SystemExit("Refusing condensation because source parse errors are nonzero.")

    compacted_indexes = source_scan["compacted_indexes"]
    keep_latest = max(0, args.keep_latest_compacted)
    selected_indexes = compacted_indexes[: max(0, len(compacted_indexes) - keep_latest)]
    groups = build_groups(selected_indexes, raw_rows, args.receipt_group_size)
    evidence_json = EVIDENCE / f"codex-compacted-history-condensation-{stamp}.json"

    output_scan: dict[str, Any] | None = None
    if not args.dry_run:
        write_candidate(raw_rows, groups, destination, evidence_json, stamp)
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
        "source_scan": {key: value for key, value in source_scan.items() if key != "compacted_indexes"},
        "keep_latest_compacted": keep_latest,
        "receipt_group_size": args.receipt_group_size,
        "condensed_compacted_rows": len(selected_indexes),
        "receipt_rows_inserted": len(groups),
        "estimated_original_bytes_represented": sum(group["original_bytes"] for group in groups),
        "output": output_scan or {},
        "production_session_edits": 0,
        "source_session_rewrites": 0,
        "jsonl_derivatives_promoted": 0,
        "auth_file_copies": 0,
        "automatic_codex_launches": 0,
        "permanent_deletes": 0,
        "protocol_deviations": 0,
    }
    if args.write_evidence:
        summary["evidence_paths"] = write_evidence(summary, groups, stamp)
    return summary


def main() -> None:
    args = parse_args()
    summary = run(args)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
