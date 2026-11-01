<!-- redact: public copy; source sha256 fdf0fd95539793ac66e7ef33f611a7044f07192ebbb9b29d7c5d727bbe8d5669; rules 8; mode history; words 22; sessions 0 whole, 0 truncated; host paths 3; decisions 0 -->
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
   change gets one in `Receipts/`. Quantitative, including what failed and
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

`Scripts/inventory_worker_threads.py` classifies the store. Run it before any
cleanup. `unknown` should read `0`; if it does not, a session shape exists that
the model has not learned yet.

## Your first hour, in order

```bash
[words sha256=706d1c8c16edd30aed3e1ffce552f2499fbc4c075557910c8847ad255726700c]

[words sha256=f96470fd1204502ee030a18077636fde501997b8158a747340a2dddb032fc8c9]
[words sha256=59efc0bf024732c7b177d0ead65761754ba2e150eba052054ff2b1f4c475b757]

[words sha256=4430268adcb657e0dfa2ca70eaefeaa6fe392b54979ac1c1d4028bcf5775bf6f]
[words sha256=b1225184a53ed5858139ff2235c08ea73b14864b4b2f24b1a391cd846ca521f6]
[words sha256=8e22f4b800dd029dfb1915a00e50e5e7561cedfc4894ab7125f3e557c60d88ea]

[words sha256=bc499c0431957f1d5bdd7ab1a916effee732cc788052f5d6a50c776816e3dcd2]
[words sha256=ff61742917c5f25d107f15d052bc7ddaafbbcaad2ff1b9abec629584d5be011a]
[words sha256=82f527fcaa51c8eda46023491a0a3faaebcecbacf91a8a89d3eafda287b04953]

[words sha256=5f7c95a68f00eda8adc42e83ba81a4b36ec07960d95e3fd15550e3dbc1e12118]
[words sha256=f34026aeac66ab918465861077903a0cb46fe10991d49e60cd4322df64a55233]
[words sha256=9ead942577f038492cb54862b939e7996197b7054ce4bfb04de40d18ad8958fd]
[words sha256=6d69f2ac09017b8a49d050ab336e953b8fa02ae08c24396916ea7ea42418e627]
[words sha256=5b330b05cc88e640e6b0bdb8fa301f5ec4f0b3b8ce6ff28ee1c9b77b52aebe09]
[words sha256=353e0a82d88822e33f8c5c5a05ab62931e12e1e02596af9252b498b219c26e65]
[words sha256=688e42cd6e27533e360cbff37b06b7cb9c6675148b97cec5fe8abf29428cae14]
  [words sha256=e20718d7928c801abad30c69546ea3dfb7f6fa7a732ea8b801436213547a4954]
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
`Receipts/worker-thread-doctrine-20260731.md`. Seventeen worker threads had
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
