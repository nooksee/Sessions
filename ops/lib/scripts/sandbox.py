#!/usr/bin/env python3
"""Prepare an isolated Codex session JSONL sandbox without launching Codex.

Lane: session asset management.
Authority: `Sessions/Plans/session-jsonl-sandbox-load-test.md`.

This script is a harness, not a repair tool. It reads source/candidate JSONL
evidence, writes an isolated test object under ignored `Sessions/Lab/`, and
records measurements needed for a later human load test. It does not edit production
session files, copy auth material, move Dropbox payload, or launch Codex.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import re
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
TEMP_ROOT = ROOT / "Sessions" / "Lab" / "Codex-Session-Sandbox"
ROLLOUT_DATE_RE = re.compile(r"rollout-(\d{4})-(\d{2})-(\d{2})T")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Source JSONL or JSONL backup to measure.")
    parser.add_argument(
        "--candidate",
        help="Optional prebuilt derivative candidate. If omitted, the source is used as a baseline candidate.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Print the planned sandbox layout without writing files.")
    mode.add_argument("--prepare", action="store_true", help="Copy the candidate into an isolated sandbox and write receipts.")
    parser.add_argument(
        "--sandbox-root",
        default=str(TEMP_ROOT),
        help="Parent directory for sandbox runs. Default: Sessions/Lab/Codex-Session-Sandbox.",
    )
    parser.add_argument(
        "--stamp",
        help="Optional stable run stamp for repeatable tests. Default: current local timestamp.",
    )
    parser.add_argument(
        "--no-auth",
        action="store_true",
        default=True,
        help="Required default posture. Accepted for explicitness; auth files are never copied by this script.",
    )
    return parser.parse_args()


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def command_version(label: str, cmd: list[str]) -> dict[str, str]:
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        return {"label": label, "command": " ".join(cmd), "stdout": "", "stderr": "missing executable"}
    stderr = proc.stderr.strip()
    if proc.returncode != 0 and not stderr:
        stderr = f"exit_code={proc.returncode}"
    return {
        "label": label,
        "command": " ".join(cmd),
        "stdout": proc.stdout.strip(),
        "stderr": stderr,
    }


def environment_evidence() -> dict[str, Any]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "commands": [
            command_version("codex", ["codex", "--version"]),
            command_version("code", ["code", "--version"]),
            command_version("git", ["git", "--version"]),
            command_version("uname", ["uname", "-a"]),
            command_version("lsb_release", ["lsb_release", "-a"]),
        ],
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_jsonl(path: Path) -> dict[str, Any]:
    line_count = 0
    parse_error_count = 0
    largest_line_bytes = 0
    largest_line_number = 0
    first_parse_errors: list[dict[str, Any]] = []

    with path.open("rb") as handle:
        for raw in handle:
            line_count += 1
            line_bytes = len(raw)
            if line_bytes > largest_line_bytes:
                largest_line_bytes = line_bytes
                largest_line_number = line_count
            try:
                json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                parse_error_count += 1
                if len(first_parse_errors) < 10:
                    first_parse_errors.append(
                        {
                            "line_number": line_count,
                            "line_bytes": line_bytes,
                            "error": str(exc),
                        }
                    )

    stat = path.stat()
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": stat.st_size,
        "modified": dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "sha256": sha256_file(path),
        "line_count": line_count,
        "parse_error_count": parse_error_count,
        "largest_line_bytes": largest_line_bytes,
        "largest_line_number": largest_line_number,
        "first_parse_errors": first_parse_errors,
    }


def session_date_from_name(path: Path) -> tuple[str, str, str]:
    match = ROLLOUT_DATE_RE.search(path.name)
    if match:
        return match.group(1), match.group(2), match.group(3)
    today = dt.datetime.now()
    return today.strftime("%Y"), today.strftime("%m"), today.strftime("%d")


def loadable_session_name(path: Path) -> str:
    name = path.name
    if name.endswith(".jsonl.backup"):
        return name[: -len(".backup")]
    if name.endswith(".backup"):
        return name[: -len(".backup")]
    return name


def build_layout(args: argparse.Namespace) -> dict[str, Any]:
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise SystemExit(f"Source file not found: {source}")

    candidate = Path(args.candidate).expanduser().resolve() if args.candidate else source
    if not candidate.exists() or not candidate.is_file():
        raise SystemExit(f"Candidate file not found: {candidate}")

    stamp = args.stamp or now_stamp()
    sandbox_root = Path(args.sandbox_root).expanduser().resolve()
    run_root = sandbox_root / stamp
    codex_home = run_root / "codex-home"
    year, month, day = session_date_from_name(candidate)
    session_dir = codex_home / "sessions" / year / month / day
    destination = session_dir / loadable_session_name(candidate)

    warnings: list[str] = []
    if not destination.name.endswith(".jsonl"):
        warnings.append("destination_session_name_does_not_end_jsonl")
    if not destination.name.startswith("rollout-"):
        warnings.append("destination_session_name_does_not_start_rollout")
    if args.candidate is None:
        warnings.append("candidate_omitted_source_used_as_baseline_candidate")

    return {
        "stamp": stamp,
        "sandbox_root": str(sandbox_root),
        "run_root": str(run_root),
        "codex_home": str(codex_home),
        "session_dir": str(session_dir),
        "destination": str(destination),
        "source": str(source),
        "candidate": str(candidate),
        "candidate_is_source": source == candidate,
        "warnings": warnings,
    }


def receipt_template(manifest: dict[str, Any]) -> str:
    destination = manifest["paths"]["destination"]
    return f"""# Codex Session Sandbox Load-Test Receipt

Status: untested.

Prepared: {manifest["generated"]}
Sandbox run: `{manifest["paths"]["run_root"]}`
Sandbox CODEX_HOME: `{manifest["paths"]["codex_home"]}`
Candidate session: `{destination}`

## Required Human Test Record
- command or UI path used:
- exact Codex version:
- exact VS Code version:
- session appeared in picker: unknown
- session opened: unknown
- thread accepted a new message: unknown
- repo path coherent: unknown
- operator rules coherent: unknown
- observed errors:
- load outcome: untested

## Safety Counts
- copied_auth_files: {manifest["safety_counts"]["copied_auth_files"]}
- production_files_edited: {manifest["safety_counts"]["production_files_edited"]}
- source_session_rewrites: {manifest["safety_counts"]["source_session_rewrites"]}
- dropbox_payload_files_moved: {manifest["safety_counts"]["dropbox_payload_files_moved"]}
- permanent_deletes: {manifest["safety_counts"]["permanent_deletes"]}
- automatic_codex_launches: {manifest["safety_counts"]["automatic_codex_launches"]}

## Operator Promotion Check
A candidate may not be promoted until this receipt is updated with a `pass` or
explicitly accepted `partial` result and the operator approves promotion.
"""


def build_manifest(layout: dict[str, Any], prepared: bool) -> dict[str, Any]:
    source = Path(layout["source"])
    candidate = Path(layout["candidate"])
    destination = Path(layout["destination"])
    destination_stats = inspect_jsonl(destination) if destination.exists() else None
    manifest = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "prepared": prepared,
        "authority": "Sessions/Plans/session-jsonl-sandbox-load-test.md",
        "paths": layout,
        "environment": environment_evidence(),
        "source": inspect_jsonl(source),
        "candidate": inspect_jsonl(candidate),
        "destination": {
            "path": str(destination),
            "exists": destination.exists(),
            "bytes": destination_stats["bytes"] if destination_stats else 0,
            "modified": destination_stats["modified"] if destination_stats else "",
            "sha256": destination_stats["sha256"] if destination_stats else "",
            "line_count": destination_stats["line_count"] if destination_stats else 0,
            "parse_error_count": destination_stats["parse_error_count"] if destination_stats else 0,
            "largest_line_bytes": destination_stats["largest_line_bytes"] if destination_stats else 0,
            "largest_line_number": destination_stats["largest_line_number"] if destination_stats else 0,
            "first_parse_errors": destination_stats["first_parse_errors"] if destination_stats else [],
        },
        "safety_counts": {
            "copied_auth_files": 0,
            "production_files_edited": 0,
            "source_session_rewrites": 0,
            "dropbox_payload_files_moved": 0,
            "permanent_deletes": 0,
            "automatic_codex_launches": 0,
        },
    }
    return manifest


def prepare_sandbox(layout: dict[str, Any]) -> dict[str, Path]:
    run_root = Path(layout["run_root"])
    session_dir = Path(layout["session_dir"])
    destination = Path(layout["destination"])
    candidate = Path(layout["candidate"])

    if run_root.exists():
        raise SystemExit(f"Sandbox run already exists: {run_root}")
    session_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(candidate, destination)
    (Path(layout["codex_home"]) / "README-SANDBOX.txt").write_text(
        "Isolated Codex home for session load testing. No auth material was copied.\n",
        encoding="utf-8",
    )
    return {
        "run_root": run_root,
        "manifest": run_root / "manifest.json",
        "receipt": run_root / "load-test-receipt.md",
    }


def main() -> None:
    args = parse_args()
    layout = build_layout(args)

    if args.dry_run:
        manifest = build_manifest(layout, prepared=False)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        print("sandbox_prepared: 0")
        print("manifest_written: 0")
        print("receipt_template_written: 0")
        print("production_files_edited: 0")
        print("source_session_rewrites: 0")
        print("copied_auth_files: 0")
        print("dropbox_payload_files_moved: 0")
        print("automatic_codex_launches: 0")
        return

    paths = prepare_sandbox(layout)
    manifest = build_manifest(layout, prepared=True)
    paths["manifest"].write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths["receipt"].write_text(receipt_template(manifest), encoding="utf-8")

    print(f"sandbox_prepared: 1")
    print(f"run_root: {paths['run_root']}")
    print(f"manifest: {paths['manifest']}")
    print(f"receipt: {paths['receipt']}")
    print(f"candidate_destination: {layout['destination']}")
    print("manifest_written: 1")
    print("receipt_template_written: 1")
    print("production_files_edited: 0")
    print("source_session_rewrites: 0")
    print("copied_auth_files: 0")
    print("dropbox_payload_files_moved: 0")
    print("automatic_codex_launches: 0")


if __name__ == "__main__":
    main()
