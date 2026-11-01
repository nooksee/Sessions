#!/usr/bin/env python3
"""Build a derivative Codex JSONL with structural session IDs rewritten.

Lane: session asset management.
Authority: `Sessions/Plans/session-jsonl-sandbox-load-test.md`.

This tool creates an evidence-only candidate under an operator-selected path.
It does not edit production sessions, copy auth material, update SQLite state,
update the session index, launch Codex, or promote a candidate.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


STRUCTURAL_ID_KEYS = {"id", "thread_id", "session_id"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Source JSONL or JSONL-derived file.")
    parser.add_argument("--destination", required=True, help="Destination derivative JSONL path.")
    parser.add_argument("--old-id", required=True, help="Source session UUID to replace in structural fields.")
    parser.add_argument("--new-id", required=True, help="Target session UUID for structural fields.")
    parser.add_argument(
        "--target-cwd",
        help="Optional cwd value for session_meta payloads. Omit to preserve source cwd.",
    )
    parser.add_argument(
        "--target-cli-version",
        help="Optional cli_version value for session_meta payloads. Omit to preserve source version.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Measure planned changes without writing output.")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_structural_ids(value: Any, old_id: str, new_id: str, stats: dict[str, int]) -> Any:
    if isinstance(value, dict):
        changed: dict[str, Any] = {}
        for key, item in value.items():
            if key in STRUCTURAL_ID_KEYS and item == old_id:
                changed[key] = new_id
                stats[f"structural_{key}_replacements"] = stats.get(f"structural_{key}_replacements", 0) + 1
            else:
                changed[key] = replace_structural_ids(item, old_id, new_id, stats)
        return changed
    if isinstance(value, list):
        return [replace_structural_ids(item, old_id, new_id, stats) for item in value]
    return value


def rewrite_session_meta(obj: dict[str, Any], args: argparse.Namespace, stats: dict[str, int]) -> None:
    if obj.get("type") != "session_meta":
        return
    payload = obj.get("payload")
    if not isinstance(payload, dict):
        return
    if args.target_cwd and payload.get("cwd") != args.target_cwd:
        payload["cwd"] = args.target_cwd
        stats["session_meta_cwd_replacements"] = stats.get("session_meta_cwd_replacements", 0) + 1
    if args.target_cli_version and payload.get("cli_version") != args.target_cli_version:
        payload["cli_version"] = args.target_cli_version
        stats["session_meta_cli_version_replacements"] = stats.get("session_meta_cli_version_replacements", 0) + 1


def scan_or_write(args: argparse.Namespace) -> dict[str, Any]:
    source = Path(args.source).expanduser().resolve()
    destination = Path(args.destination).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise SystemExit(f"Source not found: {source}")
    if source == destination:
        raise SystemExit("Destination must not equal source.")
    if destination.exists() and not args.dry_run:
        raise SystemExit(f"Destination already exists: {destination}")

    stats: dict[str, int] = {
        "lines_read": 0,
        "lines_written": 0,
        "parse_errors": 0,
        "source_old_id_literal_hits": 0,
        "source_new_id_literal_hits": 0,
        "destination_old_id_literal_hits": 0,
        "destination_new_id_literal_hits": 0,
        "production_session_edits": 0,
        "source_session_rewrites": 0,
        "auth_files_copied": 0,
        "automatic_codex_launches": 0,
    }

    writer = None
    if not args.dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        writer = destination.open("w", encoding="utf-8", newline="\n")

    first_parse_errors: list[dict[str, Any]] = []
    try:
        with source.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, 1):
                stats["lines_read"] += 1
                stats["source_old_id_literal_hits"] += line.count(args.old_id)
                stats["source_new_id_literal_hits"] += line.count(args.new_id)
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    stats["parse_errors"] += 1
                    if len(first_parse_errors) < 10:
                        first_parse_errors.append(
                            {"line_number": line_number, "error": str(exc), "line_bytes": len(line.encode("utf-8"))}
                        )
                    if writer is not None:
                        writer.write(line)
                        stats["lines_written"] += 1
                    continue
                obj = replace_structural_ids(obj, args.old_id, args.new_id, stats)
                rewrite_session_meta(obj, args, stats)
                output_line = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
                stats["destination_old_id_literal_hits"] += output_line.count(args.old_id)
                stats["destination_new_id_literal_hits"] += output_line.count(args.new_id)
                if writer is not None:
                    writer.write(output_line)
                    stats["lines_written"] += 1
    finally:
        if writer is not None:
            writer.close()

    result: dict[str, Any] = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "dry_run": args.dry_run,
        "source": {
            "path": str(source),
            "bytes": source.stat().st_size,
            "sha256": sha256_file(source),
        },
        "destination": {
            "path": str(destination),
            "exists": destination.exists(),
            "bytes": destination.stat().st_size if destination.exists() else 0,
            "sha256": sha256_file(destination) if destination.exists() else "",
        },
        "old_id": args.old_id,
        "new_id": args.new_id,
        "target_cwd": args.target_cwd or "",
        "target_cli_version": args.target_cli_version or "",
        "stats": stats,
        "first_parse_errors": first_parse_errors,
        "notes": [
            "Only exact structural id/thread_id/session_id values are rewritten.",
            "Transcript text, command arguments, command output, patches, and diffs are preserved as evidence.",
            "This candidate is not extension-registered and is not promoted.",
        ],
    }
    return result


def main() -> None:
    args = parse_args()
    result = scan_or_write(args)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
