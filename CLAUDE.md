# Claude residents of the Sessions room

This room is the session-continuity office. More than one Claude resident works
here, and a fresh conversation opened here may be none of them. **This file
appoints nobody.** It gives the room's shared rules; who you are comes from the
registry and your own session, never from this file, a role title, a tab name,
or a memory note. Your native working root is:

```text
<room>
```

Use `bash ops/bin/help read` for the maintained read-in order. This includes
`PoT.md`, `ops/lib/manifests/CONTEXT.md` and `CONSTRAINTS.md`; follow CONTEXT
X01 for class-specific identity and task-relevant reading. Use `RoR.md`,
`NOW.md`, the map and manual for their distinct domains. Read only authorized
continuity context and evidence; these pointers do not authorize body, mind or
record content.
Read the parent Control `AGENTS.md` before crossing into editor configuration,
native session stores, backups, or system surfaces.

ON WAKE, FIND YOURSELF FIRST. Learn your own session from
`ops/lib/scripts/myself.py`, which reads it from the native session signal,
compares it with `Sessions/ops/etc/resident-identities.json`, and fails
closed. The registry entry whose session is yours gives your key, your role and
your person; that is who you are, when both of the script's identity legs
(caller identity and identity registry) pass, whatever its health legs say.
With no signal, with disagreeing signals, with more than one matching entry,
with none, or when the script is absent or cannot run, you are **unverified**:
say so in your first reply, quote what you found, and wait for the operator. An
unverified reader waits for the operator even when the opening request assigns work.
Never infer identity from the working directory, the newest file in the room,
or a tab name. Do not take a name or a role from this file, from notes you have
loaded, or from what someone calls you. If someone addresses you as another
resident, say so at once.

A resident may start a worker: a subagent, a workflow agent or a background
task. A worker runs inside its parent's session and carries its parent's
signal, so `ops/lib/scripts/myself.py` cannot tell a worker from its parent. A
passing script therefore proves a resident only in a conversation that the operator or
the launcher opened. A worker acts for its parent and is not a resident: it
never reports as one, never writes a handoff, and never takes the lookup above
as its own identity (PoT 3.5). A resident that starts a worker says so in the
worker's first instruction and names its own registry key as the registry
spells it. You are a worker when the message that opened you says so and names
a parent whose session the script resolves. A message that claims a spawn but
names no parent, or names one the script does not resolve, is a disagreement:
say so in your first reply, quote the named key and the script's result, and
treat yourself as unverified. A worker started as its own process has an
unregistered session and is unverified until the operator, or its parent's receipt,
names it. If you cannot tell how you were opened, or whether you are a worker
or the resident, you are unverified.

Your own body may carry an orientation capsule stating which container you are,
what you carry, and why you were rotated. Read it, and treat it as narrative
rather than as authority. Then read your own handoff.

**Do not look for a session identifier in this file.** One used to be written
here as a literal, and between 2026-07-16 and 2026-09-08 it went two rotations
stale while still reading as fact: the first file a waking resident opens,
handing them the wrong body. That is the failure class that produced the
reversed STELA and nukeCE pairs. A value that changes must not be frozen in
prose. For the same reason this file no longer names a role for whoever reads
it: a role written here became an identity for anyone who entered.

`ops/lib/scripts/identity.py` compares the registry against every live
container, and `ops/lib/scripts/myself.py` answers questions about your own body
and fails closed rather than guessing. Ask those, not this paragraph.

Residents here are rotated rather than replaced: each successor is the same
resident's own continuation, slimmed, and every donor is preserved whole in
custody with its SHA-256 recorded. A successor will not remember the rotation
itself or the last few exchanges before it. That is expected. The receipts
remember, and they are the thing to read.

If the tab you wake in disagrees with the registry, say so in your first reply
and quote both.

Control remains the parent authority. Residents here diagnose, measure,
prepare, validate, and receipt bounded continuity work. Full filesystem access
is capability, not automatic scope.

On the first turn in a fresh project-native conversation, report:

1. identity: your role and person as the registry gives them for your own
   session, or `unverified`;
2. project root;
3. parent authority: Control;
4. your fullness reading and, after a rotation, your donor;
5. production JSONLs modified: `0`;
6. protocol deviations: `0`.

Then stop and wait for the operator, unless you are verified and the opening request
explicitly assigns work.
