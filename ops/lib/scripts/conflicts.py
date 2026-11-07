#!/usr/bin/env python3
"""Report the active-writer condition that can hang or refuse a chat.

Written after the night of 2026-08-07, which cost Kevin a day. One observed
failure was an active-writer conflict, in Codex's own words from its log:

    Failed to create session: thread-store conflict:
    thread 0000d7d7-… already has an active writer

Codex enforces one writer per thread. The remote-control app-server daemon had
resumed that thread and kept the claim after PyCharm closed, so every later
attempt to open it was refused. The editor did not surface that refusal and
remained on "Initializing". The editor of 2026-11-06 did show the same refusal
as an error, so a held thread can look either way.

This detector is intentionally not a universal diagnosis. On 2026-08-08 the
exact George Friend thread reproduced the same visible symptom while Remote
was inactive and provider process count was `0`. That second failure came from
a malformed rotation body whose compaction `replacement_history` had been
replayed as ordinary dialogue. Writer-conflict success therefore rules out one
failure class; it does not prove that a session body will resume.

This reports, read-only, for one moment and one Codex home:

  * which lock files exist, and every readable process holding each one open;
  * whether each holder is an editor bridge, a visible terminal CLI, or a
    background daemon;
  * whether the kernel's own lock table shows that file locked;
  * what could not be read, by count;
  * the exact command to clear a daemon's or a terminal's claim.

A reading shows a holder; it never clears one. It is a moment's reading, and a
holder can come or go in the next instant. It looks in one home, and counts any
lock descriptor it sees in another. A process whose descriptors it cannot read
is a count and no more, though the kernel's table still covers it. An editor
bridge is not a harmless holder: that chat is open in one editor, and any second
window, server or client that tries to write it is refused. So no exit status
and no empty list authorizes a resume, a takeover or a write.

It changes nothing. Releasing a claim means stopping a service, which is an
operator decision, and doing it while a turn is in flight risks a torn write on
a live body.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[3]   # the room, resolved as gauge.py does


def codex_home(environ=os.environ) -> tuple[Path, str]:
    """The home the provider itself would choose, and which rule chose it."""
    chosen = environ.get("CODEX_HOME")
    if chosen:
        return Path(chosen), "CODEX_HOME"
    return Path.home() / ".codex", "default"


PROC = Path("/proc")
CODEX, CODEX_SOURCE = codex_home()
LOCKS = CODEX / "thread-writer-locks"
STATE = CODEX / "state_5.sqlite"
LOCK_DIR_NAME = "thread-writer-locks"
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

LIMIT = (
    "LIMIT: one moment and one home. A reading can show a holder; it cannot clear one. "
    "Exit 0 and an empty list authorize no resume, takeover or write."
)

# An editor bridge holding a thread means that chat is open in one editor. It
# still refuses every other writer, a second window included. It is told apart
# here because the operator can see it, and a background daemon nobody sees.
EDITOR_MARKERS = ("acp-agents", "codex-acp", "JetBrains")
DAEMON_MARKERS = ("app-server", "remote-control")
BLOCKING_KINDS = ("background-daemon", "terminal-cli", "unknown")


def classify_holder(executable: str, command: str) -> str:
    if any(marker in executable or marker in command for marker in EDITOR_MARKERS):
        return "editor-bridge"
    if any(marker in command for marker in DAEMON_MARKERS):
        return "background-daemon"
    if "codex" in Path(executable).name or "codex" in executable:
        return "terminal-cli"
    return "unknown"


def holders() -> tuple[dict[int, dict], int]:
    """Map pid to identity, from the resolved executable, never an argv substring.

    Matching on the command line is how a check that mentions PyCharm finds
    itself; that mistake blocked a rotation for a full day on 2026-08-05.
    The second value counts processes refused to this reader.
    """
    out: dict[int, dict] = {}
    refused = 0
    for entry in PROC.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            exe = os.readlink(entry / "exe")
            cmd = (entry / "cmdline").read_bytes().decode("utf-8", "replace").replace("\0", " ")
        except PermissionError:
            refused += 1
            continue
        except OSError:
            continue  # a kernel thread, or a process that ended between the reads
        if "codex" not in Path(exe).name and "codex" not in exe:
            continue
        kind = classify_holder(exe, cmd)
        out[pid] = {"exe": exe, "cmd": cmd.strip(), "kind": kind}
    return out, refused


def _all_pids() -> list[int]:
    return [int(p.name) for p in PROC.iterdir() if p.name.isdigit()]


def scan_lock_fds(pids: list[int], targets: frozenset[str] | set[str] = frozenset()) -> tuple[list[dict], int]:
    """Every descriptor naming a writer-lock file, in every table this reader may read.

    One pass over the process table, in the order given. A descriptor counts when
    its link names the lock folder, or equals a listed lock's resolved path: a
    symlinked folder or file resolves to a name that need not hold the folder's.
    The second value counts the tables refused to this reader.
    """
    rows: list[dict] = []
    refused = 0
    for pid in pids:
        try:
            links = list((PROC / str(pid) / "fd").iterdir())
        except (FileNotFoundError, ProcessLookupError):
            continue
        except OSError:
            refused += 1
            continue
        for link in links:
            try:
                text = os.readlink(link)
            except OSError:
                continue
            if LOCK_DIR_NAME not in text and text not in targets:
                continue
            try:
                seen = os.stat(link)
                identity = (seen.st_dev, seen.st_ino)
            except OSError:
                identity = None
            rows.append({"pid": pid, "path": text, "identity": identity})
    return rows, refused


def kernel_locks() -> tuple[dict[tuple[int, int, int], list[int]], bool]:
    """Files the kernel's table shows locked, each with the pids it names.

    A waiter is no holder. One row that cannot be parsed makes the table
    unreadable as a whole, so a change of format reads as unknown and never as
    not locked. The second value is whether the table could be read.
    """
    try:
        text = (PROC / "locks").read_text(encoding="ascii")
    except (OSError, UnicodeDecodeError):
        return {}, False
    table: dict[tuple[int, int, int], list[int]] = {}
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        if len(parts) > 1 and parts[1] == "->":
            continue
        try:
            major, minor, inode = parts[5].split(":")
            key = (int(major, 16), int(minor, 16), int(inode))
            pid = int(parts[4])
        except (IndexError, ValueError):
            return {}, False
        table.setdefault(key, []).append(pid)
    return table, True


def kernel_state(identity, table, table_read: bool) -> tuple[str, list[int]]:
    """locked, not-locked or unknown, for one file's device and inode."""
    if not table_read or identity is None:
        return "unknown", []
    device, inode = identity
    key = (os.major(device), os.minor(device), inode)
    if key in table:
        return "locked", sorted(table[key])
    if any(row_inode == inode for _, _, row_inode in table):
        return "unknown", []  # the same inode under another device number: not comparable
    return "not-locked", []


def holder_state(held: bool, kernel: str) -> str:
    if held:
        return "open-not-locked" if kernel == "not-locked" else "held"
    if kernel == "locked":
        return "held-unseen"
    return "stale" if kernel == "not-locked" else "unknown"


def thread_names() -> dict[str, str]:
    if not STATE.exists():
        return {}
    try:
        con = sqlite3.connect(f"file:{STATE}?mode=ro", uri=True)
        return {i: (c or "") for i, c in con.execute("select id,cwd from threads")}
    except sqlite3.Error:
        return {}


def registry() -> dict[str, str]:
    p = SESSIONS / "ops" / "etc" / "resident-identities.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {i["session_id"]: f"{i['role']} ({i['person']})" for i in data["identities"]}


def collect() -> dict:
    """One finding per lock file, its holders inside it, and what could not be read."""
    procs, processes_refused = holders()
    order = list(procs) + [p for p in _all_pids() if p not in procs]
    locks = sorted(LOCKS.glob("*.lock")) if LOCKS.is_dir() else []
    fds, tables_refused = scan_lock_fds(order, {str(lock.resolve()) for lock in locks})
    table, table_read = kernel_locks()
    who = registry()
    cwds = thread_names()
    findings = []
    skipped = 0
    matched: set[int] = set()

    for lock in locks:
        m = UUID_RE.search(lock.name)
        if not m:
            skipped += 1
            continue
        tid = m.group(0)
        target = str(lock.resolve())
        try:
            seen = lock.stat()
            identity = (seen.st_dev, seen.st_ino)
        except OSError:
            identity = None
        pids: list[int] = []
        for index, row in enumerate(fds):
            if identity is not None and row["identity"] is not None:
                same = row["identity"] == identity
            else:
                same = row["path"] == target
            if same:
                matched.add(index)
                if row["pid"] not in pids:
                    pids.append(row["pid"])
        kinds = [procs.get(pid, {}).get("kind", "unknown") for pid in pids]
        kernel, kernel_pids = kernel_state(identity, table, table_read)
        state = holder_state(bool(pids), kernel)
        if pids:
            kind = kinds[0]
        else:
            kind = "gone" if state == "stale" else "unknown"
        findings.append({
            "thread": tid,
            "resident": who.get(tid, "unregistered"),
            "room": cwds.get(tid, ""),
            "holder_pid": pids[0] if pids else None,
            "holder_kind": kind,
            "holder_count": len(pids),
            "holders": [{"pid": pid, "kind": k} for pid, k in zip(pids, kinds)],
            "holder_state": state,
            "kernel_lock": kernel,
            "kernel_lock_pids": kernel_pids,
            "blocks_editor": (
                any(k in BLOCKING_KINDS for k in kinds)
                or state in ("held-unseen", "unknown")
            ),
            "blocks_other_writer": state in ("held", "held-unseen", "open-not-locked", "unknown"),
            "stale": state == "stale",
        })

    home = str(LOCKS.resolve())
    other_home = 0
    unlisted = 0
    for index, row in enumerate(fds):
        if index in matched:
            continue
        if str(Path(row["path"]).parent) == home:
            unlisted += 1
        else:
            other_home += 1

    return {
        "limit": LIMIT,
        "coverage": {
            "codex_home": str(CODEX),
            "home_source": CODEX_SOURCE,
            "processes_unreadable": processes_refused,
            "fd_tables_unreadable": tables_refused,
            "lock_table_read": table_read,
            "lock_files_skipped": skipped,
            "lock_fds_other_home": other_home,
            "lock_fds_unlisted": unlisted,
        },
        "findings": findings,
    }


def describe(finding: dict) -> str:
    state = finding["holder_state"]
    if state in ("held", "open-not-locked"):
        people = ", ".join(f"pid {h['pid']} ({h['kind']})" for h in finding["holders"])
        verb = "held by" if state == "held" else "open, and not locked, in"
        return f"{verb} {people}; kernel lock: {finding['kernel_lock']}"
    if state == "held-unseen":
        named = ", ".join(str(pid) for pid in finding["kernel_lock_pids"])
        return f"locked with no visible holder; the kernel names pid {named}"
    if state == "stale":
        return "STALE, no visible holder and no kernel lock"
    return "UNKNOWN, no visible holder and the kernel's table gives no answer"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    result = collect()
    findings = result["findings"]

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(LIMIT)
    print(f"thread writer claims: {len(findings)}")
    blocking = [f for f in findings if f["blocks_editor"]]
    for f in findings:
        flag = "  <-- the editor cannot open this" if f["blocks_editor"] else ""
        print(f"  {f['thread'][:8]}  {f['resident'][:44]:46} {describe(f)}{flag}")

    if not findings:
        print("  none. No lock file under this home; that clears no chat.")
    c = result["coverage"]
    print(f"coverage: home {c['home_source']}; processes refused {c['processes_unreadable']}; "
          f"descriptor tables refused {c['fd_tables_unreadable']}; "
          f"lock table {'read' if c['lock_table_read'] else 'NOT read'}; "
          f"lock files skipped {c['lock_files_skipped']}; "
          f"lock descriptors in another home {c['lock_fds_other_home']}; "
          f"on a file not listed {c['lock_fds_unlisted']}")
    editors = [f for f in findings if f["holder_kind"] == "editor-bridge" and not f["blocks_editor"]]
    if editors:
        print(f"\n{len(editors)} thread(s) are open in an editor. Any second window, server or")
        print("client that tries to write one of them is refused.")
    if blocking:
        print(f"\n{len(blocking)} thread(s) are claimed by something that is not the editor.")
        print("Opening one can sit on \"Initializing\" or show an active-writer error.")
        daemon_claims = [
            finding for finding in blocking
            if any(h["kind"] == "background-daemon" for h in finding["holders"])
        ]
        terminal_claims = [
            finding for finding in blocking
            if any(h["kind"] == "terminal-cli" for h in finding["holders"])
        ]
        unknown_claims = [
            finding for finding in blocking
            if finding["holder_kind"] == "unknown"
            or any(h["kind"] == "unknown" for h in finding["holders"])
        ]
        if daemon_claims:
            print("\nRemote daemon claim: finish the Remote turn, then run:")
            print("    systemctl --user stop codex-remote-control.service")
        if terminal_claims:
            print("\nTerminal claim: finish the turn and exit that Codex console cleanly.")
        if unknown_claims:
            print("\nUnknown claim: inspect the exact holder before changing any service.")
        print("\nDo not kill a holder mid-turn. It is appending to a live session")
        print("body, and a torn write there is unrecoverable for that row.")
    raise SystemExit(1 if blocking else 0)


if __name__ == "__main__":
    main()
