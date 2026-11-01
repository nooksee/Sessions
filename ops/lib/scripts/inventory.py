#!/usr/bin/env python3
"""Inventory local Codex session assets without modifying them.

Session files are treated as forensic evidence. This script reports size,
location, modified time, optional line statistics, and optional SHA-256 hashes.
It does not prune, rewrite, move, delete, or archive sessions.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
INVENTORY = ROOT / "Sessions" / "logs"
SESSION_SUFFIXES = {".jsonl", ".backup"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--inventory-dir", default=str(INVENTORY))
    parser.add_argument("--include-archived", action="store_true", help="Also scan archived_sessions.")
    parser.add_argument("--inspect-lines", action="store_true", help="Read JSONL lines for counts and largest-record statistics.")
    parser.add_argument("--hash", action="store_true", help="Compute SHA-256 for every discovered session file.")
    parser.add_argument("--current-alias", action="store_true", help="Also write codex-session-assets-current reports.")
    return parser.parse_args()


def iso_from_timestamp(value: float) -> str:
    return dt.datetime.fromtimestamp(value).isoformat(timespec="seconds")


def session_roots(codex_home: Path, include_archived: bool) -> list[tuple[str, Path]]:
    roots = [("sessions", codex_home / "sessions")]
    if include_archived:
        roots.append(("archived_sessions", codex_home / "archived_sessions"))
    return roots


def is_session_file(path: Path) -> bool:
    if not path.is_file():
        return False
    name = path.name.lower()
    if name.endswith(".jsonl") or name.endswith(".jsonl.backup"):
        return True
    return path.suffix.lower() in SESSION_SUFFIXES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_lines(path: Path) -> dict[str, Any]:
    line_count = 0
    invalid_json = 0
    largest_line_bytes = 0
    largest_line_number = 0
    top_key_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()

    with path.open("rb") as handle:
        for raw in handle:
            line_count += 1
            size = len(raw)
            if size > largest_line_bytes:
                largest_line_bytes = size
                largest_line_number = line_count
            try:
                payload = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                invalid_json += 1
                continue
            if isinstance(payload, dict):
                top_key_counts.update(payload.keys())
                for key in ("type", "event_type", "kind", "role"):
                    value = payload.get(key)
                    if isinstance(value, str):
                        if key == "role":
                            role_counts[value] += 1
                        else:
                            type_counts[f"{key}:{value}"] += 1

    return {
        "line_count": line_count,
        "invalid_json": invalid_json,
        "largest_line_bytes": largest_line_bytes,
        "largest_line_number": largest_line_number,
        "top_keys": dict(top_key_counts.most_common(12)),
        "type_counts": dict(type_counts.most_common(12)),
        "role_counts": dict(role_counts.most_common(12)),
    }


def collect_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    codex_home = Path(args.codex_home).expanduser().resolve()
    rows: list[dict[str, Any]] = []
    for area, base in session_roots(codex_home, args.include_archived):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*"), key=lambda item: str(item).lower()):
            if not is_session_file(path):
                continue
            stat = path.stat()
            row: dict[str, Any] = {
                "area": area,
                "path": str(path),
                "relative_path": str(path.relative_to(base)),
                "suffix": ".jsonl.backup" if path.name.lower().endswith(".jsonl.backup") else path.suffix.lower(),
                "bytes": stat.st_size,
                "modified": iso_from_timestamp(stat.st_mtime),
                "sha256": "",
                "line_count": "",
                "invalid_json": "",
                "largest_line_bytes": "",
                "largest_line_number": "",
                "top_keys_json": "",
                "type_counts_json": "",
                "role_counts_json": "",
            }
            if args.hash:
                row["sha256"] = sha256_file(path)
            if args.inspect_lines and path.name.lower().endswith((".jsonl", ".jsonl.backup")):
                stats = inspect_lines(path)
                row["line_count"] = stats["line_count"]
                row["invalid_json"] = stats["invalid_json"]
                row["largest_line_bytes"] = stats["largest_line_bytes"]
                row["largest_line_number"] = stats["largest_line_number"]
                row["top_keys_json"] = json.dumps(stats["top_keys"], sort_keys=True)
                row["type_counts_json"] = json.dumps(stats["type_counts"], sort_keys=True)
                row["role_counts_json"] = json.dumps(stats["role_counts"], sort_keys=True)
            rows.append(row)
    return rows


def write_reports(rows: list[dict[str, Any]], inventory_dir: Path, args: argparse.Namespace) -> dict[str, Path]:
    inventory_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = inventory_dir / f"codex-session-assets-{stamp}.csv"
    json_path = inventory_dir / f"codex-session-assets-{stamp}.json"
    summary_path = inventory_dir / f"codex-session-assets-{stamp}-summary.txt"
    fieldnames = [
        "area",
        "relative_path",
        "path",
        "suffix",
        "bytes",
        "modified",
        "sha256",
        "line_count",
        "invalid_json",
        "largest_line_bytes",
        "largest_line_number",
        "top_keys_json",
        "type_counts_json",
        "role_counts_json",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    total_bytes = sum(int(row["bytes"]) for row in rows)
    largest = sorted(rows, key=lambda row: int(row["bytes"]), reverse=True)[:10]
    summary = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "codex_home": str(Path(args.codex_home).expanduser().resolve()),
        "include_archived": bool(args.include_archived),
        "inspect_lines": bool(args.inspect_lines),
        "hash": bool(args.hash),
        "session_files": len(rows),
        "total_bytes": total_bytes,
        "largest": largest,
        "per_area": dict(Counter(row["area"] for row in rows)),
    }
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    largest_lines = "\n".join(
        f"- {row['relative_path']} :: {int(row['bytes'])} bytes :: {row['modified']}"
        for row in largest
    )
    summary_text = f"""Codex Session Asset Inventory
generated: {summary['generated']}
codex_home: {summary['codex_home']}
session_files: {summary['session_files']}
total_bytes: {summary['total_bytes']}
include_archived: {summary['include_archived']}
inspect_lines: {summary['inspect_lines']}
hash: {summary['hash']}
payload_moves: 0
permanent_deletes: 0

Largest session files:
{largest_lines if largest_lines else "- none"}
"""
    summary_path.write_text(summary_text, encoding="utf-8")

    if args.current_alias:
        (inventory_dir / "codex-session-assets-current.csv").write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
        (inventory_dir / "codex-session-assets-current.json").write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
        (inventory_dir / "codex-session-assets-summary.txt").write_text(summary_text, encoding="utf-8")

    return {"csv": csv_path, "json": json_path, "summary": summary_path}


def main() -> None:
    args = parse_args()
    rows = collect_rows(args)
    paths = write_reports(rows, Path(args.inventory_dir), args)
    total_bytes = sum(int(row["bytes"]) for row in rows)
    print(f"session_files: {len(rows)}")
    print(f"total_bytes: {total_bytes}")
    print(f"csv: {paths['csv']}")
    print(f"json: {paths['json']}")
    print(f"summary: {paths['summary']}")
    print("payload_moves: 0")
    print("permanent_deletes: 0")


if __name__ == "__main__":
    main()
