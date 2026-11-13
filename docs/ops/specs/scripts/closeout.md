# Technical Specification: closeout

Script: `Sessions/ops/lib/scripts/closeout.py` (writer: Claudine Colbert). Tests: `Sessions/tools/test/test_closeout.py`. Card: `Sessions/ops/src/reports/closeout.md.tpl`. Spec writer: Claude Shannon, 2026-10-30, from the operator's direction. Status: built and tested by its writer; the independent review of the code is pending. Nothing is installed: wiring a hook into any resident's settings needs the Auditor's review and the operator's named go.

## First Principles Rationale

The operator, 2026-10-30: an organism that is to die carries its death process encoded within it; in the same way, a model needs some means of knowing that its time has come, so that the closeout does not depend on him remembering to send the prompt.

Until now, a resident's end was noticed by someone else: a percentage read by hand, a packet carried in late, or never. Joy's closing packet of 2026-10-29 never reached her. The closeout must be built into the resident and triggered by its own measured state, not by anyone's memory.

The closeout is also the moment a resident writes to the mind any idea it learned that stays true, every time, in the same way, with no approval asked (the operator's design of 2026-11-09; `docs/ops/specs/scripts/mind.md`).

## Mechanics and Sequencing

### Shared pressure decision (W4 source increment, not activation)

`pressure_band(tokens, window)` is the one reserve/band calculation for the
prompt hook and the proposed operator-only notice adapter. It preserves the
existing 70 percent line, 50,000-token reserve and five-point bands. It
returns `None` only for a valid below-trigger reading and an integer band
otherwise. Invalid types, booleans, negative tokens, nonpositive/too-small
windows and over-window counters raise `Unknown`, never healthy. Equality
with the trigger enters band zero. Tests cover both equality boundaries,
the next band, different windows and invalid input. No live hook, desktop
notification or timer is installed by factoring this decision.

1. **The meter.** After every working turn, the provider writes the exact token count into the resident's own body (`gauge.md`).
2. **The trigger line: a reserve, not a percent.** Joe Codex measured on 2026-10-30 that, at a busy pace, the step from 65 to 70 percent lasts minutes (7.6 for Claudio, 8.6 for George, 24 for Shannon, 42 for Joy). So the closeout begins when **50,000 tokens remain before the 70 percent line**, whatever the window: 65 percent of 1,000,000, about 59.5 of 475,000, and about 50.6 of 258,400. The card stops new work, so the reserve covers a calm closeout. The operator may veto this rule.
3. **The signal (Claude residents).** A `UserPromptSubmit` hook runs `closeout.py` on each prompt.
   - **Reading.** The hook reads the hook input's own `transcript_path`, and only that file, takes its newest usage reading the way `gauge` does, and divides by that model's window.
   - **Current readings only.** It acts only on the state `last observed`. After a compaction it stays silent until a fresh reading exists.
   - **Covered sessions only.** It acts only when the transcript's session id is registered in `resident-identities.json`. Helpers, subagents, sidechains and unregistered sessions are always silent.
   - **Silence.** Above the reserve it prints nothing.
   - **At the reserve or beyond,** it prints one block that Claude Code adds to the resident's context: the measured figure and the closeout card below. It repeats once per 5 points crossed, recorded in an ignored state file keyed by session. The state re-arms when the figure falls back above the reserve, after a compaction or a rotation.
   - **The operator's copy.** The same crossing sends the operator a notification, as the wire bell does.
   - **Unknown.** With no reading or no known window, it prints nothing to the resident and logs "unknown". After 3 consecutive unknowns, one notification goes to the operator, so that an unknown is never silent for everyone. The operator may decline this.
   - **Never in the way** (Claudio C3). Claude Code erases the prompt when a `UserPromptSubmit` hook exits with code 2. So the hook catches every error, never uses an argument parser that exits on its own, always exits 0, routes any failure to the "unknown" path, and runs under an explicit 5-second timeout.
   - **Limit.** A hook fires on a prompt, not during a turn. One long turn can cross both lines with no prompt to carry the card. The backstop is the `gauge` timer's notification to the operator, on his go.
4. **The signal (Codex residents).** Codex CLI 0.166 documents the same `UserPromptSubmit` hook, able to add developer context (Joe Codex, `joe.md`, block 3). The PyCharm path is untested, so the route is designed the same way and tested on one Codex resident before relying on it. Until then, and for Copilot, the `gauge` timer notifies the operator, and he pastes the card.
5. **The card.** The resident follows the card in order, the same every time. Its text has one source, the template `ops/src/reports/closeout.md.tpl`. `closeout.py` renders that template, filling the measured percent, the window, the reading time and the rotation writer, and this spec does not restate it. A template the hook cannot read or fill is an "unknown", never a hand-written fallback card. The rotation writer is read from the registry's roles: the Integrator (PoT 4.1.3) runs every rotation but its own, and the card names its desk. The Integrator's own is run by the Contractor the operator assigns to it (PoT 4.1.4); the registry holds no such assignment, so the card says so in the clause's own words and names nobody. A registry that does not name exactly one Integrator, or that names no Contractor for the Integrator's own rotation, is an "unknown". The fields of a mind entry are defined in `mind.md`.
6. **The rotation** follows `rotate.md`. The meter's 70 percent is the due point.

## Anecdotal Anchor

On 2026-10-29 Joy reached 77.8 percent. A closing packet for her was written and left on the operator's Desktop, and it never reached her. Her own state note, written earlier because the operator had mentioned a rotation, saved the day. On 2026-10-30 the first `gauge` run found Claudine at 84.6 percent and Alan Codex at 73.3, both past the line with nobody aware. A signal from inside each resident would have started both closeouts at 65.

## Integrity Filter Warnings

- **Own file only.** The hook reads only its own `transcript_path`, never another body, and never prints message content. A shared room cannot route one resident's signal to another.
- **Silent when unsure.** An unknown reading or window produces no signal and no guess.
- **Role names.** The tool looks for two roles by the names the policy gives them, and its suite compares those names, and the card's words for the Contractor it cannot name, with clauses 4.1.3 and 4.1.4 of the tree under test. The registry must carry the same names (PoT 1.3.5). A second Integrator in the registry, in this room or another, makes every card unknown; so does a registry that still carries another text for the role.
- **Advice, not control.** The card tells the resident what to do; it never blocks a prompt, a tool or a compaction.
- **Concepts only.** The resident writes its own leaves through the mind tool, whose screen refuses the fact of the moment.
- **Authority.** Wiring the hook into any resident's settings, and any notification, needs the Auditor's review and the operator's named go, one resident first (Shannon), then the rest.

## State destination and legacy boundary

The source default is `<room>/logs/closeout/`, not `storage/`. It contains
`state.json`, `log.jsonl`, `.lock` and atomic-write temporary files. Fresh
state directories are mode 0700; fresh state, log and lock files are mode
0600, including with umask 0000. Existing permissions and state bytes are not
silently normalized or migrated. The explicit `--state-dir=PATH` interface
remains available for bounded fixtures or an authorized existing selection;
that flag does not itself authorize a live state move.

Before using the default for a registered session, the hook checks whether
`<room>/storage/closeout` exists at all, including an empty directory, file,
broken symlink or special node. If so, it emits no card and follows the
existing unknown-recording path in the new default location. That path may
create a private diagnostic state/log containing unknown counts, but records
no delivered band, copies no legacy bytes and follows no legacy link. An
unregistered session remains silent without creating either destination.
Legacy evidence is not treated as an empty or successfully migrated state.
An uninspectable legacy path, including an inaccessible or non-directory
parent, is also unknown, not evidence of absence. Only FileNotFoundError
permits default operation without a migration hold.

Before wiring the source, the named migration owner inventories the actual
old/new inputs and consumers. If old state exists, preserve and hash it,
stage the exact reviewed state at the new location with private modes, verify
that its delivered bands remain intact, and release the old canonical path
only under the named custody/migration operation. Retained evidence belongs
at its approved kept location, not an automatically deleted backup. If the
old canonical path still exists, default operation remains unknown. The tool
does not perform that migration or infer its authority. No hook, notification,
service or live consumer is activated by this source change.

The state-location suite stages the real script and gauge into an invented
room and exercises the actual default paths in subprocesses. It covers fresh
defaults, legacy-byte preservation, empty/file/link/FIFO refusal, explicit
override, reviewed fixture-copy deduplication, unregistered silence and fresh
privacy modes. This does not prove live native delivery or production custody.
