# CC GUI: the settings continuity relies on

Registry entry: `docs/ops/registry/runbook.md` (`RUNBOOK-05`). Written 2026-11-24 by the Session Continuity Manager, on the operator's direction, after a panel-by-panel walk of the plugin with him. Status: maintained by the Session Continuity Manager; changed when the plugin, the operator's choices or a measurement changes.

## 1. What this page is

CC GUI is the JetBrains plugin "Claude, Codex and More", plugin id `com.github.idea-claude-code-gui`, measured at version 0.6.6-fix1. Since JetBrains AI Chat was removed on 2026-11-24, it is the operator's surface for the Codex residents. Swttch remains the surface for the Claude residents.

The plugin's settings are host software and stay off the repository. They live in the user's `~/.codemoss/` folder, in the IDE's own options, and in the configuration that every resident shares: `~/.codex/` for Codex and `~/.claude/` for Claude. This page records only the settings that continuity depends on: the value, why, and who may change it. It also records what the plugin was measured to do, and how to check it again after an update.

One page per program. Settings are not portable between programs, so this page borrows nothing from another, and a later surface gets its own page.

**Who does what:**
- The operator decides every value.
- The Desktop Software and Maintenance resident changes host software and shared configuration on the operator's word.
- The Session Continuity Manager measures, keeps this page and its working parts, and runs the re-check in section 5.

## 2. Settings, panel by panel

| Panel | Setting | Value | Why | Changed by |
| --- | --- | --- | --- | --- |
| Basic, Behavior | AI session title generation | Disabled | When enabled it names threads, and it can write a Codex thread's own name. | the operator |
| Basic, Behavior | Match sessions by Git remote repository | Disabled | When enabled, history from other folders with the same remote is mixed in, and the rooms blur. | the operator |
| Basic, Behavior | Send Opened File Path | Disabled | A resident prompt carries only what the operator types. | the operator |
| Basic, Environment | Claude CLI path, working directory | empty | The defaults are used; Claude residents are not run here. | the operator |
| Provider Management, Codex | providers | only the Codex CLI login | Adding, importing or switching a provider rewrites the shared Codex login of every Codex resident, as happened on 2026-11-23. Revoke Authorization withdraws the plugin's use of that login. Neither is done while residents run. | the operator, then the maintenance resident |
| Provider Management, Claude Code | local settings and CLI login | not authorized | Claude residents are attended in Swttch. Authorizing would let the plugin use and write the Claude settings that every Claude resident shares. | the operator |
| Provider Management, CLI | Codex CLI | the standalone package behind `~/.local/bin/codex`, at least the version that last wrote any resident thread | An older reader over threads written by a newer one is avoided. The page's hint to install the CLI with npm globally is not followed, since it would place a second Codex beside the standalone one. | the maintenance resident |
| Permissions | Codex sandbox | danger-full-access | Equal to the shared Codex configuration the residents already run under. | the operator |
| none: the shared Codex configuration, `~/.codex/config.toml` | `approval_policy` | `never` | The residents already run under it; a program that changes it changes the turns of every Codex resident. | the operator, then the maintenance resident |
| none: the shared Codex configuration, `~/.codex/config.toml` | `notify` | Token Tracker's script, `~/.tokentracker/bin/notify.cjs`, run by `node` through `/usr/bin/env` | It runs after each turn of every Codex resident. It is Token Tracker's, kept by the operator with the usage page; any other value is reported. | the operator, then the maintenance resident |
| Prompt Library | prompts | global prompts only: the four of `prompts.json` (section 4) | Global prompts are kept in `~/.codemoss/prompt.json`. Project prompts are written into the project folder (`.codemoss/prompt.json`), which this room's Git ignores and the parent Control repository does not. | the operator |
| Prompts (custom prompts) | attached to a resident | none | Such a prompt is sent as system instructions at the start of a conversation, above the resident's own. | the operator |
| Prompt Enhancer | use on a resident prompt | never | It rewrites what was typed before sending. | the operator |
| Skills; MCP Servers (Codex) | toggles | as the shared Codex configuration holds them | A toggle here edits the configuration every Codex resident runs with. | the maintenance resident, on the operator's word |
| Hooks | Claude Stop and SessionEnd | Token Tracker's, kept | The operator keeps the usage page for budgeting. The tracker's own telemetry is off in its own configuration. | the operator |
| Usage Statistics | the page | kept | It is Token Tracker: opening it starts the tracker and installs its hooks again. | the operator |
| Session history | delete | not used | Deleting removes the session file permanently, with no trash. Archive through the Codex CLI instead (`codex archive`, reversed by `codex unarchive`). | the operator |
| Appearance, notifications, pet | all | free | No bearing on continuity. | the operator |

## 3. What the plugin was measured to do

- **Lists.** The Codex history of a window is the window's folder and everything below it. The Control window therefore lists every room, and a room window lists its own residents only. The Sessions view reads the session files themselves, so a deleted file leaves it at once.
- **Folders.** A resumed chat keeps the working folder recorded in its own thread; the window's folder applies only to a new chat.
- **Identity signal.** The plugin's bridge passes its own permission key, `CLAUDE_SESSION_ID`, to every command a Codex resident runs. The identity check does not read that variable (DP-SES-0019), so a Codex resident in CC GUI verifies by its caller and registry legs.
- **File Context.** The chip attaches the editor's open file to a prompt. It is checked before a resident prompt is sent.
- **Titles.** A custom title is written only to `~/.codemoss/session-titles.json`; the Codex thread's own name is untouched. The title is what the history search finds.
- **Archive.** `codex archive` refuses a thread whose session file is already gone, and leaves it unchanged.
- **Prompts in the input.** An exclamation mark typed in the chat input opens a list of the global and project prompts, with an entry to create a new one.
- **Import.** A prompt whose id is already in the library is a conflict, resolved by the operator's choice of Skip, Overwrite or Duplicate; a prompt with a new id is added. A name is 1 to 30 characters.

## 4. Working parts

The page's working parts sit in the room's runbook home, `ops/src/runbook/ccgui/`, beside the other runbook assets. The folder carries the page's one-word name, and each part has a one-word name of its own:
- `baseline.json`: the values section 5 compares against, the adapter between this program and the room. When the plugin changes, this file and this page change, and the residents do not.
- `prompts.json`: the operator's four global prompts, in the Prompt Library's own export format: Identity check, Wake check, Closeout card and Packet status. Each keeps the id of the prompt the operator saved, so an import that chooses Overwrite replaces that prompt in place. The room is written as `<room>`, and the operator is named by role.

`prompts.json` is the master, and the Prompt Library is a copy of it. Every change to the prompts, and every return of them after a reinstall, runs in this order:
1. **Export first.** The operator exports the library into the room's scratch, `var/tmp/ccgui/`, never into a folder of the room's checkout that Git does not ignore: any file there that Git lists stops the next ship. The export is the way back, and it shows any prompt changed in the plugin since the last import.
2. **The master changes by packet.** The Session Continuity Manager edits `prompts.json` in a packet, folding in any change the export shows; several changes travel in one packet. A new prompt is added when a routine repeats, not before.
3. **A copy with the room's path.** From the master on `main`, or from a tree the Auditor passed, the Session Continuity Manager writes a copy with the room's path in place of `<room>` into the same scratch folder.
4. **Import with Overwrite.** The operator imports that copy as global prompts and chooses Overwrite.
5. **Export again and compare.** The operator exports once more; the Session Continuity Manager compares that export with the copy, prompt by prompt.
   - **On a difference, stop.** Every file stays where it is: the first export is the way back, and all three are the evidence. The difference is reported to the operator.
   - **On a match,** the hash of each file goes into the Session Continuity Manager's handoff first. The copy and the second export are rebuildable from the master and are then deleted. The first export is deleted only when every prompt in it equals a version of the master in Git or was folded in at step 2; otherwise it goes to the day's custody batch before it is deleted (CONSTRAINTS C01).

Nothing for this program is kept in `storage/`, which holds case payload and handoffs, not tool state (PoT 1.1.4). Neither file holds a secret value; a login is checked only for its size, time and mode.

## 5. After an update, or when something looks changed

Before any resident turn, in this order. `baseline.json` holds the expected values of each step:

1. **The plugin's version and the Codex CLI's version.** Provider Management, CLI, and the CLI's own `--version`.
2. **The shared Codex login and configuration.** The login file's size, time and mode, read by `stat` and never opened, equal `baseline.json` unless the operator logged in again; after a new login its new values replace them there. The sandbox, approval and notify entries are as section 2 holds them.
3. **The plugin's own configuration.** `aiTitleGenerationEnabled` is false; the current Codex provider is the CLI login; no stored provider exists.
4. **The shared Claude settings.** Their hooks are as section 2 holds them.
5. **Token Tracker.** Its telemetry is still off.
6. **The Behavior panel.** Its rows in section 2 hold.
7. **The Prompt Library.** The four global prompts of `prompts.json` are present, each with its text as written there and the room's path in place of `<room>`; if not, they are put back as section 4 says.
8. **One resident's identity check, through the new build.** Both identity lines, caller and registry, pass.

A difference is reported to the operator and the maintenance resident with what was measured. It is not corrected by the continuity desk, which measures and records.
