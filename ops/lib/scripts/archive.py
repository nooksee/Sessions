#!/usr/bin/env python3
"""Archive selected Codex session files into root Backup.

Dry-run is default. Apply mode copies session files and writes a manifest.
It never edits, prunes, moves, or deletes the source session file.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
BACKUP_ROOT = ROOT / "Sessions" / "Archived"
INVENTORY = ROOT / "Sessions" / "logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--session", action="append", default=[], help="Specific session file to archive.")
    parser.add_argument("--latest", action="store_true", help="Archive the most recently modified session JSONL.")
    parser.add_argument("--include-paired-backup", action="store_true", help="Also include <session>.backup when present.")
    parser.add_argument("--backup-root", default=str(BACKUP_ROOT))
    parser.add_argument("--inventory-dir", default=str(INVENTORY))
    parser.add_argument("--label", default="codex-session-archive")
    parser.add_argument("--apply", action="store_true", help="Copy selected session files.")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_session(codex_home: Path) -> Path | None:
    sessions = codex_home / "sessions"
    if not sessions.exists():
        return None
    candidates = [path for path in sessions.rglob("*.jsonl") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def selected_sources(args: argparse.Namespace) -> list[Path]:
    codex_home = Path(args.codex_home).expanduser().resolve()
    sources: list[Path] = []
    for raw in args.session:
        sources.append(Path(raw).expanduser().resolve())
    if args.latest:
        latest = latest_session(codex_home)
        if latest is None:
            raise SystemExit(f"No session JSONL files found under {codex_home / 'sessions'}")
        sources.append(latest)
    if not sources:
        raise SystemExit("Select at least one source with --session or --latest.")

    expanded: list[Path] = []
    for source in sources:
        if not source.exists() or not source.is_file():
            raise SystemExit(f"Missing source file: {source}")
        expanded.append(source)
        if args.include_paired_backup:
            paired = Path(str(source) + ".backup")
            if paired.exists() and paired.is_file():
                expanded.append(paired)

    unique: dict[str, Path] = {}
    for source in expanded:
        unique[str(source)] = source
    return list(unique.values())


def destination_for(source: Path, codex_home: Path, run_root: Path) -> Path:
    try:
        rel = source.relative_to(codex_home)
    except ValueError:
        rel = Path(source.name)
    return run_root / rel


def archive(args: argparse.Namespace) -> tuple[list[dict[str, Any]], Path]:
    codex_home = Path(args.codex_home).expanduser().resolve()
    backup_root = Path(args.backup_root).resolve()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_label = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in args.label).strip("-") or "codex-session-archive"
    run_root = backup_root / f"{safe_label}-{stamp}"
    sources = selected_sources(args)
    rows: list[dict[str, Any]] = []

    for source in sources:
        stat = source.stat()
        dest = destination_for(source, codex_home, run_root)
        status = "would_copy"
        sha256 = ""
        if args.apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            sha256 = sha256_file(dest)
            status = "copied"
        rows.append(
            {
                "source": str(source),
                "destination": str(dest),
                "bytes": stat.st_size,
                "modified": dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                "sha256": sha256,
                "status": status,
            }
        )

    return rows, run_root


def write_reports(rows: list[dict[str, Any]], run_root: Path, args: argparse.Namespace) -> dict[str, Path]:
    inventory_dir = Path(args.inventory_dir)
    inventory_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = inventory_dir / f"codex-session-archive-{stamp}.csv"
    json_path = inventory_dir / f"codex-session-archive-{stamp}.json"
    summary_path = inventory_dir / f"codex-session-archive-{stamp}-summary.txt"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "destination", "bytes", "modified", "sha256", "status"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    copied = sum(1 for row in rows if row["status"] == "copied")
    would_copy = sum(1 for row in rows if row["status"] == "would_copy")
    total_bytes = sum(int(row["bytes"]) for row in rows)
    payload = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "mode": "apply" if args.apply else "dry-run",
        "run_root": str(run_root),
        "rows": rows,
        "file_count": len(rows),
        "copied": copied,
        "would_copy": would_copy,
        "total_bytes": total_bytes,
        "payload_moves": 0,
        "permanent_deletes": 0,
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    summary_text = f"""Codex Session Archive
generated: {payload['generated']}
mode: {payload['mode']}
run_root: {payload['run_root']}
file_count: {payload['file_count']}
copied: {payload['copied']}
would_copy: {payload['would_copy']}
total_bytes: {payload['total_bytes']}
payload_moves: 0
permanent_deletes: 0
source_edits: 0
"""
    summary_path.write_text(summary_text, encoding="utf-8")

    if args.apply:
        run_root.mkdir(parents=True, exist_ok=True)
        (run_root / "manifest.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        (run_root / "README.md").write_text(
            "# Codex Session Archive\n\n"
            "This folder preserves copied Codex session files as cold evidence.\n\n"
            "The source session files were not edited, moved, pruned, or deleted.\n",
            encoding="utf-8",
        )

    return {"csv": csv_path, "json": json_path, "summary": summary_path}


def main() -> None:
    args = parse_args()
    rows, run_root = archive(args)
    paths = write_reports(rows, run_root, args)
    print(f"mode: {'apply' if args.apply else 'dry-run'}")
    print(f"file_count: {len(rows)}")
    print(f"total_bytes: {sum(int(row['bytes']) for row in rows)}")
    print(f"run_root: {run_root}")
    print(f"csv: {paths['csv']}")
    print(f"json: {paths['json']}")
    print(f"summary: {paths['summary']}")
    print("payload_moves: 0")
    print("permanent_deletes: 0")
    print("source_edits: 0")


if __name__ == "__main__":
    main()
