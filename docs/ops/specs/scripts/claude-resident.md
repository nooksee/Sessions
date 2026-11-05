# Technical Specification: claude-resident

Script: `Sessions/ops/bin/claude-resident` (writer: Claudine Colbert). Tests: `Sessions/tools/test/test_claude_resident.py`. Spec writer: Claudine Colbert. Status: the wrapper's logic and its dry run, written 2026-11-05 under the Session Continuity Manager's packet `packet-claudine-w5-wrapper`; it never executes the provider, and no plugin setting points at it. Map: `docs/ops/README.md`. Authority: the first-wins plan W5; the Session Continuity Manager's notebook design of 2026-10-31 (the launch wrapper's three duties and five branches) as adapted by the decided notebook home; PoT 5.1 and 6.1.

## First Principles Rationale

Claude Code chooses its automatic memory (the notebook) by Git root, so every resident who shares a repository shares one notebook, and a notebook gives a reader a name and a posture before any registry check. The design gives each Claude resident one notebook of its own, bound to its registry key, and a launch wrapper that attaches it only when the launch names exactly one registered Claude session. Every other launch runs with auto memory off: nobody is handed anyone's notebook while unverified. The wrapper never blocks a launch; it only decides what the launch carries.

A Claude row registered to another room is verified too, by the same registry, as that room's resident; its present notebook is the provider's default for its own room, and this wrapper has no say over other rooms, so its launch passes through untouched (the Session Continuity Manager's decision, 2026-11-05).

The decided home is one folder per registry key under `<room>/ops/etc/notebooks/`, mode 0700, out of Git (PR #14). The mind tool projects the current leaf into that folder's `MEMORY.md`, seals the folder at seams and restores it from a seal (`docs/ops/specs/scripts/mind.md`). This wrapper is the third duty: choosing, at launch, which notebook a run gets.

## Mechanics and Sequencing

**Form.** `claude-resident --dry-run [--room DIR] [--registry FILE] -- <provider arguments>`. In this slice `--dry-run` must be the first argument, wrapper options come before `--`, and every argument after `--` belongs to the provider and is passed through unchanged. Any other form is refused with exit 2 and a usage line on standard error that echoes no argument; nothing is executed in any form. `--room` defaults to the room that holds the wrapper; `--registry` defaults to `<room>/ops/etc/resident-identities.json`. The interpreter is Python 3 started with `-I -B` through `/usr/bin/env -S`; the wrapper uses the standard library and the room's mind tool.

**The decision, in order.**
1. **The registry.** It must be a regular file (not a link), owned by this user, at mode 0600, at most 1 MiB, read without following a link, UTF-8 JSON with an `identities` list. Every row must carry a non-empty string key, provider, session and room; every key must be a plain registry key (`^[a-z0-9][a-z0-9-]*$`); no key may appear in two rows. Any failure is the **broken registry** branch, whatever the arguments say, so a broken registry shows on every launch.
2. **The session named.** The provider's arguments are scanned up to the provider's own `--`: `--resume <id>`, `--resume=<id>`, `-r <id>`, `--session-id <id>` and `--session-id=<id>` name a session. A flag with no value (the next argument absent or starting with `-`), `-c` or `--continue`, or no such flag at all names none; `--fork-session` gives the run a new session. Each of these is the **new** branch. Two different sessions named is the **ambiguous** branch; the same session named twice is one.
3. **The row.** The Claude rows (provider `claude`) whose session equals the one named: none is the **unregistered** branch (a row of another provider does not count); more than one is the **ambiguous** branch; exactly one is the **registered** candidate.
4. **The room.** If the candidate's room resolves to another room, the branch is **registered elsewhere**: the launch passes through untouched, with no environment change, no notebook attached and auto memory left as the provider's default for that room.
5. **The notebook.** For a candidate of this room, its folder `<room>/ops/etc/notebooks/<key>/` must pass the mind tool's private-path rules (every component present and none a link; this user's folder at 0700; an existing `MEMORY.md` this user's single-link regular file at 0600) and the mind tool's Git rule (outside Git, or ignored by the nearest repository). Every projection marker in its `MEMORY.md` must be a well-formed marker of this key, so a folder holding another key's projection is never attached. When all of that holds, the branch is **registered** and the notebook is attached; when any of it fails, the branch stays **registered** but nothing is attached and auto memory is off, with the reason.

**What a run carries.** The attached branch adds no environment change of its own; the route that points the provider at the folder is unproven (below) and is printed as such. The registered-elsewhere branch adds nothing at all. Every other outcome sets `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` and attaches nothing. An unexpected error anywhere in the decision is the **error** outcome, handled the same way: auto memory off, nothing attached, exit 0.

**Output.** One JSON object on standard output, with sorted keys: `mode` (`dry-run`), `executed` (`false`), `branch`, `notebook` (`attached` or `none`), `auto_memory`, `env` (only the variables the run would add or override, never the inherited environment), `argv` (`<provider>` followed by the provider's arguments exactly as given), `notebook_route`, `reason` and `unproven` (the list below). The reason is fixed text: it names no key, person, role, note, room or session, and paths in it are written as `<room>` and `<notebook>`. A session identifier appears only inside `argv`, where the provider's own arguments carry it. Exit 0 for every branch.

**Native proof still needed before any real run** (the wiring's, through George's route, with the Independent Reviewer's review and the operator's named go; the Session Continuity Manager first, PoT 6.1.2 and 6.1.6):
1. The provider executable the real run would exec, and that the exec passes every argument, the standard streams and the exit status through unchanged.
2. The route that points the provider at the attached notebook: a `--settings` file naming the folder (`autoMemoryDirectory`, as the design measured on 2026-10-31), an environment variable, or another provider-documented route; and that the provider then loads that folder's `MEMORY.md` and writes its memory there.
3. That `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` turns auto memory off for that run in the installed provider.
4. That every launch path of the plugin (a new chat, a resume, a continue, a fork) passes its session as `--resume` or `--session-id`, as measured for one resident on 2026-10-31.
5. The modes the provider gives files it writes in the notebook (George's F2: unknown).
6. That the interpreter line (`/usr/bin/env -S python3 -I -B`) resolves in the plugin's launch environment.

## Recovery and limits

- **Nothing to recover in this slice.** The wrapper writes nothing, executes nothing and changes no setting; removing it removes the slice.
- **Residents of another room** pass through untouched (the registered-elsewhere branch). On this host, 8 of the registry's 10 Claude rows are registered to another room (counted 2026-11-05, values not read out); a launch path pointed at this wrapper for every Claude launch leaves their present notebooks as they are. The wrapper gives such a run no notebook of this room's home, even when a folder of that key exists here.
- **The argument scan** knows only the documented session flags. A positional argument that happens to look like one of them would be read as one; at worst a run then names an unregistered session and runs with auto memory off.
- **No seam detection.** Like the mind tool, the wrapper cannot see whether another writer holds the notebook.
- **Not in this slice:** the real exec and its argument contract without `--dry-run` and `--`, the notebook route, seeding a notebook, and any change to the plugin's launch path.

## Anecdotal Anchor

On 2026-10-31 the Control notebook, 56 notes mostly the Session Continuity Manager's, loaded for three other residents, and the Sessions notebook slot was empty, so its owner woke without his notes. On 2026-11-05 the Sessions slot held five notes written from more than one session, loading for every Claude conversation opened in the room. The notebook was choosing the reader before the registry could. This wrapper reverses the order: registry first, then the notebook, and no notebook at all when the registry cannot answer.

## Integrity Filter Warnings

- A dry run is not a launch. Passing tests prove the decision on synthetic registries and rooms, not that any provider loads a notebook.
- `notebook: attached` means the folder passed every check, not that the provider reads it; the route is unproven until the native proof above.
- The wrapper reads the registry. It must never print a registry value or a session identifier outside the passed-through arguments; the tests check every branch for that.
