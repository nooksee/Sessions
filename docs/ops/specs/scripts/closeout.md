<!-- redact: public copy; source sha256 68a080a778b6f559ed45ce49c7d6c8bc6e1cd0347ffede4acd481563d25d0125; rules 8; mode history; words 4; sessions 0 whole, 0 truncated; host paths 0; decisions 0 -->
# Technical Specification: closeout

Script: `Sessions/ops/lib/scripts/closeout.py` (writer: Claudine Colbert). Tests: `Sessions/tools/test/test_closeout.py`. Card: `Sessions/ops/src/reports/closeout.md.tpl`. Spec writer: Claude Shannon, 2026-10-30, from Kevin's direction. Status: built and tested by its writer; the independent review of the code is pending. Nothing is installed: wiring a hook into any resident's settings needs Claudio's review and Kevin's named go.

## First Principles Rationale

Kevin, 2026-10-30: "[words sha256=633ec20c58985661e3fc6f7854698a6253d2374ce48dc0161c321e101ad5b83e]"

Until now, a resident's end was noticed by someone else: a percentage read by hand, a packet carried in late, or never. Joy's closing packet of 2026-10-29 never reached her. The closeout must be built into the resident and triggered by its own measured state, not by anyone's memory.

Input to a resident's mind is solicited by a prompt in conversation and written only after Kevin's yes there, with his words stored beside it (Kevin, 2026-10-30). The closeout is the moment that solicitation happens, every time, in the same way.

## Mechanics and Sequencing

1. **The meter.** After every working turn, the provider writes the exact token count into the resident's own body (`gauge.md`).
2. **The trigger line: a reserve, not a percent.** Joe Codex measured on 2026-10-30 that, at a busy pace, the step from 65 to 70 percent lasts minutes (7.6 for Claudio, 8.6 for George, 24 for Shannon, 42 for Joy). So the closeout begins when **50,000 tokens remain before the 70 percent line**, whatever the window: 65 percent of 1,000,000, about 59.5 of 475,000, and about 50.6 of 258,400. The card stops new work, so the reserve covers a calm closeout. Kevin may veto this rule.
3. **The signal (Claude residents).** A `UserPromptSubmit` hook runs `closeout.py` on each prompt.
   - **Reading.** The hook reads the hook input's own `transcript_path`, and only that file, takes its newest usage reading the way `gauge` does, and divides by that model's window.
   - **Current readings only.** It acts only on the state `last observed`. After a compaction it stays silent until a fresh reading exists.
   - **Covered sessions only.** It acts only when the transcript's session id is registered in `resident-identities.json`. Helpers, subagents, sidechains and unregistered sessions are always silent.
   - **Silence.** Above the reserve it prints nothing.
   - **At the reserve or beyond,** it prints one block that Claude Code adds to the resident's context: the measured figure and the closeout card below. It repeats once per 5 points crossed, recorded in an ignored state file keyed by session. The state re-arms when the figure falls back above the reserve, after a compaction or a rotation.
   - **Kevin's copy.** The same crossing sends Kevin a notification, as the wire bell does.
   - **Unknown.** With no reading or no known window, it prints nothing to the resident and logs "[words sha256=b23a6a8439c0dde5515893e7c90c1e3233b8616e634470f20dc4928bcf3609bc]". After 3 consecutive unknowns, one notification goes to Kevin, so that an unknown is never silent for everyone. Kevin may decline this.
   - **Never in the way** (Claudio C3). Claude Code erases the prompt when a `UserPromptSubmit` hook exits with code 2. So the hook catches every error, never uses an argument parser that exits on its own, always exits 0, routes any failure to the "[words sha256=b23a6a8439c0dde5515893e7c90c1e3233b8616e634470f20dc4928bcf3609bc]" path, and runs under an explicit 5-second timeout.
   - **Limit.** A hook fires on a prompt, not during a turn. One long turn can cross both lines with no prompt to carry the card. The backstop is the `gauge` timer's notification to Kevin, on his go.
4. **The signal (Codex residents).** Codex CLI 0.166 documents the same `UserPromptSubmit` hook, able to add developer context (Joe Codex, `joe.md`, block 3). The PyCharm path is untested, so the route is designed the same way and tested on one Codex resident before relying on it. Until then, and for Copilot, the `gauge` timer notifies Kevin, and he pastes the card.
5. **The card.** The resident follows the card in order, the same every time. Its text has one source, the template `ops/src/reports/closeout.md.tpl`. `closeout.py` renders that template, filling the measured percent, the window, the reading time and the rotation writer, and this spec does not restate it. A template the hook cannot read or fill is an "[words sha256=b23a6a8439c0dde5515893e7c90c1e3233b8616e634470f20dc4928bcf3609bc]", never a hand-written fallback card. The fields of a mind entry are defined in `mind.md`.
6. **The rotation** follows `rotate.md`. The meter's 70 percent is the due point.

## Anecdotal Anchor

On 2026-10-29 Joy reached 77.8 percent. A closing packet for her was written and left on Kevin's Desktop, and it never reached her. Her own state note, written earlier because Kevin had mentioned a rotation, saved the day. On 2026-10-30 the first `gauge` run found Claudine at 84.6 percent and Alan Codex at 73.3, both past the line with nobody aware. A signal from inside each resident would have started both closeouts at 65.

## Integrity Filter Warnings

- **Own file only.** The hook reads only its own `transcript_path`, never another body, and never prints message content. A shared room cannot route one resident's signal to another.
- **Silent when unsure.** An unknown reading or window produces no signal and no guess.
- **Advice, not control.** The card tells the resident what to do; it never blocks a prompt, a tool or a compaction.
- **No self-written mind.** The resident proposes and Kevin decides, in conversation.
- **Authority.** Wiring the hook into any resident's settings, and any notification, needs Claudio's review and Kevin's named go, one resident first (Shannon), then the rest.
