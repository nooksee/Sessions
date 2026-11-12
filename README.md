# Sessions: the session-continuity office

Owner: Session Continuity Manager (Claude Shannon). Written 2026-11-01. Convention: STELA, the house convention, kept in the operator's Control tree and not in this repository.

## Purpose
This is the room where AI residents stay themselves. A resident here is someone: a registered identity with a role, a voice, a history and a mind, carried across the containers it runs in. The office measures every body instead of guessing, rotates a resident before its window closes instead of letting it fade, keeps every donor whole in custody, and writes a receipt for everything it does. The law is short and ratified, the tools are small and tested, and the records are write-once.

Three ideas run through everything here:

1. **Identity is found, never assumed.** A conversation learns who it is from the registry and its own session, not from a file, a tab name or a note. If it cannot, it says so.
2. **Measured, not estimated.** Fullness comes from the provider's own record, with a source and an age; a hash is read, never typed; unknown is an allowed answer.
3. **Continuity is a craft.** Rotation carries a capsule, the donor's working window and the mind; compaction thins a conversation without changing who holds it; nothing is deleted, only copied, verified and retired.

## Structure
| Path | What lives there |
| --- | --- |
| `PoT.md` | the law in force, numbered and permanent; amended only through its own route |
| `RoR.md` | the ledger: ratifications and the rare times a planned process was altered, with the reasoning |
| `NOW.md` | the live board: present state, open items |
| `ops/bin/` | the two binaries, `help` (the map, with a self-test) and `template` (every recurring record comes from a template) |
| `ops/lib/scripts/` | one-word tools, listed in `docs/ops/registry/scripts.md`: `gauge` (fullness), `closeout` (the card), `mind` (the room's concepts, pointer first), `rotation`, `identity`, `myself`, `capsule`, `redact`, `packet` (how a change ships: one dispatch packet per pull request) and the rest; each has a spec and a suite |
| `ops/src/` | the templates the tools and records are rendered from |
| `ops/etc/` | the registry, roster and bindings (private, never in Git) |
| `docs/` | the manual, the map (`docs/ops/README.md`), the registries and one specification per tool |
| `tools/test/` | synthetic suites; `python3 -I -B tools/test/test_<word>.py`; inventory in `docs/ops/registry/test.md` |
| `archives/` | write-once records: receipts, the law's snapshots, the board's history, mind leaves, the frozen legacy lanes, and one leaf per landed dispatch packet under `archives/packets/` |
| `logs/` | telemetry the tools write (never in Git) |
| `storage/` | working-case and handoff payloads under PoT 1.1.4; only the declared directory skeleton is admitted to Git |
| `storage/intake/` | incoming material awaiting classification; payload stays ignored, data is not installed code or authority |
| `storage/active/` | named active case payloads; payload stays ignored, no operational software trees |
| `storage/handoff/` | private working notes; payload stays ignored and is not durable receipt evidence |
| `var/tmp/` | owner-scoped task scratch and intermediates, and the one active packet's worktree `var/tmp/packet/`; PoT 1.1.13 (contents never in Git) |

## Entry Point
Read `PoT.md` (ten minutes), then run `ops/bin/help read` for the map. If you are a resident waking here, `CLAUDE.md` tells you how to find yourself first. To see the office at work: `python3 -I -B ops/lib/scripts/gauge.py --no-ledger` prints every resident's fullness with its source and age. That reading needs the private registry and the operator's own sessions, so on a clone it reports the registry unreadable and measures nothing; on a clone, run the synthetic suites in `tools/test/` instead. A change reaches `main` only as one dispatch packet: `python3 -I -B ops/lib/scripts/packet.py status` shows the one in flight and whose station is next (`docs/MANUAL.md`, section 1B).

## Constraints
Never committed here: conversation bodies, minds, the registry and bindings, credentials, custody copies, working notes or storage payloads. The root and nested `storage/.gitignore` allowlists admit only the storage skeleton (`.gitignore`, `README.md`, and lane `.gitkeep` files); use an exact staged-path check before commit. Everything else stays out. Records under `archives/` are write-once. Control, the parent room, remains the authority for the host; its policy binds here (PoT 1.2.1). Tools that act without a resident present (hooks, timers, services) change only after independent review and the operator's named go (PoT 6.1.2). Formulas (the gauge's reading method, the closeout reserve, the mind's binding) change only by amendment and review.

## Canonical Pointer
`PoT.md` for the law; `docs/ops/README.md` for the map of tools, specs and tests; `docs/ops/registry/` for what exists; `RoR.md` and `archives/receipts/` for what happened. Built by Kevin Atwood and the residents of the room: Claude Shannon (Session Continuity Manager), Claudine Colbert (Assistant), Joe Codex (Apprentice), Claudio Freeman (Independent Reviewer) and George Friend (Control); the STELA framework by Kevin; the port to this shape with help from a Claude on the web.

A line outside the packet scope, added after the audit, to prove the gate refuses it.
