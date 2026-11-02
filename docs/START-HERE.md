<!-- redact: public copy; source sha256 7bcdf8db0314d22c847bf6c69272a6c6892b5b4a4685dd170a0e9f82983c96f5; rules 8; mode history; words 23; sessions 0 whole, 0 truncated; host paths 3; decisions 0 -->
# Start Here

You are new. This gets you oriented in about five minutes. Everything here is
a pointer; nothing here is authority.

Read this once, then read `DOCTRINE.md`. Do not treat this file as a substitute
for it.

---

## What this place is

A **session-health clinic**. Kevin runs roughly twenty-five long-lived AI
sessions — Codex and Claude Code — one per project. They accumulate context,
degrade, and eventually have to be migrated to fresh containers without losing
who they are. This repository is the method, the tools, and the evidence trail
for doing that safely.

The sessions themselves live **outside** this repo, in the provider stores
(`[host path 1]`, `[host path 2]`). Those files are evidence. **The
repository is canon.** When they disagree, the repository wins.

## The five files that matter

| file | what it is | when to read it |
|---|---|---|
| `DOCTRINE.md` | the canonical method | before touching any session file |
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
   (`[host path 3]`); prefer it over anything we invent.
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
[words sha256=4c2d68593c2ce7a71a2d1007ae7f34a2ca20d99fff80432568859cd1f0cd0e27]
  [words sha256=eeedfc43f3701127b1caa02bd474a41ba80d4517ee71a4e5f365c83a7fd8b64c]
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
[words sha256=706d1c8c16edd30aed3e1ffce552f2499fbc4c075557910c8847ad255726700c]

[words sha256=f96470fd1204502ee030a18077636fde501997b8158a747340a2dddb032fc8c9]
[words sha256=f2f27eba0d8bda4901c80153c1f40929ad6b29730e8210c5ac083b82ab367017]

[words sha256=4430268adcb657e0dfa2ca70eaefeaa6fe392b54979ac1c1d4028bcf5775bf6f]
[words sha256=b363cd7925ae8449f7def57661040a6790f44c3a31c379805b928acd61687168]
[words sha256=063b82a7178162714b405571bcf4bed4919015b9c460bf86c8694292818fd476]

[words sha256=bc499c0431957f1d5bdd7ab1a916effee732cc788052f5d6a50c776816e3dcd2]
[words sha256=95b0758d5d22d64e1934959155883271e4828493312c1d24b70d79b5461de75a]
[words sha256=d6b4ccfa490c5c3967eb27f2254c2ee40efccc8ed8b775830684e985bba8093d]

[words sha256=a1344b9e0433b388904998225595170bec0163e03e2188f8280eb9dd1ffb0392]
[words sha256=bb77e8c90f6c92818d39d26b55dcf33a7215af1e6522b3faf03878495244e1c3]
[words sha256=aeba1c569adebd2e9867cd2b3b614f7cc0f00139888884b8d433093db38d6e27]
[words sha256=9ead942577f038492cb54862b939e7996197b7054ce4bfb04de40d18ad8958fd]
[words sha256=6d69f2ac09017b8a49d050ab336e953b8fa02ae08c24396916ea7ea42418e627]
[words sha256=5b330b05cc88e640e6b0bdb8fa301f5ec4f0b3b8ce6ff28ee1c9b77b52aebe09]
[words sha256=353e0a82d88822e33f8c5c5a05ab62931e12e1e02596af9252b498b219c26e65]
[words sha256=4fc977703e08bc23d7a063f99feb25f619571cbed66f567c7e9eff26372df15b]
  [words sha256=265f35aab6d3448ad2c7b4393f65e7e9e490d94884b55c6e02fda534fc881a55]
[words sha256=f4894ffadb40d08a4b86d4dc1f97a9632168caa9f5f63329e211102d17dd7117]
[words sha256=8a331fdde7032f33a71e1b2e257d80166e348e00fcb17914f48bdb57a1c63007]
```

All of that is read-only. Run it freely. Nothing above writes.

## Where the authority sits

- **Kevin** owns objectives, priorities, and final acceptance. Nothing lands
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
"[words sha256=bd21059c22fa488ea479988481bacae55126333d4f70fc0d57d1e224dc02cbbb]" pile is usually a category you have not learned yet, not
garbage. Sweep it and the evidence is gone; name it and the system gets more
honest.**

## What to do when you are unsure

Stop and ask. Every irreversible operation in this house has a gate in front of
it, and the gates exist because someone once found out the hard way. If a gate
refuses you, it is probably right. Do not route around it — understand it
first.
