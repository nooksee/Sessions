#!/usr/bin/env python3
"""Report, and on explicit request enforce, the official session-folder policy.

Kevin set the policy on 2026-08-08 after finding the provider session store had
become, in his words, an Arlington-Cemetery-sized graveyard of JSONL files. It
is short:

    The official provider session folders hold registered ACTIVE bodies only.
    Everything else lives in backup or quarantine custody. Nothing is deleted.

Official folders are the provider's own stores. This resident's Lab, Candidates,
and Attic are working surfaces and are deliberately out of scope; the policy is
about the floors the providers read from, not about research space.

Retention is measured, never guessed, and "in use" has two independent meanings.
A body is kept when its identifier appears in `ops/etc/resident-identities.json`,
the identity authority, OR when any editor chat is still bound to it. The second
clause was learned by breaking it: the first sweep moved bodies the registry did
not list but PyCharm chats still pointed at, and the Remote Device chat came back
with `failed to resolve rollout path ...: file does not exist`. Registered is not
the same as referenced.

Everything else is classified and reported with its age and size so the operator
can see what a sweep would move before it moves.

Two hard refusals, because this tool moves real session bodies:

  * a registered active or editor-bound body is never moved, under any flag;
  * `--sweep` refuses to run unless the writer gate is clean, because relocating
    a body an editor or provider currently holds open risks a torn write.

Deletion is not implemented and is not a flag. Moves go to dated quarantine with
a hashed manifest, and every copy is verified byte-for-byte before the source is
unlinked.
"""

from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SESSIONS = Path(__file__).resolve().parents[3]   # the room, resolved as gauge.py does
REGISTRY = SESSIONS / "ops/etc/resident-identities.json"

OFFICIAL = {
    "codex-live": Path.home() / ".codex/sessions",
    "codex-archived": Path.home() / ".codex/archived_sessions",
    "claude-live": Path.home() / ".claude/projects",
}

# .PRE-UNSWAP, .PRE-SEAT and .PRE-RESEAT were added 2026-10-08. Nine such
# scaffolds from the 2026-08-08 container reversal sat on the field for two
# months classed "active", because they carry a registered identifier in
# their name and the suffix list predated them. A scaffold is a scaffold
# whatever its suffix spells.
SCAFFOLD_SUFFIXES = (".PRE-ROTATION", ".PRE-ORIENTATION", ".PRE-RESEED",
                     ".PRE-UNSWAP", ".PRE-SEAT", ".PRE-RESEAT",
                     ".bak", ".NEW", ".tmp")


def active_ids() -> dict[str, str]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {i["session_id"]: f"{i['role']} ({i['person']})" for i in data["identities"]}


def chat_bound_ids() -> dict[str, str]:
    """Thread identifiers any editor chat is still bound to.

    Registered is not the same as referenced, and this policy learned that the
    hard way on 2026-08-08. The first sweep moved bodies that were not in the
    identity registry but that PyCharm chats were still bound to, including the
    pre-rotation donor of the Remote Device seat. Kevin opened that chat and got:

        Failed to initialize ACP session. Error: Internal error:
        "failed to resolve rollout path ...019f6b4c...: file does not exist"

    A chat records its thread in an `.agentsession` file as
    `<agentId>:<threadId>`, and it keeps that binding long after the resident has
    been rotated onto a newer body. Twenty-four such bodies were moved and had to
    be restored from quarantine.

    Anything an editor still points at is therefore in use, whatever the registry
    says, and is never swept.
    """
    bound: dict[str, str] = {}
    for root in Path.home().glob(".config/JetBrains/PyCharm*/aia-task-history"):
        for path in root.glob("*.agentsession"):
            try:
                value = path.read_text(encoding="utf-8").strip()
            except OSError:
                continue
            thread = value.rsplit(":", 1)[-1]
            if len(thread) == 36:
                bound[thread] = path.stem[:8]
    return bound


def thread_source(path: Path) -> str | None:
    """Read row zero only. A worker thread declares itself in session_meta."""
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            row = json.loads(fh.readline())
    except (OSError, json.JSONDecodeError):
        return None
    return row.get("payload", {}).get("thread_source")


def classify(root: Path, active: dict[str, str],
             bound: dict[str, str] | None = None) -> list[dict]:
    out: list[dict] = []
    if not root.is_dir():
        return out
    for path in sorted(root.rglob("*.jsonl*")):
        if not path.is_file():
            continue
        name = path.name
        bound = bound or {}
        matched = next((sid for sid in active if sid in name), None)
        held = next((sid for sid in bound if sid in name), None)
        if name.endswith(SCAFFOLD_SUFFIXES):
            kind = "scaffold"
        elif matched:
            kind = "active"
        elif held:
            kind = "editor-bound"
        elif thread_source(path) == "subagent":
            kind = "worker"
        else:
            kind = "retired"
        stat = path.stat()
        out.append({
            "path": path,
            "kind": kind,
            "resident": active.get(matched, "") or (f"editor chat {bound.get(held)}" if held else ""),
            "bytes": stat.st_size,
            "age_days": (datetime.datetime.now()
                         - datetime.datetime.fromtimestamp(stat.st_mtime)).days,
        })
    return out


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def held_open_under(roots: list[Path]) -> dict[Path, list[int]]:
    """Every file under `roots` that some running process holds open, with pids.

    Added 2026-10-08 after this tool, run while a Claude workflow was in
    flight, swept three live agent transcripts and the workflow journal out
    from under their processes. They sat under a session's `subagents/`
    directory, unregistered and unbound, which is exactly what a sweep is for
    when the work is finished and exactly wrong while it is running. The
    operator's ad-hoc guard checked only top-level bodies. The question is not
    "is this a body" but "is anything holding it", so this asks the kernel
    about every path under every official root, and a sweep that would move a
    held file refuses outright rather than skipping it quietly.
    """
    roots = [r.resolve() for r in roots]
    held: dict[Path, list[int]] = {}
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            fds = list((proc / "fd").iterdir())
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            continue
        for fd in fds:
            try:
                raw = os.readlink(fd)
            except (OSError, RuntimeError):
                continue
            tp = Path(raw.removesuffix(" (deleted)"))
            if any(str(tp).startswith(str(r) + "/") for r in roots):
                held.setdefault(tp, []).append(int(proc.name))
    return held


def live_claude_session_bodies(records_dir: Path | None = None,
                               projects_root: Path | None = None) -> dict[Path, int]:
    """Bodies of live Claude sessions, by their own records, with pids.

    Added 2026-10-08. A Claude session -- interactive, the GUI's per-turn
    `-p --resume`, or a background session served for Remote Control -- holds
    no file descriptor on its body between turns, so the kernel scan above
    cannot see it. Claude Code writes ~/.claude/sessions/<pid>.json with the
    sessionId while the process lives; that record is the truth about which
    bodies are live, and a sweep must treat them as held.
    """
    records = records_dir or (Path.home() / ".claude" / "sessions")
    projects = projects_root or (Path.home() / ".claude" / "projects")
    out: dict[Path, int] = {}
    if not records.exists():
        return out
    for rec_path in records.glob("*.json"):
        try:
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        pid, sid = rec.get("pid"), rec.get("sessionId")
        if not isinstance(pid, int) or not isinstance(sid, str) or not Path(f"/proc/{pid}").exists():
            continue
        for body in projects.glob(f"*/{sid}.jsonl"):
            out[body.resolve()] = pid
    return out


def gate_clean() -> bool:
    checker = SESSIONS / "ops/lib/scripts/gate.py"
    if not checker.exists():
        return False
    result = subprocess.run([sys.executable, str(checker)],
                            capture_output=True, text=True)
    return "GATE: CLEAN" in result.stdout


def human(n: int) -> str:
    return f"{n / 1e6:,.1f} MB"


def _volume_root(name: str) -> Path:
    """One volume root from the room's private host fingerprint, read only where a path needs it. A missing or
    malformed file refuses this tool by name with exit 1 and names no value (fingerprint.py)."""
    path = Path(__file__).resolve().with_name("fingerprint.py")
    key = f"fingerprint@{path}"
    module = sys.modules.get(key)
    if module is None:
        spec = importlib.util.spec_from_file_location(key, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module   # the dataclass in it looks its module up here
        spec.loader.exec_module(module)
    return module.volume_root(Path(__file__).name, name)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sweep", action="store_true",
                    help="relocate non-active bodies to quarantine; never deletes")
    ap.add_argument("--quarantine", type=Path, default=None,
                    help="where --sweep moves bodies; default: Project-Archives/Session-Quarantine on the archive "
                         "volume named by the host fingerprint")
    ap.add_argument("--include-archived", action="store_true",
                    help="also sweep the provider's own archived_sessions folder")
    args = ap.parse_args()

    active = active_ids()
    findings: dict[str, list[dict]] = {}
    bound = chat_bound_ids()
    for label, root in OFFICIAL.items():
        findings[label] = classify(root, active, bound)

    movable: list[dict] = []
    print(f"registry active identifiers: {len(active)}\n")
    for label, rows in findings.items():
        by = collections.Counter(r["kind"] for r in rows)
        size = collections.Counter()
        for r in rows:
            size[r["kind"]] += r["bytes"]
        total = sum(r["bytes"] for r in rows)
        print(f"{label}  ({OFFICIAL[label]})")
        print(f"  files {len(rows):4}   {human(total)}")
        for kind in ("active", "editor-bound", "scaffold", "worker", "retired"):
            if by[kind]:
                mark = "  keep" if kind in ("active", "editor-bound") else "  move"
                print(f"    {kind:9} {by[kind]:4}   {human(size[kind]):>12}{mark}")
        if label == "codex-archived" and not args.include_archived:
            print("    (archived folder held back; pass --include-archived to sweep it)")
            continue
        movable += [r for r in rows if r["kind"] not in ("active", "editor-bound")]
        print()

    print(f"would move: {len(movable)} files, {human(sum(r['bytes'] for r in movable))}")
    keep = sum(1 for rows in findings.values() for r in rows
               if r["kind"] in ("active", "editor-bound"))
    print(f"would keep: {keep} bodies (registered active plus editor-bound)")
    print(f"editor chat bindings seen: {len(bound)}")

    if not args.sweep:
        print("\nreport only. Pass --sweep to relocate, which never deletes.")
        return

    if not gate_clean():
        raise SystemExit("\nREFUSED: writer gate is not clean. Relocating a body a "
                         "provider holds open risks a torn write.")
    if any(r["kind"] in ("active", "editor-bound") for r in movable):
        raise SystemExit("\nREFUSED: an active or editor-bound body reached the "
                         "move set. This is a bug.")
    held = held_open_under(list(OFFICIAL.values()))
    for body, pid in live_claude_session_bodies().items():
        held.setdefault(body, []).append(pid)
    movers_held = [r for r in movable if r["path"].resolve() in held]
    if movers_held:
        lines = "\n".join(f"  {r['path']}  pids={held[r['path'].resolve()]}"
                          for r in movers_held[:10])
        raise SystemExit("\nREFUSED: "
                         f"{len(movers_held)} prospective mover(s) are held open by "
                         "a running process. A finished transcript is sweepable; a "
                         f"live one is not.\n{lines}")

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    quarantine = args.quarantine if args.quarantine is not None else (
        _volume_root("archive") / "Project-Archives" / "Session-Quarantine")
    dest = quarantine / stamp
    dest.mkdir(parents=True, exist_ok=True)
    manifest, moved, failed = [], 0, 0
    for row in movable:
        src: Path = row["path"]
        target = dest / src.name
        n = 1
        while target.exists():
            target = dest / f"{src.stem}.{n}{src.suffix}"
            n += 1
        digest = sha256(src)
        shutil.copy2(src, target)
        if sha256(target) != digest:
            print(f"  HASH MISMATCH, source kept: {src.name}")
            failed += 1
            continue
        src.unlink()
        moved += 1
        manifest.append({"file": target.name, "origin": str(src), "kind": row["kind"],
                         "bytes": row["bytes"], "sha256": digest})

    (dest / "MANIFEST.json").write_text(
        json.dumps({"swept": stamp, "policy": "official folders hold registered active bodies only",
                    "moved": moved, "failed": failed, "files": manifest}, indent=2),
        encoding="utf-8")
    print(f"\nmoved {moved} file(s) to {dest}")
    print(f"hash failures (source kept): {failed}")
    print("deletions: 0")


if __name__ == "__main__":
    main()
