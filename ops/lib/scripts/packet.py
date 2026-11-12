#!/usr/bin/env python3
"""packet: one dispatch packet per pull request, end to end. Standard library only.

A change reaches `main` only as a packet: one id, one branch, one pull request
and one kept record. The stations are draft and open (the Manager), work and
close (the Writer), audit (the Auditor) and ship (the Orchestrator). Each
station is one command, and each refuses when the one before it is not proved.

Working files are latest-wins and disposable: the draft at
`storage/handoff/PACKET.md`, the gate log at `storage/handoff/RESULTS.md`, and
the one Git worktree at `var/tmp/packet/`. None is committed and none is kept.
The room's own checkout stays on clean `main`. The one kept thing is the leaf,
`archives/packets/DP-SES-NNNN.md`: the contract, the results this tool
measured, and the audit verdict bound to the exact tree.

`gate` is the same law read from Git objects alone; the required check runs it
on every pull request. A station command binds to the caller's own identity,
resolved as the mind tool resolves it. Run the room's own copy, never the copy
inside the worktree.

Filing authority: PoT 1.1.4, 1.1.12 and 1.1.13. The draft and the gate log are
handoffs under storage/handoff/; the worktree and what an abandon keeps are
scratch under var/tmp/; the ledger and the lock are telemetry under
logs/packets/; the leaf is a kept record under archives/packets/.

Spec: docs/ops/specs/scripts/packet.md. This tool reads no session body, and
its records quote nobody.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unicodedata
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[3]
REGISTRY = SESSIONS / "ops" / "etc" / "resident-identities.json"
TOOL = "ops/lib/scripts/packet.py"
LEAVES = "archives/packets"                     # the kept records, one per packet
DRAFT = Path("storage") / "handoff" / "PACKET.md"
RESULTS = Path("storage") / "handoff" / "RESULTS.md"
WORKTREE = Path("var") / "tmp" / "packet"
DRAFT_PREVIOUS = Path("var") / "tmp" / "PACKET.md.prev"
ABANDONED = Path("var") / "tmp" / "PACKET.abandoned.patch"
LEDGER = Path("logs") / "packets" / "ledger.jsonl"
LOCK = Path("logs") / "packets" / "lock"
# The gate's own law: a pull request that changes one of these is named in the gate's output.
LAW = (TOOL, "ops/lib/scripts/redact.py", ".github/workflows/sessions-gates.yml")

TITLE_LIMIT = 58           # characters, so a commit subject (the id, then the title) stays under 72
LINE_LIMIT = 200           # an authority line, an amendment reason, a fallback or abandon reason
OBJECTIVE_LIMIT = 800
NARRATIVE_LIMIT = 2000
NOTE_LIMIT = 1500
SCOPE_LIMIT = 60           # entries
GATE_LIMIT = 80            # entries
GIT_TIMEOUT = 60           # seconds for one local Git answer
NET_TIMEOUT = 300          # seconds for one answer from origin or GitHub
GATE_TIMEOUT = 3600        # seconds for one gate
REVIEW_SETTLE = 300        # seconds a pull request's head rests before it may merge, so a review can land
REQUIRED_CHECK = "sessions-gates"
SEAM = "MIND_TEST_CALLER"  # mind.py's test seam; never passed on to a gate

ID_RE = re.compile(r"^DP-SES-(\d{4})$")
LEAF_NAME_RE = re.compile(r"^DP-SES-(\d{4})\.md$")
BRANCH_RE = re.compile(r"^agent/dp-ses-(\d{4})-(\d{4}-\d{2}-\d{2})$")
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
WORD_RE = re.compile(r"^[a-z][a-z0-9_]*$")
GATE_LINE_RE = re.compile(r"^exit (-?\d+) in (\d+) s: (\S.*)$")
AMENDMENT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) ([a-z0-9][a-z0-9-]*) added (\S+): (\S.*)$")
DRAFT_FIELD_RE = re.compile(r"^(Title|Writer|Auditor|Orchestrator|Authority):[ \t]*(.*?)\s*$")
CREDENTIAL_RE = re.compile(r"(\w+://)[^/@\s]+@")

HEAD_KEYS = ("Packet", "Branch", "Base", "Opened", "Manager", "Writer", "Auditor", "Orchestrator", "Authority")
RESULT_KEYS = ("Closed", "Writer", "Paths changed", "Deviations", "Tree")
AUDIT_KEYS = ("Verdict", "Auditor", "Audited", "Tree")
SECTIONS = ("Objective", "Scope", "Gates", "Amendments", "Results", "Narrative", "Audit", "Audit note")
SEATS = ("Manager", "Writer", "Auditor", "Orchestrator")
DRAFT_FIELDS = ("Title", "Writer", "Auditor", "Orchestrator", "Authority")
SELF_TESTS = ("help", "template")              # gate words that name ops/bin/<word> --test
# Variables that tell Git where a repository is. A caller's own must never redirect this tool.
GIT_PLACE = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_COMMON_DIR",
             "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_PREFIX", "GIT_CEILING_DIRECTORIES")

DRAFT_HEAD = (
    "# Draft dispatch packet\n\n"
    f"Fill every field, then run: python3 -I -B {TOOL} open\n"
    "Each field is one line. No quotation marks. Paths are relative to the room; a folder ends in a slash.\n"
    "Authority is cited by ledger number or digest, never quoted. Gates: the word full, or suite words.\n\n")


class Refused(Exception):
    """Fail closed: the station did not run. Exit 2."""


class Failed(Exception):
    """The station ran and the answer is no: a gate or the required check failed. Exit 1."""


class Pending(Exception):
    """Neither an error nor done: run the same command again. Exit 3."""


# --------------------------------------------------------------------------
# Small helpers.
# --------------------------------------------------------------------------
def iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def clock() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def telling_line(text: str) -> str:
    """The one line of a program's complaint worth relaying, with any address credential removed."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    told = next((line for line in lines if line.startswith(("fatal:", "error:", "remote:", "refused:"))), lines[0] if lines else "no message")
    return CREDENTIAL_RE.sub(r"\1", told)


_SIBLINGS: dict = {}


def sibling(name: str):
    """A room script beside this one, loaded once by path; never a second copy of its logic."""
    if name not in _SIBLINGS:
        path = Path(__file__).with_name(name + ".py")
        spec = importlib.util.spec_from_file_location("packet_" + name, path)
        if spec is None or spec.loader is None or not path.is_file():
            raise Refused(f"{name}.py is not beside this tool, so this station cannot run")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module     # a dataclass resolves its own module while the module runs
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            sys.modules.pop(spec.name, None)
            raise Refused(f"{name}.py cannot run ({exc.__class__.__name__}), so this station cannot run") from None
        _SIBLINGS[name] = module
    return _SIBLINGS[name]


def git_env(extra: dict | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in GIT_PLACE}
    env.update(LC_ALL="C", LANGUAGE="C")
    env.update(extra or {})
    return env


def git_try(cwd: Path, *args: str, env: dict | None = None, timeout: int = GIT_TIMEOUT) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout, env=env or git_env())
    except FileNotFoundError:
        raise Refused("Git is not installed or not on PATH") from None
    except subprocess.TimeoutExpired:
        raise Refused(f"git {args[0]} gave no answer within {timeout} seconds") from None


def git(cwd: Path, *args: str, env: dict | None = None, timeout: int = GIT_TIMEOUT, strip: bool = True) -> str:
    result = git_try(cwd, *args, env=env, timeout=timeout)
    if result.returncode:
        raise Refused(f"git {' '.join(args[:2])} failed (exit {result.returncode}): {telling_line(result.stderr)}")
    return result.stdout.strip() if strip else result.stdout


def push(cwd: Path, *args: str) -> str | None:
    """A plain push, never forced; returns why it failed, or None. Push negotiation is only an optimization, and
    where a host has switched it on it breaks a push that only deletes, so it is switched off for this call."""
    done = git_try(cwd, "-c", "push.negotiate=false", "push", "--quiet", "origin", *args, timeout=NET_TIMEOUT)
    return f"git push failed (exit {done.returncode}): {telling_line(done.stderr)}" if done.returncode else None


def name_status(cwd: Path, *args: str, env: dict | None = None) -> list[tuple[str, str]]:
    """Changed paths as (status, path), exact for any path: no quoting and no rename guessing."""
    parts = git(cwd, "diff", "--name-status", "--no-renames", "-z", *args, env=env, strip=False).split("\0")
    return [(parts[i], parts[i + 1]) for i in range(0, len(parts) - 1, 2)]


# --------------------------------------------------------------------------
# The leaf: render and parse. It is valid only in canonical form.
# --------------------------------------------------------------------------
def render_leaf(leaf: dict) -> str:
    head = leaf["head"]
    out = [f"# {head['Packet']}: {leaf['title']}", ""]
    out += [f"- {k}: {head[k]}" for k in HEAD_KEYS] + [""]
    out += ["## Objective", "", leaf["objective"], ""]
    out += ["## Scope", ""] + [f"- {p}" for p in leaf["scope"]] + [""]
    out += ["## Gates", ""] + [f"- {g}" for g in leaf["gates"]] + [""]
    if leaf["amendments"]:
        out += ["## Amendments", ""] + [f"- {a}" for a in leaf["amendments"]] + [""]
    if leaf["results"] is not None:
        results = leaf["results"]
        out += ["## Results", ""] + [f"- {k}: {results['head'][k]}" for k in RESULT_KEYS]
        out += [f"- Gate: exit {code} in {seconds} s: {name}" for code, seconds, name in results["gates"]] + [""]
        out += ["## Narrative", "", results["narrative"], ""]
    if leaf["audit"] is not None:
        audit = leaf["audit"]
        out += ["## Audit", ""] + [f"- {k}: {audit['head'][k]}" for k in AUDIT_KEYS] + [""]
        out += ["## Audit note", "", audit["note"], ""]
    return "\n".join(out)


def contract_text(leaf: dict) -> str:
    """The part no station changes by hand: everything above Results."""
    return render_leaf(dict(leaf, results=None, audit=None))


def contract_digest(leaf: dict) -> str:
    return sha256(contract_text(leaf).encode("utf-8"))


def _pairs(lines: list[str], keys: tuple, what: str) -> dict:
    found = {}
    for key, line in zip(keys, lines):
        if line.startswith(f"- {key}: "):
            found[key] = line[len(key) + 4:]
    if len(found) != len(keys):
        raise Refused(f"the leaf's {what} must name {', '.join(keys)}, in that order")
    return found


def _bullets(body: list[str], what: str) -> list[str]:
    if not body or any(not line.startswith("- ") for line in body):
        raise Refused(f"the leaf's {what} must be a list, one `- ` line per entry")
    return [line[2:] for line in body]


def parse_leaf(text: str) -> dict:
    lines = text.split("\n")
    count = len(HEAD_KEYS)
    title = re.match(r"^# (DP-SES-\d{4}): (\S.*)$", lines[0])
    if title is None or len(lines) < count + 4 or lines[1] != "" or lines[count + 2] != "":
        raise Refused("a leaf opens with `# DP-SES-NNNN: title`, a blank line and its nine header lines")
    if any(line != line.rstrip() for line in lines):
        raise Refused("the leaf is not in canonical form: a line ends in a space")
    head = _pairs(lines[2:count + 2], HEAD_KEYS, "header")
    sections: list[tuple[str, list[str]]] = []
    for line in lines[count + 3:]:
        if line.startswith("## "):
            sections.append((line[3:], []))
        elif not sections:
            raise Refused("text stands between the leaf's header and its first section")
        else:
            sections[-1][1].append(line)
    names = [name for name, _ in sections]
    if names != [name for name in SECTIONS if name in names] or names[:3] != ["Objective", "Scope", "Gates"] \
            or ("Results" in names) != ("Narrative" in names) or ("Audit" in names) != ("Audit note" in names) \
            or ("Audit" in names and "Results" not in names):
        raise Refused("the leaf's sections are not the known ones in their order")
    bodies = {}
    for name, body in sections:
        if len(body) < 3 or body[0] != "" or body[-1] != "" or body[1] == "" or body[-2] == "":
            raise Refused(f"the leaf's {name} section is not set between two single blank lines")
        bodies[name] = body[1:-1]
    leaf = {"title": title.group(2), "head": head, "objective": "\n".join(bodies["Objective"]),
            "scope": _bullets(bodies["Scope"], "Scope"), "gates": _bullets(bodies["Gates"], "Gates"),
            "amendments": _bullets(bodies["Amendments"], "Amendments") if "Amendments" in bodies else [],
            "results": None, "audit": None}
    if "Results" in bodies:
        rows = _bullets(bodies["Results"], "Results")
        gates = []
        for row in rows[len(RESULT_KEYS):]:
            m = GATE_LINE_RE.match(row[6:]) if row.startswith("Gate: ") else None
            if m is None:
                raise Refused("a Results line after the first five is not a gate line")
            gates.append((int(m.group(1)), int(m.group(2)), m.group(3)))
        leaf["results"] = {"head": _pairs(bodies["Results"][:len(RESULT_KEYS)], RESULT_KEYS, "Results"),
                           "gates": gates, "narrative": "\n".join(bodies["Narrative"])}
    if "Audit" in bodies:
        if len(bodies["Audit"]) != len(AUDIT_KEYS):
            raise Refused("the leaf's Audit section holds exactly four lines")
        leaf["audit"] = {"head": _pairs(bodies["Audit"], AUDIT_KEYS, "Audit"), "note": "\n".join(bodies["Audit note"])}
    if title.group(1) != head["Packet"] or render_leaf(leaf) != text:
        raise Refused("the leaf is not in canonical form")
    return leaf


def clean_text(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip("\n")


def text_problems(value: str, label: str, limit: int, one_line: bool = False) -> list[str]:
    if not value.strip():
        return [f"{label}: empty"]
    problems = []
    if len(value) > limit:
        problems.append(f"{label}: {len(value)} characters; the limit is {limit}")
    if one_line and ("\n" in value or value != value.strip()):
        problems.append(f"{label}: must be one line with no outer spaces")
    elif value != clean_text(value):
        problems.append(f"{label}: trailing spaces or outer blank lines")
    if any(line.startswith("#") for line in value.split("\n")):
        problems.append(f"{label}: a line begins with #, which would read as a heading")
    odd = next((c for c in value if c != "\n" and not 32 <= ord(c) <= 126), None)
    if odd is not None:
        problems.append(f"{label}: not plain ASCII (the first such character is {unicodedata.name(odd, f'U+{ord(odd):04X}')}); "
                        "a kept record uses plain punctuation")
    return problems


def scope_problem(entry: str) -> str | None:
    """Why a scope entry is refused; None when it is an exact path or a folder prefix ending in /."""
    core = entry[:-1] if entry.endswith("/") else entry
    if not core or entry.startswith(("/", "~", "-")) or any(not 33 <= ord(c) <= 126 or c in "*?[]{}\\\"'`<>|;&$" for c in entry):
        return "not a plain path relative to the room (no spaces, patterns or quotes)"
    if posixpath.normpath(core) != core or core.split("/")[0] in ("..", ".", ".git"):
        return "not a normal path inside the room"
    if (entry.endswith("/") and (LEAVES + "/").startswith(entry)) or \
            (posixpath.dirname(core) == LEAVES and LEAF_NAME_RE.match(posixpath.basename(core))):
        return "packet leaves are never in scope; the tool writes the one leaf itself"
    return None


def in_scope(path: str, scope: list[str]) -> bool:
    return any(path == entry or (entry.endswith("/") and path.startswith(entry)) for entry in scope)


def gate_names(gates: list[str]) -> list[str] | None:
    """The record names of suite-word gates, in order; None for `full`, whose list is the worktree's own."""
    if gates == ["full"]:
        return None
    return [f"ops/bin/{g} --test" if g in SELF_TESTS else f"tools/test/test_{g}.py" for g in gates]


def leaf_problems(leaf: dict) -> list[str]:
    """Every reason a parsed leaf is not a valid record; empty when it is."""
    head, problems = leaf["head"], []
    number, branch = ID_RE.match(head["Packet"]), BRANCH_RE.match(head["Branch"])
    if number is None:
        problems.append("Packet: not DP-SES-NNNN")
    if branch is None or number is None or branch.group(1) != number.group(1):
        problems.append("Branch: not agent/dp-ses-NNNN-YYYY-MM-DD for this packet")
    if not (head["Base"].startswith("commit ") and OID_RE.match(head["Base"][7:])):
        problems.append("Base: not the word commit and a full commit id")
    if not TIME_RE.match(head["Opened"]):
        problems.append("Opened: not a UTC time")
    problems += [f"{seat}: not a registry key" for seat in SEATS if not KEY_RE.match(head[seat])]
    if head["Writer"] == head["Auditor"]:
        problems.append("Writer and Auditor are the same key; no seat audits its own work (PoT 4.2.2)")
    problems += text_problems(leaf["title"], "Title", TITLE_LIMIT, one_line=True)
    problems += text_problems(head["Authority"], "Authority", LINE_LIMIT, one_line=True)
    problems += text_problems(leaf["objective"], "Objective", OBJECTIVE_LIMIT)
    scope = leaf["scope"]
    if len(scope) > SCOPE_LIMIT or len(set(scope)) != len(scope):
        problems.append(f"Scope: at most {SCOPE_LIMIT} entries, each once")
    problems += [f"Scope entry {entry!r}: {why}" for entry in scope for why in [scope_problem(entry)] if why]
    gates = leaf["gates"]
    if len(gates) > GATE_LIMIT or len(set(gates)) != len(gates) or any(not WORD_RE.match(g) for g in gates) \
            or ("full" in gates and gates != ["full"]):
        problems.append("Gates: the one word full, or suite words, each once (help and template name the two self-tests)")
    for line in leaf["amendments"]:
        m = AMENDMENT_RE.match(line)
        if m is None or m.group(3) not in scope or text_problems(m.group(4), "reason", LINE_LIMIT, one_line=True):
            problems.append("Amendments: a line is not `<time> <key> added <path in scope>: <reason>`")
    results = leaf["results"]
    if results is not None:
        r = results["head"]
        if not TIME_RE.match(r["Closed"]) or r["Writer"] != head["Writer"]:
            problems.append("Results: Closed is not a UTC time, or its Writer is not the packet's Writer")
        if not r["Paths changed"].isdigit() or int(r["Paths changed"]) < 1 or not r["Deviations"].isdigit():
            problems.append("Results: Paths changed is a count of at least 1 and Deviations is a count")
        if not (r["Tree"].startswith("tree ") and OID_RE.match(r["Tree"][5:])):
            problems.append("Results: Tree is not the word tree and a full tree id")
        failed = [name for code, _, name in results["gates"] if code != 0]
        named = gate_names(gates)
        if not results["gates"] or failed:
            problems.append(f"Results: {len(failed)} gate(s) did not exit 0" if failed else "Results: no gate was run")
        elif named is not None and [name for _, _, name in results["gates"]] != named:
            problems.append("Results: the gates run are not the gates the contract names")
        problems += text_problems(results["narrative"], "Narrative", NARRATIVE_LIMIT)
    audit = leaf["audit"]
    if audit is not None:
        a = audit["head"]
        if a["Verdict"] not in ("PASS", "FAIL") or a["Auditor"] != head["Auditor"] or not TIME_RE.match(a["Audited"]):
            problems.append("Audit: the Verdict is PASS or FAIL, by the packet's Auditor, at a UTC time")
        if not (a["Tree"].startswith("tree ") and OID_RE.match(a["Tree"][5:])):
            problems.append("Audit: Tree is not the word tree and a full tree id")
        problems += text_problems(audit["note"], "Audit note", NOTE_LIMIT)
    return problems


def public_problems(text: str, what: str = "the leaf") -> list[str]:
    """A leaf is published. It must pass the room's own redaction check with nothing to redact."""
    redact = sibling("redact")
    try:
        spans, _ = redact.classify(text, {})
        found = redact.counts(spans)
    except Exception as exc:
        return [f"the redaction check could not read {what} ({exc.__class__.__name__})"]
    kinds = (("words", "quoted words"), ("sessions", "session identifiers"), ("truncated", "truncated identifiers"),
             ("paths", "host paths"), ("unclassified", "quotations or hexadecimal runs the rules cannot place"))
    held = [f"{found[k]} {label}" for k, label in kinds if found.get(k)]
    if held:
        return [f"{what} holds what a public record may not: " + ", ".join(held) + "; cite and never quote, "
                "give paths relative to the room, and give a Git id after the word commit or tree"]
    return []


# --------------------------------------------------------------------------
# The draft: a fill-in form, latest-wins.
# --------------------------------------------------------------------------
def render_draft(fields: dict, objective: str, scope: list[str], gates: list[str]) -> str:
    out = DRAFT_HEAD + "".join(f"{k}: {fields.get(k, '')}".rstrip() + "\n" for k in DRAFT_FIELDS)
    out += "\n## Objective\n\n" + (objective + "\n" if objective else "")
    out += "\n## Scope\n\n" + "".join(f"- {p}\n" for p in scope)
    out += "\n## Gates\n\n" + "".join(f"- {g}\n" for g in gates)
    return out


def parse_draft(text: str) -> dict:
    fields, sections, current = {}, {}, None
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
        else:
            m = DRAFT_FIELD_RE.match(line)
            if m and m.group(1) not in fields:
                fields[m.group(1)] = m.group(2)
    missing = [k for k in DRAFT_FIELDS if not fields.get(k)]
    missing += [f"## {name}" for name in ("Objective", "Scope", "Gates") if not any(l.strip() for l in sections.get(name, []))]
    if missing:
        raise Refused("the draft is not filled: " + ", ".join(missing))
    lists = {}
    for name in ("Scope", "Gates"):
        rows = [l.strip() for l in sections[name] if l.strip()]
        if any(not row.startswith("- ") for row in rows):
            raise Refused(f"the draft's {name} is a list, one `- ` line per entry")
        lists[name] = [row[2:].strip() for row in rows]
    return {"fields": fields, "objective": clean_text("\n".join(sections["Objective"])),
            "scope": lists["Scope"], "gates": lists["Gates"]}


# --------------------------------------------------------------------------
# The room: private files, the lock, the ledger and the caller.
# --------------------------------------------------------------------------
def private_parents(room: Path, path: Path) -> None:
    current = room
    for part in path.parent.relative_to(room).parts:
        current = current / part
        if not current.exists() and not current.is_symlink():
            current.mkdir(mode=0o700)


def write_private(room: Path, rel: Path, content: str | bytes) -> None:
    path = room / rel
    private_parents(room, path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix="." + path.name + ".")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content.encode("utf-8") if isinstance(content, str) else content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


@contextlib.contextmanager
def room_lock(room: Path):
    """One station at a time in one room."""
    path = room / LOCK
    private_parents(room, path)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def ledger_append(room: Path, line: dict) -> None:
    path = room / LEDGER
    private_parents(room, path)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, (json.dumps(line, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def ledger_last(room: Path, packet: str, field: str) -> dict | None:
    """The newest ledger line for this packet that carries the field."""
    path, found = room / LEDGER, None
    if path.is_file():
        for row in path.read_text(encoding="utf-8", errors="replace").splitlines():
            with contextlib.suppress(ValueError):
                line = json.loads(row)
                if isinstance(line, dict) and line.get("packet") == packet and field in line:
                    found = line
    return found


def record(args, packet: str, action: str, actor: str, **facts) -> None:
    ledger_append(args.room, dict(facts, packet=packet, action=action, actor=actor, time=iso(args.now)))


def caller(args) -> str:
    """The caller's registry key, resolved exactly as the mind tool resolves it; never a session id."""
    mind = sibling("mind")
    if os.environ.get(mind.SEAM) is None and args.registry.resolve() != REGISTRY.resolve():
        raise Refused("the caller is verified through the room's canonical registry; another registry serves tests only")
    try:
        return mind.caller_key(types.SimpleNamespace(room=args.room, registry=args.registry))
    except mind.Refused as exc:
        raise Refused(f"the caller is not verified, so no station runs: {exc}") from None


def registry_problems(args, keys: dict) -> list[str]:
    """Each named key must be registered exactly once, to this room. keys maps a label to a key."""
    mind = sibling("mind")
    try:
        registry = mind.read_registry(args.registry)
    except mind.Refused as exc:
        return [str(exc)]
    return [f"{label}: {problem}" for label, key in keys.items() for problem in mind.registered(registry, key, args.room)[1]]


def one_line(value: str, label: str) -> str:
    value = clean_text(value)
    problems = text_problems(value, label, LINE_LIMIT, one_line=True)
    if problems:
        raise Refused("; ".join(problems))
    return value


def read_text_arg(source: str, label: str, limit: int) -> str:
    """A narrative or a note, checked before anything slow runs: bounded, plain, and fit to publish."""
    try:
        text = clean_text(sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise Refused(f"the {label} file is unreadable ({exc.__class__.__name__})") from None
    problems = text_problems(text, label, limit) or public_problems(text, f"the {label}")
    if problems:
        raise Refused("; ".join(problems))
    return text


# --------------------------------------------------------------------------
# Git facts. State is derived from them, never stored.
# --------------------------------------------------------------------------
def room_problem(room: Path) -> str | None:
    answer = git_try(room, "rev-parse", "--show-toplevel", "--git-dir", "--git-common-dir")
    rows = answer.stdout.splitlines()
    if answer.returncode or len(rows) != 3 or Path(rows[0]).resolve() != room:
        return "the room is not the root of a Git checkout"
    if (room / rows[1]).resolve() != (room / rows[2]).resolve():
        return "this is a linked Git worktree, not the room's own checkout; run the room's own copy of the tool"
    return None


def dirty_paths(checkout: Path) -> list[str]:
    return [line[3:] for line in git(checkout, "status", "--porcelain", strip=False).splitlines() if line]


def clean_main(room: Path) -> str:
    """The room is on `main` with nothing uncommitted; returns its commit."""
    branch = git(room, "rev-parse", "--abbrev-ref", "HEAD")
    if branch != "main":
        raise Refused(f"the room is on {branch}, not main; the room's own checkout stays on main")
    dirty = dirty_paths(room)
    if dirty:
        raise Refused(f"the room's own checkout has {len(dirty)} uncommitted path(s), the first {dirty[0]}; "
                      f"packet work lives under {WORKTREE.as_posix()}/, and the room stays clean main")
    return git(room, "rev-parse", "HEAD")


def level_main(room: Path) -> str:
    """Clean `main`, and the same commit as origin's `main` fetched now; returns it."""
    local = clean_main(room)
    git(room, "fetch", "--quiet", "origin", "main", timeout=NET_TIMEOUT)
    remote = git(room, "rev-parse", "refs/remotes/origin/main")
    if local != remote:
        behind = git_try(room, "merge-base", "--is-ancestor", local, remote).returncode == 0
        raise Refused("the room's main is behind origin/main; run `packet.py sync` first" if behind else
                      "the room's main holds commits origin/main does not; never force; stop and report")
    return local


def sync_room(room: Path) -> str:
    """Bring clean `main` level with origin's `main` by fast-forward only; returns the commit."""
    local = clean_main(room)
    git(room, "fetch", "--quiet", "origin", "main", timeout=NET_TIMEOUT)
    remote = git(room, "rev-parse", "refs/remotes/origin/main")
    if local != remote:
        if git_try(room, "merge-base", "--is-ancestor", local, remote).returncode:
            raise Refused("the room's main holds commits origin/main does not; never force; stop and report")
        git(room, "merge", "--ff-only", "--quiet", "refs/remotes/origin/main")
    if git(room, "rev-parse", "HEAD") != remote or dirty_paths(room):
        raise Refused("after the fast-forward the room is not clean main level with origin/main; stop and report")
    return remote


@contextlib.contextmanager
def private_index():
    """A throwaway index, so a question about a tree never touches a checkout's own index."""
    with tempfile.TemporaryDirectory(prefix="packet-index-") as tmp:
        yield git_env({"GIT_INDEX_FILE": str(Path(tmp) / "index")})


def tree_of_worktree(wt: Path, leaf_rel: str, base: str) -> tuple[str, list[tuple[str, str]]]:
    """The tree a commit of the worktree would hold, without the leaf, and each path changed since base."""
    with private_index() as env:
        git(wt, "read-tree", "HEAD", env=env)
        git(wt, "add", "-A", "--", ".", env=env)
        git(wt, "update-index", "--force-remove", "--", leaf_rel, env=env)
        return git(wt, "write-tree", env=env), name_status(wt, "--cached", base, env=env)


def tree_of_commit(repo: Path, commit: str, leaf_rel: str) -> str:
    """The tree of a commit without the leaf, from Git objects alone."""
    with private_index() as env:
        git(repo, "read-tree", commit, env=env)
        git(repo, "update-index", "--force-remove", "--", leaf_rel, env=env)
        return git(repo, "write-tree", env=env)


def leaf_numbers(repo: Path, revision: str) -> list[int]:
    listing = git_try(repo, "ls-tree", "--name-only", revision, LEAVES + "/").stdout
    return sorted(int(m.group(1)) for m in (LEAF_NAME_RE.match(posixpath.basename(line)) for line in listing.splitlines()) if m)


def outside_scope(changes: list[tuple[str, str]], scope: list[str]) -> list[str]:
    return [path for _, path in changes if not in_scope(path, scope)]


class Active:
    """The one active packet, read from the worktree."""

    def __init__(self, args, lenient: bool = False):
        self.room, self.wt = args.room, args.room / WORKTREE
        if not self.wt.is_dir():
            raise Refused("no packet is active; the Manager drafts and opens one")
        top = git_try(self.wt, "rev-parse", "--show-toplevel")
        if top.returncode or Path(top.stdout.strip()).resolve() != self.wt.resolve():
            raise Refused(f"{WORKTREE.as_posix()}/ exists but is not this room's packet worktree; stop and report")
        self.branch = git(self.wt, "rev-parse", "--abbrev-ref", "HEAD")
        m = BRANCH_RE.match(self.branch)
        if m is None:
            raise Refused(f"the worktree is on {self.branch!r}, which is not a packet branch; stop and report")
        self.id = f"DP-SES-{m.group(1)}"
        self.leaf_rel = f"{LEAVES}/{self.id}.md"
        self.leaf_path = self.wt / self.leaf_rel
        opened = ledger_last(self.room, self.id, "seats") or {}
        self.leaf, self.damage = None, None
        try:
            try:
                leaf = parse_leaf(self.leaf_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                raise Refused(f"the worktree holds no readable leaf at {self.leaf_rel}") from None
            if leaf["head"]["Packet"] != self.id or leaf["head"]["Branch"] != self.branch:
                raise Refused("the leaf names another packet or branch than the worktree it is in")
            self.leaf = leaf
        except Refused as exc:
            if not lenient:
                raise Refused(f"{exc}; the packet is damaged: its Manager abandons it (the work is kept as a patch) "
                              "and opens it again") from None
            self.damage = str(exc)
        self.head = self.leaf["head"] if self.leaf else (opened.get("seats") if isinstance(opened.get("seats"), dict) else None)
        self.base = self.leaf["head"]["Base"][7:] if self.leaf else opened.get("base")

    def require_contract(self) -> None:
        opened = ledger_last(self.room, self.id, "contract")
        if opened is None or opened["contract"] != contract_digest(self.leaf):
            raise Refused("the packet's contract is not the one the ledger recorded at open or amend; only `amend` "
                          "changes a contract (packet hash failure: stop and report)")

    def tree(self) -> tuple[str, list[tuple[str, str]]]:
        tree, changes = tree_of_worktree(self.wt, self.leaf_rel, self.base)
        return tree, [(status, path) for status, path in changes if path != self.leaf_rel]

    def write(self, leaf: dict) -> None:
        text = render_leaf(leaf)
        problems = leaf_problems(leaf) or public_problems(text)
        if problems:
            raise Refused("; ".join(problems))
        self.leaf_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.leaf_path.with_name("." + self.leaf_path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.chmod(tmp, 0o644)
        os.replace(tmp, self.leaf_path)
        self.leaf = leaf


def gate_plan(wt: Path, gates: list[str]) -> list[tuple[str, list[str]]]:
    """Each gate as (name in the record, command). No shell and no free command: suites and the two self-tests."""
    names = gate_names(gates)
    if names is None:
        names = [f"tools/test/{p.name}" for p in sorted((wt / "tools" / "test").glob("test_*.py"))]
        names += [f"ops/bin/{word} --test" for word in SELF_TESTS if (wt / "ops" / "bin" / word).is_file()]
    plan = []
    for name in names:
        target = name.split()[0]
        if not (wt / target).is_file():
            raise Refused(f"a gate names {target}, which is not in the worktree")
        plan.append((name, [target, "--test"] if name.endswith(" --test") else [sys.executable, "-I", "-B", target]))
    if not plan:
        raise Refused("the packet's gates name nothing that can run")
    return plan


def run_gates(wt: Path, plan: list[tuple[str, list[str]]]) -> tuple[list[tuple[int, int, str]], str]:
    """Run each gate in the worktree at umask 0002, as the required check does. Returns the rows and the log."""
    env = {k: v for k, v in os.environ.items() if k != SEAM and k not in GIT_PLACE}
    rows, log = [], []
    for name, command in plan:
        started = time.monotonic()
        try:
            done = subprocess.run(command, cwd=wt, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  timeout=GATE_TIMEOUT, env=env, preexec_fn=lambda: os.umask(0o002))
            code, output = done.returncode, done.stdout + done.stderr
        except subprocess.TimeoutExpired:
            code, output = 124, f"no result within {GATE_TIMEOUT} seconds"
        except OSError as exc:
            code, output = 126, f"could not run ({exc.__class__.__name__})"
        seconds = int(time.monotonic() - started)
        rows.append((code, seconds, name))
        tail = "\n".join(output.rstrip().splitlines()[-40:])
        log.append(f"## exit {code} in {seconds} s: {name}\n\n~~~text\n{tail}\n~~~\n")
        print(f"gate: exit {code} in {seconds} s: {name}", flush=True)
    return rows, "\n".join(log)


# --------------------------------------------------------------------------
# GitHub, through `gh api` only.
# --------------------------------------------------------------------------
def repo_slug(room: Path) -> str:
    parts = [p for p in re.split(r"[/:]", git(room, "remote", "get-url", "origin").rstrip("/")) if p]
    if len(parts) < 2:
        raise Refused("the origin address does not name an owner and a repository")
    return f"{parts[-2]}/{parts[-1].removesuffix('.git')}"


def gh(room: Path, method: str, endpoint: str, fields: dict | None = None, body_file: Path | None = None):
    command = ["gh", "api", "-X", method, endpoint]
    for key, value in (fields or {}).items():
        command += ["-f", f"{key}={value}"]
    if body_file is not None:
        command += ["-F", f"body=@{body_file}"]
    what = f"{method} {endpoint.split('?')[0]}"
    try:
        done = subprocess.run(command, cwd=room, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=NET_TIMEOUT)
    except FileNotFoundError:
        raise Refused("gh is not installed or not on PATH; the ship station needs it, signed in") from None
    except subprocess.TimeoutExpired:
        raise Refused(f"gh gave no answer to {what} within {NET_TIMEOUT} seconds") from None
    if done.returncode:
        raise Refused(f"GitHub refused {what}: {telling_line(done.stderr or done.stdout)}")
    try:
        return json.loads(done.stdout) if done.stdout.strip() else None
    except ValueError:
        raise Refused(f"GitHub's answer to {what} is not JSON") from None


def find_pull(room: Path, slug: str, branch: str) -> dict | None:
    """The newest pull request from this branch, in any state."""
    pulls = gh(room, "GET", f"repos/{slug}/pulls?head={slug.split('/')[0]}:{branch}&state=all&per_page=10") or []
    return max(pulls, key=lambda p: p.get("number") or 0) if pulls else None


def required_check(room: Path, slug: str, commit: str) -> dict | None:
    """The newest run of the required check on this commit."""
    runs = (gh(room, "GET", f"repos/{slug}/commits/{commit}/check-runs?per_page=100") or {}).get("check_runs", [])
    runs = [r for r in runs if r.get("name") == REQUIRED_CHECK]
    return max(runs, key=lambda r: r.get("started_at") or "") if runs else None


def unanswered_findings(room: Path, slug: str, pull: dict) -> list[str]:
    """Review comments by anyone but the pull request's own account that it has not replied to."""
    author = (pull.get("user") or {}).get("login")
    comments, page = [], 1
    while True:
        batch = gh(room, "GET", f"repos/{slug}/pulls/{pull['number']}/comments?per_page=100&page={page}") or []
        comments += batch
        if len(batch) < 100:
            break
        page += 1
    answered = {c.get("in_reply_to_id") for c in comments if (c.get("user") or {}).get("login") == author}
    return [f"{c.get('path')}:{c.get('line') or c.get('original_line')}" + (f" {c['html_url']}" if c.get("html_url") else "")
            for c in comments
            if c.get("in_reply_to_id") is None and (c.get("user") or {}).get("login") != author and c.get("id") not in answered]


def seconds_since(args, when: str | None) -> float:
    """Seconds from a GitHub time to now; a time that cannot be read counts as long ago."""
    try:
        then = dt.datetime.fromisoformat((when or "").replace("Z", "+00:00"))
        return ((args.now if args.fixed_now else clock()) - then).total_seconds()
    except (ValueError, TypeError):
        return float(REVIEW_SETTLE)


# --------------------------------------------------------------------------
# Stations.
# --------------------------------------------------------------------------
def previous_seats(room: Path) -> dict:
    """The Auditor and the Orchestrator of the newest landed packet: a prefill for the form, nothing more."""
    with contextlib.suppress(Refused, ValueError):
        number = max(leaf_numbers(room, "main"))
        head = parse_leaf(git(room, "show", f"main:{LEAVES}/DP-SES-{number:04d}.md", strip=False))["head"]
        return {"Auditor": head["Auditor"], "Orchestrator": head["Orchestrator"]}
    return {}


def cmd_draft(args):
    path = args.room / DRAFT
    if not path.parent.is_dir():
        raise Refused(f"{DRAFT.parent.as_posix()}/ does not exist in this room")
    carried = previous_seats(args.room)
    fields = {"Title": args.title or "", "Writer": args.writer or "", "Authority": args.authority or "",
              "Auditor": args.auditor or carried.get("Auditor", ""),
              "Orchestrator": args.orchestrator or carried.get("Orchestrator", "")}
    objective = ""
    if args.objective:
        objective = clean_text(sys.stdin.read() if args.objective == "-" else Path(args.objective).read_text(encoding="utf-8"))
    note = ""
    if path.is_file():
        write_private(args.room, DRAFT_PREVIOUS, path.read_bytes())
        note = f"; the draft it replaced is at {DRAFT_PREVIOUS.as_posix()} until the next one"
    write_private(args.room, DRAFT, render_draft(fields, objective, args.scope or [], args.gate or ["full"]))
    print(f"packet: draft written to {DRAFT.as_posix()} (latest-wins{note})")
    print("next: the Manager fills it, then runs `packet.py open`")
    return 0


def cmd_open(args):
    me = caller(args)
    with room_lock(args.room):
        room, wt = args.room, args.room / WORKTREE
        if wt.exists():
            raise Refused(f"a packet is already active in {WORKTREE.as_posix()}/; one packet at a time: it ships or is abandoned first")
        try:
            draft = parse_draft((room / DRAFT).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            raise Refused(f"no readable draft at {DRAFT.as_posix()}; run `packet.py draft` and fill it") from None
        base = level_main(room)
        number = max(leaf_numbers(room, "main"), default=0) + 1
        if number > 9999:
            raise Refused("the packet numbers are used up")
        packet, branch = f"DP-SES-{number:04d}", f"agent/dp-ses-{number:04d}-{args.now:%Y-%m-%d}"
        f = draft["fields"]
        head = {"Packet": packet, "Branch": branch, "Base": f"commit {base}", "Opened": iso(args.now), "Manager": me,
                "Writer": f["Writer"], "Auditor": f["Auditor"], "Orchestrator": f["Orchestrator"], "Authority": f["Authority"]}
        leaf = {"title": f["Title"], "head": head, "objective": draft["objective"], "scope": draft["scope"],
                "gates": draft["gates"], "amendments": [], "results": None, "audit": None}
        text = render_leaf(leaf)
        problems = leaf_problems(leaf) or registry_problems(args, {seat: head[seat] for seat in SEATS}) or public_problems(text)
        if problems:
            raise Refused("; ".join(problems))
        pattern = f"agent/dp-ses-{number:04d}-*"
        remote = git_try(room, "ls-remote", "--heads", "origin", pattern, timeout=NET_TIMEOUT)
        if remote.returncode:
            raise Refused("origin did not answer, so the tool cannot tell whether the number is free; run it again")
        taken = [line.split("refs/heads/", 1)[1] + " on origin" for line in remote.stdout.splitlines() if "refs/heads/" in line]
        taken += [ref[len("refs/heads/"):] + " here" for ref in
                  git(room, "for-each-ref", "--format=%(refname)", f"refs/heads/{pattern}").splitlines()]
        if taken:
            raise Refused(f"a branch for {packet} already exists: " + ", ".join(taken) + "; if it is what an abandoned or "
                          "rehearsed packet left behind, the Orchestrator deletes it (`git push origin --delete NAME`, or "
                          "`git branch -D NAME` here) and the Manager opens again; otherwise stop and report")
        try:
            git(room, "worktree", "add", "--quiet", "-b", branch, str(wt), "main")
            (wt / LEAVES).mkdir(parents=True, exist_ok=True)
            (wt / LEAVES / f"{packet}.md").write_text(text, encoding="utf-8")
            record(args, packet, "open", me, contract=contract_digest(leaf), base=base, branch=branch,
                   seats={seat: head[seat] for seat in SEATS})
        except BaseException:
            git_try(room, "worktree", "remove", "--force", str(wt))
            git_try(room, "branch", "-D", branch)
            raise
        with contextlib.suppress(OSError):
            (room / DRAFT).unlink()
    print(f"packet: {packet} is open on {branch}, base {base[:12]}")
    print(f"next: the Writer ({head['Writer']}) edits only under {WORKTREE.as_posix()}/, only in scope, then runs `packet.py close`")
    return 0


def cmd_amend(args):
    me = caller(args)
    reason = one_line(args.reason, "reason")
    with room_lock(args.room):
        active = Active(args)
        if me != active.head["Manager"]:
            raise Refused(f"the caller is {me!r}; only the packet's Manager ({active.head['Manager']}) changes its scope")
        active.require_contract()
        leaf = dict(active.leaf, scope=list(active.leaf["scope"]), amendments=list(active.leaf["amendments"]),
                    results=None, audit=None)
        for path in args.add:
            if path in leaf["scope"]:
                raise Refused(f"{path!r} is already in scope")
            leaf["scope"].append(path)
            leaf["amendments"].append(f"{iso(args.now)} {me} added {path}: {reason}")
        active.write(leaf)
        record(args, active.id, "amend", me, contract=contract_digest(leaf), added=args.add)
    print(f"packet: {active.id} scope now holds {len(leaf['scope'])} entries ({len(args.add)} added); any earlier close is void")
    print(f"next: the Writer ({active.head['Writer']}) runs `packet.py close`")
    return 0


def scoped_tree(active: Active, moment: str) -> tuple[str, list[tuple[str, str]]]:
    tree, changes = active.tree()
    outside = outside_scope(changes, active.leaf["scope"])
    if outside:
        raise Refused(f"{len(outside)} changed path(s) are outside the packet's scope {moment}: " + ", ".join(outside[:10])
                      + "; the Manager amends the scope, or the change is undone")
    if not changes:
        raise Refused("nothing in scope has changed; there is nothing to close")
    return tree, changes


def cmd_close(args):
    me = caller(args)
    narrative = read_text_arg(args.narrative, "narrative", NARRATIVE_LIMIT)
    with room_lock(args.room):
        active = Active(args)
        if me != active.head["Writer"]:
            raise Refused(f"the caller is {me!r}; only the packet's Writer ({active.head['Writer']}) closes it")
        active.require_contract()
        clean_main(args.room)
        scoped_tree(active, "before the gates")
        rows, log = run_gates(active.wt, gate_plan(active.wt, active.leaf["gates"]))
        write_private(args.room, RESULTS, f"# {active.id} gate log (latest-wins, private)\n\nClose attempt: {iso(args.now)} by {me}\n\n{log}")
        failed = [name for code, _, name in rows if code != 0]
        if failed:
            raise Failed(f"{len(failed)} of {len(rows)} gate(s) did not exit 0, the first {failed[0]}; "
                         f"the log is {RESULTS.as_posix()}; the packet stays at the work station")
        tree, changes = scoped_tree(active, "after the gates")
        closed = args.now if args.fixed_now else clock()          # when the gates had finished, not when they began
        results = {"head": {"Closed": iso(closed), "Writer": me, "Paths changed": str(len(changes)),
                            "Deviations": str(args.deviations), "Tree": f"tree {tree}"}, "gates": rows, "narrative": narrative}
        active.write(dict(active.leaf, results=results, audit=None))
        record(args, active.id, "close", me, tree=tree, gates=len(rows), paths=len(changes), deviations=args.deviations)
    print(f"packet: {active.id} closed: {len(changes)} path(s), {len(rows)} of {len(rows)} gates passed, "
          f"deviations {args.deviations}, tree {tree[:12]}")
    print(f"next: the Auditor ({active.head['Auditor']}) reads `packet.py diff`, then runs `packet.py audit --verdict pass|fail --note FILE`")
    return 0


def cmd_audit(args):
    me = caller(args)
    note = read_text_arg(args.note, "audit note", NOTE_LIMIT)
    with room_lock(args.room):
        active = Active(args)
        if me != active.head["Auditor"]:
            raise Refused(f"the caller is {me!r}; only the packet's Auditor ({active.head['Auditor']}) records its verdict")
        active.require_contract()
        results = active.leaf["results"]
        if results is None:
            raise Refused("the packet is not closed; there is nothing to audit")
        tree, _ = active.tree()
        if f"tree {tree}" != results["head"]["Tree"]:
            raise Refused("the worktree changed after close; the Writer closes again before any verdict")
        verdict = args.verdict.upper()
        audit = {"head": {"Verdict": verdict, "Auditor": me, "Audited": iso(args.now), "Tree": f"tree {tree}"}, "note": note}
        active.write(dict(active.leaf, audit=audit))
        record(args, active.id, "audit", me, verdict=verdict, tree=tree)
    print(f"packet: {active.id} audit {verdict} on tree {tree[:12]}")
    print(f"next: the Orchestrator ({active.head['Orchestrator']}) runs `packet.py ship`" if verdict == "PASS" else
          f"next: the Writer ({active.head['Writer']}) reworks and runs `packet.py close` again")
    return 0


def station(leaf: dict, tree: str) -> tuple[str, str]:
    """The next station and the key whose turn it is."""
    head, results, audit = leaf["head"], leaf["results"], leaf["audit"]
    if results is None:
        return "work: the Writer edits in scope, then runs `packet.py close`", head["Writer"]
    if results["head"]["Tree"] != f"tree {tree}":
        return "work: the worktree changed after close; the Writer runs `packet.py close` again", head["Writer"]
    if audit is None:
        return "audit: the Auditor reads `packet.py diff`, then runs `packet.py audit --verdict pass|fail --note FILE`", head["Auditor"]
    if audit["head"]["Verdict"] != "PASS":
        return "rework: the audit is FAIL; the Writer reworks and runs `packet.py close` again", head["Writer"]
    return "ship: the Orchestrator runs `packet.py ship` until it prints LANDED", head["Orchestrator"]


def cmd_status(args):
    room = args.room
    branch, dirty = git(room, "rev-parse", "--abbrev-ref", "HEAD"), dirty_paths(room)
    local = git(room, "rev-parse", "HEAD")
    remote = git_try(room, "rev-parse", "--verify", "--quiet", "refs/remotes/origin/main").stdout.strip()
    print(f"room: {branch} at {local[:12]}, {'clean' if not dirty else f'{len(dirty)} uncommitted path(s)'}, "
          f"{'level' if local == remote else 'NOT level'} with origin/main as last fetched")
    if branch != "main" or dirty:
        print("room: STOP: the room's own checkout must be clean main before any station runs")
    print(f"tools: git found, gh {'found' if shutil.which('gh') else 'MISSING (the ship station needs it)'}")
    try:
        me = caller(args)
        print(f"you: {me}")
    except Refused as exc:
        me = None
        print(f"you: unverified ({exc})")
    if not (room / WORKTREE).is_dir():
        print(f"packet: none active; the next is DP-SES-{max(leaf_numbers(room, 'main'), default=0) + 1:04d}")
        print("station: " + (f"open: a draft waits at {DRAFT.as_posix()}; the Manager runs `packet.py open`"
                             if (room / DRAFT).is_file() else "draft: the Manager runs `packet.py draft`"))
        return 0
    active = Active(args, lenient=True)
    if active.leaf is None:
        print(f"packet: {active.id} on {active.branch}")
        print(f"station: STOP: {active.damage}; the packet is damaged: its Manager runs `packet.py abandon` "
              "(the work is kept as a patch) and opens it again")
        return 0
    head = active.head
    tree, changes = active.tree()
    outside = outside_scope(changes, active.leaf["scope"])
    print(f"packet: {active.id}: {active.leaf['title']}")
    print(f"branch: {active.branch}, base {active.base[:12]}, worktree {WORKTREE.as_posix()}/")
    print("seats: " + ", ".join(f"{seat} {head[seat]}" for seat in SEATS))
    print(f"work: {len(changes)} path(s) changed, {len(outside)} outside scope, tree {tree[:12]}")
    for path in outside[:10]:
        print(f"work: outside scope: {path}")
    text, whose = station(active.leaf, tree)
    print(f"station: {text} ({whose}{', which is you' if whose == me else ''})")
    return 0


def cmd_diff(args):
    """The exact change the audit binds: everything since the base, new files included, without the leaf."""
    active = Active(args)
    form = {"stat": ["--stat"], "names": ["--name-status"]}.get(args.form, [])
    with private_index() as env:
        git(active.wt, "read-tree", "HEAD", env=env)
        git(active.wt, "add", "-A", "--", ".", env=env)
        git(active.wt, "update-index", "--force-remove", "--", active.leaf_rel, env=env)
        tree = git(active.wt, "write-tree", env=env)
        shown = git(active.wt, "-c", "core.quotePath=false", "diff", "--cached", "--no-color", *form, active.base, env=env, strip=False)
    print(f"# {active.id}: the change since base {active.base[:12]}, without the leaf; tree {tree}")
    print(shown, end="" if shown.endswith("\n") or not shown else "\n")
    return 0


def cmd_sync(args):
    me = caller(args)
    with room_lock(args.room):
        head = sync_room(args.room)
        record(args, "-", "sync", me, main=head)
    print(f"packet: the room's main is {head[:12]}, clean, level with origin/main")
    return 0


def require_shipper(args, orchestrator: str, me: str, fallback: str | None, act: str) -> None:
    """Work that touches origin or `main` is the Orchestrator's; another resident does it only on a recorded reason."""
    if me == orchestrator:
        if fallback:
            raise Refused("the caller is the packet's Orchestrator; no fallback applies")
        return
    if not fallback:
        raise Refused(f"the caller is {me!r}, not the packet's Orchestrator ({orchestrator}); another resident {act} only "
                      "with --fallback and a one-line reason, which is recorded (CONSTRAINTS C16)")
    problems = public_problems(fallback, "the fallback reason") or registry_problems(args, {"the caller": me})
    if problems:
        raise Refused("; ".join(problems))


def pull_body(active: Active, shipper: str, fallback: str | None) -> str:
    leaf, head = active.leaf, active.head
    results, audit = leaf["results"], leaf["audit"]
    lines = [f"Dispatch packet {active.id}. The record is `{active.leaf_rel}`.", "", "## Objective", "", leaf["objective"], "",
             "## Results", "", f"- Paths changed: {results['head']['Paths changed']}, all inside the packet's scope",
             f"- Gates: {len(results['gates'])} of {len(results['gates'])} exit 0, run by the packet tool",
             f"- Deviations: {results['head']['Deviations']}",
             f"- Audit: {audit['head']['Verdict']} by {audit['head']['Auditor']} on {audit['head']['Tree']}",
             "- Seats: " + ", ".join(f"{seat} {head[seat]}" for seat in SEATS)]
    if fallback:
        lines.append(f"- Shipped by {shipper} in place of the Orchestrator: {fallback}")
    return "\n".join(lines) + "\n"


def authorized(wt: Path, base: str, commit: str) -> None:
    """The PoT authorization gate, run here before anything is pushed, exactly as the required check runs it."""
    constitution = Path(__file__).with_name("constitution.py")
    if not constitution.is_file():
        return
    try:
        law = subprocess.run([sys.executable, "-I", "-B", str(constitution), "--root", str(wt), "--base", base, "--head", commit],
                             capture_output=True, text=True, timeout=GIT_TIMEOUT, env=git_env())
    except subprocess.TimeoutExpired:
        raise Refused("the PoT authorization gate gave no answer; stop and report") from None
    if law.returncode:
        raise Refused("the PoT authorization gate refuses this commit: " + telling_line(law.stderr or law.stdout))


def publish(args, active: Active, me: str, fallback: str | None, slug: str, pull: dict | None) -> dict:
    """Commit, push, pull request, required check, findings, merge. Each step is skipped when already true."""
    room, wt, leaf, head = args.room, active.wt, active.leaf, active.head
    if clean_main(room) != active.base:
        raise Refused("the room's main is not the commit this packet opened on; stop and report")
    git(room, "fetch", "--quiet", "origin", "main", timeout=NET_TIMEOUT)
    if git(room, "rev-parse", "refs/remotes/origin/main") != active.base:
        raise Refused("origin/main moved since this packet opened; a packet lands on the main it started from: "
                      "its Manager abandons it (the work is kept as a patch) and opens it again on the new main")
    tree, changes = active.tree()
    if not f"tree {tree}" == leaf["audit"]["head"]["Tree"] == leaf["results"]["head"]["Tree"]:
        raise Refused("the content is not the tree the Auditor passed; the Writer closes again and the Auditor audits again")
    outside = outside_scope(changes, leaf["scope"])
    if outside:
        raise Refused(f"{len(outside)} changed path(s) are outside scope: " + ", ".join(outside[:10]))
    git(wt, "add", "-A", "--", ".")
    git(wt, "add", "-f", "--", active.leaf_rel)      # the leaf ships even where an ignore rule would hide it
    if git_try(wt, "diff", "--cached", "--quiet", "HEAD").returncode:
        message = (f"{active.id}: {leaf['title']}\n\nPacket: {active.leaf_rel}\nWriter: {head['Writer']}\n"
                   f"Auditor: {head['Auditor']} (PASS on tree {tree})\nOrchestrator: {head['Orchestrator']}\n"
                   + (f"Shipped-by: {me} (fallback)\n" if fallback else ""))
        git(wt, "commit", "--quiet", "-m", message)
        record(args, active.id, "commit", me, commit=git(wt, "rev-parse", "HEAD"), fallback=fallback)
    commit = git(wt, "rev-parse", "HEAD")
    if tree_of_commit(wt, commit, active.leaf_rel) != tree or git_try(wt, "cat-file", "-e", f"{commit}:{active.leaf_rel}").returncode \
            or dirty_paths(wt):
        raise Refused("the commit is not the audited tree with its leaf, or the worktree is not clean after it; stop and report")
    print(f"commit: {commit[:12]}", flush=True)
    authorized(wt, active.base, commit)
    on_origin = git(room, "ls-remote", "--heads", "origin", active.branch, timeout=NET_TIMEOUT).split("\t")[0]
    if on_origin != commit:
        failed = push(wt, "-u", active.branch)
        if failed:
            raise Refused(failed)
    print(f"push: origin/{active.branch}", flush=True)
    if pull is None or pull.get("state") != "open":
        with tempfile.TemporaryDirectory(prefix="packet-body-") as tmp:
            body = Path(tmp) / "body.md"
            body.write_text(pull_body(active, me, fallback), encoding="utf-8")
            pull = gh(room, "POST", f"repos/{slug}/pulls", {"base": "main", "head": active.branch,
                                                            "title": f"{active.id}: {leaf['title']}"}, body)
        record(args, active.id, "pull-request", me, number=pull["number"])
    print(f"pull request: #{pull['number']}", flush=True)
    deadline = time.monotonic() + args.wait
    while True:
        check = required_check(room, slug, commit)
        if check is not None and check.get("status") == "completed":
            break
        if time.monotonic() >= deadline:
            raise Pending(f"the required check {REQUIRED_CHECK} " + ("has not started" if check is None else "is running")
                          + f" on pull request #{pull['number']}; run `packet.py ship` again")
        time.sleep(min(20.0, max(1.0, deadline - time.monotonic())))
    if check.get("conclusion") != "success":
        raise Failed(f"the required check {REQUIRED_CHECK} ended {check.get('conclusion')} on pull request #{pull['number']}; "
                     "the packet returns to the Writer, who reworks and closes again")
    print(f"gates: {REQUIRED_CHECK} success", flush=True)
    rest = REVIEW_SETTLE - seconds_since(args, check.get("started_at"))
    if rest > 0:
        if args.fixed_now or time.monotonic() + rest > deadline:
            raise Pending(f"the pull request's head rests {REVIEW_SETTLE} seconds before it merges, so a review can land; "
                          f"{int(rest) + 1} remain; run `packet.py ship` again")
        time.sleep(rest)
    findings = unanswered_findings(room, slug, pull)
    if findings:
        raise Refused(f"{len(findings)} review finding(s) are unanswered on pull request #{pull['number']} ("
                      + ", ".join(findings[:10]) + "); each is answered there, fixed or declined with a reason, before the merge")
    print("findings: none unanswered", flush=True)
    if args.hold:
        raise Pending(f"held before the merge, as asked; pull request #{pull['number']} is ready; run `packet.py ship` to land it")
    answer = gh(room, "PUT", f"repos/{slug}/pulls/{pull['number']}/merge", {"merge_method": "rebase", "sha": commit}) or {}
    if not answer.get("merged"):
        raise Refused("GitHub did not merge the pull request; stop and report")
    record(args, active.id, "merge", me, number=pull["number"], merged=answer.get("sha"))
    print(f"merge: #{pull['number']} by rebase", flush=True)
    return pull


def keep_work(room: Path, active: Active) -> bool:
    """Before a worktree is thrown away, its work since the base is kept as one private patch, without the leaf."""
    with private_index() as env:
        git(active.wt, "read-tree", "HEAD", env=env)
        git(active.wt, "add", "-A", "--", ".", env=env)
        git(active.wt, "update-index", "--force-remove", "--", active.leaf_rel, env=env)
        patch = subprocess.run(["git", "-C", str(active.wt), "diff", "--cached", "--binary", active.base or "HEAD"],
                               capture_output=True, timeout=GIT_TIMEOUT, env=env)
    if patch.returncode:
        raise Refused("the work could not be read as a patch, so nothing is thrown away; stop and report")
    if patch.stdout:
        write_private(room, ABANDONED, patch.stdout)
    return bool(patch.stdout)


def remove_packet(room: Path, active: Active, on_origin: bool) -> None:
    """Remove the packet branch on origin, then the worktree and the branch here. Origin first: if the branch cannot
    be removed there, nothing here is thrown away and the same command is simply run again."""
    if on_origin:
        failed = push(room, "--delete", active.branch)       # the host may have removed it already; what counts is below
        if git(room, "ls-remote", "--heads", "origin", active.branch, timeout=NET_TIMEOUT):
            raise Refused(f"origin still holds {active.branch} ({failed or 'the push reported no error'}); "
                          "run the same command again, or stop and report")
    git(room, "worktree", "remove", "--force", str(active.wt))
    git_try(room, "worktree", "prune")
    git_try(room, "branch", "-D", active.branch)
    git_try(room, "branch", "-dr", f"origin/{active.branch}")


def cmd_ship(args):
    me = caller(args)
    fallback = one_line(args.fallback, "fallback reason") if args.fallback else None
    with room_lock(args.room):
        active = Active(args)
        room, wt, leaf = args.room, active.wt, active.leaf
        require_shipper(args, active.head["Orchestrator"], me, fallback, "ships")
        active.require_contract()
        if leaf["results"] is None or leaf["audit"] is None or leaf["audit"]["head"]["Verdict"] != "PASS":
            raise Refused("the packet has no PASS from its Auditor; nothing ships")
        slug = repo_slug(room)
        pull = find_pull(room, slug, active.branch)
        if not (pull and pull.get("merged_at")):
            pull = publish(args, active, me, fallback, slug, pull)
        if dirty_paths(wt):
            raise Refused("the worktree holds uncommitted paths after the merge; stop and report")
        landed, want = sync_room(room), git(wt, "rev-parse", "HEAD^{tree}")
        if git(room, "rev-parse", "main^{tree}") != want:
            raise Refused("main is level with origin but its tree is not this packet's tree; stop and report")
        print(f"sync: main {landed[:12]} is origin/main; tree {want[:12]}", flush=True)
        remove_packet(room, active, on_origin=True)
        record(args, active.id, "landed", me, main=landed, tree=want, number=pull["number"], fallback=fallback)
        with contextlib.suppress(Refused):
            gh(room, "POST", f"repos/{slug}/issues/{pull['number']}/comments",
               {"body": f"Landed {active.id}: main is commit {landed}, level with origin; tree {want}. "
                        f"The packet branch and worktree are removed. Shipped by {me}."})
    print(f"LANDED: {active.id}; the room is clean main, level with origin; the next packet may open")
    return 0


def cmd_abandon(args):
    me = caller(args)
    reason = one_line(args.reason, "reason")
    fallback = one_line(args.fallback, "fallback reason") if args.fallback else None
    with room_lock(args.room):
        active = Active(args, lenient=True)
        room, seats = args.room, active.head
        if seats is None:
            raise Refused(f"the leaf is damaged ({active.damage}) and the ledger holds no open line for {active.id}, so the "
                          "tool cannot tell whose packet it is; stop and report")
        listed = git_try(room, "ls-remote", "--heads", "origin", active.branch, timeout=NET_TIMEOUT)
        if listed.returncode:
            raise Refused("origin did not answer, so the tool cannot tell whether the branch is there; run it again")
        on_origin = bool(listed.stdout.strip())
        if on_origin:
            require_shipper(args, seats["Orchestrator"], me, fallback, "abandons a packet whose branch is on origin")
            slug = repo_slug(room)
            pull = find_pull(room, slug, active.branch)
            if pull and pull.get("merged_at"):
                raise Refused("the pull request is merged; run `packet.py ship` to finish, not abandon")
        elif me != seats["Manager"]:
            raise Refused(f"the caller is {me!r}; only the packet's Manager ({seats['Manager']}) abandons it")
        kept = keep_work(room, active)
        if on_origin and pull and pull.get("state") == "open":
            gh(room, "PATCH", f"repos/{slug}/pulls/{pull['number']}", {"state": "closed"})
        remove_packet(room, active, on_origin)
        record(args, active.id, "abandon", me, reason=reason, fallback=fallback, kept=kept)
    print(f"packet: {active.id} is abandoned; its number is free again; the room holds no active packet")
    if kept:
        print(f"work: kept as a patch at {ABANDONED.as_posix()} (latest-wins); `git apply` it in the next packet's worktree")
    return 0


# --------------------------------------------------------------------------
# The gate: the same law from Git objects alone. It writes no ref and no checkout file.
# --------------------------------------------------------------------------
def gate_failures(root: Path, base: str, head: str, branch: str) -> tuple[list[str], list[str]]:
    """Why a pull request is not one valid packet, and what a reader should notice. No failure means it is one."""
    m = BRANCH_RE.match(branch or "")
    if m is None:
        return [f"the branch {branch!r} is not agent/dp-ses-NNNN-YYYY-MM-DD; a change reaches main only as a packet"], []
    number = int(m.group(1))
    packet, leaf_rel = f"DP-SES-{number:04d}", f"{LEAVES}/DP-SES-{number:04d}.md"
    merge_base = git(root, "merge-base", base, head)
    changes = name_status(root, merge_base, head)
    notices = [f"this pull request changes the gate that judges it: {path}" for _, path in changes if path in LAW]
    failures = []
    if merge_base != base:
        failures.append("main moved since this packet opened; a packet lands on the main it started from")
    leaves = [(status, path) for status, path in changes
              if posixpath.dirname(path) == LEAVES and LEAF_NAME_RE.match(posixpath.basename(path))]
    if leaves != [("A", leaf_rel)]:
        return failures + [f"the pull request must add exactly one leaf, {leaf_rel}, and change no other; it has "
                           + (", ".join(f"{status} {path}" for status, path in leaves) or "none")], notices
    expected = max(leaf_numbers(root, base), default=0) + 1
    if number != expected:
        failures.append(f"{packet} is not the next number; main holds up to {expected - 1:04d}, so the next packet is {expected:04d}")
    text = git(root, "show", f"{head}:{leaf_rel}", strip=False)
    try:
        leaf = parse_leaf(text)
    except Refused as exc:
        return failures + [f"{leaf_rel}: {exc}"], notices
    failures += [f"{leaf_rel}: {problem}" for problem in leaf_problems(leaf) + public_problems(text)]
    if leaf["head"]["Packet"] != packet or leaf["head"]["Branch"] != branch:
        failures.append(f"{leaf_rel} names another packet or branch than this pull request")
    if leaf["head"]["Base"] != f"commit {merge_base}":
        failures.append("the leaf's Base is not the commit this branch was cut from")
    outside = outside_scope([c for c in changes if c[1] != leaf_rel], leaf["scope"])
    if outside:
        failures.append(f"{len(outside)} changed path(s) are outside the packet's scope: " + ", ".join(outside[:10]))
    results, audit = leaf["results"], leaf["audit"]
    if results is None or audit is None:
        failures.append("the leaf holds no Results or no Audit; a packet is closed and audited before it ships")
    else:
        tree = f"tree {tree_of_commit(root, head, leaf_rel)}"
        if audit["head"]["Verdict"] != "PASS":
            failures.append("the audit verdict is not PASS")
        if results["head"]["Tree"] != tree or audit["head"]["Tree"] != tree:
            failures.append("the tree the Auditor passed is not the tree of this pull request without its leaf; "
                            "content changed after the audit")
    return failures, notices


def chain_failures(root: Path, head: str) -> list[str]:
    """The leaves on a commit are numbered 0001 upward without a gap, and each names its own number."""
    numbers = leaf_numbers(root, head)
    failures = [] if numbers == list(range(1, len(numbers) + 1)) else \
        ["the packet leaves are not numbered 0001 upward without a gap: " + ", ".join(f"{n:04d}" for n in numbers)]
    for number in numbers:
        rel = f"{LEAVES}/DP-SES-{number:04d}.md"
        if not git_try(root, "show", f"{head}:{rel}").stdout.startswith(f"# DP-SES-{number:04d}: "):
            failures.append(f"{rel} does not open with its own packet id")
    return failures


def cmd_gate(args):
    root = args.root.resolve()
    head = git(root, "rev-parse", "--verify", "--quiet", f"{args.head}^{{commit}}")
    notices: list[str] = []
    if args.chain:
        failures, label = chain_failures(root, head), f"leaf chain at {head[:12]}"
    else:
        base = git(root, "rev-parse", "--verify", "--quiet", f"{args.base}^{{commit}}")
        if git_try(root, "cat-file", "-e", f"{base}:{TOOL}").returncode:
            print("packet gate: bootstrap: the base holds no packet tool, so the gate does not apply to this pull request")
            return 0
        failures, notices = gate_failures(root, base, head, args.branch)
        label = f"{args.branch} at {head[:12]}"
    for notice in notices:
        print(f"NOTICE {notice}")
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"packet gate: {label}: " + ("PASS" if not failures else f"{len(failures)} failure(s)"))
    return 1 if failures else 0


# --------------------------------------------------------------------------
# Command line.
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="packet.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--room", type=Path, default=SESSIONS, help="the room whose main, worktree and ledger this run uses")
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--now", default=None, help="ISO time to use instead of the clock (tests)")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("status", help="the room, the active packet, and whose station is next")
    p.set_defaults(run=cmd_status)
    p = sub.add_parser("diff", help="the exact change the audit binds: everything since the base, without the leaf")
    p.add_argument("form", nargs="?", choices=("full", "stat", "names"), default="full", help="the whole diff, a summary, or the paths")
    p.set_defaults(run=cmd_diff)
    p = sub.add_parser("draft", help=f"write the fill-in form to {DRAFT.as_posix()} (latest-wins)")
    for flag in ("title", "writer", "auditor", "orchestrator", "authority"):
        p.add_argument(f"--{flag}")
    p.add_argument("--objective", help="a file holding the objective, or - for standard input")
    p.add_argument("--scope", action="append", help="one scope entry; repeat for more")
    p.add_argument("--gate", action="append", help="one gate word; repeat for more; the default is full")
    p.set_defaults(run=cmd_draft)
    p = sub.add_parser("open", help="the Manager: make the draft the one active packet, from clean main")
    p.set_defaults(run=cmd_open)
    p = sub.add_parser("amend", help="the Manager: add paths to the active packet's scope")
    p.add_argument("--add", action="append", required=True, help="one path to add; repeat for more")
    p.add_argument("--reason", required=True)
    p.set_defaults(run=cmd_amend)
    p = sub.add_parser("close", help="the Writer: check scope, run the gates, write the results")
    p.add_argument("--deviations", type=int, required=True, help="protocol deviations, as a count")
    p.add_argument("--narrative", required=True, help=f"a file of at most {NARRATIVE_LIMIT} characters, or - for standard input")
    p.set_defaults(run=cmd_close)
    p = sub.add_parser("audit", help="the Auditor: record PASS or FAIL, bound to the exact tree")
    p.add_argument("--verdict", required=True, choices=("pass", "fail", "PASS", "FAIL"))
    p.add_argument("--note", required=True, help=f"a file of at most {NOTE_LIMIT} characters, or - for standard input")
    p.set_defaults(run=cmd_audit)
    p = sub.add_parser("ship", help="the Orchestrator: commit, push, pull request, gates, merge, sync, cleanup; "
                                    "run it again until it prints LANDED")
    p.add_argument("--fallback", help="another resident ships in the Orchestrator's place; this one-line reason is recorded")
    p.add_argument("--hold", action="store_true", help="do everything up to the merge, then stop")
    p.add_argument("--wait", type=int, default=0, help="seconds to wait for the required check before returning; the default is 0")
    p.set_defaults(run=cmd_ship)
    p = sub.add_parser("abandon", help="end the active packet without shipping it; the work is kept as a patch")
    p.add_argument("--reason", required=True)
    p.add_argument("--fallback", help="another resident acts in the Orchestrator's place; this one-line reason is recorded")
    p.set_defaults(run=cmd_abandon)
    p = sub.add_parser("sync", help="bring the room's clean main level with origin/main, by fast-forward only")
    p.set_defaults(run=cmd_sync)
    p = sub.add_parser("gate", help="the required check: judge one pull request, or the leaf chain, from Git objects")
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--base")
    p.add_argument("--branch")
    p.add_argument("--chain", action="store_true", help="check only that the leaves at --head are numbered without a gap")
    p.set_defaults(run=cmd_gate)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.fixed_now = args.now is not None
        try:
            args.now = clock() if args.now is None else \
                dt.datetime.fromisoformat(args.now.replace("Z", "+00:00")).astimezone(dt.timezone.utc).replace(microsecond=0)
        except ValueError:
            raise Refused(f"--now {args.now!r} is not an ISO time") from None
        if args.command == "gate":
            if not args.chain and not (args.base and args.branch):
                raise Refused("gate needs --base and --branch, or --chain")
        else:
            args.room = args.room.resolve()
            problem = room_problem(args.room)
            if problem:
                raise Refused(problem)
            if getattr(args, "deviations", 0) < 0 or getattr(args, "wait", 0) < 0:
                raise Refused("--deviations and --wait are counts; neither can be negative")
        return args.run(args)
    except Pending as exc:
        print(f"PENDING: {exc}")
        return 3
    except Failed as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"refused: {exc.__class__.__name__}: {exc.strerror or exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
