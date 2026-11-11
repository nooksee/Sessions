# Technical Specification: myself

Script: `Sessions/ops/lib/scripts/myself.py` (original writer not recorded; port writer: Claude (Fable 5.1, that session), not a registered resident; shared-counter correction writer: Session Continuity Apprentice (Joe Codex); model-keyed window writer: Assistant Session Continuity Manager (Claudine Colbert), 2026-11-05). Tests: `Sessions/tools/test/test_myself.py`. Original spec writer: the port writer; shared-counter spec correction: Session Continuity Apprentice (Joe Codex). Source status: shared gauge reader with synthetic coverage; independent review and integration are recorded in the owning change receipt. No hook, timer or service is installed by this source change. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Measure one resident's native identity and session health, without writes." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/resident-self-check-canary-20260809.md` (2026-08-09); 10 receipt(s) name it in all.

## Mechanics and Sequencing

1. Port provenance: `Scripts/check_myself.py` (sha256 `e4b2fad6d0d64d223fe904626374d5b3cbf993cafcbac876b336c2ed3baf3bc8`) was copied to `ops/lib/scripts/myself.py` on 2026-11-01 with one edit: parents[1] -> parents[3]. The later shared-counter correction replaces only the duplicated context-usage selection; identity, row/parse metrics and timestamp-cluster inspection keep their separate body analysis.
2. Command line: `python3 -I -B ops/lib/scripts/myself.py`; the script declares no argparse options (it reads its inputs from fixed paths or from the environment, as its docstring says).
3. Context selection loads the sibling `gauge.py` and calls its `read_codex` or `read_claude` on the exact selected body. The gauge specification owns the counter-selection and tail bound. Main-chain usage, incomplete final rows, zero usage and later compaction therefore use the same selection as gauge and closeout. The pressure leg reports unknown after compaction until a fresh complete reading; it does not reuse an older Codex window when the newest reading lacks one.
4. **The Claude window** (W3, 2026-11-05, from the Session Continuity Apprentice's health-desk finding of 14:24:52): the leg looks up the caller's own model, as the caller's native body names it, in the gauge's reviewed window table (`gauge.window_table` on the gauge's own spec, `docs/ops/specs/scripts/gauge.md`, unless a test names another table) through `gauge.resolve_window`. The leg reports the row's source and observation date as `window_source=gauge spec table: <source>, observed <date>`, beside `tokens_source=caller-native-body` and the model. It stays UNDETERMINED, strictly, when the table has no row for the model, when the table is unreadable or has no rows, or when the gauge cannot load; a reading before the first complete post-compaction measurement stays UNDETERMINED as before (item 3). The shared status-line record (`logs/resource-state.json`), which whichever session last ran writes and which switched between two models three times in about nine minutes on 2026-11-05 (the Apprentice's observation), is no longer read by this leg: it is passed to `resolve_window` as absent, so the gauge's unverified status-line fallback never applies here. The token count stays the caller's own native body figure; the rotation line, the percentage formula and every threshold are unchanged; there is no second table and no copied window. The leg names the actual body, the gauge source and the table it read. The Codex window still comes from the caller's own body record, as before.
5. **The orientation row** follows the rule in `docs/ops/specs/scripts/identity.md`, "What counts as an orientation row": the tag must begin the row's own message content, after any leading IDE notices, and the identity is read from the text after them.
6. Missing/unreadable gauge source or reader failure makes pressure undetermined, without a second reader fallback. Other identity/body-metric legs still run. A native Codex count above its reported window is undetermined, not a clean result. Repeated runs read current input; no pressure result is cached. No new output, state, registry, binding or body write is added.
7. **Auto memory** (2026-11-09), the tenth leg, a health leg: whether this launch of a Claude resident of this room runs with the provider's auto memory off, as the room requires. A resident here wakes from its own mind and handoff (CONTEXT X01); with auto memory on, the provider would load one memory shared by every resident of the room. The launch is the nearest Claude process in the ancestry whose own arguments name this session. The leg reads, in the provider's order of precedence and stopping at the first that decides:
   - the auto-memory switch `CLAUDE_CODE_DISABLE_AUTO_MEMORY` in the launch's environment as the kernel holds it (`/proc/<pid>/environ`), loosely: any value but empty, `0` or `false` reads as on, and on is a PASS;
   - each `--settings` source among the launch's own arguments, up to its own `--` (a file path, or inline JSON as the provider also takes it);
   - the room's `.claude/settings.local.json`, then its `.claude/settings.json`.

   A source that sets `autoMemoryEnabled` decides: `false` is a PASS, `true` is a FINDING, any other value is a FINDING. When nothing sets it, the leg is a FINDING that names the setting the room needs. The leg passes with nothing to judge for a caller that is not Claude and for a row of another room. It is UNDETERMINED, never PASS, with no identity, no room configured, a row naming no room, no process naming the session, an unreadable environment, or a settings source that is not a regular file holding one JSON object of at most 64 KiB (a link is not followed). **Its limit:** it sees what the launch carried and what the room's files say, not what the provider then loaded, and it does not read managed policy or the user's own settings. It prints no session and no argument, and writes nothing.

## Anecdotal Anchor

`Receipts/resident-self-check-canary-20260809.md` is the earliest of 10 receipt(s) naming `check_myself.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Measure one resident's native identity and session health, without writes." "A working directory is never identity."
- Host consumer selection belongs to Control; this source change neither repoints nor restarts a consumer. The module and its sibling gauge reader must remain together in the source layout.
- The focused regression set covers eleven synthetic agreement/currentness cases plus reader failure, invalid-window and repeated-run checks. Those cases are not a live fleet or provider-version acceptance claim. Claude window resolution follows the gauge's reviewed table; a model the table lacks is an explicit unknown, and the table's rows are reviewed in the gauge's spec, not here.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]

## Caller signals (added 2026-11-11)

The caller is resolved from a native session variable only when it is corroborated above the caller in the process tree:
- **Claude:** `CLAUDE_CODE_SESSION_ID` or `CLAUDE_SESSION_ID`, and the same identifier in a Claude ancestor's arguments.
- **Codex:** `CODEX_THREAD_ID`, and that thread's writer lock held open by a Codex ancestor.
- **Copilot:** `COPILOT_AGENT_SESSION_ID`, and that session's own state folder holding an in-use lock named for a Copilot ancestor's process (`inuse.<pid>.lock`). Measured on 2026-11-11 by variable names and a yes or no only: the Orchestrator's session carries the variable, and its value equals the seat's registry row.

A variable alone resolves nobody. A Copilot seat is registry-only, so the roster, binding and body legs stay as they were for it; the two identity legs are what this adds.
