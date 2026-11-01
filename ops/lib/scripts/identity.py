#!/usr/bin/env python3
"""Verify that every resident's identity agrees in all four places it is written.

Identity for a resident lives in four places, and until 2026-08-05 nothing
checked that they matched:

  1. ops/etc/resident-identities.json  -- the authority
  2. the launcher roster display_name
  3. the launcher host bindings session_id
  4. the identity written inside the resident's own body: a `compacted` lineage
     capsule for Codex, a `<session_clinic_orientation>` row for Claude

When these drift, a resident wakes disagreeing with the name its operator uses.
That happened twice in one week: a swapped Integrator and Contractor pair, and
a nukeCE resident who told Kevin outright that he was being called by the wrong
name. Both were found by a human noticing, not by a tool.

PyCharm's label is what Kevin actually sees, so where a PyCharm title map is
readable it is treated as ground truth and the registry is checked against it.
Codex ACP tab names are not written to disk while the IDE is running, so those
cannot be verified here; they are reported as unverifiable rather than assumed
correct.

Copilot residents (provider "copilot") are registry-only. The launcher roster
and host bindings must NOT name them, because the launcher rejects the whole
roster when it meets a provider it does not support. Their body is the Copilot
session directory: workspace.yaml must carry the registry session and the
registry room, and the latest `<session_clinic_orientation>` user message is
the name they wake to. Their label is the operator-set Agent Dock chat title
in the room's own window. A provider this script does not know is reported as
unsupported and incomplete, never scanned as Codex.

Kevin decided on 2026-10-23 that Gordon Bell and Grace Hopper are to be
admitted registry-only at first, held from the launcher until the launcher
diagnosis returns. A `claude` or `codex` registry row marks that with
"launcher": "held", and the resident must then be absent from the launcher
roster and host bindings, like a Copilot row. The launcher serves a resident
only when the roster and the bindings both carry its key: a held resident
present in both would be served, and present in only one makes the launcher
reject the whole roster, an outage for every resident. A bindings row under
another key that carries the held session is reported for the same reasons.
The body and label legs are checked as for any resident of the provider. Any
other value of "launcher" is a mismatch, never ignored, and so is "held" on a
Copilot or unknown-provider row or with a session id that is not a string.

Read-only. Exit 0 when everything agrees and every leg was compared; 1 on any
mismatch or any leg that could not be compared.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[3]
REGISTRY = SESSIONS / "ops/etc/resident-identities.json"
ROSTER = SESSIONS / "ops/etc/residents.json"
BINDINGS = SESSIONS / "ops/etc/host-bindings.json"
CLAUDE_PROJECTS = Path.home() / ".claude/projects"
CODEX_SESSIONS = Path.home() / ".codex/sessions"
COPILOT_SESSIONS = Path.home() / ".copilot/session-state"
AGENT_DOCK_PROJECTS = Path.home() / ".agent-dock/projects"
AGENT_DOCK_ADAPTER = "github-copilot-cli"
# Providers the launcher roster and host bindings may name. Copilot joins this
# set only in the same change as Resident Center launcher support.
LAUNCHER_PROVIDERS = frozenset({"claude", "codex"})


def expected_display(ident: dict) -> str:
    return f"{ident['role']} ({ident['person']})"


def body_identity(ident: dict) -> tuple[str | None, str]:
    """The name the resident itself will read on wake, and where it came from."""
    sid = ident["session_id"]
    if ident["provider"] == "claude":
        hits = list(CLAUDE_PROJECTS.glob(f"*/{sid}.jsonl"))
        if not hits:
            return None, "container missing"
        # Structural match only. Searching lines for the tag finds it inside
        # ordinary prose and inside recorded tool calls: this resident writes
        # orientation text for OTHER residents as shell arguments, and its own
        # transcript therefore contains their orientation blocks verbatim. On
        # 2026-08-05 that made this checker report that Claude Shannon was
        # Claudine Colbert. It is the fourth time in one day that matching a
        # marker string in content rather than in position produced a confident
        # wrong answer, so this reads the row's own message content and requires
        # the tag to begin it.
        found = None
        for line in hits[0].read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("type") != "user":
                continue
            content = (row.get("message") or {}).get("content")
            if not isinstance(content, str):
                continue
            if not content.lstrip().startswith("<session_clinic_orientation>"):
                continue
            found = content
        if found is None:
            return None, "no orientation row"
        # Prefer the canonical labelled form, which states the whole label and
        # survives rewording. Case-insensitive here is safe because the label is
        # delimited by backticks and parentheses rather than by capitalisation.
        m = re.search(r"You are\s+`([^`]+?)\s*\(([^`()]+)\)`", found, re.I)
        if m:
            return m.group(2).strip(), "orientation row"
        # Fallback for older bodies. This one must stay case-SENSITIVE: it
        # identifies the name by its all-capitals shape, so relaxing case makes
        # it match ordinary prose. Measured 2026-08-08: with re.I it read
        # "You are NOT Shannon and you are not his successor" and reported the
        # resident's name as "Not Shannon".
        m = re.search(r"You are ([A-Z][A-Z '\-\.]+?)(?:,| and | the )", found)
        return (m.group(1).strip().title() if m else None), "orientation row"

    if ident["provider"] != "codex":
        return None, f"unsupported provider {ident['provider']!r}"

    hits = [p for p in CODEX_SESSIONS.rglob("*.jsonl")
            if sid in p.name and not p.name.endswith("PRE-ROTATION")]
    if not hits:
        return None, "container missing"
    for line in hits[0].read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("type") != "compacted":
            continue
        msg = row.get("payload", {}).get("message", "")
        # Preferred: the canonical labelled form written since 2026-08-08,
        # `You are ``Role (Person)`` `. It states the whole label rather than a
        # fragment of prose, so it survives rewording of the capsule. The older
        # all-capitals prose form is kept as a fallback for bodies built before
        # that date, which are still in service.
        # Case-insensitive: orientation text is sometimes written in capitals
        # for emphasis, and a resident whose label cannot be read is reported
        # as uncompared, which is a false alarm rather than a real gap.
        m = re.search(r"You are\s+`([^`]+?)\s*\(([^`()]+)\)`", msg, re.I)
        if m:
            return m.group(2).strip(), "lineage capsule"
        # Case-SENSITIVE for the same reason as the orientation fallback above.
        m = re.search(r"You are ([A-Z][A-Z '\-\.]+?)(?:,| and | the )", msg)
        return (m.group(1).strip().title() if m else None), "lineage capsule"
    return None, "no lineage capsule"


COPILOT_PLAIN = "workspace.yaml not in the plain form this checker reads"
# Copilot reads and writes this file with two YAML libraries: a native
# serde_yaml reader on unsafe-libyaml (YAML 1.1) restores the stored folder,
# and a JavaScript YAML 1.2 library (eemeli yaml) parses and writes it when
# a session is forked. NEL, LS and PS are line breaks to the first and text
# to the second, and libyaml refuses the other controls and U+FFFE/U+FFFF
# (measured 2026-10-22). A file holding any of them is unreadable here. A
# carriage return, which both writers escape, and a byte-order mark are
# refused by policy.
COPILOT_UNSAFE = re.compile("[\x00-\x08\x0b-\x1f\x7f-\x9f\u2028\u2029\ufeff\ufffe\uffff]")
# A block-scalar header: literal or folded, with an optional chomping sign
# and an optional indentation digit, in either order (`|-`, `|2-`, `>+3`).
COPILOT_BLOCK = re.compile(r"[|>](?:[1-9][+-]?|[+-][1-9]?)?")
# A complete one-line quoted value, with only escapes both libraries accept:
# no surrogate and nothing above U+10FFFF, which libyaml refuses.
COPILOT_QUOTED = re.compile(
    r'"(?:[^"\\]|\\(?:[0abt\tnvfre "/\\N_LP]|x[0-9A-Fa-f]{2}'
    r"|u(?![dD][89a-fA-F])[0-9A-Fa-f]{4}"
    r"|U(?:0000(?![dD][89a-fA-F])[0-9A-Fa-f]{4}|000[1-9A-Fa-f][0-9A-Fa-f]{4}|0010[0-9A-Fa-f]{4})))*\""
    r"|'(?:[^']|'')*'")
# Keys YAML resolves to a boolean or null, so that two spellings collide.
COPILOT_CORE_KEYS = {"null", "true", "false", "yes", "no", "on", "off", "y", "n"}


def _copilot_plain(value: str) -> bool:
    """True when a one-line value is plain text to both YAML libraries.

    A plain value may not open with an indicator, nor hold a comment after a
    space or tab, a `: ` or a final `:`. Each of those is read differently by
    YAML, or not at all. `<<` and `=` are YAML 1.1 merge and value keys.
    """
    if not value:
        return True
    if value in ("<<", "=") or value[0] in "[]{},#&*!|>'\"%@`":
        return False
    if value[0] in "-?:" and (len(value) == 1 or value[1] in " \t"):
        return False
    return not re.search(r"[ \t]#|:(?:[ \t]|$)", value)


def _copilot_workspace(path: Path) -> tuple[dict[str, str] | None, str]:
    """Strict read of workspace.yaml: one `key: value` per line.

    Copilot parses this file as YAML. A duplicate key, a second document, a
    comment, an anchor, alias or tag, a flow collection, an unclosed quote or
    any other value that YAML would read differently from its text makes the
    file unreadable here rather than letting a guess win (reviews of
    2026-10-21, PR #108 and 2026-10-22).

    `id` and `cwd` must be plain one-line values. A value that YAML would
    resolve to a number, boolean or null is still read as its text; such text
    can never equal a registry session id or an absolute room, so it can only
    fail the comparison. Another key may also hold a
    complete one-line quoted value, or a block scalar whose lines are indented
    by spaces, never less than its first line (or its indentation digit), and
    are content, never keys. Copilot writes a block scalar when it names a
    session after a multi-line first prompt (measured on JoJo's admission
    body, 2026-10-22). A final `...` line, which libyaml writes after some
    blocks, is allowed. Folded multi-line plain values are not read.
    """
    try:
        if not path.is_file():
            return None, "container missing"
        text = path.read_bytes().decode("utf-8")
    except (OSError, ValueError):
        return None, "workspace.yaml unreadable"
    if COPILOT_UNSAFE.search(text):
        return None, COPILOT_PLAIN
    values: dict[str, str] = {}
    in_block = ended = False
    block_indent = None
    leading_spaces = 0
    for line in text.split("\n"):
        if not line.strip(" "):
            # A space-only line before a block's first line may not be deeper
            # than that line.
            if in_block and block_indent is None:
                leading_spaces = max(leading_spaces, len(line))
            continue
        if ended:
            return None, COPILOT_PLAIN
        indent = len(line) - len(line.lstrip(" "))
        if indent:
            if not in_block or (block_indent is not None and indent < block_indent):
                return None, COPILOT_PLAIN
            if block_indent is None:
                # libyaml refuses a tab where it is still finding the indent.
                if leading_spaces > indent or line[indent] == "\t":
                    return None, COPILOT_PLAIN
                block_indent = indent
            continue
        in_block = False
        if line == "...":
            ended = True
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(?:[ \t]+(.*?))?[ \t]*$", line)
        if (not m or m.group(1) in values or len(m.group(1)) > 1024
                or m.group(1).lower() in COPILOT_CORE_KEYS):
            return None, COPILOT_PLAIN
        key, value = m.group(1), m.group(2) or ""
        if key not in ("id", "cwd") and COPILOT_BLOCK.fullmatch(value):
            digit = re.search(r"[1-9]", value)
            in_block, leading_spaces = True, 0
            block_indent = int(digit.group(0)) if digit else None
        elif key not in ("id", "cwd") and value.startswith(("'", '"')):
            if not COPILOT_QUOTED.fullmatch(value):
                return None, COPILOT_PLAIN
        elif not _copilot_plain(value):
            return None, COPILOT_PLAIN
        values[key] = value
    if not values.get("id") or not values.get("cwd"):
        return None, COPILOT_PLAIN
    return values, ""


def copilot_body(ident: dict) -> tuple[str | None, str, str | None, str]:
    """A Copilot body's wake name and its source, plus its stored folder.

    The folder is the `cwd` in workspace.yaml, which is what Agent Dock uses to
    decide which window lists the chat. `/cwd` changes the live folder without
    rewriting this file, and a reload from the old window silently reverts it
    (measured 2026-10-20 on Copilot 1.0.101), so a body is only in its room
    when the stored folder says so. The fourth value says why the folder could
    not be read, when it could not.
    """
    sid = ident["session_id"]
    directory = COPILOT_SESSIONS / sid
    workspace, why = _copilot_workspace(directory / "workspace.yaml")
    if workspace is None:
        return None, why, None, why
    cwd = workspace["cwd"]
    if workspace["id"] != sid:
        return None, "workspace.yaml names another session", None, \
            "workspace.yaml names another session"
    events = directory / "events.jsonl"
    try:
        if not events.is_file():
            return None, "container missing", cwd, ""
        # A live append can leave a cut final line; it simply fails to parse.
        lines = events.read_bytes().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return None, "events.jsonl unreadable", cwd, ""
    try:
        first = json.loads(lines[0]) if lines else {}
    except json.JSONDecodeError:
        first = {}
    if not isinstance(first, dict) or first.get("type") != "session.start":
        return None, "unsupported events schema", cwd, ""
    start = first.get("data")
    if not isinstance(start, dict):
        return None, "unsupported events schema", cwd, ""
    if start.get("sessionId") != sid:
        return None, "session.start names another session", cwd, ""
    # Same structural rule as the Claude reader: the tag must begin the main
    # agent's own message content. Sub-agent rows carry a row-level agentId.
    # A cleared conversation no longer holds an earlier orientation.
    found = None
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        if row.get("type") == "session.context_cleared":
            found = None
            continue
        if row.get("type") != "user.message" or row.get("agentId"):
            continue
        data = row.get("data")
        content = data.get("content") if isinstance(data, dict) else None
        if not isinstance(content, str):
            continue
        if not content.lstrip().startswith("<session_clinic_orientation>"):
            continue
        found = content
    if found is None:
        return None, "no orientation row", cwd, ""
    m = re.search(r"You are\s+`([^`]+?)\s*\(([^`()]+)\)`", found, re.I)
    if m:
        return m.group(2).strip(), "orientation row", cwd, ""
    m = re.search(r"You are ([A-Z][A-Z '\-\.]+?)(?:,| and | the )", found)
    return (m.group(1).strip().title() if m else None), "orientation row", cwd, ""


def agent_dock_title(sid: str, room: str) -> str | None:
    """The chat title the operator set for this session in the room's window.

    Agent Dock keeps one index per window folder, named by replacing every
    character outside [A-Za-z0-9] with a hyphen. Only the room's own window
    counts, so a title left on the donor chat in another window cannot vouch
    for this body. Only operator-set titles (`titleUserSet`) on chats that are
    not archived count; an automatic title is the first prompt, not a label.
    Two different titles for one session are ambiguous and left uncompared, as
    is an index whose titled chat lists its sessions in an unsupported shape.
    """
    slug = re.sub(r"[^A-Za-z0-9]", "-", room).strip("-")
    index = AGENT_DOCK_PROJECTS / slug / "index.json"
    try:
        if not index.is_file():
            return None
        chats = json.loads(index.read_bytes().decode("utf-8"))
    except (OSError, ValueError):
        return None
    titles: set[str] = set()
    for chat in chats if isinstance(chats, list) else []:
        if (not isinstance(chat, dict) or chat.get("titleUserSet") is not True
                or chat.get("archived") is True):
            continue
        title = chat.get("title")
        if not isinstance(title, str) or not title:
            continue
        sessions = chat.get("sessions") or []
        if not isinstance(sessions, list):
            return None
        for session in sessions:
            if (isinstance(session, dict)
                    and session.get("adapterName") == AGENT_DOCK_ADAPTER
                    and session.get("sessionId") == sid):
                titles.add(title)
    return titles.pop() if len(titles) == 1 else None


def acp_titles() -> dict[str, str]:
    """Map a Codex thread identifier to the chat label the operator sees.

    It was believed no such mapping existed on disk, because Codex ACP tab names
    are not flushed while the IDE runs. That belief cost three reversed resident
    pairs on 2026-08-08, assigned by container creation order instead.

    The mapping does exist, in two halves that have to be joined:

      * `aia-task-history/<chatUid>.agentsession` holds `<agentId>:<threadId>`;
      * `workspace/<projectHash>.xml` holds a `SerializedChat` per chat, keyed by
        the same `uid`, carrying the operator's custom `SerializedChatTitle`.

    Joining them on the chat uid yields thread to label directly, which is what
    the identity lock needs and what nobody had assembled. Neither half is
    sufficient alone, which is why the gap survived so long.
    """
    bindings: dict[str, str] = {}
    for path in Path.home().glob(
            ".config/JetBrains/PyCharm*/aia-task-history/*.agentsession"):
        try:
            bindings[path.stem] = path.read_text(encoding="utf-8").strip().rsplit(":", 1)[-1]
        except OSError:
            continue

    labels: dict[str, str] = {}
    chat = re.compile(r"<SerializedChat>.*?</SerializedChat>", re.S)
    uid = re.compile(r'<option name="uid" value="([0-9a-f-]{36})" />\s*</SerializedChat>')
    custom = re.compile(
        r'<option name="custom" value="true" />\s*<option name="text" value="([^"]*)"')
    for path in Path.home().glob(".config/JetBrains/PyCharm*/workspace/*.xml"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for block in chat.findall(text):
            u, t = uid.search(block), custom.search(block)
            if u and t:
                labels[u.group(1)] = t.group(1)

    return {bindings[u]: t for u, t in labels.items() if u in bindings}


def pycharm_titles() -> dict[str, str]:
    out: dict[str, str] = {}
    for f in CLAUDE_PROJECTS.glob("*/.claude-code-gui-session-titles.json"):
        try:
            out.update(json.loads(f.read_text()))
        except Exception:
            continue
    out.update(acp_titles())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true", help="print only problems")
    args = ap.parse_args()

    reg = json.loads(REGISTRY.read_text())
    roster = {e["key"]: e for e in json.loads(ROSTER.read_text())["residents"]}
    binds = {e["key"]: e for e in json.loads(BINDINGS.read_text())["residents"]}
    titles = pycharm_titles()

    problems: list[str] = []
    unverified: list[str] = []
    uncompared: list[str] = []   # a leg that could not be read at all
    dock_uncompared: list[str] = []   # the same, for Copilot's Agent Dock leg
    incomplete: list[str] = []   # any resident with an uncompared leg

    for ident in reg["identities"]:
        key = ident["key"]
        want = expected_display(ident)
        notes: list[str] = []

        held = ident.get("launcher") == "held"
        if "launcher" in ident and not held:
            problems.append(
                f"{key}: registry launcher value {ident['launcher']!r} is not "
                f"'held', the only value this script knows")
        elif held and ident["provider"] not in LAUNCHER_PROVIDERS:
            problems.append(
                f"{key}: registry launcher value 'held' applies only to a "
                f"claude or codex row, not provider {ident['provider']!r}")
            held = False

        r = roster.get(key)
        b = binds.get(key)
        # A held row whose session id is not a string is reported, and its
        # body and label legs are skipped as uncompared, so the run continues
        # for every other resident. (An unheld row keeps its older behaviour.)
        bad_session = held and not isinstance(ident["session_id"], str)
        if bad_session:
            problems.append(
                f"{key}: registry session_id {ident['session_id']!r} is not a "
                f"string; its body and label legs are not compared")
        if ident["provider"] not in LAUNCHER_PROVIDERS or held:
            # Registry-only: absence is the correct state. For a provider the
            # launcher does not support, presence breaks the launcher for every
            # resident. For a held resident, presence in both files lets the
            # launcher serve it, and presence in one makes it reject the whole
            # roster.
            for where, entry in (("roster", r), ("bindings", b)):
                if entry is None:
                    continue
                if held:
                    problems.append(
                        f"{key}: present in {where} although the registry "
                        f"holds it from the launcher (in both roster and bindings "
                        f"the launcher would serve it; in one alone it rejects "
                        f"the whole roster)")
                else:
                    problems.append(
                        f"{key}: present in {where} before launcher support for "
                        f"provider {ident['provider']!r} (the launcher rejects "
                        f"the whole roster)")
            if held:
                # The launcher serves by key. A bindings row under another key
                # that carries the held session would be served under that key
                # if the roster has the same key, and alone it makes the
                # launcher reject the whole roster. Keys are sorted by repr so
                # a malformed, non-string key is reported, not a crash.
                for other in sorted((k for k, e in binds.items() if k != key
                                     and e.get("session_id") == ident["session_id"]),
                                    key=repr):
                    problems.append(
                        f"{key}: held session {str(ident['session_id'])[:13]} is "
                        f"bound under launcher key {other!r} (with a roster row "
                        f"of that key the launcher would serve it; without one "
                        f"it rejects the whole roster)")
        else:
            if r is None:
                problems.append(f"{key}: absent from roster")
            elif r["display_name"] != want:
                problems.append(
                    f"{key}: roster says {r['display_name']!r}, registry says {want!r}")

            if b is None:
                problems.append(f"{key}: absent from bindings")
            elif b["session_id"] != ident["session_id"]:
                problems.append(
                    f"{key}: bindings point at {b['session_id'][:13]}, "
                    f"registry says {ident['session_id'][:13]}")

        copilot = ident["provider"] == "copilot"
        if copilot:
            room = ident.get("room")
            if (not isinstance(room, str) or not os.path.isdir(room)
                    or os.path.realpath(room) != room):
                problems.append(
                    f"{key}: registry room {room!r} is not an existing "
                    f"canonical directory")
                room = None
            name, source, cwd, why = copilot_body(ident)
            if cwd is None:
                notes.append(f"Copilot stored folder unreadable ({why}); "
                             f"room leg NOT compared")
            elif room is not None and cwd != room:
                problems.append(
                    f"{key}: Copilot body is stored in {cwd!r}, registry room "
                    f"is {room!r} -- Agent Dock lists it in the wrong window "
                    f"and it loads that folder's instructions")
        else:
            name, source = ((None, "session_id is not a string") if bad_session
                            else body_identity(ident))
        if name is None:
            notes.append(f"body identity unreadable ({source})")
        elif name.lower() != ident["person"].lower():
            problems.append(
                f"{key}: body says {name!r} ({source}), registry says "
                f"{ident['person']!r} -- this resident will wake disagreeing "
                f"with its own label")

        if copilot:
            title = (agent_dock_title(ident["session_id"], room)
                     if room is not None else None)
            if title is None:
                dock_uncompared.append(f"{key}: {want}")
                notes.append("Agent Dock title in the room's window not set by "
                             "the operator, or ambiguous; this leg was NOT "
                             "compared")
            elif title not in (want, ident["person"]):
                problems.append(
                    f"{key}: Agent Dock title {title!r} does not match "
                    f"registry {want!r}")
        elif bad_session:
            uncompared.append(f"{key}: {want}")
            notes.append("PyCharm label NOT compared: session_id is not a string")
        elif (title := titles.get(ident["session_id"])) is None:
            # Found by Claudine Winslow, Auditor, on 2026-08-08: this leg was
            # compared for 8 of 22 residents and skipped for the other 14, all
            # of them Codex, whose ACP tab names are not written to disk while
            # the IDE runs. The old guard was `if title and ...`, so a missing
            # label fell through with no note and the row still printed `ok`.
            # Nothing distinguished "compared and matched" from "never read".
            # A version upgrade is exactly the event that relocates label
            # files, so the tool was most confident when least informed.
            uncompared.append(f"{key}: {want}")
            notes.append("PyCharm label not on disk; this leg was NOT compared")
        elif title != want and ident["person"] not in title:
            problems.append(
                f"{key}: PyCharm label {title!r} does not match registry {want!r}")

        if ident.get("verified") == "unverified":
            unverified.append(f"{key}: {want}" +
                              (f" -- {ident['note']}" if ident.get("note") else ""))

        if notes:
            incomplete.append(key)

        if not args.quiet:
            mark = "ok " if not notes else "?  "
            print(f"  {mark} {key:26s} {want}"
                  + ("   [held from launcher]" if held else ""))
            for n in notes:
                print(f"        {n}")

    total = len(reg["identities"])
    docked = sum(1 for i in reg["identities"] if i["provider"] == "copilot")
    held_total = sum(1 for i in reg["identities"] if i.get("launcher") == "held"
                     and i["provider"] in LAUNCHER_PROVIDERS)
    pycharm_total = total - docked
    print(f"\nidentities: {total}   mismatches: {len(problems)}   "
          f"unverified: {len(unverified)}   "
          f"incomplete: {len(incomplete)}   "
          f"PyCharm leg compared: {pycharm_total - len(uncompared)}/{pycharm_total}"
          + (f"   Agent Dock leg compared: "
             f"{docked - len(dock_uncompared)}/{docked}" if docked else "")
          + (f"   held from launcher: {held_total}" if held_total else ""))
    for p in problems:
        print(f"  MISMATCH  {p}")
    if uncompared and not args.quiet:
        print("\nPyCharm label absent from disk, so that leg was never compared:")
        for u in uncompared:
            print(f"  - {u}")
    if dock_uncompared and not args.quiet:
        print("\nAgent Dock title not set by the operator in the room's window, "
              "so that leg was never compared:")
        for u in dock_uncompared:
            print(f"  - {u}")
    if unverified and not args.quiet:
        print("\nnot yet confirmed against PyCharm (provisional):")
        for u in unverified:
            print(f"  - {u}")
    # A check that did not run is not a check that passed. Coverage gaps exit
    # non-zero so a caller cannot read silence as agreement.
    return 1 if (problems or incomplete) else 0


if __name__ == "__main__":
    raise SystemExit(main())
