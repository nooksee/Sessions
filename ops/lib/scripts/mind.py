#!/usr/bin/env python3
"""mind: the room's mind, pointer first. Standard library only.

The root `MIND.md` is an index and nothing else: one line per live leaf, each
naming the leaf's id, its agent and its title. A leaf is one idea a resident
holds, an abstraction that stays true, kept as one immutable file under
`archives/mind/`, named by its id, `MIND-<date>-<NNN>.md`. Every write is one
line of telemetry in `logs/mind/ledger.jsonl`: the id, the agent, the action,
the time, and the leaf's SHA-256 and size.

A mind holds concepts, never the present. A leaf that names a date, a time, a
count, a path, an address, an identifier, a command or the state of the moment
is refused at the door, because that is what goes stale, and a stale fact read
as memory misleads. Facts about the present live in the board, the ledger and
the handoffs, where they are dated and replaced.

There is no per-entry approval. A registered resident writes, supersedes and
retires its own leaves; the limits, the screen and the ledger keep the mind
bounded and auditable. All of it stays out of Git (PoT 5.1.3).

Spec: docs/ops/specs/scripts/mind.md. This tool never reads a session body.
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
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[3]
REGISTRY = SESSIONS / "ops" / "etc" / "resident-identities.json"
INDEX = "MIND.md"
LEAVES = Path("archives") / "mind"
LEDGER = Path("logs") / "mind" / "ledger.jsonl"
LOCK = Path("logs") / "mind.lock"
LEGACY_LOCK = Path("storage") / "mind.lock"

TITLE_LIMIT = 100        # characters in a title
BODY_LIMIT = 2000        # characters in a body
INDEX_LIMIT = 200        # live leaves in the index; the index is refused, never trimmed, when full
GIT_TIMEOUT = 30
HEAD_KEYS = ("id", "agent", "written", "title", "supersedes")

KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ID_RE = re.compile(r"^MIND-(?P<date>\d{4}-\d{2}-\d{2})-(?P<seq>\d{3})$")
LEAF_NAME_RE = re.compile(r"^(MIND-\d{4}-\d{2}-\d{2}-\d{3})\.md$")
WRITTEN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
LINE_RE = re.compile(r"^- \[(MIND-\d{4}-\d{2}-\d{2}-\d{3})\]\(archives/mind/\1\.md\) ([a-z0-9][a-z0-9-]*) — (\S.*)$")
LEGACY_LINE_RE = re.compile(r"^resident=")
LEGACY_LEAF_RE = re.compile(r"^MIND-.+\.md$")

INDEX_HEAD = (
    "# Mind\n\n"
    "Pointers only. Each line is one leaf: an idea a resident holds, never a fact about the present. "
    "Only the mind tool writes this file. Read a leaf with `mind.py read <id>`.\n\n")

# --------------------------------------------------------------------------
# The screen. Each pattern names a kind of content that goes stale or does not
# belong in a mind. A refusal names the kind, never the matched text.
# --------------------------------------------------------------------------
IDENTITY_RES = (
    re.compile(r"[0-9a-f]{8}\s?-\s?[0-9a-f]{4}\s?-\s?[0-9a-f]{4}\s?-\s?[0-9a-f]{4}\s?-\s?[0-9a-f]{12}", re.I),
    re.compile(r"\b[0-9a-f]{32,}\b", re.I),
    re.compile(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*[0-9])[0-9a-f]{8,}\b", re.I),
)
MEDICAL_RE = re.compile(
    r"biopsy|medication|surgery|hospital|prescription|oncolog|chemotherap|radiolog|pathology report|cancer"
    r"|tumou?r|\bMRI\b|CT scan|diagnosed with|medical diagnosis|therapy session|(doctor|dr\.?)'?s? appointment"
    r"|appointment with (a |the )?(doctor|dr\.?)|Hurley", re.I)
SECRET_RE = re.compile(
    r"password\s*[=:]|password\s+is\b|passwd|api[_-]?key|secret\s*[=:]|token\s*[=:]|BEGIN [A-Z ]*PRIVATE KEY"
    r"|sk-[A-Za-z0-9]{16,}|sk-ant-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_|xox[abpr]-"
    r"|AKIA[0-9A-Z]{16}|eyJ[A-Za-z0-9_-]{10,}\.|Bearer\s+[A-Za-z0-9._-]{20,}", re.I)
MONTHS = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
CONCEPT_SCREEN = (
    ("a date", re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b(19|20)\d{2}\b"
                          r"|\b" + MONTHS + r"\s+\d{1,2}\b|\b\d{1,2}\s+" + MONTHS + r"(?![a-z])", re.I)),
    ("a time", re.compile(r"\b\d{1,2}:\d{2}\b")),
    ("a word that dates the text", re.compile(
        r"\b(today|tonight|yesterday|tomorrow|currently|nowadays|right now|at the moment|as of|for now"
        r"|this (morning|afternoon|evening|week|month|year|quarter|session|sprint)"
        r"|(last|next) (night|week|month|year|quarter|session|sprint))\b", re.I)),
    ("a count or size", re.compile(r"(?<![\d.\-])\d{2,}(?![\d.])|\b\d+(\.\d+)?\s?(percent|%)|\bPID\s?\d+|\bport\s\d+\b", re.I)),
    ("a path or file name", re.compile(
        r"(^|[\s(\[\"'`])(~|\.{1,2})?/[\w.-]|\b[A-Za-z]:\\|\b[\w.-]+/[\w.-]+/|\b[\w-]+\.(py|sh|md|json|jsonl|toml"
        r"|ya?ml|txt|tar|lock|tpl|cfg|ini|js|ts|log|csv)\b", re.I)),
    ("an address", re.compile(r"\b[a-z][a-z0-9+.-]*://|\bwww\.|\b[\w.+-]+@[\w-]+\.[\w.]+", re.I)),
    ("a pull request, issue or version number", re.compile(r"#\d+\b|\bv\d+(\.\d+)+\b", re.I)),
    ("code or a command line", re.compile(r"```|~~~|^\s*(\$|>>>|#!)|(^|\s)--?[a-z][\w-]*", re.I | re.M)),
)


class Refused(Exception):
    """Fail closed: nothing was written, or nothing is served."""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def policy_digest() -> str:
    """The first 16 hex digits of a digest of every limit and screen; printed by check."""
    body = {"limits": [TITLE_LIMIT, BODY_LIMIT, INDEX_LIMIT], "head": list(HEAD_KEYS),
            "screens": [rx.pattern for rx in (*IDENTITY_RES, MEDICAL_RE, SECRET_RE)]
            + [f"{label}={rx.pattern}" for label, rx in CONCEPT_SCREEN]}
    return sha256(json.dumps(body, sort_keys=True).encode("utf-8"))[:16]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return re.sub("[‐-―−﹘﹣－]", "-", text)


def screen(value: str, label: str, multiline: bool = False) -> list[str]:
    """Every reason value cannot enter a mind; empty when it can."""
    allowed = {"\n"} if multiline else set()
    problems = []
    hidden = sorted({f"U+{ord(c):04X}" for c in value
                     if c not in allowed and unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp")})
    if hidden:
        problems.append(f"{label}: control or invisible characters {', '.join(hidden)}")
    norm = normalize(value)
    if any(rx.search(norm) for rx in IDENTITY_RES):
        problems.append(f"{label}: an identifier; identity lives in the registry")
    if MEDICAL_RE.search(norm):
        problems.append(f"{label}: medical content")
    if SECRET_RE.search(norm):
        problems.append(f"{label}: possible secret")
    kinds = [kind for kind, rx in CONCEPT_SCREEN if rx.search(norm)]
    if kinds:
        problems.append(f"{label}: {', '.join(kinds)}; a mind holds the idea, not the fact of the moment")
    return problems


def limits(title: str, body: str) -> list[str]:
    problems = []
    if not title.strip() or title != title.strip() or "\n" in title:
        problems.append("title: one line of text with no outer spaces")
    if len(title) > TITLE_LIMIT:
        problems.append(f"title: {len(title)} characters; the limit is {TITLE_LIMIT}")
    if not body.strip():
        problems.append("body: empty")
    if len(body) > BODY_LIMIT:
        problems.append(f"body: {len(body)} characters; the limit is {BODY_LIMIT}")
    return problems


# --------------------------------------------------------------------------
# Leaves and the index: render and parse. Each is valid only in canonical
# form: parsing it and rendering the result gives back the same bytes.
# --------------------------------------------------------------------------
def clean_body(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(lines).strip("\n")


def render_leaf(head: dict, body: str) -> str:
    return "---\n" + "".join(f"{k}: {head[k]}\n" for k in HEAD_KEYS) + "---\n\n" + body + "\n"


def parse_leaf(text: str) -> tuple[dict, str]:
    lines = text.split("\n")
    if len(lines) < len(HEAD_KEYS) + 4 or lines[0] != "---" or lines[len(HEAD_KEYS) + 1] != "---":
        raise Refused("a leaf must open with its front matter between two --- lines")
    head = {}
    for key, line in zip(HEAD_KEYS, lines[1:len(HEAD_KEYS) + 1]):
        if not line.startswith(key + ": "):
            raise Refused(f"a leaf's front matter must name {', '.join(HEAD_KEYS)}, in that order")
        head[key] = line[len(key) + 2:]
    body = "\n".join(lines[len(HEAD_KEYS) + 3:]).removesuffix("\n")
    if render_leaf(head, body) != text:
        raise Refused("a leaf is not in canonical form")
    return head, body


def head_problems(head: dict) -> list[str]:
    problems = []
    if not ID_RE.match(head["id"]) or not valid_date(ID_RE.match(head["id"]).group("date")):
        problems.append("id: not MIND-<date>-<NNN>")
    if not KEY_RE.match(head["agent"]):
        problems.append("agent: not a registry key")
    if not WRITTEN_RE.match(head["written"]):
        problems.append("written: not a UTC time")
    if head["supersedes"] != "none" and not ID_RE.match(head["supersedes"]):
        problems.append("supersedes: neither none nor a leaf id")
    return problems


def valid_date(value: str) -> bool:
    try:
        return bool(dt.date.fromisoformat(value))
    except ValueError:
        return False


def index_text(lines: list[tuple[str, str, str]]) -> str:
    return INDEX_HEAD + "".join(f"- [{i}](archives/mind/{i}.md) {agent} — {title}\n" for i, agent, title in lines)


def read_index(room: Path) -> list[tuple[str, str, str]] | None:
    """The index as (id, agent, title) lines, or None when the room has none yet."""
    path = room / INDEX
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file():
        raise Refused(f"{INDEX} is not a regular file")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Refused(f"{INDEX} is unreadable ({exc.__class__.__name__})") from None
    return parse_index(text)


def parse_index(text: str) -> list[tuple[str, str, str]]:
    """The (id, agent, title) lines of an index text; refused unless canonical."""
    if any(LEGACY_LINE_RE.match(line) for line in text.splitlines()) or not text.startswith(INDEX_HEAD):
        raise Refused(f"{INDEX} is not a pointer index; if it is the retired chain format, move it and every "
                      f"archives/MIND-*.md at the archives root to custody, then run again")
    lines = []
    for raw in text[len(INDEX_HEAD):].splitlines():
        m = LINE_RE.match(raw)
        if m is None:
            raise Refused(f"{INDEX} holds a line that is not a pointer")
        lines.append(m.groups())
    if index_text(lines) != text:
        raise Refused(f"{INDEX} is not in canonical form")
    ids = [i for i, _, _ in lines]
    if len(set(ids)) != len(ids):
        raise Refused(f"{INDEX} names a leaf twice")
    return lines


def legacy_leaves(room: Path) -> list[str]:
    archives = room / "archives"
    if not archives.is_dir():
        return []
    return sorted(p.name for p in archives.iterdir() if LEGACY_LEAF_RE.match(p.name))


def read_ledger(room: Path) -> list[dict]:
    path = room / LEDGER
    if not path.exists() and not path.is_symlink():
        return []
    if path.is_symlink() or not path.is_file():
        raise Refused(f"{LEDGER.as_posix()} is not a regular file")
    records = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Refused(f"{LEDGER.as_posix()} is unreadable ({exc.__class__.__name__})") from None
    for number, line in enumerate(text.splitlines(), 1):
        try:
            record = json.loads(line)
        except ValueError:
            raise Refused(f"{LEDGER.as_posix()} line {number} is not JSON") from None
        if (not isinstance(record, dict) or record.get("action") not in ("add", "retire")
                or not isinstance(record.get("id"), str) or not isinstance(record.get("sha256"), str)):
            raise Refused(f"{LEDGER.as_posix()} line {number} is not a mind record")
        records.append(record)
    return records


def read_registry(path: Path) -> dict[str, list[dict]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise Refused(f"the registry is unreadable ({exc.__class__.__name__})") from None
    identities = data.get("identities") if isinstance(data, dict) else None
    if not isinstance(identities, list):
        raise Refused("the registry has no identities list")
    found: dict[str, list[dict]] = {}
    for item in identities:
        if isinstance(item, dict) and isinstance(item.get("key"), str):
            found.setdefault(item["key"], []).append(item)
    return found


def registered(reg: dict, key: str, room: Path | None = None) -> tuple[dict | None, list[str]]:
    """The one registry entry for key; with room, it must live in that room. Never prints a session id."""
    found = reg.get(key, [])
    if len(found) != 1:
        return None, [f"{key!r} is registered {len(found)} times; it must be exactly once"]
    entry = found[0]
    if room is not None and (not isinstance(entry.get("room"), str) or Path(entry["room"]).resolve() != room):
        return None, [f"{key!r} is registered to another room, not this one"]
    return entry, []


# --------------------------------------------------------------------------
# Writing: one lock, exclusive leaves, an atomic index, an appended ledger.
# Every directory the tool creates is created at mode 0700, one at a time.
# --------------------------------------------------------------------------
def private_parents(room: Path, path: Path) -> None:
    current = room
    for part in path.parent.relative_to(room).parts:
        current = current / part
        if not current.exists() and not current.is_symlink():
            current.mkdir(mode=0o700)


@contextlib.contextmanager
def room_lock(room: Path):
    spec = importlib.util.spec_from_file_location("mind_statepaths", Path(__file__).resolve().parents[1] / "statepaths.py")
    statepaths = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(statepaths)
    try:
        statepaths.require_absent_legacy(room, LEGACY_LOCK)
    except statepaths.StatePathError as exc:
        raise Refused(f"mind lock: {exc}") from None
    path = room / LOCK
    private_parents(room, path)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        view = view[os.write(fd, view):]


def write_exclusive(room: Path, path: Path, data: bytes) -> None:
    """Create a new leaf at mode 0600; never overwrite one."""
    private_parents(room, path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        write_all(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def write_atomic(path: Path, data: bytes) -> None:
    """Replace the index by rename, at mode 0600."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix="." + path.name + ".")
    try:
        write_all(fd, data)
        os.fsync(fd)
        os.close(fd)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.close(fd)
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def append_ledger(room: Path, record: dict) -> None:
    path = room / LEDGER
    private_parents(room, path)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        write_all(fd, (json.dumps(record, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def git_env() -> dict:
    """Git's answer must not depend on the caller's Git variables or language."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(LC_ALL="C", LANGUAGE="C", GIT_DISCOVERY_ACROSS_FILESYSTEM="1")
    return env


def run_git(room: Path, *args: str) -> subprocess.CompletedProcess:
    """One Git call. No answer at all is a refusal that names its cause."""
    try:
        return subprocess.run(["git", "-C", str(room), *args], capture_output=True, text=True,
                              timeout=GIT_TIMEOUT, env=git_env())
    except FileNotFoundError:
        raise Refused("Git is not installed or not on PATH, so whether this room is in Git cannot be established") from None
    except subprocess.TimeoutExpired:
        raise Refused(f"git {args[0]} gave no answer within {GIT_TIMEOUT:g} seconds") from None
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refused(f"git {args[0]} could not run ({exc.__class__.__name__})") from None


def first_line(text: str) -> str:
    return (text.strip().splitlines() or ["no message"])[0]


def git_exposed(room: Path, paths: list[Path]) -> list[str]:
    """Why a write must stop for Git's sake; empty only on Git's own positive answers.

    Outside Git is accepted only when Git says "not a git repository" and no `.git` exists in the room
    or above it (a broken repository makes Git say the same). Inside a work tree, each path must be
    ignored: check-ignore exit 0. Every other answer, and no answer, is a refusal naming its cause."""
    try:
        inside = run_git(room, "rev-parse", "--is-inside-work-tree")
        if inside.returncode != 0:
            if "not a git repository" not in inside.stderr:
                return [f"git rev-parse failed (exit {inside.returncode}: {first_line(inside.stderr)})"]
            marks = [p / ".git" for p in (room, *room.parents) if (p / ".git").exists() or (p / ".git").is_symlink()]
            if marks:
                return [f"Git says no repository, but {marks[0]} exists: a broken repository is not proof of being outside Git"]
            return []
        if inside.stdout.strip() != "true":
            return [f"git rev-parse answered {inside.stdout.strip()!r}, not 'true': the room is not a plain work tree"]
        markers = [directory / ".git" for directory in (room, *room.parents)
                   if (directory / ".git").exists() or (directory / ".git").is_symlink()]
        if not markers:
            return ["Git reports a work tree, but no .git marker exists in the room or its ancestors"]
        top = run_git(room, "rev-parse", "--show-toplevel")
        if top.returncode != 0:
            return [f"git rev-parse --show-toplevel failed (exit {top.returncode}: {first_line(top.stderr)})"]
        top_level = top.stdout.strip()
        if not top_level or os.path.realpath(top_level) != os.path.realpath(markers[0].parent):
            return [f"Git resolved this room to {top_level or 'an empty path'}, but the nearest .git marker "
                    f"is at {markers[0].parent}; a broken repository is not proof of being outside Git"]
        problems = []
        for path in paths:
            rel = path.relative_to(room).as_posix()
            result = run_git(room, "check-ignore", "-q", str(path))
            if result.returncode == 1:
                problems.append(f"{rel} is not ignored by Git; minds live out of Git, so an ignore rule must land first")
            elif result.returncode != 0:
                problems.append(f"git check-ignore failed for {rel} (exit {result.returncode}: {first_line(result.stderr)})")
        return problems
    except Refused as exc:
        return [str(exc)]


def private_paths(room: Path) -> list[Path]:
    return [room / INDEX, room / LEAVES / "MIND-0000-00-00-000.md", room / LEDGER]


# --------------------------------------------------------------------------
# Verification.
# --------------------------------------------------------------------------
def load_leaf(room: Path, leaf_id: str) -> tuple[dict, str, bytes]:
    path = room / LEAVES / f"{leaf_id}.md"
    if path.is_symlink() or not path.is_file():
        raise Refused(f"{leaf_id}: no leaf on disk")
    data = path.read_bytes()
    try:
        head, body = parse_leaf(data.decode("utf-8"))
    except UnicodeDecodeError:
        raise Refused(f"{leaf_id}: not UTF-8") from None
    except Refused as exc:
        raise Refused(f"{leaf_id}: {exc}") from None
    return head, body, data


def ledger_state(records: list[dict]) -> tuple[dict, set]:
    """The add record of every id, and the ids retired or superseded."""
    added, gone = {}, set()
    for r in records:
        if r["action"] == "add":
            if r["id"] in added:
                raise Refused(f"{LEDGER.as_posix()} adds {r['id']} twice")
            added[r["id"]] = r
            if isinstance(r.get("supersedes"), str) and r["supersedes"] != "none":
                gone.add(r["supersedes"])
        else:
            gone.add(r["id"])
    return added, gone


def verify(room: Path, reg: dict) -> tuple[list[tuple[str, str, str]], list[str]]:
    """Every (status, gate, detail) row of the room's mind, and the blocking failures. Reads only; runs nothing."""
    rows: list[tuple[str, str, str]] = []
    failures: list[str] = []

    def row(status, gate, detail):
        rows.append((status, gate, detail))
        if status == "FAIL":
            failures.append(f"{gate}: {detail}")

    legacy = legacy_leaves(room)
    if legacy:
        row("FAIL", "legacy", f"{len(legacy)} archives/MIND-*.md files of the retired chain format sit at the archives "
                              f"root; move them to custody")
    try:
        lines = read_index(room)
    except Refused as exc:
        row("FAIL", "index", str(exc))
        return rows, failures
    try:
        added, gone = ledger_state(read_ledger(room))
    except Refused as exc:
        row("FAIL", "ledger", str(exc))
        return rows, failures
    if lines is None:
        if added:
            row("FAIL", "index", f"no {INDEX}, but the ledger records {len(added)} leaves")
        else:
            row("PASS", "index", f"no {INDEX} yet; the room holds no mind")
        return rows, failures
    if len(lines) > INDEX_LIMIT:
        row("FAIL", "index", f"{len(lines)} pointers; the limit is {INDEX_LIMIT}")
    else:
        row("PASS", "index", f"{len(lines)} of {INDEX_LIMIT} pointers, policy {policy_digest()}")
    for leaf_id, agent, title in lines:
        try:
            head, body, data = load_leaf(room, leaf_id)
        except Refused as exc:
            row("FAIL", "leaf", str(exc))
            continue
        problems = head_problems(head)
        if head["id"] != leaf_id or head["agent"] != agent or head["title"] != title:
            problems.append("the index line does not match the leaf's front matter")
        record = added.get(leaf_id)
        if record is None:
            problems.append("the ledger records no add of this leaf")
        elif record.get("sha256") != sha256(data) or record.get("agent") != agent:
            problems.append("the leaf is not the one the ledger recorded; leaves are immutable")
        if leaf_id in gone:
            problems.append("the ledger retired or superseded this leaf, but the index still points at it")
        _, unregistered = registered(reg, agent, room)
        problems += [f"agent: {p}" for p in unregistered]
        if problems:
            row("FAIL", "leaf", f"{leaf_id}: " + "; ".join(problems))
            continue
        drift = limits(title, body) + screen(title, "title") + screen(body, "body", multiline=True)
        if drift:
            row("REPORT", "leaf", f"{leaf_id}: no longer passes the current screen ({'; '.join(drift)}); "
                                  f"supersede or retire it")
        else:
            row("PASS", "leaf", f"{leaf_id} {agent}")
    directory = room / LEAVES
    if directory.is_dir():
        live = {i for i, _, _ in lines}
        strays = sorted(p.name for p in directory.iterdir()
                        if not (LEAF_NAME_RE.match(p.name) and LEAF_NAME_RE.match(p.name).group(1) in live | gone))
        if strays:
            row("REPORT", "strays", f"{len(strays)} files under {LEAVES.as_posix()}/ are neither live nor retired")
    return rows, failures


def require_clean(room: Path, reg: dict) -> list[tuple[str, str, str]]:
    rows, failures = verify(room, reg)
    if failures:
        raise Refused("the mind is not served until its check passes: " + "; ".join(failures))
    return read_index(room) or []


# --------------------------------------------------------------------------
# Commands.
# --------------------------------------------------------------------------
def next_id(room: Path, date: str, records: list[dict]) -> str:
    used = [int(m.group("seq")) for m in (ID_RE.match(r["id"]) for r in records) if m and m.group("date") == date]
    directory = room / LEAVES
    if directory.is_dir():
        for p in directory.iterdir():
            m = LEAF_NAME_RE.match(p.name)
            if m and ID_RE.match(m.group(1)).group("date") == date:
                used.append(int(ID_RE.match(m.group(1)).group("seq")))
    seq = max(used, default=0) + 1
    if seq > 999:
        raise Refused(f"the room has written 999 leaves on {date}; no id is left for that day")
    return f"MIND-{date}-{seq:03d}"


def writable(args) -> tuple[dict, list]:
    reg = read_registry(args.registry)
    _, problems = registered(reg, args.agent, args.room)
    if problems:
        raise Refused("; ".join(problems))
    legacy = legacy_leaves(args.room)
    if legacy:
        raise Refused(f"{len(legacy)} archives/MIND-*.md files of the retired chain format sit at the archives root; "
                      f"move them to custody, then run again")
    exposed = git_exposed(args.room, private_paths(args.room))
    if exposed:
        raise Refused("; ".join(exposed))
    return reg, read_index(args.room) or []


def read_text_arg(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    try:
        return Path(source).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Refused(f"the body file is unreadable ({exc.__class__.__name__})") from None


def owned(lines: list, leaf_id: str, agent: str) -> int:
    for position, (i, owner, _) in enumerate(lines):
        if i == leaf_id:
            if owner != agent:
                raise Refused(f"{leaf_id} belongs to {owner}; a resident changes only its own leaves")
            return position
    raise Refused(f"{leaf_id} is not a live leaf in {INDEX}")


def cmd_add(args):
    title = normalize(args.title).strip()
    body = clean_body(normalize(read_text_arg(args.body)))
    problems = limits(title, body) + screen(title, "title") + screen(body, "body", multiline=True)
    if problems:
        raise Refused("; ".join(problems))
    with room_lock(args.room):
        _, lines = writable(args)
        records = read_ledger(args.room)
        position = None
        if args.supersedes:
            position = owned(lines, args.supersedes, args.agent)
        elif len(lines) >= INDEX_LIMIT:
            raise Refused(f"{INDEX} holds {INDEX_LIMIT} pointers, its limit; supersede or retire a leaf first")
        leaf_id = next_id(args.room, args.now.date().isoformat(), records)
        head = {"id": leaf_id, "agent": args.agent, "written": iso(args.now), "title": title,
                "supersedes": args.supersedes or "none"}
        data = render_leaf(head, body).encode("utf-8")
        write_exclusive(args.room, args.room / LEAVES / f"{leaf_id}.md", data)
        append_ledger(args.room, {"action": "add", "id": leaf_id, "agent": args.agent, "time": iso(args.now),
                                  "sha256": sha256(data), "bytes": len(data), "supersedes": head["supersedes"]})
        line = (leaf_id, args.agent, title)
        if position is None:
            lines = lines + [line]
        else:
            lines = lines[:position] + [line] + lines[position + 1:]
        write_atomic(args.room / INDEX, index_text(lines).encode("utf-8"))
    note = f", superseding {args.supersedes}" if args.supersedes else ""
    print(f"mind: {leaf_id} written by {args.agent}{note}; {len(lines)} of {INDEX_LIMIT} pointers")
    return 0


def cmd_retire(args):
    with room_lock(args.room):
        _, lines = writable(args)
        position = owned(lines, args.id, args.agent)
        path = args.room / LEAVES / f"{args.id}.md"
        data = path.read_bytes() if path.is_file() and not path.is_symlink() else b""
        append_ledger(args.room, {"action": "retire", "id": args.id, "agent": args.agent, "time": iso(args.now),
                                  "sha256": sha256(data), "bytes": len(data)})
        lines = lines[:position] + lines[position + 1:]
        write_atomic(args.room / INDEX, index_text(lines).encode("utf-8"))
    print(f"mind: {args.id} retired by {args.agent}; the leaf stays on disk; {len(lines)} of {INDEX_LIMIT} pointers")
    return 0


def cmd_show(args):
    lines = require_clean(args.room, read_registry(args.registry))
    if args.agent:
        lines = [line for line in lines if line[1] == args.agent]
    if not lines:
        print("the mind holds no leaves" + (f" for {args.agent}" if args.agent else ""))
        return 0
    sys.stdout.write("".join(f"- [{i}](archives/mind/{i}.md) {agent} — {title}\n" for i, agent, title in lines))
    return 0


def cmd_read(args):
    lines = require_clean(args.room, read_registry(args.registry))
    if args.id not in {i for i, _, _ in lines}:
        raise Refused(f"{args.id} is not a live leaf in {INDEX}; only live leaves are served")
    _, _, data = load_leaf(args.room, args.id)
    sys.stdout.write(data.decode("utf-8"))
    return 0


def cmd_check(args):
    rows, failures = verify(args.room, read_registry(args.registry))
    if (args.room / INDEX).exists() or (args.room / LEDGER).exists():
        exposed = git_exposed(args.room, private_paths(args.room))
        rows.insert(1, ("FAIL" if exposed else "PASS", "out-of-git",
                        "; ".join(exposed) or "the index, the leaves and the ledger are out of Git"))
        failures += [f"out-of-git: {p}" for p in exposed]
    print(f"mind check: room {args.room}")
    for status, gate, detail in rows:
        print(f"{status} {gate} : {detail}")
    print(f"blocking failures: {len(failures)}")
    return 1 if failures else 0


def parse_now(value: str | None) -> dt.datetime:
    if value is None:
        return utc_now()
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc).replace(microsecond=0)
    except ValueError:
        raise SystemExit(f"--now {value!r} is not an ISO time") from None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="mind.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--room", type=Path, default=SESSIONS, help="the room whose MIND.md, archives/mind/ and ledger hold the mind")
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--now", default=None, help="ISO time to use instead of the clock (tests)")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("add", help="write one new leaf and point the index at it")
    p.add_argument("--agent", required=True, help="the registry key of the resident whose leaf this is")
    p.add_argument("--title", required=True, help=f"one line, at most {TITLE_LIMIT} characters")
    p.add_argument("--body", required=True, help=f"a file holding the idea, at most {BODY_LIMIT} characters, or - for stdin")
    p.add_argument("--supersedes", help="the id of the agent's own live leaf this one replaces in the index")
    p.set_defaults(run=cmd_add)
    p = sub.add_parser("retire", help="take one of the agent's own leaves out of the index; the leaf stays on disk")
    p.add_argument("--agent", required=True)
    p.add_argument("id")
    p.set_defaults(run=cmd_retire)
    p = sub.add_parser("show", help="print the verified index lines, all or one agent's")
    p.add_argument("--agent")
    p.set_defaults(run=cmd_show)
    p = sub.add_parser("read", help="print one verified live leaf, byte for byte")
    p.add_argument("id")
    p.set_defaults(run=cmd_read)
    p = sub.add_parser("check", help="every gate of the room's mind")
    p.set_defaults(run=cmd_check)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    args.room = args.room.resolve()
    args.now = parse_now(args.now)
    for name in ("agent",):
        value = getattr(args, name, None)
        if value is not None and not KEY_RE.match(value):
            print(f"refused: --{name} {value!r} is not a registry key", file=sys.stderr)
            return 2
    for name in ("id", "supersedes"):
        value = getattr(args, name, None)
        if value is not None and not ID_RE.match(value):
            print(f"refused: {value!r} is not a leaf id, MIND-<date>-<NNN>", file=sys.stderr)
            return 2
    try:
        return args.run(args)
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"refused: {exc.__class__.__name__}: {exc.strerror or exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
