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
ENTRY_START = re.compile(r"(?m)^### RoR-")
ENTRY_NUMBER = re.compile(r"^### RoR-([0-9]+):[^\r\n]+$")
FIELD_LINE = re.compile(r"(?m)^-[ \t]+\*\*([^*]+):\*\*[ \t]*(.*?)\s*$")
AUTHORITY_LINE = re.compile(r"^([A-Za-z][A-Za-z0-9 -]*):[ \t]*(.*?)\s*$")
DECISION_ACT = re.compile(
    r"Decision: Operator\. Scope: PoT\.md\. Target policy SHA-256: "
    r"([0-9a-f]{64})\. (.+)\Z"
)


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
    starts = list(ENTRY_START.finditer(text))
    entries = []
    previous = 0
    for index, start in enumerate(starts):
        end = text.find("\n", start.start())
        heading = text[start.start():end if end >= 0 else len(text)]
        match = ENTRY_NUMBER.fullmatch(heading)
        if not match:
            raise Refused("RoR ledger contains a malformed entry heading")
        number = int(match.group(1))
        if number <= previous:
            raise Refused("RoR entry numbers must be unique and strictly increasing")
        previous = number
        entry_end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        entries.append((number, text[start.start():entry_end]))
    return entries


def entry_fields(entry: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for match in FIELD_LINE.finditer(entry):
        name, value = match.groups()
        if name in result:
            raise Refused(f"RoR entry contains duplicate {name!r} fields")
        result[name] = value.strip()
    required = {"Given", "Words", "Act", "Record", "Entered by"}
    if result.keys() != required:
        raise Refused("latest RoR entry must contain exactly one of each required field")
    return result


def authority_fields(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        match = AUTHORITY_LINE.fullmatch(line)
        if not match:
            continue
        name, value = match.groups()
        if name in result:
            raise Refused(f"authority leaf contains duplicate {name!r} fields")
        result[name] = value
    required = {
        "Authority", "Scope", "Target policy SHA-256", "Words SHA-256", "Record"
    }
    if result.keys() != required:
        raise Refused("authority leaf must contain exactly one of each required field")
    return result


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
    new_entries = head_entries[len(base_entries):]
    if len(head_entries) != len(base_entries) + 1:
        raise Refused("changed PoT requires exactly one new RoR decision entry")
    entry_number, decision = new_entries[0]
    if entry_number != last_base + 1:
        raise Refused("new RoR decision number must be the next ledger sequence")

    fields = entry_fields(decision)
    act = fields["Act"]
    words = fields["Words"]
    record = fields["Record"]
    digest_match = re.fullmatch(r'"\[words sha256=([0-9a-f]{64})\]"', words)
    if not digest_match:
        raise Refused("new RoR decision must carry a private-source words SHA-256 digest")
    words_hash = digest_match.group(1)
    act_match = DECISION_ACT.fullmatch(act)
    labels = ("Decision:", "Scope:", "Target policy SHA-256:")
    if (
        not act_match
        or act_match.group(1) != target_hash
        or any(act.count(label) != 1 for label in labels)
    ):
        raise Refused("new RoR entry is not an exact operator decision for this PoT hash")
    expected_record = [
        "PoT.md", snapshot, authority, "private words source archives/RoR-words.md",
        f"Words SHA-256: {words_hash}",
    ]
    if record.split("; ") != expected_record:
        raise Refused("RoR record must name exactly the policy, snapshot, authority, and words digest")

    authority_leaf = authority_fields(blob(root, head, authority).decode("utf-8"))
    expected_authority = {
        "Authority": "Operator decision (protected provenance; not authenticated by this checker)",
        "Scope": "PoT.md",
        "Target policy SHA-256": target_hash,
        "Words SHA-256": words_hash,
        "Record": (
            f"RoR.md#RoR-{entry_number}; {snapshot}; {authority}; "
            f"Words SHA-256: {words_hash}"
        ),
    }
    if authority_leaf != expected_authority:
        raise Refused("sanitized authority fields do not exactly match the RoR decision")

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
