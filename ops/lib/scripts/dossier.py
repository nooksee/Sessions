#!/usr/bin/env python3
"""Build a deterministic Codex session handoff packet.

The packet points a future session at canon, current Git state, and latest
session-asset inventory evidence. It does not read secrets, edit sessions, or
claim that transcript content outranks canon.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
INVENTORY = ROOT / "Sessions" / "logs"
CANON = [
    "README.md",
    "START.md",
    "STATUS.md",
    "REVIEW.md",
    "llms.txt",
    "Sessions/README.md",
    "Sessions/INDEX.md",
    "Sessions/Plans/session-asset-management.md",
    "Sessions/Plans/session-succession-management.md",
    "Plans/github-publication-privacy.md",
    "Plans/operator-and-system-continuity-audit-current.md",
    "Sessions/archives/legacy/Scripts/README.md",
    "Sessions/logs/README.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", default=str(INVENTORY))
    parser.add_argument("--output", help="Optional explicit output path.")
    return parser.parse_args()


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        return result.stderr.strip()
    return result.stdout.strip()


def latest_session_inventory(inventory_dir: Path) -> tuple[Path | None, dict]:
    current = inventory_dir / "codex-session-assets-current.json"
    if current.exists():
        try:
            return current, json.loads(current.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return current, {}
    candidates = sorted(inventory_dir.glob("codex-session-assets-*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for candidate in candidates:
        if candidate.name.endswith("-summary.json"):
            continue
        try:
            return candidate, json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return candidate, {}
    return None, {}


def build_packet(inventory_dir: Path) -> str:
    generated = dt.datetime.now().isoformat(timespec="seconds")
    head = run_git(["rev-parse", "--short", "HEAD"])
    branch = run_git(["branch", "--show-current"])
    status = run_git(["status", "--short"])
    remote = run_git(["remote", "-v"])
    inv_path, inv = latest_session_inventory(inventory_dir)
    largest = inv.get("largest", [])[:5] if isinstance(inv, dict) else []

    canon_lines = "\n".join(f"- `{path}`" for path in CANON)
    largest_lines = "\n".join(
        f"- `{row.get('relative_path', '')}` :: {row.get('bytes', '')} bytes :: {row.get('modified', '')}"
        for row in largest
        if isinstance(row, dict)
    )
    if not largest_lines:
        largest_lines = "- No session inventory evidence available."

    status_block = status if status else "clean"
    remote_block = remote if remote else "no remote configured"
    inv_ref = str(inv_path.relative_to(ROOT)) if inv_path and inv_path.is_relative_to(ROOT) else str(inv_path) if inv_path else "none"
    session_files = inv.get("session_files", "unknown") if isinstance(inv, dict) else "unknown"
    total_bytes = inv.get("total_bytes", "unknown") if isinstance(inv, dict) else "unknown"

    return f"""Codex Session Handoff Packet
generated: {generated}

## Authority Rule
Session files are cold evidence and continuity inputs. They do not outrank canon.

## Boot Canon
{canon_lines}

## Git State
- branch: `{branch}`
- head: `{head}`
- remote:
```text
{remote_block}
```
- status:
```text
{status_block}
```

## Session Asset Evidence
- latest inventory: `{inv_ref}`
- session files: `{session_files}`
- total bytes: `{total_bytes}`

Largest known session assets:
{largest_lines}

## Continuity Procedure
1. Read `README.md`, `START.md`, `STATUS.md`, and `llms.txt`.
2. Read `Sessions/Plans/session-asset-management.md`.
3. Treat `Sessions/logs/codex-session-assets-*` reports as evidence.
4. Preserve raw session files before any derivative experiment.
5. Promote only operator-approved findings into canon.
6. Keep private session backups out of Dropbox payload and out of Git tracking.

payload_moves: 0
permanent_deletes: 0
source_session_edits: 0
"""


def main() -> None:
    args = parse_args()
    inventory_dir = Path(args.inventory_dir)
    inventory_dir.mkdir(parents=True, exist_ok=True)
    if args.output:
        output = Path(args.output)
    else:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        output = inventory_dir / f"codex-session-handoff-{stamp}.txt"
    output.write_text(build_packet(inventory_dir), encoding="utf-8")
    current = inventory_dir / "codex-session-handoff-current.txt"
    current.write_text(output.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"handoff: {output}")
    print(f"current: {current}")
    print("payload_moves: 0")
    print("permanent_deletes: 0")
    print("source_session_edits: 0")


if __name__ == "__main__":
    main()
