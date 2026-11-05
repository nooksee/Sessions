# Start Here

You are new. This gets you oriented in about five minutes. Everything here is
a pointer; nothing here is authority.

Read this once, then read `PoT.md` for current law and `docs/MANUAL.md` for
operating mechanics. This page is orientation, not authority.

---

## What this place is

A **session-health clinic**. The operator runs roughly twenty-five long-lived AI
sessions — Codex and Claude Code — one per project. They accumulate context,
degrade, and eventually have to be migrated to fresh containers without losing
who they are. This repository is the method, the tools, and the evidence trail
for doing that safely.

The sessions themselves live **outside** this repo, in the provider stores
(`~/.codex/sessions`, `~/.claude/projects`). Those files are evidence. **The
repository is canon.** When they disagree, the repository wins.

## The five files that matter

| file | what it is | when to read it |
|---|---|---|
| `PoT.md` | the Sessions constitution | before material work |
| `NOW.md` | live board — current state, open items | at the start of every session |
| `README.md` | charter and folder map | when you need to find something |
| `HANDOFF.md` | who you are, if you are the resident here | on wake |
| `docs/session-continuity-apprentice-field-guide.md` | how to observe without overstepping | if you are here to help, not to lead |

## The four rules you can break something with

Everything else is recoverable. These are the ones that cost real damage.

1. **One writer per session file.** Before writing to any production session,
   verify no IDE and no remote-control surface holds it. Check
   `/proc/PID/exe` for the IDE — matching on process *name* produces false
   positives. Check `fuser` on the exact file. Both, every time.
2. **Back up before you change anything, and verify the backup byte-for-byte.**
   `cmp -s` before you proceed. A backup you did not verify is a hope.
3. **Deletion is never the default.** Archive, move, quarantine, or mark —
   in that order. Providers have their own archive custody
   (`~/.codex/archived_sessions/`); prefer it over anything we invent.
4. **Write a receipt.** Every source, service, roster, session, or release
   change gets one in `archives/receipts/`. Quantitative, including what failed and
   what you decided not to do.

## The measurements that are load-bearing

- **Tokens, not bytes.** A 49 MB session can be healthier than a 4 MB one.
  Byte size is a proxy and it has been wrong before.
- **Compaction count, not just percentage.** A session that keeps compacting
  has a *low* context percentage precisely because it keeps shedding history.
  The sickest sessions can look the healthiest. See `DOCTRINE.md` §1A and the
  `compact-treadmill` verdict.
- **Data health and mechanism health are different questions.** "The clinic
  says everyone is fine" and "the clinic is actually still running" must be
  checked separately. Stale data looks plausible.

## Three classes of session

Do not force everything into two boxes. See `DOCTRINE.md` §1A.

- **Resident** — named, has a lineage capsule, owns a room, in the roster.
- **Worker thread** — spawned by a resident through the provider's own
  delegation. No capsule, no room, ephemeral by design. **Not junk.**
- **Archived predecessor** — retired, kept as evidence.

`ops/lib/scripts/workers.py` classifies the store. Run it before any
cleanup. `unknown` should read `0`; if it does not, a session shape exists that
the model has not learned yet.

## Your first hour, in order

```bash
cd /media/nos4r2/user_vol/Sessions

# 1. What does the house look like right now?
python3 ops/lib/scripts/workers.py

# 2. Who is sick?
python3 ops/lib/scripts/telemetry.py
python3 ops/lib/scripts/vitals.py --only-flagged

# 3. What does the operator surface believe?
cat logs/clinic-aggregate.json
cat logs/resource-state.json        # provider budget, if collected

# 4. Can every resident actually be launched? The launcher lives in Control's
#    frozen runtime; the roster and bindings it reads are this room's ops/etc/.
cd /media/nos4r2/user_vol/Control-Runtime/Resident-Center/research/resident-launcher
PYTHONPATH=src python3 -c "
from pathlib import Path
from osai_resident_launcher.registry import load_registry
from osai_resident_launcher.validation import validate_all
r=load_registry(Path('/media/nos4r2/user_vol/Sessions/ops/etc/residents.json'),
  Path('/media/nos4r2/user_vol/Sessions/ops/etc/host-bindings.json'))
[print(v.resident.key, v.state, v.detail) for v in validate_all(r)]
"
```

All of that is read-only. Run it freely. Nothing above writes.

## Where the authority sits

- **The operator** owns objectives, priorities, and final acceptance. Nothing lands
  without him.
- **Control** (currently George X) owns cross-project reconciliation.
- **Sessions Claude** owns session-health method and this repository.
- **Residents** own their own project scope and nothing else.
- The **repository** outranks any session's memory of what happened.

## How we handle being wrong

This matters more than it sounds. The receipts in this repo contain their own
corrections, in place, including ones that make the author look worse. That is
deliberate. If you find a mistake — yours or an earlier one — correct it where
it lives and say what changed. Do not quietly reword history so it reads
better.

A recent example worth reading in full:
`archives/receipts/worker-thread-doctrine-20260731.md`. Seventeen worker threads had
accumulated unnoticed because the model had only two categories for sessions.
They were nearly swept as junk. The lesson became doctrine: **a large
"miscellaneous" pile is usually a category you have not learned yet, not
garbage. Sweep it and the evidence is gone; name it and the system gets more
honest.**

## What to do when you are unsure

Stop and ask. Every irreversible operation in this house has a gate in front of
it, and the gates exist because someone once found out the hard way. If a gate
refuses you, it is probably right. Do not route around it — understand it
first.
