#!/usr/bin/env python3
"""Fail closed when a PoT change lacks a coupled, hash-bound operator decision.

Reads only Git objects and the candidate checkout. It writes nothing and never
reads private words, session bodies, identities, or live host state.

Filing authority: PoT 1.1.4 and 1.1.13. Task-local intermediates use SCRATCH;
new case payloads use storage/active/; incoming data use storage/intake/.
Existing state consumers are inventoried in docs/ops/README.md and are not
moved by this source-only gate.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[3]
SCRATCH = SESSIONS / "var" / "tmp"
SPEC = SESSIONS / "docs" / "ops" / "specs" / "scripts" / "constitution.md"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
ENTRY = re.compile(r"(?m)^### RoR-([0-9]+):[^\n]*$")


class Refused(Exception):
    """A candidate did not meet the constitutional authorization contract."""


def git(root: Path, *args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise Refused(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def blob(root: Path, revision: str, path: str) -> bytes:
    entry = git(root, "ls-tree", revision, "--", path).decode("utf-8").rstrip("\n")
    metadata, separator, actual_path = entry.partition("\t")
    fields = metadata.split()
    if not separator or actual_path != path or len(fields) != 3:
        raise Refused(f"{revision}:{path} is missing or is not a tracked file")
    if fields[0] != "100644" or fields[1] != "blob":
        raise Refused(f"{revision}:{path} must be a regular, non-executable file")
    return git(root, "show", f"{revision}:{path}")


def resolve_commit(root: Path, revision: str) -> str:
    value = git(root, "rev-parse", "--verify", f"{revision}^{{commit}}").decode().strip()
    if not COMMIT.fullmatch(value):
        raise Refused(f"{revision!r} did not resolve to a full commit ID")
    return value


def appended_entries(text: str) -> list[tuple[int, str]]:
    matches = list(ENTRY.finditer(text))
    return [
        (int(match.group(1)),
         text[match.start():matches[index + 1].start()
              if index + 1 < len(matches) else len(text)])
        for index, match in enumerate(matches)
    ]


def field(entry: str, name: str) -> str | None:
    match = re.search(rf"(?m)^-[ \t]+\*\*{re.escape(name)}:\*\*[ \t]*(.+)$", entry)
    return match.group(1).strip() if match else None


def require_line(text: str, name: str, expected: str) -> None:
    match = re.search(rf"(?m)^{re.escape(name)}:[ \t]*(.+)$", text)
    if not match or match.group(1).strip() != expected:
        raise Refused(f"authorization record has missing or inconsistent {name} field")


def check(root: Path, base_ref: str, head_ref: str) -> str:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise Refused(f"repository root is not a directory: {root}")
    if git(root, "rev-parse", "--show-toplevel").decode().strip() != str(root):
        raise Refused(f"not the root of a Git checkout: {root}")
    if git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise Refused("candidate checkout is dirty; commit or remove only task-owned scratch")

    base = resolve_commit(root, base_ref)
    head = resolve_commit(root, head_ref)
    if subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", base, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode:
        raise Refused("base is not an ancestor of candidate head")

    base_law = blob(root, base, "PoT.md")
    head_entry = git(root, "ls-tree", head, "--", "PoT.md").decode("utf-8").rstrip("\n")
    if not head_entry:
        raise Refused("candidate deletes or renames PoT.md")
    head_law = blob(root, head, "PoT.md")
    if base_law == head_law:
        return "PASS: PoT unchanged; no authorization record is required"

    changes = git(root, "diff", "--name-status", "-M", base, head).decode().splitlines()
    statuses: dict[str, str] = {}
    for line in changes:
        parts = line.split("\t")
        if parts[0].startswith("R") or parts[0].startswith("C"):
            for path in parts[1:]:
                statuses[path] = parts[0]
        elif len(parts) == 2:
            statuses[parts[1]] = parts[0]
    if statuses.get("PoT.md") != "M":
        raise Refused("a changed PoT.md must be modified in place, not added, deleted, or renamed")

    target_hash = hashlib.sha256(head_law).hexdigest()
    short_hash = target_hash[:8]
    snapshot = f"archives/PoT-{short_hash}.md"
    authority = f"archives/PoT-authority-{short_hash}.md"
    if statuses.get(snapshot) != "A" or statuses.get(authority) != "A":
        raise Refused("changed PoT.md requires newly added exact-hash snapshot and authority leaf")
    if blob(root, head, snapshot) != head_law:
        raise Refused("PoT snapshot bytes do not equal the candidate PoT.md")

    try:
        base_ror = blob(root, base, "RoR.md")
        head_ror = blob(root, head, "RoR.md")
    except Refused as exc:
        raise Refused("changed PoT.md requires a coupled RoR.md ledger update") from exc
    if statuses.get("RoR.md") != "M" or not head_ror.startswith(base_ror):
        raise Refused("RoR.md must be appended in the same candidate; historical bytes must remain unchanged")

    base_entries = appended_entries(base_ror.decode("utf-8"))
    head_entries = appended_entries(head_ror.decode("utf-8"))
    last_base = max((number for number, _ in base_entries), default=0)
    new_entries = [(number, entry) for number, entry in head_entries if number > last_base]
    matching = []
    for number, entry in new_entries:
        act = field(entry, "Act") or ""
        if f"Target policy SHA-256: {target_hash}" in act:
            matching.append((number, entry))
    if not matching or matching[-1][0] != max(number for number, _ in new_entries):
        raise Refused("latest new RoR entry is not an operator decision for this exact PoT hash")
    _, decision = matching[-1]
    act = field(decision, "Act") or ""
    words = field(decision, "Words") or ""
    record = field(decision, "Record") or ""
    digest_match = re.fullmatch(r'"\[words sha256=([0-9a-f]{64})\]"', words)
    if not digest_match:
        raise Refused("new RoR decision must carry a private-source words SHA-256 digest")
    words_hash = digest_match.group(1)
    if "Scope: PoT.md" not in act or "Decision: Operator" not in act:
        raise Refused("new RoR entry is not an operator decision specifically scoped to PoT.md")
    if snapshot not in record or authority not in record:
        raise Refused("RoR record pointers do not name the exact snapshot and authority leaf")
    if f"Words SHA-256: {words_hash}" not in record:
        raise Refused("RoR entry does not bind its private-source digest in the record")

    authority_text = blob(root, head, authority).decode("utf-8")
    require_line(authority_text, "Authority", "Operator decision (protected provenance; not authenticated by this checker)")
    require_line(authority_text, "Scope", "PoT.md")
    require_line(authority_text, "Target policy SHA-256", target_hash)
    require_line(authority_text, "Words SHA-256", words_hash)
    if re.search(r'(?m)^Words:\s*"', authority_text):
        raise Refused("authority leaf must not contain raw operator words")

    return f"PASS: PoT change is coupled to operator decision, snapshot, and ledger ({target_hash})"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="constitution",
        description="check a PoT change against exact base/head authorization evidence",
    )
    ap.add_argument("--base", required=True, help="accepted base commit or ref")
    ap.add_argument("--head", required=True, help="candidate head commit or ref")
    ap.add_argument("--root", type=Path, default=SESSIONS, help="clean Git checkout (default: Sessions)")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(check(args.root, args.base, args.head))
    except (OSError, UnicodeError, Refused) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
