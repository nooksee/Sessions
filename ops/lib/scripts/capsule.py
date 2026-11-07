#!/usr/bin/env python3
"""Build a six-question Codex succession capsule from repo canon and evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
INVENTORY = ROOT / "Sessions" / "logs"
CANON_FILES = [
    "README.md",
    "START.md",
    "STATUS.md",
    "REVIEW.md",
    "llms.txt",
    "Sessions/README.md",
    "Sessions/INDEX.md",
    "Sessions/Plans/session-asset-management.md",
    "Sessions/Plans/session-succession-management.md",
    "Plans/operator-familiarity-management.md",
    "Decisions/file-media-type-doctrine.md",
    "Sessions/archives/legacy/Scripts/README.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", default=str(INVENTORY))
    parser.add_argument("--output", help="Optional output path.")
    return parser.parse_args()


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()


def read_first_lines(path: Path, max_lines: int) -> str:
    if not path.exists():
        return "missing"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[:max_lines])


def read_summary(path: Path) -> str:
    if not path.exists():
        return "No current evidence file found."
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return text[:6000]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_capsule(inventory_dir: Path) -> str:
    now = dt.datetime.now().isoformat(timespec="seconds")
    branch = run_git(["branch", "--show-current"])
    head = run_git(["rev-parse", "--short", "HEAD"])
    status = run_git(["status", "--short"]) or "clean"
    canon_lines = "\n".join(f"- `{item}`" for item in CANON_FILES)
    session_assets = load_json(inventory_dir / "codex-session-assets-current.json")
    bloat = load_json(inventory_dir / "codex-session-bloat-analysis-current.json")
    status_excerpt = read_first_lines(ROOT / "STATUS.md", 60)
    review_excerpt = read_first_lines(ROOT / "REVIEW.md", 80)
    session_summary = read_summary(inventory_dir / "codex-session-assets-summary.txt")
    bloat_summary = read_summary(inventory_dir / "codex-session-bloat-analysis-summary.txt")

    session_files = session_assets.get("session_files", "unknown")
    total_bytes = session_assets.get("total_bytes", "unknown")
    parse_errors = bloat.get("parse_errors", "unknown")
    line_count = bloat.get("line_count", "unknown")

    return f"""# Codex Succession Capsule

Generated: {now}

## 1. Operator And Interaction Rules
The operator holds final authority. The working root for this repo is `{ROOT}`.

Standing behavior rules:

- No contractions across any scope, including project documents.
- Quantitative reporting is required for deviations from protocol.
- Absolute literalism applies; ambiguity should be clarified before risky action.
- Repo canon outranks session memory.
- Payload-changing operations require evidence, logs, and reversible posture unless explicitly authorized otherwise.

## 2. Active Repo And Canon
- Branch: `{branch}`
- Head: `{head}`
- Status:

```text
{status}
```

Boot canon:

{canon_lines}

## 3. Current Active Work Lanes
Current status excerpt:

```text
{status_excerpt}
```

Current human-review excerpt:

```text
{review_excerpt}
```

## 4. Changes Since Prior Checkpoint
Session evidence currently reports `{session_files}` local session assets totaling `{total_bytes}` bytes.

Latest session bloat analysis reports `{line_count}` JSONL lines and `{parse_errors}` parse errors for the analyzed session.

Session asset summary:

```text
{session_summary}
```

Session bloat summary:

```text
{bloat_summary}
```

## 5. Risks, Hard Rules, And Boundaries
- Do not edit live Codex session files.
- Do not commit raw sessions, repaired seeds, auth files, tokens, or credential material.
- Do not put live session storage inside Dropbox payload.
- Treat session derivatives as experimental boot aids, not canon.
- Preserve quarantine outside Dropbox payload.
- Exact duplicate retirement requires hash evidence.
- Non-exact duplicate or derivative-family work requires adjudication evidence.
- `Dropbox/Projects/home-ops` is for handoffs and instructions only.

## 6. Next Concrete Move
If this capsule is used by a successor thread:

1. Read `README.md`, `START.md`, `STATUS.md`, `REVIEW.md`, and `llms.txt`.
2. Read `Sessions/Plans/session-asset-management.md` and `Sessions/Plans/session-succession-management.md`.
3. Run `git status --short --branch`.
4. Refresh only the evidence lane requested by the operator.
5. If session repair is the task, run read-only analysis first and operate on copies only.

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
        output = inventory_dir / f"codex-succession-capsule-{stamp}.md"
    text = build_capsule(inventory_dir)
    output.write_text(text, encoding="utf-8")
    current = inventory_dir / "codex-succession-capsule-current.md"
    current.write_text(text, encoding="utf-8")
    print(f"capsule: {output}")
    print(f"current: {current}")
    print("payload_moves: 0")
    print("permanent_deletes: 0")
    print("source_session_edits: 0")


if __name__ == "__main__":
    main()
