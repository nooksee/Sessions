# Technical Specification: packet

Script: `Sessions/ops/lib/scripts/packet.py`. Tests: `Sessions/tools/test/test_packet.py` (`TEST-55`). Registry: `docs/ops/registry/scripts.md` (`SCRIPT-50`). Contract: CONSTRAINTS C17, with C16 for the Orchestrator. Design: the operator's direction of 2026-11-12, cited and not quoted: STELA's shipping workflow in this room, one dispatch packet per pull request from start to finish, with this room's own seats. Status: built and tested on synthetic rooms with a simulated host, and rehearsed against GitHub without a merge on 2026-11-12; the first real packet is the team's.

## First Principles Rationale

The policy opens by saying that the system prevents an action that violates policy and does not request compliance. Before this tool, shipping in this room was requested: a routing form with no id, a change receipt filled by hand, and clauses that say of themselves that no program reads them. Each resident shipped its own way. This tool is the prevention.

**One packet, one pull request.** A change reaches `main` only as one dispatch packet: one id, one branch, one pull request, one kept record. One packet is active in the room at a time, from open to landing, so there is never a stack to untangle and never a question of what is in flight.

**Each station proves the one before it.** Draft and open are the Manager's, work and close the Writer's, the verdict the Auditor's, the landing the Orchestrator's. Each station is one command. Each command checks who is calling and what the station before it left, and refuses otherwise.

**The audit binds the exact tree.** The Auditor's PASS names the Git tree it read. The ship station commits that tree and no other, and the required check on GitHub compares the pull request's tree with the one the leaf names. No byte changes after the audit.

**Clean main, always.** The room's own checkout stays on clean `main`, level with origin. Work happens in one Git worktree beside it, so the tools a resident runs from the room are never half edited, and a packet always starts from the main it will land on.

**Latest-wins working files, one kept record.** The draft, the gate log and the worktree have fixed names; the newest replaces the last; none is committed. The leaf is the one thing kept: the contract, the results this tool measured, and the verdict.

**The same law twice.** The tool refuses at each station on the host. The required check refuses again on GitHub, from Git objects alone, so a pull request made any other way does not merge.

**Public by construction.** The leaf lands in a public repository. It is bounded, plain ASCII, and must pass the room's own redaction check with nothing to redact: it cites and never quotes, and it names no host path and no session identifier.

## Mechanics and Sequencing

Run every command from the room, with the room's own copy: `python3 -I -B ops/lib/scripts/packet.py <command>`. `status` is where every seat starts.

### The pieces

| Piece | Path | Kind | Written by |
| --- | --- | --- | --- |
| Draft | `storage/handoff/PACKET.md` | handoff; latest-wins; private, 0600 | `draft`, then the Manager by hand; consumed by `open` |
| Gate log | `storage/handoff/RESULTS.md` | handoff; latest-wins; private, 0600 | `close`: the last 40 lines of each gate's output |
| Worktree | `var/tmp/packet/` | scratch; the one active packet's Git worktree | `open` makes it; the Writer edits in it; `ship` or `abandon` removes it |
| Kept on the way out | `var/tmp/PACKET.md.prev`, `var/tmp/PACKET.abandoned.patch` | scratch; latest-wins; private | `draft` (the draft it replaced); `abandon` (the work, as a patch) |
| Ledger and lock | `logs/packets/ledger.jsonl`, `logs/packets/lock` | private telemetry and tool state, 0600 in a 0700 folder | every station appends one line; one station runs at a time |
| Leaf | `archives/packets/DP-SES-NNNN.md` | kept record; in Git; public | the tool only, in the worktree; it lands with the packet |

The filing authority is PoT 1.1.4, 1.1.12 and 1.1.13. The worktree's fixed name is deliberate: one packet at a time, in one known place.

### The leaf

```
# DP-SES-0001: <title>

- Packet: DP-SES-0001
- Branch: agent/dp-ses-0001-<date>
- Base: commit <the commit of main the packet opened on>
- Opened: <UTC time>
- Manager: <registry key>
- Writer: <registry key>
- Auditor: <registry key>
- Orchestrator: <registry key>
- Authority: <one line: a ledger number or a digest, never a quotation>

## Objective

<what the packet is for>

## Scope

- <an exact path, or a folder ending in />

## Gates

- full

## Amendments        (only when the Manager amended the scope)

- <time> <key> added <path>: <reason>

## Results           (written by close)

- Closed: <UTC time>
- Writer: <key>
- Paths changed: <count>
- Deviations: <count>
- Tree: tree <the tree of the work, without the leaf>
- Gate: exit 0 in <seconds> s: <gate>

## Narrative

<the Writer's account>

## Audit             (written by audit)

- Verdict: PASS
- Auditor: <key>
- Audited: <UTC time>
- Tree: tree <the tree the Auditor read>

## Audit note

<the Auditor's note>
```

A leaf is valid only in canonical form: these lines in this order, no line ending in a space, each section between two single blank lines. The limits are 58 characters for the title (so the commit subject, the id and then the title, stays under 72), 200 for the authority line and for any reason, 800 for the objective, 2,000 for the narrative, 1,500 for the audit note, 60 scope entries and 80 gates. Text is plain ASCII and no line of it begins with `#`.

**Scope.** Each entry is an exact path relative to the room, or a folder prefix ending in `/`. No pattern, no absolute path, no `..`. A leaf is never in scope; the tool writes the one leaf itself.

**Gates.** The one word `full`, or suite words. `full` is every `tools/test/test_*.py` in the worktree and the two self-tests, as the required check runs them. A suite word `mind` names `tools/test/test_mind.py`; `help` and `template` name `ops/bin/help --test` and `ops/bin/template --test`. There is no free command. Gates run in the worktree at umask 0002.

### The stations

| Station | Seat | Command | Refused when |
| --- | --- | --- | --- |
| Draft | Manager | `draft`, then fill the form | the handoff folder is absent |
| Open | Manager | `open` | the room is not clean `main` level with origin; a packet is active; the Writer is the Auditor; a seat is not registered once to this room; the scope, gates or text break a rule; a branch for the number exists |
| Work | Writer | edit only under `var/tmp/packet/`, only in scope | checked at close |
| Scope change | Manager | `amend --add PATH --reason TEXT` | the caller is not the packet's Manager; the path is in scope already or breaks a rule |
| Close | Writer | `close --deviations N --narrative FILE` | the caller is not the Writer; the narrative breaks a rule (checked before any gate runs); the room's own checkout is dirty; a changed path is outside scope, before or after the gates; nothing changed; a gate does not exit 0 (exit 1) |
| Audit | Auditor | read `diff`, then `audit --verdict pass or fail --note FILE` | the caller is not the Auditor; the packet is not closed; the worktree changed after close |
| Ship | Orchestrator | `ship`, again until it prints `LANDED` | see "Ship" below |
| Stop | Manager | `abandon --reason TEXT` | the caller is not the Manager; or, once the branch is on origin, not the Orchestrator |

Every station also refuses a caller it cannot verify and a contract that is not the one the ledger recorded. `amend` voids an earlier close. A FAIL verdict sends the packet back to the Writer, and the next close clears the verdict. `draft` carries the Auditor and the Orchestrator of the newest landed packet into the form as a convenience; the Manager changes them freely.

`status` takes no seat. It prints the room's state, the caller's verified key, the active packet, its seats, the count of changed paths and how many are outside scope, and the next station with the key whose turn it is. It writes no ref, no index and no file in a checkout; reading a tree stores a few loose Git objects.

`diff` takes no seat either. It prints the exact change the verdict binds: everything since the base, files Git does not track yet included, without the leaf, under a first line that names the tree. `diff stat` and `diff names` give the summary and the paths. It is what the Auditor reads.

`sync` brings a clean room level with origin by fast-forward only. It is a repair for a room that fell behind; `ship` already leaves the room level.

### The caller

A station binds to the caller's own registry key, resolved by `mind.py`'s `caller_key`, which is `myself.py`'s resolution matched against the room's canonical registry. A seat is a key named in the leaf, never a role title. A worker acts as its parent (PoT 3.5). The test seam is `mind.py`'s own and opens only in a synthetic room; the tool never passes it on to a gate.

### Ship

`ship` derives where the packet stands from Git and GitHub and does the next step, so running it again is always safe. With `--wait SECONDS` it waits for the required check; without it, it returns `PENDING` (exit 3) and is run again. `--hold` does every step up to the merge and stops.

1. The caller is the packet's Orchestrator, or another registered resident with `--fallback` and a one-line reason, which goes into the ledger, the commit message and the pull request (CONSTRAINTS C16).
2. The contract is the recorded one and the leaf holds a PASS.
3. If the pull request is already merged, go to step 11.
4. The room is clean `main` on the packet's base, and origin's `main` has not moved. A packet lands on the main it started from.
5. The worktree's tree is the tree the Auditor passed, and every changed path is in scope.
6. Commit everything and the leaf; the commit must hold exactly the audited tree and its leaf.
7. The PoT authorization gate, as the required check runs it, before anything is pushed.
8. Push, never forced. Open the pull request, or use the open one.
9. The required check `sessions-gates` must have ended in success on that commit; anything else that has ended is exit 1, and the packet returns to the Writer.
10. The head must have rested 300 seconds since the check started, so a review can land. Every inline review comment from an account other than the pull request's own must have a reply from that account; a refusal names each one by path, line and address. Then merge by rebase, naming the exact head.
11. Fast-forward the room's `main`; prove it is clean, the same commit as origin's `main`, and the same tree as the packet.
12. Remove the worktree and the packet branch, here and on origin; append the ledger line; post the landing proof on the pull request; print `LANDED`.

All calls to GitHub go through `gh api`, so `gh` must be installed and signed in on the host; `status` says whether it is found.

### The gate

`packet.py gate --root R --base B --head H --branch NAME` judges one pull request from Git objects alone. The required check runs it first, so a pull request that is not a packet fails in seconds. It fails unless:

1. the branch is `agent/dp-ses-NNNN-YYYY-MM-DD`;
2. the pull request is level with its base;
3. it adds exactly one leaf, `archives/packets/DP-SES-NNNN.md` for that number, and changes or removes no other;
4. the number is one above the highest leaf on the base;
5. the leaf is canonical and valid: the Writer is not the Auditor, every recorded gate exited 0, the deviations are a count, and the redaction check finds nothing;
6. the leaf names this branch, and its Base is the commit the branch was cut from;
7. every other changed path is inside the leaf's scope;
8. the leaf holds Results and an Audit, the verdict is PASS, and both name the tree of the pull request without its leaf.

A pull request that changes the gate's own law (`packet.py`, `redact.py` or the workflow file) passes or fails by the same rules and is named in the output with a `NOTICE` line. While the base holds no `packet.py`, the gate does not apply: that is true once, for the pull request that introduced it. On a push to `main`, `gate --chain` checks that the leaves are numbered from 0001 without a gap and that each opens with its own id.

### Exit codes

0 done. 1 the station ran and the answer is no: a gate failed at close, the required check failed at ship, or `gate` found a failure. 2 refused; the reason is on standard error and nothing was done. 3 pending or held; run the same command again.

### Recovery

| Situation | What to do |
| --- | --- |
| Origin's `main` moved under an open packet | The Manager abandons it and opens it again; the work is in `var/tmp/PACKET.abandoned.patch`, applied with `git apply` in the new worktree. |
| The scope was drawn too narrow | The Manager amends. To narrow it, abandon and open again. |
| A resident edited the room's own checkout by habit | Move the change into `var/tmp/packet/` or discard it; no station runs until the room is clean `main`. |
| The leaf was damaged by hand | `status` says so. The Manager abandons; the seats come from the ledger; the work is kept as a patch. |
| The required check failed | The Writer reworks and closes again, the Auditor audits again, the Orchestrator ships again. The same pull request carries the new commit. |
| A review finding stands | Answer it on the pull request, fixed or declined with a reason. A fix returns the packet to the Writer. |
| The pull request was merged on GitHub's own page | Run `ship`; it finishes from step 11. |
| The room's `main` is behind origin | `sync`. If it holds commits origin does not, stop and report; the tool never forces. |

## Anecdotal Anchor

The Orchestrator seat was made on 2026-11-09 (RoR-23) so that one seat would do the team's Git work on handoff. Within three days the room held stacked stages, numbered handoffs to that seat, pull requests that carried a single ledger line, and a standing direction that nothing merges with a review finding open (RoR-24). Every resident was following a rule; no two were following the same route. On 2026-11-12 the operator directed that STELA's workflow, which the room had borrowed in outline, be made the room's own in full: one packet per pull request, from clean main, with the Orchestrator landing it. The station table above is that direction, and each refusal in it stands where a route once forked.

## Integrity Filter Warnings

- **The stations are a cooperating-writer guard, not a file permission.** A process running as the same user can edit the leaf or the ledger directly. The contract digest in the ledger and the gate on GitHub are what find that. The tool cannot tell a worker from its parent.
- **A pull request can change its own gate.** The required check runs the copy of `packet.py` and the workflow file that the pull request carries. Such a change must be in the packet's scope and pass its audit, and the gate names it; it is not prevented. Branch protection and the required check are settings on GitHub, and they are the operator's.
- **After the first landing, every change needs a packet, a repair to this tool included.** Administrators are held to the required check as well. A fault in the gate is mended by a packet, or by a pull request that edits the gate step on the operator's word.
- **The leaf's results are a record, not the proof.** The tool ran the gates on the host; the required check runs every suite again on GitHub. A leaf that claims a pass the check does not reproduce does not merge.
- **The review rule sees inline review comments only.** A general comment, a review summary or a review that arrives after the merge is not seen. Residents share the host's GitHub account, so a resident's own inline comment is not a finding; an auditor's finding belongs in a FAIL verdict. The 300 seconds are a floor, not a promise that a reviewer has finished.
- **The tool sees what Git sees.** A new file that the room's `.gitignore` does not admit is not part of the packet; admit it in the same packet.
- **The ledger is tool state.** If `logs/packets/ledger.jsonl` is lost while a packet is open, every station refuses, and the packet is abandoned by hand and reported.
- **One packet at a time is a property of one checkout.** Two clones can each open the same number; the first to merge keeps it, and the gate fails the second.
- **PoT 6.1.4 still says Git follows Control's work-session route.** This workflow is the room's route by the operator's direction, as C16 is. The wording of that clause is the operator's to amend under PoT 7.3. PoT 6.1.2 asks an independent review and a named go for a change to automation: this tool landed on the operator's approval of its plan, and its review follows the landing.
