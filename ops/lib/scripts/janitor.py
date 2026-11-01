#!/usr/bin/env python3
"""Release writer claims the remote daemon is squatting on, automatically.

Written 2026-08-11 after the third evening lost to the same failure class:
processes holding thread writer claims after the thing that needed them is
gone. The operator should not have to remember `systemctl`. This runs from a
systemd user timer and makes forgetting harmless.

The mechanism it corrects, measured tonight:

  * chats opened in the phone app stay attached at the backend indefinitely;
  * every daemon start -- every boot -- re-claims that attached set;
  * the claims then block the editor ("Initializing", no error shown) and
    outlive any actual phone use by days. Frank Codex sat claimed for three
    days after his last write.

The safe release for a daemon-held claim is restarting the daemon, because a
claim is an open file descriptor and only its holder can drop it. Measured
2026-08-11: a freshly started daemon holds `0` claims, so a restart both
releases the squat and keeps remote available. This janitor therefore:

  1. reads the writer-claim state with the existing conflict checker;
  2. acts only when EVERY daemon-held thread's body has been idle for at
     least IDLE_MINUTES -- one recent write anywhere and it stands down,
     because a restart mid-turn risks a torn write on a live body;
  3. restarts the remote-control service;
  4. verifies the claims are gone and says so in the journal.

It acts on background-daemon claims only. Editor and terminal claims mean a
human is (or recently was) present, and this tool does not outrank humans.
Everything it does is visible: `journalctl --user -u codex-claim-janitor`.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "conflicts.py"
STATE = Path.home() / ".codex" / "state_5.sqlite"
SERVICE = "codex-remote-control.service"
IDLE_MINUTES = 60


def claims() -> list[dict]:
    out = subprocess.run([sys.executable, str(CHECKER), "--json"],
                         capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout)["findings"]


def body_idle_minutes(thread_id: str) -> float | None:
    try:
        con = sqlite3.connect(f"file:{STATE}?mode=ro", uri=True)
        row = con.execute("select rollout_path from threads where id=?",
                          (thread_id,)).fetchone()
    except sqlite3.Error:
        return None
    if not row or not row[0]:
        return None
    p = Path(row[0])
    if not p.exists():
        return None
    return (time.time() - p.stat().st_mtime) / 60


def main() -> None:
    found = claims()
    daemon_held = [f for f in found if f["holder_kind"] == "background-daemon"]
    if not daemon_held:
        print(f"claims={len(found)} daemon-held=0; nothing to do")
        return

    ages = {}
    for f in daemon_held:
        idle = body_idle_minutes(f["thread"])
        ages[f["thread"][:13]] = idle
        if idle is None or idle < IDLE_MINUTES:
            print(f"daemon-held={len(daemon_held)} but {f['thread'][:13]} "
                  f"idle={idle if idle is None else round(idle, 1)}min "
                  f"< {IDLE_MINUTES}; standing down (possible turn in flight)")
            return

    print(f"daemon-held={len(daemon_held)} all idle >= {IDLE_MINUTES}min "
          f"{ {k: round(v, 1) for k, v in ages.items()} }; restarting {SERVICE}")
    subprocess.run(["systemctl", "--user", "restart", SERVICE],
                   check=True, timeout=120)
    time.sleep(20)
    after = [f for f in claims() if f["holder_kind"] == "background-daemon"]
    if after:
        print(f"WARNING: {len(after)} daemon claim(s) re-acquired after "
              f"restart; upstream behaviour has changed, do not escalate "
              f"automatically -- report to the operator")
    else:
        print("released; daemon running with 0 claims, remote still available")


if __name__ == "__main__":
    main()
