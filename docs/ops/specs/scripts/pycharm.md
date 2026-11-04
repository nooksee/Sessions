# Technical Specification: pycharm

Script: `Sessions/ops/lib/scripts/pycharm.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident; chats-file edit writer: Claude (Opus 5.5), a worker started by the Session Continuity Manager (`session-doctor`) on 2026-11-02; not a registered resident). Tests: `Sessions/tools/test/test_pycharm.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/reconcile_pycharm_ai_surfaces.py`, which this tree no longer holds; built as it was, 0 edit(s) at the port and 1 edit since (2026-11-02), listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Reconcile known PyCharm AI-session surface residue without touching JSONL bodies." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/session-control-reconciliation-20260714.md` (2026-07-14); 1 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/reconcile_pycharm_ai_surfaces.py` (sha256 `3c666f747d3684ce30b711b15f476168ee6fa19b93cfb99f55ac09e157970111`) was copied to `ops/lib/scripts/pycharm.py` on 2026-11-01 with 0 edit(s): none. One edit since, on 2026-11-02: the 20 IDE chat identifiers (`GEORGE_VI_CHAT`, `TEMP_OSAI_CHAT`, `LEGACY_CLAUDE_CHAT` and the 17 `SHELL_ONLY_STUBS`) left the code for the chats file in item 4. With that file holding the same values, the behavior is unchanged, and the retired task identifiers keep the same order.
2. Command line: `python3 -I -B ops/lib/scripts/pycharm.py`. Options as the script declares them:
   - `--workspace-dir`: (no help text in the script)
   - `--task-history`: (no help text in the script)
   - `--osai-workspace`: (no help text in the script)
   - `--control-workspace`: (no help text in the script)
   - `--preview-dir`: (no help text in the script)
   - `--apply`: (no help text in the script)
   - `--custody-dir`: (no help text in the script)
   - `--chats`: the chats file of IDE chat identifiers (default: ops/etc/pycharm-chats.json in the room)
3. Reads and writes: as the docstring states (833 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write. The 2026-11-02 edit added one read, the chats file, which comes before every other read.
4. The chats file. The tool resolves the room from its own location, three folders above `ops/lib/scripts/`, as `gauge` and `myself` do, and reads `ops/etc/pycharm-chats.json` there unless `--chats` names another path. The file is host data: `.gitignore` ignores `/ops/etc/*.json`, so the file never enters Git, and no identifier it holds is written in this tree. It is one JSON object with exactly four keys: `george_vi_chat`, `temp_osai_chat` and `legacy_claude_chat`, each a string, and `shell_only_stubs`, a list of strings. Every value is a 36-character lowercase hyphenated hex identifier (groups of 8, 4, 4, 4 and 12), and no value appears twice, within the list or across keys. The retired task identifiers are derived in this order: the stubs in file order, then `temp_osai_chat`, then `legacy_claude_chat`. `george_vi_chat` is repaired and never retired.
5. Refusal. The tool loads the chats file first, after parsing its arguments. When the file is absent, unreadable, not UTF-8 text or not valid JSON, when it holds anything but an object, lacks a key, has an extra key or repeats a key, when a value has the wrong type or is not such an identifier, or when an identifier appears twice, the tool prints one line to standard error and exits with status 1. The line reads `pycharm.py refuses: the chats file <path> <fault>. Nothing else was read or written.` The fault names the key or list position and never the value. The refusal comes before the tool reads `/proc`, the task history or any workspace file, and before it writes anything.

## Anecdotal Anchor

`Receipts/session-control-reconciliation-20260714.md` is the earliest of 1 receipt(s) naming `reconcile_pycharm_ai_surfaces.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Reconcile known PyCharm AI-session surface residue without touching JSONL bodies." "The default mode is read-only." "This tool deliberately does not archive, delete, move, or rewrite Codex or Claude JSONL files."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/reconcile_pycharm_ai_surfaces.py` until Control repoints them; this room's own documents name `ops/lib/scripts/pycharm.py`.
- The loader proves the form of the chats file, not that its identifiers are the right ones. The existing pending and reconciled checks remain the guard on content: a `george_vi_chat` that matches no chat leaves `george_vi_verified` at 0, and the tool stops with `protocol_deviations` 1 before any write.
- Until the host file is installed, the tool refuses on this host. The Session Continuity Manager installs `ops/etc/pycharm-chats.json`, mode 0600, from the file prepared on 2026-11-02, when this change merges.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
