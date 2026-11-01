#!/usr/bin/env python3
"""Verify the single-writer gate before any session-body write.

Why this exists as a script rather than a shell one-liner.

The gate used to be checked ad hoc with `pgrep -f pycharm` and
`pgrep -cf codex-acp`. Both match against the WHOLE command line of every
process, including the checking command's own text. A gate check that mentions
"pycharm" therefore finds itself and reports the editor as running. On
2026-08-05 that false positive blocked a scheduled rotation for a full day
while PyCharm was in fact closed; the only real match was the checker's own
shell.

The rule this script enforces: identify a process by what it IS -- its resolved
`/proc/PID/exe` and its argv[0] -- never by a substring of its arguments. And
never count yourself or your own ancestors.

A false positive is the safe direction, since it blocks work rather than
permitting an unsafe write. It is still a defect: an instrument that cries wolf
gets overridden, and an overridden gate is no gate.

Read-only. Exit 0 when the gate is clean, 1 when a writer is present.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

PROC = Path("/proc")

# argv[0]/exe basenames that indicate a real editor holding session state.
IDE_BINARIES = {"pycharm", "pycharm.sh", "idea", "idea.sh", "webstorm", "goland"}

# The JetBrains Toolbox background daemon. It updates and launches IDEs but
# holds no session file, so it is reported and explicitly not counted.
TOOLBOX_DAEMONS = {"jetbrainsd", "jetbrains-toolbox"}

BRIDGE_BINARIES = {"codex-acp"}
PROVIDER_BINARIES = {"claude", "codex"}

# Where session bodies live. A provider binary is only a writer when it is
# actually holding one of these open.
SESSION_ROOTS = (
    str(Path.home() / ".codex" / "sessions"),
    str(Path.home() / ".codex" / "archived_sessions"),
    str(Path.home() / ".claude" / "projects"),
)


def ancestors(pid: int) -> set[int]:
    """Every pid from `pid` up to init, so a checker never counts itself."""
    out: set[int] = set()
    cur = pid
    while cur and cur not in out:
        out.add(cur)
        try:
            stat = (PROC / str(cur) / "stat").read_text()
            cur = int(stat.rsplit(")", 1)[1].split()[1])
        except Exception:
            break
    return out


def read_proc(pid: int) -> dict | None:
    base = PROC / str(pid)
    try:
        exe = os.path.realpath(base / "exe")
        argv = (base / "cmdline").read_bytes().split(b"\0")
        cwd = os.path.realpath(base / "cwd")
    except Exception:
        return None
    if not exe or exe == str(base / "exe"):
        return None
    argv0 = argv[0].decode("utf-8", "replace") if argv and argv[0] else ""
    return {
        "pid": pid,
        "exe": exe,
        "exe_name": Path(exe).name,
        "argv0_name": Path(argv0).name if argv0 else "",
        "cwd": cwd,
    }


def classify(p: dict) -> str | None:
    """Identity comes from exe and argv[0] only. Arguments are never searched."""
    names = {p["exe_name"], p["argv0_name"]} - {""}
    if names & TOOLBOX_DAEMONS:
        return "toolbox-daemon"
    if names & IDE_BINARIES:
        return "ide"
    if names & BRIDGE_BINARIES:
        return "acp-bridge"
    if names & PROVIDER_BINARIES:
        return "provider-cli"
    return None


def open_session_bodies(pid: int) -> list[str]:
    """Session JSONL files this pid currently holds open.

    Presence of a provider binary is not evidence of a writer. The Codex
    remote-control app-server and its pid-update-loop daemon both run
    continuously under the Resident Center and hold no session file at all;
    counting them blocked the gate on 2026-08-05 for no reason. What matters is
    whether the process has a session body open, so that is what is measured.
    """
    out: list[str] = []
    try:
        for fd in (PROC / str(pid) / "fd").iterdir():
            try:
                target = os.path.realpath(fd)
            except Exception:
                continue
            if target.endswith(".jsonl") and target.startswith(SESSION_ROOTS):
                out.append(target)
    except Exception:
        pass
    return out


def holders(target: Path) -> list[int]:
    """Pids holding `target` open, by walking /proc/*/fd rather than fuser."""
    out: list[int] = []
    want = str(target.resolve())
    for entry in PROC.iterdir():
        if not entry.name.isdigit():
            continue
        fd_dir = entry / "fd"
        try:
            for fd in fd_dir.iterdir():
                try:
                    if os.path.realpath(fd) == want:
                        out.append(int(entry.name))
                        break
                except Exception:
                    continue
        except Exception:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", type=Path, help="also verify this file is not held open")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    mine = ancestors(os.getpid())
    found: dict[str, list[dict]] = {}
    for entry in PROC.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid in mine:
            continue
        p = read_proc(pid)
        if not p:
            continue
        kind = classify(p)
        if kind:
            p["bodies"] = open_session_bodies(pid) if kind != "toolbox-daemon" else []
            # An editor blocks on presence: it drives many sessions and can
            # begin writing any of them at any moment.
            #
            # A provider process blocks only the specific files it holds. It
            # used to block everything, which was wrong in a way that matters:
            # on 2026-08-05 the Codex app-server held George Friend's body open
            # while four unrelated residents needed a capsule amendment, and the
            # gate refused all four. A process holding session Y is not evidence
            # about the safety of writing session X, and a gate that blocks work
            # it cannot justify is a gate that will eventually be overridden.
            # Pass --file to get the precise answer for a specific target.
            p["blocks"] = kind == "ide"
            p["holds"] = bool(p["bodies"])
            found.setdefault(kind, []).append(p)

    blocking = {
        k: [p for p in v if p["blocks"]]
        for k, v in found.items()
        if any(p["blocks"] for p in v)
    }

    if not args.quiet:
        print(f"self and ancestors excluded: {sorted(mine)}")
        for kind in ("ide", "acp-bridge", "provider-cli", "toolbox-daemon"):
            rows = found.get(kind, [])
            note = "  (not a writer)" if kind == "toolbox-daemon" else ""
            print(f"\n{kind}: {len(rows)}{note}")
            for p in rows:
                if p["blocks"]:
                    mark = "BLOCKS ALL"
                elif p.get("holds"):
                    mark = "holds a session body; blocks only that file"
                else:
                    mark = "idle, holds no session body"
                print(f"  pid {p['pid']:<8} [{mark}] {p['exe']}")
                print(f"      cwd {p['cwd']}")
                for b in p["bodies"]:
                    print(f"      open: {b}")

    held: list[int] = []
    if args.file:
        held = [h for h in holders(args.file) if h not in mine]
        if not args.quiet:
            print(f"\ntarget: {args.file}")
            print(f"  held open by: {held if held else 'nobody'}")

    clean = not blocking and not held
    print(f"\nGATE: {'CLEAN' if clean else 'NOT CLEAN'}")
    if not clean:
        for kind, rows in blocking.items():
            print(f"  blocked by {len(rows)} {kind} process(es)")
        if held:
            print(f"  target held open by pids {held}")
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
