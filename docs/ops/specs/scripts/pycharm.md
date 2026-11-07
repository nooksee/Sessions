# Technical Specification: pycharm

Script: `Sessions/ops/lib/scripts/pycharm.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident; chats-file edit writer: Claude (Opus 5.5), a worker started by the Session Continuity Manager (`session-doctor`) on 2026-11-02; not a registered resident). Tests: `Sessions/tools/test/test_pycharm.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: **retired from routine use on 2026-11-07,** the source, its tests and the host's chats file kept. Ported on 2026-11-01 from `Scripts/reconcile_pycharm_ai_surfaces.py`, which this tree no longer holds; built as it was, 0 edit(s) at the port and 2 edits since (2026-11-02, and the live folder rule of 2026-11-06), listed below; no reviewer named, since it is not relied on. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Reconcile known PyCharm AI-session surface residue without touching JSONL bodies." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/session-control-reconciliation-20260714.md` (2026-07-14); 1 receipt(s) name it in all.

## Retired from routine use

This is a validator of one past migration, not a check of the IDE's health. Its pending and reconciled states each need exactly 1 verification of one historical chat, so with that chat gone both are false and it exits nonzero with `protocol_deviations=1`, even when every retired target is already absent and nothing would change. Its 2026-11-06 reading of 0 verified and 19 retired is that case. **A nonzero exit here says nothing about today's IDE. Do not read it as a finding, and do not weaken the refusal to obtain exit 0.** Use `identity.py` and the rooms' own readers for the IDE.

By the Apprentice's read of 2026-11-07 (`storage/handoff/joe.md`, "Queue job 3 return and claim release"), the inspected user services and timers and Control's tracked routes hold no executable caller of it. Hidden or manual callers were not inventoried. A new reconciliation needs its own operation defined first, its own review, and its own go; this tool is not the way back to one. Inverse of the retirement: revert this text through the owning Git route. Control's frozen copy, if any change is wanted, is Control's.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/reconcile_pycharm_ai_surfaces.py` (sha256 `3c666f747d3684ce30b711b15f476168ee6fa19b93cfb99f55ac09e157970111`) was copied to `ops/lib/scripts/pycharm.py` on 2026-11-01 with 0 edit(s): none. One edit since, on 2026-11-02: the 20 IDE chat identifiers (`GEORGE_VI_CHAT`, `TEMP_OSAI_CHAT`, `LEGACY_CLAUDE_CHAT` and the 17 `SHELL_ONLY_STUBS`) left the code for the chats file in item 4. With that file holding the same values, the behavior is unchanged, and the retired task identifiers keep the same order.
2. Command line: `python3 -I -B ops/lib/scripts/pycharm.py`. Options as the script declares them:
   - `--workspace-dir`: default `workspace` in the live settings folder
   - `--task-history`: default `aia-task-history` in the live settings folder
   - `--osai-workspace`: (no help text in the script)
   - `--control-workspace`: (no help text in the script)
   - `--preview-dir`: (no help text in the script)
   - `--apply`: (no help text in the script)
   - `--custody-dir`: (no help text in the script)
   - `--chats`: the chats file of IDE chat identifiers (default: ops/etc/pycharm-chats.json in the room)
3. Reads and writes: as the docstring states (1228 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write. The 2026-11-02 edit added one read, the chats file, which comes before every other read.
4. The live settings folder (2026-11-06). The tool pinned `PyCharm2026.1` until the update to 2026.3 left that folder two versions behind, with `--apply` aimed at it by default. Now each of the two options above that is not given takes its folder from the live settings folder, by the rule of `identity.py`, loaded from beside this file: the highest `PyCharm<year>.<n>` under `~/.config/JetBrains`, by number. With no such folder, or two that read as the same version, the tool refuses with one message and a nonzero exit, after the chats file and before anything else. Given both options, it reads no folder for this. `Control-Runtime/Scripts/reconcile_pycharm_ai_surfaces.py` line 51 carries the same pin; that copy is Control's, reported and not touched. The guard before an apply knows a running IDE by its resolved executable, `pycharm` or `pycharm.sh`, or `java` with the IDE's main class, including one that reads as deleted after an update in place; no version stands in that rule, and a command line that only mentions the IDE is not the IDE.
5. The chats file. The tool resolves the room from its own location, three folders above `ops/lib/scripts/`, as `gauge` and `myself` do, and reads `ops/etc/pycharm-chats.json` there unless `--chats` names another path. The file is host data: `.gitignore` ignores `/ops/etc/*.json`, so the file never enters Git, and no identifier it holds is written in this tree. It is one JSON object with exactly four keys: `george_vi_chat`, `temp_osai_chat` and `legacy_claude_chat`, each a string, and `shell_only_stubs`, a list of strings. Every value is a 36-character lowercase hyphenated hex identifier (groups of 8, 4, 4, 4 and 12), and no value appears twice, within the list or across keys. The retired task identifiers are derived in this order: the stubs in file order, then `temp_osai_chat`, then `legacy_claude_chat`. `george_vi_chat` is repaired and never retired.
6. Refusal. The tool loads the chats file first, after parsing its arguments. When the file is absent, unreadable, not UTF-8 text or not valid JSON, when it holds anything but an object, lacks a key, has an extra key or repeats a key, when a value has the wrong type or is not such an identifier, or when an identifier appears twice, the tool prints one line to standard error and exits with status 1. The line reads `pycharm.py refuses: the chats file <path> <fault>. Nothing else was read or written.` The fault names the key or list position and never the value. The refusal comes before the tool reads `/proc`, the task history or any workspace file, and before it writes anything.

## Anecdotal Anchor

`Receipts/session-control-reconciliation-20260714.md` is the earliest of 1 receipt(s) naming `reconcile_pycharm_ai_surfaces.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Reconcile known PyCharm AI-session surface residue without touching JSONL bodies." "The default mode is read-only." "This tool deliberately does not archive, delete, move, or rewrite Codex or Claude JSONL files."
- The earlier statement here, that the rounds timer and Control CI call the legacy path, is not supported by the Apprentice's read of the current routes. Control's frozen `Control-Runtime/Scripts/README.md` still mentions that path, as documentation.
- The loader proves the form of the chats file, not that its identifiers are the right ones. The existing pending and reconciled checks remain the guard on content: a `george_vi_chat` that matches no chat leaves `george_vi_verified` at 0, and the tool stops with `protocol_deviations` 1 before any write.
- The host's `ops/etc/pycharm-chats.json` is installed, mode 0600, and stays; the tool still refuses without it.
- Not to be relied on: retired above. Its reader in `identity.py`'s shared folder rule runs the other way, `pycharm.py` importing `identity.py`, so the retirement moves no rule there.
