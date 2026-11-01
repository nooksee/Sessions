#!/usr/bin/env python3
"""Classify Codex sessions into residents, worker threads, and unknowns.

Background. Codex exposes a `multi_agent_v1` toolset and proactive delegation.
A resident can spawn a child thread, which Codex nicknames automatically and
records in `session_meta.source` as:

    {"subagent": {"thread_spawn": {"parent_thread_id": ..., "depth": 1,
                                   "agent_nickname": "Wegener",
                                   "agent_role": "explorer"}}}

Each spawned thread gets a full session file. It is a real, budget-consuming
conversation, but it is NOT a resident: it has no lineage capsule, owns no
room, appears in no roster, and is not intended to persist.

Before this tool existed the house model had exactly two categories -- resident
and archived predecessor -- so worker threads were classified as junk and swept
as orphans. Seventeen of them had accumulated before anyone looked. This gives
them a name and an owner.

Read-only. Reports; archives only with --archive-idle and an explicit hours
threshold, and never touches a file another process holds.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
from pathlib import Path

CODEX = Path.home() / ".codex"
LIVE = CODEX / "sessions"
ARCHIVE = CODEX / "archived_sessions"

# Promotion registry. The `session_meta.source` subagent marker records where a
# thread CAME FROM and is never rewritten -- origin is a fact. Whether it has
# since been promoted to a resident is a separate decision, recorded here.
# Keeping them apart means a promoted resident never has to pretend it was
# always one.
PROMOTIONS = Path(__file__).resolve().parents[3] / "ops" / "etc" / "promoted-workers.json"

# A worker thread past this size has stopped being a helper and is doing
# sustained work under a parent's budget without appearing in any roster.
OUTLIER_ROWS = 2000

# Length of a full session identifier. The guard matches on the whole thing;
# see load_promotions for why a prefix is not acceptable.
FULL_ID_LEN = 36


def spawn_info(meta: dict) -> dict | None:
    source = meta.get("source")
    if not isinstance(source, dict):
        return None
    return (source.get("subagent") or {}).get("thread_spawn")


def load_promotions() -> dict[str, dict]:
    """Load the promotion registry, keyed on the FULL session identifier.

    This used to key on an 8-character prefix. Codex identifiers are
    time-ordered, so threads spawned in the same batch share a leading prefix:
    measured 2026-08-05 across the live store, 5 of 23 distinct prefixes
    covered more than one session, one of them covering three. A prefix key can
    therefore shield the wrong session, or shield three when one was promoted.

    This guard exists because an ad-hoc prefix match deleted Ray Codex on
    2026-07-31. A safety device that matches loosely is not a safety device, so
    a short or malformed entry is a hard error rather than a silent downgrade.
    """
    try:
        data = json.loads(PROMOTIONS.read_text())
    except FileNotFoundError:
        return {}
    except Exception as exc:
        raise SystemExit(f"promotion registry unreadable, refusing to run: {exc}")

    out: dict[str, dict] = {}
    for entry in data.get("promoted", []):
        sid = entry.get("session_id") or entry.get("session_id_prefix") or ""
        if len(sid) < FULL_ID_LEN:
            raise SystemExit(
                f"promotion registry entry {sid!r} is not a full session id "
                f"({len(sid)} chars, need {FULL_ID_LEN}). Refusing to run: a "
                f"partial key cannot shield reliably. Fix {PROMOTIONS}."
            )
        out[sid] = entry
    return out


def scan(root: Path) -> list[dict]:
    out: list[dict] = []
    if not root.is_dir():
        return out
    promoted = load_promotions()
    now = dt.datetime.now(dt.timezone.utc)
    for path in sorted(root.rglob("*.jsonl")):
        try:
            meta = json.loads(path.open(encoding="utf-8").readline())["payload"]
        except Exception:
            continue
        rows = 0
        capsule = None
        for line in path.open(encoding="utf-8"):
            rows += 1
            if capsule is None and "LINEAGE MEMORY" in line:
                try:
                    message = json.loads(line).get("payload", {}).get("message", "")
                    if "LINEAGE MEMORY" in message:
                        capsule = message[:120]
                except Exception:
                    pass
        try:
            last = json.loads(path.read_bytes().rsplit(b"\n", 2)[-2])
            stamp = dt.datetime.fromisoformat(last["timestamp"].replace("Z", "+00:00"))
            idle_hours = (now - stamp).total_seconds() / 3600
        except Exception:
            idle_hours = float("inf")

        spawn = spawn_info(meta)
        sid_full = meta.get("id") or ""
        sid = sid_full[:8]  # display only; never used to match the guard
        promo = promoted.get(sid_full)
        if promo:
            # Spawned as a worker, promoted since. Reports as a resident; the
            # origin stays visible so the history is never lost.
            kind = "resident"
        elif spawn:
            kind = "worker"
        elif capsule:
            kind = "resident"
        else:
            kind = "unknown"

        out.append(
            {
                "path": path,
                "kind": kind,
                "id": sid,
                "id_full": sid_full,
                "cwd": meta.get("cwd", ""),
                "promoted_name": (promo or {}).get("resident_name"),
                "rows": rows,
                "bytes": path.stat().st_size,
                "idle_hours": idle_hours,
                "nickname": (spawn or {}).get("agent_nickname"),
                "role": (spawn or {}).get("agent_role"),
                "parent": ((spawn or {}).get("parent_thread_id") or "")[:8],
                "depth": (spawn or {}).get("depth"),
            }
        )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--archive-idle",
        type=float,
        metavar="HOURS",
        help="Move worker threads idle longer than HOURS into archived custody.",
    )
    ap.add_argument(
        "--purge",
        type=float,
        metavar="HOURS",
        help=(
            "Delete worker threads idle longer than HOURS. Operator standing "
            "order 2026-08-01: subagents are disposable. Promoted residents are "
            "never eligible; see PROMOTED_GUARD."
        ),
    )
    ap.add_argument("--apply", action="store_true", help="Perform the archive or purge.")
    args = ap.parse_args()

    live = scan(LIVE)
    archived = scan(ARCHIVE)

    if args.json:
        payload = {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "live": [
                {k: (str(v) if k == "path" else v) for k, v in r.items()} for r in live
            ],
            "archived_workers": sum(1 for r in archived if r["kind"] == "worker"),
        }
        print(json.dumps(payload, indent=2))
        return

    for kind in ("resident", "worker", "unknown"):
        rows = [r for r in live if r["kind"] == kind]
        if not rows:
            continue
        print(f"\n== {kind.upper()} ({len(rows)} live) ==")
        for r in sorted(rows, key=lambda r: -r["rows"]):
            label = r["promoted_name"] or r["nickname"] or Path(r["cwd"]).name or "?"
            role = f"/{r['role']}" if r["role"] else ""
            parent = ""
            if r["parent"]:
                parent = (
                    f"  <- {r['parent']} (promoted, was {r['nickname']})"
                    if r["promoted_name"]
                    else f"  <- {r['parent']}"
                )
            flag = "  ** OUTLIER" if kind == "worker" and r["rows"] >= OUTLIER_ROWS else ""
            idle = "live" if r["idle_hours"] < 1 else f"{r['idle_hours']:.0f}h idle"
            print(
                f"  {r['id']:9s} {label:<14s}{role:<10s} {r['rows']:>6} rows "
                f"{r['bytes']/1e6:>6.1f}MB  {idle:<10s}{parent}{flag}"
            )

    workers = [r for r in live if r["kind"] == "worker"]
    print(
        f"\nlive: residents {sum(1 for r in live if r['kind']=='resident')}, "
        f"workers {len(workers)}, unknown {sum(1 for r in live if r['kind']=='unknown')}"
    )
    print(f"archived worker threads: {sum(1 for r in archived if r['kind']=='worker')}")

    if args.purge is not None:
        # PROMOTED_GUARD. A promoted resident keeps its `subagent` origin marker
        # because origin is a fact -- see DOCTRINE 1A. That makes it look like a
        # worker to any classifier reading the marker alone. On 2026-08-01 an
        # ad-hoc purge deleted Ray Codex for exactly this reason; he survived
        # only because a backup existed. Nothing in `promoted` is ever eligible.
        promoted = load_promotions()
        due = [
            r for r in workers
            if r["idle_hours"] > args.purge and r["id_full"] not in promoted
        ]
        shielded = [r for r in workers if r["id_full"] in promoted]
        for r in shielded:
            print(f"  PROTECTED (promoted resident): {r['id']} {r['promoted_name']}")
        print(f"worker threads idle over {args.purge}h, eligible to delete: {len(due)}")
        freed = 0
        for r in due:
            if os.system(f'fuser -s "{r["path"]}" 2>/dev/null') == 0:
                print(f"  SKIP (active): {r['id']} {r['nickname']}")
                continue
            print(f"  delete {r['id']} {r['nickname']} ({r['rows']} rows)")
            if args.apply:
                freed += r["bytes"]
                r["path"].unlink()
        if args.apply:
            print(f"\nfreed {freed/1e6:.1f} MB")
        else:
            print("\ndry run. pass --apply to delete.")
        return

    if args.archive_idle is None:
        return

    promoted = load_promotions()
    due = [
        r for r in workers
        if r["idle_hours"] > args.archive_idle and r["id_full"] not in promoted
    ]
    print(f"\nworker threads idle over {args.archive_idle}h: {len(due)}")
    for r in due:
        held = os.system(f'fuser -s "{r["path"]}" 2>/dev/null') == 0
        note = "  SKIP (held open)" if held else ""
        print(f"  {r['id']} {r['nickname']} {r['rows']} rows{note}")
        if args.apply and not held:
            target = ARCHIVE / r["path"].relative_to(LIVE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(r["path"]), str(target))
    if due and not args.apply:
        print("\ndry run. pass --apply to archive.")


if __name__ == "__main__":
    main()
