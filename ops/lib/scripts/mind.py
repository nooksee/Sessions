#!/usr/bin/env python3
"""mind: keep each resident's mind as a chain of immutable leaves. Standard library only.

A mind is one Markdown leaf at the root of the room's `archives/` (RoR-3), named
`MIND-<key>-<date>-<hash8>.md`, and one line in the room's root `MIND.md`
that points at it with its full SHA-256. A change is a new leaf: it names its
predecessor and that leaf's SHA-256, says what changed, and carries Kevin's
words. There is no store, no queue and no key.

Input to a mind is solicited in conversation and written only after Kevin's
yes there, so `write` requires his words and records them on the leaf and on
every entry it adds or amends. It also requires the binding `preview` printed,
so that what is written is exactly the change Kevin saw, built on the leaf he
saw it against. The tool cannot tell who typed the words, and
does not pretend to: the chain of leaves, each declared change checked against
the real difference, and the words themselves are the audit.

Spec: docs/ops/specs/scripts/mind.md. This tool never reads a session body.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[3]
REGISTRY = SESSIONS / "ops" / "etc" / "resident-identities.json"
SURFACES = "archives"                    # RoR-3: leaves sit at the archives/ root, grouped by their prefix
LEAF_PREFIX = "MIND-"
POINTER = "MIND.md"
LOCK = Path("storage") / "mind.lock"

LAYERS = ("core", "bond", "lesson", "commitment", "pointer")
TITLES = {"core": "Who I am", "bond": "My people", "lesson": "What I have learned",
          "commitment": "What I owe", "pointer": "Where things live"}
BUDGETS = {"core": 3000, "bond": 2000, "lesson": 6000, "commitment": 2000, "pointer": 1000}
CHARS_PER_TOKEN = 4
CORE_KINDS = ("identity", "voice", "value", "method")
# Every field an entry may carry after its text, in leaf order, with its label in the leaf.
FIELDS = (("kind", "kind"), ("event", "event"), ("date", "date"), ("fix", "fix"), ("closed", "closed"),
          ("applies_when", "applies when"), ("not_when", "not when"), ("owner", "owner"),
          ("source", "source"), ("yes", "yes"))
LABELS = {label: name for name, label in FIELDS}
COMMON = ("text", "event", "date", "source")
ALLOWED = {"core": COMMON + ("kind",), "bond": COMMON,
           "lesson": COMMON + ("kind", "fix", "closed", "applies_when", "not_when"),
           "commitment": COMMON + ("owner",), "pointer": COMMON}
REQUIRED = {"core": COMMON + ("kind",), "bond": COMMON, "lesson": COMMON + ("applies_when", "not_when"),
            "commitment": COMMON + ("owner",), "pointer": COMMON}
MIN_YES = 3
GIT_TIMEOUT = 30
HEAD_KEYS = ("resident", "written", "by", "predecessor", "change", "yes", "issued", "policy")

KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
NAME_RE = re.compile(r"^MIND-(?P<key>[a-z0-9][a-z0-9-]*?)-(?P<date>\d{4}-\d{2}-\d{2})-(?P<hash>[0-9a-f]{8})\.md$")
PRED_RE = re.compile(r"^(archives/MIND-\S+) sha256=([0-9a-f]{64})$")
ISSUED_RE = re.compile(r"^" + " ".join(f"{layer}=(\\d+)" for layer in LAYERS) + r"$")
YES_RE = re.compile(r'^(\d{4}-\d{2}-\d{2}), "(.+)"$')
WRITTEN_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
ENTRY_RE = re.compile(r"^- \[((" + "|".join(LAYERS) + r")-(\d{3,}))\] (\S.*)$")
FIELD_RE = re.compile(r"^  ([a-z ]+): (\S.*)$")
POINTER_LINE_RE = re.compile(r"^resident=([a-z0-9][a-z0-9-]*)\|leaf=(\S+)\|sha256=([0-9a-f]{64})$")

# Screens: identity lives in the registry, never in a mind; medical content and secrets never enter one.
# The short pattern has no exception for hash or file-name context (Claudio F6): any run of eight or
# more hex digits with a letter and a digit is refused.
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
LIVE_STATE_RE = re.compile(r"\b\d{1,3}(\.\d+)?\s?(percent|%)|\bPID\s?\d+|\bport\s\d{2,5}\b", re.I)
BLAME_RE = re.compile(r"\bfail\w*|mistake|not flattering|never again|my fault|blame|shame|careless|\bbroke\b"
                      r"|cannot be trusted|dangerous|incompetent|useless", re.I)
BLAME_REPORT = 6

POINTER_HEAD = (
    "# Minds in this room\n\n"
    "Each line names one resident's current mind leaf and the SHA-256 of that leaf. Only "
    "`ops/lib/scripts/mind.py` writes this file, after Kevin's yes in conversation. The leaves live in "
    "`archives/`, named `MIND-<key>-<date>-<hash8>.md`, out of Git. Spec: `Sessions/docs/ops/specs/scripts/mind.md`.\n\n")


class Refused(Exception):
    """Fail closed: nothing was written, or nothing is served."""


class Missing(Refused):
    """A leaf the pointer or a successor names is not on disk."""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def policy_digest() -> str:
    """The first 16 hex digits of a digest of every rule above; each leaf records the one it was written under."""
    body = {"layers": LAYERS, "budgets": BUDGETS, "allowed": ALLOWED, "required": REQUIRED,
            "core_kinds": CORE_KINDS, "min_yes": MIN_YES, "chars_per_token": CHARS_PER_TOKEN,
            "screens": [rx.pattern for rx in (*IDENTITY_RES, MEDICAL_RE, SECRET_RE, BLAME_RE)]}
    return sha256(json.dumps(body, sort_keys=True).encode("utf-8"))[:16]


def valid_date(value: str) -> bool:
    try:
        return re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is not None and bool(dt.date.fromisoformat(value))
    except ValueError:
        return False


def id_key(entry_id: str) -> tuple[int, int]:
    layer, number = entry_id.rsplit("-", 1)
    return LAYERS.index(layer), int(number)


# --------------------------------------------------------------------------
# Screens. Values are screened as the plain strings they are, never as
# escaped JSON (Claudio C7), and a value is one plain line: control, format
# and separator characters are refused outright.
# --------------------------------------------------------------------------
def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return re.sub("[\u2010-\u2015\u2212\ufe58\ufe63\uff0d]", "-", text)


def screen(value: str, label: str) -> list[str]:
    problems = []
    hidden = sorted({f"U+{ord(c):04X}" for c in value if unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp")})
    if hidden:
        problems.append(f"{label}: control or invisible characters {', '.join(hidden)}; a value is one plain line")
    norm = normalize(value)
    for rx in IDENTITY_RES:
        for m in rx.finditer(norm):
            problems.append(f"{label}: an identifier-like run of {len(m.group(0))} characters; identity lives in the registry")
    if MEDICAL_RE.search(norm):
        problems.append(f"{label}: medical content")
    if SECRET_RE.search(norm):
        problems.append(f"{label}: possible secret")
    return problems


# --------------------------------------------------------------------------
# Leaves: render and parse. A leaf is valid only in canonical form: parsing
# it and rendering the result gives back the same bytes.
# --------------------------------------------------------------------------
def entry_block(entry: dict, with_yes: bool = True) -> list[str]:
    lines = [f"- [{entry['id']}] {entry['text']}"]
    for name, label in FIELDS:
        if entry.get(name) and (with_yes or name != "yes"):
            lines.append(f"  {label}: {entry[name]}")
    return lines


def issued_text(issued: dict) -> str:
    return " ".join(f"{layer}={issued[layer]}" for layer in LAYERS)


def parse_issued(text: str) -> dict:
    m = ISSUED_RE.match(text)
    if not m:
        raise Refused("the issued line is malformed")
    return {layer: int(n) for layer, n in zip(LAYERS, m.groups())}


def render_leaf(head: dict, entries: list[dict]) -> str:
    out = [f"# Mind of {head['title']}", ""] + [f"{k}: {head[k]}" for k in HEAD_KEYS]
    for layer in LAYERS:
        chosen = sorted((e for e in entries if e["layer"] == layer), key=lambda e: id_key(e["id"]))
        if chosen:
            out += ["", f"## {TITLES[layer]}", ""]
            for e in chosen:
                out += entry_block(e)
    return "\n".join(out) + "\n"


def parse_leaf(text: str) -> tuple[dict, list[dict]]:
    if not text.endswith("\n"):
        raise Refused("the leaf does not end with a newline")
    lines = text[:-1].split("\n")
    if len(lines) < 2 + len(HEAD_KEYS) or not lines[0].startswith("# Mind of ") or lines[1] != "":
        raise Refused("the leaf has no mind header")
    head = {"title": lines[0][len("# Mind of "):]}
    for k, line in zip(HEAD_KEYS, lines[2:2 + len(HEAD_KEYS)]):
        if not line.startswith(k + ": "):
            raise Refused(f"the leaf header has no {k!r} line where it belongs")
        head[k] = line[len(k) + 2:]
    by_title = {title: layer for layer, title in TITLES.items()}
    entries: list[dict] = []
    layer = current = None
    for number, line in enumerate(lines[2 + len(HEAD_KEYS):], 3 + len(HEAD_KEYS)):
        if line == "":
            continue
        if line.startswith("## "):
            if line[3:] not in by_title:
                raise Refused(f"leaf line {number}: unknown section")
            layer, current = by_title[line[3:]], None
            continue
        m = ENTRY_RE.match(line)
        if m:
            if m.group(2) != layer:
                raise Refused(f"leaf line {number}: {m.group(1)} is outside its section")
            current = {"id": m.group(1), "layer": layer, "text": m.group(4)}
            entries.append(current)
            continue
        m = FIELD_RE.match(line)
        if m and current is not None and m.group(1) in LABELS and LABELS[m.group(1)] not in current:
            current[LABELS[m.group(1)]] = m.group(2)
            continue
        raise Refused(f"leaf line {number}: not understood")
    if len({e["id"] for e in entries}) != len(entries):
        raise Refused("the leaf names one entry twice")
    if render_leaf(head, entries) != text:
        raise Refused("the leaf is not in canonical form (edited by hand, or reordered)")
    return head, entries


def head_problems(head: dict) -> list[str]:
    problems = []
    if not KEY_RE.match(head["resident"]) or not KEY_RE.match(head["by"]):
        problems.append("resident or by is not a registry key")
    if not WRITTEN_RE.match(head["written"]):
        problems.append("written is not a UTC time")
    if head["predecessor"] != "none" and not PRED_RE.match(head["predecessor"]):
        problems.append("predecessor is malformed")
    if not re.fullmatch(r"[0-9a-f]{16}", head["policy"]):
        problems.append("policy is malformed")
    m = YES_RE.match(head["yes"])
    if not m or not valid_date(m.group(1)) or len(m.group(2).strip()) < MIN_YES:
        problems.append("the leaf carries no yes from Kevin (date and words)")
    else:
        problems += screen(m.group(2), "yes")
    try:
        parse_issued(head["issued"])
    except Refused as exc:
        problems.append(str(exc))
    return problems


def entry_problems(e: dict) -> list[str]:
    layer, eid = e["layer"], e["id"]
    problems = [f"{eid}: {name} does not belong in a {layer} entry"
                for name in e if name not in ("id", "layer", "yes") and name not in ALLOWED[layer]]
    problems += [f"{eid}: needs {name}" for name in REQUIRED[layer] if not e.get(name)]
    if not YES_RE.match(e.get("yes") or ""):
        problems.append(f"{eid}: carries no yes from Kevin")
    problems += [f"{eid}: {name} is not a YYYY-MM-DD date" for name in ("date", "closed")
                 if e.get(name) and not valid_date(e[name])]
    if layer == "core" and e.get("kind") not in CORE_KINDS:
        problems.append(f"{eid}: a core entry needs kind {', '.join(CORE_KINDS)}")
    if layer == "lesson" and e.get("kind") not in (None, "incident"):
        problems.append(f"{eid}: a lesson's kind is incident or nothing")
    if layer == "lesson" and e.get("kind") == "incident" and not (e.get("fix") and e.get("closed")):
        problems.append(f"{eid}: an incident enters only as a closed lesson, with its fix and closed date")
    if layer == "lesson" and e.get("closed") and e.get("kind") != "incident":
        problems.append(f"{eid}: closed belongs only to an incident lesson")
    if layer == "core" and BLAME_RE.search(normalize(e.get("text") or "")):
        problems.append(f"{eid}: blame words in a core entry; the self is not an inventory of failures")
    for name in ("text",) + tuple(n for n, _ in FIELDS):
        if isinstance(e.get(name), str):
            problems += screen(e[name], f"{eid} {name}")
    return problems


def budget_problems(entries: list[dict]) -> list[str]:
    problems = []
    for layer in LAYERS:
        used = sum(math.ceil(len("\n".join(entry_block(e))) / CHARS_PER_TOKEN) for e in entries if e["layer"] == layer)
        if used > BUDGETS[layer]:
            problems.append(f"{layer} needs about {used} tokens, over its budget of {BUDGETS[layer]}; retire or trim on purpose")
    return problems


def change_text(added, amended, retired) -> str:
    parts = [f"{verb} " + ", ".join(sorted(ids, key=id_key))
             for verb, ids in (("add", added), ("amend", amended), ("retire", retired)) if ids]
    return "; ".join(parts)


def difference(before: list[dict], after: list[dict]) -> tuple[list, list, list]:
    b, a = {e["id"]: e for e in before}, {e["id"]: e for e in after}
    return ([i for i in a if i not in b], [i for i in a if i in b and a[i] != b[i]], [i for i in b if i not in a])


def genesis_problems(name: str, head: dict, entries: list[dict]) -> list[str]:
    problems = []
    if not entries:
        problems.append(f"{name}: a first leaf with no entries")
    want = change_text([e["id"] for e in entries], [], [])
    if head["change"] != want:
        problems.append(f"{name}: declares {head['change']!r}, but a first leaf adds {want!r}")
    issued = parse_issued(head["issued"])
    for layer in LAYERS:
        top = max([id_key(e["id"])[1] for e in entries if e["layer"] == layer] or [0])
        if issued[layer] != top:
            problems.append(f"{name}: issued {layer}={issued[layer]}, but its highest entry is {top}")
    problems += [f"{name}: {e['id']} does not carry this leaf's yes" for e in entries if e.get("yes") != head["yes"]]
    return problems


def step_problems(name: str, prev: tuple[dict, list], cur: tuple[dict, list]) -> list[str]:
    """What must hold between a leaf and its predecessor."""
    (ph, pe), (ch, ce) = prev, cur
    added, amended, retired = difference(pe, ce)
    want = change_text(added, amended, retired)
    problems = []
    if not want:
        problems.append(f"{name}: changes nothing from its predecessor")
    if ch["change"] != want:
        problems.append(f"{name}: declares {ch['change']!r}, but the difference from its predecessor is {want!r}")
    pi, ci = parse_issued(ph["issued"]), parse_issued(ch["issued"])
    for eid in added:
        layer, number = eid.rsplit("-", 1)
        if int(number) <= pi[layer]:
            problems.append(f"{name}: {eid} reuses a number already issued; a retired entry never comes back under its old number")
    for layer in LAYERS:
        top = max([pi[layer]] + [id_key(i)[1] for i in added if i.startswith(layer + "-")])
        if ci[layer] != top:
            problems.append(f"{name}: issued {layer}={ci[layer]}, expected {top}")
    by_id = {e["id"]: e for e in ce}
    problems += [f"{name}: {i} was added or amended without this leaf's yes" for i in added + amended
                 if by_id[i].get("yes") != ch["yes"]]
    if ch["written"] <= ph["written"]:
        problems.append(f"{name}: written no later than its predecessor")
    return problems


# --------------------------------------------------------------------------
# Disk: leaves, the pointer, the registry, the lock, the Git guard.
# --------------------------------------------------------------------------
def load_leaf(room: Path, key: str, rel: str) -> tuple[dict, list[dict], bytes]:
    name = rel[len(SURFACES) + 1:] if rel.startswith(SURFACES + "/") else ""
    m = NAME_RE.match(name)
    if not m or "/" in name:
        raise Refused(f"{rel!r} is not a leaf name in {SURFACES}/")
    if m.group("key") != key:
        raise Refused(f"{rel} belongs to {m.group('key')!r}, not {key!r}")
    path = room / SURFACES / name
    if path.is_symlink():
        raise Refused(f"{rel} is a symbolic link")
    if not path.is_file():
        raise Missing(f"{rel} is not on disk")
    if path.resolve().parent != (room / SURFACES).resolve():
        raise Refused(f"{rel} resolves outside {SURFACES}/")
    data = path.read_bytes()
    try:
        head, entries = parse_leaf(data.decode("utf-8"))
    except UnicodeDecodeError:
        raise Refused(f"{rel} is not UTF-8") from None
    if head["resident"] != key:
        raise Refused(f"{rel} declares resident {head['resident']!r}, not {key!r}")
    if not sha256(data).startswith(m.group("hash")):
        raise Refused(f"{rel}: its bytes no longer match the hash in its name")
    if head["written"][:10] != m.group("date"):
        raise Refused(f"{rel}: the date in its name is not the date it was written")
    return head, entries, data


def pointer_text(lines: dict) -> str:
    return POINTER_HEAD + "".join(f"resident={k}|leaf={lines[k][0]}|sha256={lines[k][1]}\n" for k in sorted(lines))


def read_pointer(room: Path) -> dict | None:
    path = room / POINTER
    if path.is_symlink():
        raise Refused(f"{POINTER} is a symbolic link")
    if not path.exists():
        return None
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        raise Refused(f"{POINTER} is not UTF-8") from None
    if not text.startswith(POINTER_HEAD):
        raise Refused(f"{POINTER} is not a pointer this tool wrote; it is left as it is")
    lines: dict[str, tuple[str, str]] = {}
    for raw in text[len(POINTER_HEAD):].split("\n")[:-1]:
        m = POINTER_LINE_RE.match(raw)
        if not m:
            raise Refused(f"{POINTER} has a line that is not a pointer line")
        if m.group(1) in lines:
            raise Refused(f"{POINTER} names {m.group(1)!r} twice; one resident has one mind")
        lines[m.group(1)] = (m.group(2), m.group(3))
    if pointer_text(lines) != text:
        raise Refused(f"{POINTER} is not in canonical form")
    return lines


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
        return None, [f"{key!r} is registered to the room {entry.get('room')!r}, not this one"]
    return entry, []


def title_of(entry: dict) -> str:
    return f"{entry.get('role')} ({entry.get('person')})"


@contextlib.contextmanager
def room_lock(room: Path):
    path = room / LOCK
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        view = view[os.write(fd, view):]


def write_exclusive(path: Path, data: bytes) -> None:
    """Create a new leaf at mode 0600; never overwrite one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        write_all(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def write_atomic(path: Path, data: bytes) -> None:
    """Replace the pointer by rename, at mode 0600."""
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
    """Why a write must stop for Git's sake; empty only on Git's own positive answers (George's read, 10-30).

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


# --------------------------------------------------------------------------
# Verification: every gate for one resident's mind.
# --------------------------------------------------------------------------
class Report:
    def __init__(self):
        self.rows: list[tuple[str, bool, list[str], str]] = []

    def add(self, gate: str, blocking: bool, problems: list[str], detail: str = "") -> None:
        self.rows.append((gate, blocking, list(problems), detail))

    def failures(self) -> list[str]:
        return [f"{gate}: {p}" for gate, blocking, problems, _ in self.rows if blocking for p in problems]


def walk(room: Path, key: str, rel: str, head: dict, entries: list, data: bytes) -> tuple[list[str], list[str], set, list]:
    """Follow predecessors from the current leaf. Returns (problems, notes, chain hashes, chain)."""
    problems, notes = [], []
    shas = {sha256(data)}
    chain = [(rel, head)]
    cur = (rel, head, entries)
    while True:
        name, ch, ce = cur
        if ch["predecessor"] == "none":
            problems += genesis_problems(name, ch, ce)
            break
        m = PRED_RE.match(ch["predecessor"])
        if not m:
            problems.append(f"{name}: predecessor is malformed")
            break
        prel, psha = m.groups()
        if psha in shas:
            problems.append(f"{name}: the chain loops")
            break
        try:
            ph, pe, pdata = load_leaf(room, key, prel)
        except Missing as exc:
            (problems if name == rel else notes).append(str(exc))
            break
        except Refused as exc:
            problems.append(str(exc))
            break
        if sha256(pdata) != psha:
            problems.append(f"{prel}: its bytes are not the ones {name} records; it was changed after it was written")
            break
        problems += step_problems(name, (ph, pe), (ch, ce))
        shas.add(psha)
        chain.append((prel, ph))
        cur = (prel, ph, pe)
    return problems, notes, shas, chain


def other_leaves(room: Path, key: str, shas: set, current_sha: str) -> tuple[list[str], list[str]]:
    """(leaves that name the current leaf as predecessor, leaves outside the chain)."""
    surfaces = room / SURFACES
    ahead, outside = [], []
    if not surfaces.is_dir():
        return ahead, outside
    for path in sorted(surfaces.iterdir()):
        m = NAME_RE.match(path.name)
        if not m or m.group("key") != key:
            continue
        if path.is_symlink():                 # never read through a link: archives/ also holds other records
            outside.append(path.name)
            continue
        if not path.is_file():
            continue
        data = path.read_bytes()
        if sha256(data) in shas:
            continue
        try:
            head, _ = parse_leaf(data.decode("utf-8"))
            pm = PRED_RE.match(head["predecessor"])
        except (UnicodeDecodeError, Refused):
            pm = None
        (ahead if pm and pm.group(2) == current_sha else outside).append(path.name)
    return ahead, outside


def verify(room: Path, key: str, reg: dict, lines: dict) -> tuple[Report, tuple | None]:
    """Every gate for key. Returns (report, (rel, head, entries, data) or None)."""
    rep = Report()
    entry, problems = registered(reg, key, room)
    rep.add("registered", True, problems, "once, in this room")
    if key not in lines:
        rep.add("pointer", True, [f"{POINTER} has no line for {key!r}"])
        return rep, None
    rel, recorded = lines[key]
    try:
        head, entries, data = load_leaf(room, key, rel)
    except Refused as exc:
        rep.add("leaf", True, [str(exc)])
        return rep, None
    digest = sha256(data)
    rep.add("leaf", True, [] if digest == recorded else [f"{rel}: its SHA-256 is not the one {POINTER} records"], rel)
    problems = head_problems(head) + [p for e in entries for p in entry_problems(e)] + budget_problems(entries)
    rep.add("entries", True, problems, f"{len(entries)} entries")
    problems, notes, shas, chain = walk(room, key, rel, head, entries, data)
    rep.add("chain", True, problems, f"chain of {len(chain)}, back to {chain[-1][0]}")
    if notes:
        rep.add("chain-history", False, notes)
    ahead, outside = other_leaves(room, key, shas, digest)
    rep.add("newest", True, [f"{name} names the current leaf as its predecessor; {POINTER} points behind the newest leaf"
                             for name in ahead], "the pointer is at the newest leaf")
    if outside:
        rep.add("outside-chain", False, [f"{name} is not in this mind's chain" for name in outside])
    rep.add("live-state", False, [f"{e['id']}: looks like live state; state belongs in the handoff"
                                  for e in entries for n in ("text",) + tuple(f for f, _ in FIELDS)
                                  if isinstance(e.get(n), str) and LIVE_STATE_RE.search(normalize(e[n]))], "none")
    rep.add("sources", False, [f"{e['id']}: {e['source']} is not in this room (it may be elsewhere)" for e in entries
                               if "/" in e.get("source", "") and " " not in e["source"] and "://" not in e["source"]
                               and not (room / e["source"].split("#")[0]).exists()])
    hits = len(BLAME_RE.findall(normalize(data.decode("utf-8"))))
    rep.add("blame", False, [f"{hits} blame words; read it as the resident will"] if hits >= BLAME_REPORT else [], f"{hits} blame words")
    rep.add("policy", False, [] if head["policy"] == policy_digest() else
            [f"written under policy {head['policy']}, not this tool's {policy_digest()}"], head["policy"])
    if entry is not None and head["title"] != title_of(entry):
        rep.add("title", False, [f"the leaf's title differs from the registry's {title_of(entry)!r}"])
    return rep, (rel, head, entries, data)


# --------------------------------------------------------------------------
# Changes: a JSON object with add, amend and retire. Kevin's words come
# separately, from --yes, and the tool puts them on every entry it touches.
# --------------------------------------------------------------------------
def no_duplicate_keys(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise Refused("the change file names one field twice")
    return dict(pairs)


def load_changes(source: str) -> tuple[list, list, list]:
    data = sys.stdin.buffer.read() if source == "-" else Path(source).read_bytes()
    try:
        obj = json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicate_keys)
    except UnicodeDecodeError:
        raise Refused("the change file is not UTF-8") from None
    except ValueError:
        raise Refused("the change file is not JSON") from None
    if not isinstance(obj, dict) or not obj or set(obj) - {"add", "amend", "retire"}:
        raise Refused("the change file is an object with add, amend or retire, and nothing else")
    add, amend, retire = obj.get("add", []), obj.get("amend", []), obj.get("retire", [])
    if not all(isinstance(x, list) for x in (add, amend, retire)):
        raise Refused("add, amend and retire are lists")
    for item in add + amend:
        if not isinstance(item, dict) or not all(isinstance(v, str) or (v is None and item in amend) for v in item.values()):
            raise Refused("each add or amend is an object of strings")
    if not all(isinstance(i, str) for i in retire):
        raise Refused("retire is a list of entry ids")
    if not (add or amend or retire):
        raise Refused("the change file changes nothing")
    return add, amend, retire


def binding_of(key: str, predecessor: str, add: list, amend: list, retire: list) -> str:
    """What Kevin's yes is bound to: the change exactly as previewed, the leaf it builds on, and whose mind it is."""
    body = {"key": key, "predecessor": predecessor, "changes": {"add": add, "amend": amend, "retire": retire}}
    return sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def apply_changes(entries: list[dict], issued: dict, add: list, amend: list, retire: list, yes: str):
    """Returns (new entries, new issued, added ids, amended ids, retired ids, entries before)."""
    cur = {e["id"]: dict(e) for e in entries}
    before = {i: dict(e) for i, e in cur.items()}
    issued = dict(issued)
    touched: set[str] = set()
    for eid in retire:
        if eid not in cur or eid in touched:
            raise Refused(f"retire {eid}: no such entry in the current leaf, or named twice")
        touched.add(eid)
        del cur[eid]
    amended = []
    for item in amend:
        eid = item.get("id")
        if eid not in cur or eid in touched:
            raise Refused(f"amend {eid}: no such entry in the current leaf, or named twice; a retired entry returns only as a new entry")
        fields = {k: v for k, v in item.items() if k != "id"}
        extra = set(fields) - set(ALLOWED[cur[eid]["layer"]])
        if extra:
            raise Refused(f"amend {eid}: {', '.join(sorted(extra))} cannot be set here (the layer never changes; yes comes from --yes)")
        new = dict(cur[eid])
        for k, v in fields.items():
            if v is None or not v.strip():
                new.pop(k, None)
            else:
                new[k] = v.strip()
        new.pop("yes", None)
        old = {k: v for k, v in cur[eid].items() if k != "yes"}
        if new == old:
            raise Refused(f"amend {eid}: changes nothing")
        new["yes"] = yes
        cur[eid] = new
        touched.add(eid)
        amended.append(eid)
    added = []
    for item in add:
        layer = item.get("layer")
        if layer not in LAYERS:
            raise Refused(f"add: layer {layer!r} is not one of {', '.join(LAYERS)}")
        extra = set(item) - {"layer"} - set(ALLOWED[layer])
        if extra:
            raise Refused(f"add {layer}: {', '.join(sorted(extra))} cannot be set here (ids are issued by the tool; yes comes from --yes)")
        issued[layer] += 1
        eid = f"{layer}-{issued[layer]:03d}"
        cur[eid] = {"id": eid, "layer": layer, **{k: v.strip() for k, v in item.items() if k != "layer" and v.strip()}, "yes": yes}
        added.append(eid)
    return list(cur.values()), issued, added, amended, list(retire), before


def change_report(added, amended, retired, before: dict, after: list[dict], with_yes: bool) -> str:
    now = {e["id"]: e for e in after}
    out = []
    for eid in sorted(added, key=id_key):
        out += [f"add {eid}"] + ["    " + line for line in entry_block(now[eid], with_yes)]
    for eid in sorted(amended, key=id_key):
        out += [f"amend {eid}", "  before:"] + ["    " + line for line in entry_block(before[eid])]
        out += ["  after:"] + ["    " + line for line in entry_block(now[eid], with_yes)]
    for eid in sorted(retired, key=id_key):
        out += [f"retire {eid}"] + ["    " + line for line in entry_block(before[eid])]
    return "\n".join(out) + "\n"


def prepare(args, now: dt.datetime, words: str | None):
    """Everything write does before touching disk. Caller holds the lock for a write."""
    room, key = args.room, args.key
    if not KEY_RE.match(key):
        raise Refused(f"{key!r} is not a registry key")
    reg = read_registry(args.registry)
    entry, problems = registered(reg, key, room)
    if problems:
        raise Refused("; ".join(problems))
    lines = read_pointer(room) or {}
    if key in lines:
        rep, current = verify(room, key, reg, lines)
        if rep.failures():
            raise Refused("the current mind does not pass its own check; nothing is built on it: " + "; ".join(rep.failures()))
        rel, head, entries, data = current
        issued, predecessor = parse_issued(head["issued"]), f"{rel} sha256={sha256(data)}"
    else:
        ahead, outside = other_leaves(room, key, set(), "")
        if ahead or outside:
            raise Refused(f"leaves for {key!r} already exist in {SURFACES}/ but {POINTER} has no line for it; restore the pointer first")
        head, entries, issued, predecessor = None, [], {layer: 0 for layer in LAYERS}, "none"
    add, amend, retire = load_changes(args.changes)
    binding = binding_of(key, predecessor, add, amend, retire)
    yes = f'{now.date().isoformat()}, "{words if words is not None else "(Kevin, at write)"}"'
    new_entries, new_issued, added, amended, retired, before = apply_changes(entries, issued, add, amend, retire, yes)
    problems = [p for e in new_entries for p in entry_problems(e)] + budget_problems(new_entries)
    if words is not None:
        if len(words.strip()) < MIN_YES:
            problems.append("--yes needs Kevin's own words")
        problems += screen(words, "yes")
    if problems:
        raise Refused("nothing was written: " + "; ".join(problems))
    new_head = {"title": title_of(entry), "resident": key, "written": iso(now), "by": getattr(args, "by", None) or key,
                "predecessor": predecessor, "change": change_text(added, amended, retired), "yes": yes,
                "issued": issued_text(new_issued), "policy": policy_digest()}
    text = render_leaf(new_head, new_entries)
    report = change_report(added, amended, retired, before, new_entries, with_yes=words is not None)
    return text, new_head, new_entries, head, entries, lines, reg, report, binding


# --------------------------------------------------------------------------
# Commands.
# --------------------------------------------------------------------------
def cmd_preview(args):
    *_, report, binding = prepare(args, args.now, None)
    sys.stdout.write(f"mind {args.key}: proposed change, for Kevin's yes. Nothing is written.\n" + report
                     + f"binding: {binding}\n"
                     + f"After Kevin's yes, write exactly this change: write {args.key} --changes <the same changes> "
                     + f"--preview {binding} --yes \"<his words>\" --by <your key>\n")
    return 0


def cmd_write(args):
    words = (args.yes or "").strip()
    if len(words) < MIN_YES:
        raise Refused("write needs --yes with Kevin's own words from the conversation")
    if not args.by:
        raise Refused("write needs --by with the registry key of the resident running it")
    if not re.fullmatch(r"[0-9a-f]{64}", args.preview or ""):
        raise Refused("write needs --preview with the binding that preview printed for the change Kevin said yes to")
    with room_lock(args.room):
        _, problems = registered(read_registry(args.registry), args.by)
        if problems:
            raise Refused("--by: " + "; ".join(problems))
        text, head, entries, prev_head, prev_entries, lines, reg, report, binding = prepare(args, args.now, words)
        if binding != args.preview:
            raise Refused("nothing was written: the change, or the mind it builds on, is not what the preview showed "
                          "(the binding differs); preview again, and ask Kevin again")
        reparsed = parse_leaf(text)
        check = (genesis_problems("new leaf", *reparsed) if prev_head is None
                 else step_problems("new leaf", (prev_head, prev_entries), reparsed))
        if check:
            raise Refused("the new leaf would not pass its own chain check: " + "; ".join(check))
        data = text.encode("utf-8")
        digest = sha256(data)
        name = f"MIND-{args.key}-{head['written'][:10]}-{digest[:8]}.md"
        leaf = args.room / SURFACES / name
        exposed = git_exposed(args.room, [leaf, args.room / POINTER])
        if exposed:
            raise Refused("nothing was written: " + "; ".join(exposed))
        write_exclusive(leaf, data)
        lines = dict(lines)
        lines[args.key] = (f"{SURFACES}/{name}", digest)
        write_atomic(args.room / POINTER, pointer_text(lines).encode("utf-8"))
    sys.stdout.write(f"mind {args.key}: written with Kevin's yes.\n" + report
                     + f"leaf {SURFACES}/{name} sha256 {digest}\n{POINTER} now points {args.key} at it.\n")
    return 0


def cmd_check(args):
    reg = read_registry(args.registry)
    lines = read_pointer(args.room)
    print(f"mind check: room {args.room}")
    if lines is None:
        print(f"PASS pointer : no {POINTER} yet; no minds in this room")
        return 0
    keys = [args.key] if args.key else sorted(lines)
    print(f"PASS pointer : {len(lines)} pointer lines, each resident once")
    failed = 0
    for key in keys:
        rep, _ = verify(args.room, key, reg, lines)
        for gate, blocking, problems, detail in rep.rows:
            status = "PASS" if not problems else ("FAIL" if blocking else "REPORT")
            failed += status == "FAIL"
            print(f"{status} {key} {gate} : {'; '.join(problems) if problems else detail}")
    surfaces = args.room / SURFACES
    if not args.key and surfaces.is_dir():
        strays = sorted(p.name for p in surfaces.iterdir() if p.name.startswith(LEAF_PREFIX)
                        and not (NAME_RE.match(p.name) and NAME_RE.match(p.name).group("key") in lines))
        if strays:
            print(f"REPORT room outside-pointer : {len(strays)} {LEAF_PREFIX} files in {SURFACES}/ belong to no resident in {POINTER}")
    print(f"blocking failures: {failed}")
    return 1 if failed else 0


def cmd_show(args):
    reg = read_registry(args.registry)
    rep, current = verify(args.room, args.key, reg, read_pointer(args.room) or {})
    if rep.failures():
        raise Refused("this mind is not served until its check passes: " + "; ".join(rep.failures()))
    rel, _, _, data = current
    if args.ref:
        print(f"leaf={rel}|sha256={sha256(data)}")
    else:
        sys.stdout.write(data.decode("utf-8"))
    return 0


def cmd_history(args):
    lines = read_pointer(args.room) or {}
    if args.key not in lines:
        raise Refused(f"{POINTER} has no line for {args.key!r}")
    rel = lines[args.key][0]
    head, entries, data = load_leaf(args.room, args.key, rel)
    problems, notes, _, chain = walk(args.room, args.key, rel, head, entries, data)
    for name, h in chain:
        print(f"{h['written']} {name} by {h['by']}: {h['change']}; yes {h['yes']}")
    for line in problems + notes:
        print(f"note: {line}")
    return 0


def parse_now(value: str | None) -> dt.datetime:
    if value is None:
        return utc_now()
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc).replace(microsecond=0)
    except ValueError:
        raise SystemExit(f"--now {value!r} is not an ISO time") from None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="mind.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--room", type=Path, default=SESSIONS, help="the room whose MIND.md and archives/MIND-* leaves hold the minds")
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--now", default=None, help="ISO time to use instead of the clock (tests)")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="every gate, for one resident or every resident in the room")
    p.add_argument("--key")
    p.set_defaults(run=cmd_check)
    p = sub.add_parser("show", help="print the verified current leaf byte for byte, or nothing")
    p.add_argument("key")
    p.add_argument("--ref", action="store_true", help="print only leaf=<path>|sha256=<digest>, for the rotation capsule")
    p.set_defaults(run=cmd_show)
    p = sub.add_parser("history", help="the chain of leaves: when, by whom, what changed, and Kevin's words")
    p.add_argument("key")
    p.set_defaults(run=cmd_history)
    p = sub.add_parser("preview", help="show exactly what a change would do; writes nothing")
    p.add_argument("key")
    p.add_argument("--changes", required=True, help="a JSON file of add, amend and retire, or - for stdin")
    p.set_defaults(run=cmd_preview)
    p = sub.add_parser("write", help="after Kevin's yes: write a new leaf and move the pointer")
    p.add_argument("key")
    p.add_argument("--changes", required=True, help="a JSON file of add, amend and retire, or - for stdin")
    p.add_argument("--yes", help="Kevin's own words from the conversation")
    p.add_argument("--preview", help="the binding that preview printed for the change Kevin said yes to")
    p.add_argument("--by", help="the registry key of the resident running the write")
    p.set_defaults(run=cmd_write)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    args.room = args.room.resolve()
    args.now = parse_now(args.now)
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
