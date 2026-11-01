#!/usr/bin/env python3
"""Detect the active-writer condition that can hang a chat on "Initializing".

Written after the night of 2026-08-07, which cost Kevin a day. One observed
failure was an active-writer conflict, in Codex's own words from its log:

    Failed to create session: thread-store conflict:
    thread 019fd1b7-… already has an active writer

Codex enforces one writer per thread. The remote-control app-server daemon had
resumed that thread and kept the claim after PyCharm closed, so every later
attempt to open it was refused. The editor did not surface that refusal and
remained on "Initializing".

This detector is intentionally not a universal diagnosis. On 2026-08-08 the
exact George Friend thread reproduced the same visible symptom while Remote
was inactive and provider process count was `0`. That second failure came from
a malformed rotation body whose compaction `replacement_history` had been
replayed as ordinary dialogue. Writer-conflict success therefore rules out one
failure class; it does not prove that a session body will resume.

This reports, read-only:

  * which threads currently have a writer claim, and which process holds it;
  * whether that holder is an editor bridge, a visible terminal CLI, or a
    background daemon;
  * any lock whose holder is gone, which is a genuinely stale lock;
  * the exact command to clear it.

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

CODEX = Path.home() / ".codex"
LOCKS = CODEX / "thread-writer-locks"
STATE = CODEX / "state_5.sqlite"
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

# A holder is benign when it is the editor's own bridge, because that means the
# editor genuinely has the thread open. It is the failure condition when a
# background daemon holds it, because nothing the operator can see owns it.
EDITOR_MARKERS = ("acp-agents", "codex-acp", "JetBrains")
DAEMON_MARKERS = ("app-server", "remote-control")


def classify_holder(executable: str, command: str) -> str:
    if any(marker in executable or marker in command for marker in EDITOR_MARKERS):
        return "editor-bridge"
    if any(marker in command for marker in DAEMON_MARKERS):
        return "background-daemon"
    if "codex" in Path(executable).name or "codex" in executable:
        return "terminal-cli"
    return "unknown"


def holders() -> dict[int, dict]:
    """Map pid to identity, from the resolved executable, never an argv substring.

    Matching on the command line is how a check that mentions PyCharm finds
    itself; that mistake blocked a rotation for a full day on 2026-08-05.
    """
    out: dict[int, dict] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            exe = os.readlink(entry / "exe")
            cmd = (entry / "cmdline").read_bytes().decode("utf-8", "replace").replace("\0", " ")
        except (OSError, PermissionError):
            continue
        if "codex" not in Path(exe).name and "codex" not in exe:
            continue
        kind = classify_holder(exe, cmd)
        out[pid] = {"exe": exe, "cmd": cmd.strip(), "kind": kind}
    return out


def lock_holder(path: Path, procs: dict[int, dict]) -> int | None:
    """Which pid holds this lock file open, by walking /proc/*/fd."""
    target = str(path.resolve())
    for pid in list(procs) + [p for p in _all_pids() if p not in procs]:
        fd = Path("/proc") / str(pid) / "fd"
        try:
            for link in fd.iterdir():
                try:
                    if os.readlink(link) == target:
                        return pid
                except OSError:
                    continue
        except (OSError, PermissionError):
            continue
    return None


def _all_pids() -> list[int]:
    return [int(p.name) for p in Path("/proc").iterdir() if p.name.isdigit()]


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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    procs = holders()
    who = registry()
    cwds = thread_names()
    findings = []

    locks = sorted(LOCKS.glob("*.lock")) if LOCKS.is_dir() else []
    for lock in locks:
        m = UUID_RE.search(lock.name)
        if not m:
            continue
        tid = m.group(0)
        pid = lock_holder(lock, procs)
        info = procs.get(pid, {}) if pid else {}
        kind = info.get("kind", "gone" if pid is None else "unknown")
        findings.append({
            "thread": tid,
            "resident": who.get(tid, "unregistered"),
            "room": cwds.get(tid, ""),
            "holder_pid": pid,
            "holder_kind": kind,
            "blocks_editor": kind in (
                "background-daemon",
                "terminal-cli",
                "unknown",
            ),
            "stale": pid is None,
        })

    if args.json:
        print(json.dumps({"findings": findings}, indent=2))
        return

    print(f"thread writer claims: {len(findings)}")
    blocking = [f for f in findings if f["blocks_editor"]]
    for f in findings:
        state = ("STALE, holder gone" if f["stale"]
                 else f"held by pid {f['holder_pid']} ({f['holder_kind']})")
        flag = "  <-- will hang the editor on Initializing" if f["blocks_editor"] else ""
        print(f"  {f['thread'][:8]}  {f['resident'][:44]:46} {state}{flag}")

    if not findings:
        print("  none. No thread is claimed; every existing chat can open.")
    if blocking:
        print(f"\n{len(blocking)} thread(s) are claimed by something that is not the editor.")
        print("Those chats will sit on \"Initializing\" forever with no error shown.")
        daemon_claims = [
            finding for finding in blocking
            if finding["holder_kind"] == "background-daemon"
        ]
        terminal_claims = [
            finding for finding in blocking
            if finding["holder_kind"] == "terminal-cli"
        ]
        unknown_claims = [
            finding for finding in blocking
            if finding["holder_kind"] == "unknown"
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
