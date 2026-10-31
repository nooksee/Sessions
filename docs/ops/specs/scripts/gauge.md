<!-- redact: public copy; source sha256 5774df1c52eeff3776aa4adf00760401543035d9ed383061eeb4aed2de16b7e4; rules 8; mode history; words 4; sessions 0 whole, 0 truncated; host paths 5; decisions 0 -->
# Technical Specification: gauge

Script: `Sessions/ops/lib/scripts/gauge.py` (writer: Claudine Colbert). Tests: `Sessions/tools/test/test_gauge.py`. Spec writer: Claude Shannon. Status: built in Sessions block 2, 2026-10-30; not on a timer and not wired to any notification. Claudio Freeman reviews it before it is relied on.

## First Principles Rationale

This desk kept estimating how full each resident was. It weighed files (a large body is not a full one), read a percentage by hand when asked, and guessed at wake figures. Manufacturing does not service a machine when someone feels it is time; it reads a meter, services at a fixed reading, and a light comes on. The meter already exists here: after every working turn, the provider's API writes the exact token count into the resident's own body. A resident's context only grows on a working turn, and every working turn writes a fresh reading, so an idle resident's last reading is still its true figure. What it needs is its age shown beside it.

So `gauge` reads that figure for every registered resident, from the end of the body, and never reads or prints message content. It prints "[words sha256=b23a6a8439c0dde5515893e7c90c1e3233b8616e634470f20dc4928bcf3609bc]" rather than a guess. It appends each reading to a ledger, so that trends and forecasts can follow, and so that the 65 and 70 percent lines become events rather than impressions.

## Mechanics and Sequencing

1. **Residents.** Read `Sessions/Evidence/resident-identities.json`. Each entry's provider and session id locate its body: Claude under `[host path 1]`, Codex under `[host path 2]` (archived bodies under the archived root), Copilot under its Agent Dock store.
2. **Reading.** Scan from the end of the body, at most 16,000,000 bytes, for the newest genuine reading:
   - **Claude:** the newest main-chain assistant call's `message.usage`, input plus cache read plus cache creation, one reading per `message.id`. Zero-usage, synthetic and sidechain rows are not readings.
   - **Codex:** the newest `token_count` event: its last input figure and its `model_context_window`. The model comes from the nearest turn context before it.
   - **Copilot:** `data.usage.inputTokens` over `maxPromptTokens`.
3. **Window,** in order of authority (Claudio section 131, C1):
   - the window the provider reports in the same record (Codex, Copilot);
   - the reviewed table below;
   - only when the table has no row for that model: Claude Code's status-line record (`Sessions/Evidence/resource-state.json`). This record is written by whichever single session last ran the status line, with no session id, so its source is shown as unverified;
   - otherwise "[words sha256=b23a6a8439c0dde5515893e7c90c1e3233b8616e634470f20dc4928bcf3609bc]".
4. **State.** Each row carries one state:
   - `last observed`: a genuine reading, with its age;
   - `before compaction`: a compaction boundary follows the reading, so the figure is no longer current;
   - `compacted`: a compaction boundary was found and no reading follows it yet, so there is no current figure (C2);
   - **Which boundaries count (Claude).** A boundary is found by its `compact_boundary` token; the line is then parsed in memory, and only a row whose top-level `type` is `system` and `subtype` is `compact_boundary` counts. Field order and the length of the line's head do not matter. A boundary on a side conversation (`isSidechain` true, a subagent's own compaction) does not compact the resident's context and changes no state; only a main-chain boundary does. The same main-chain rule already governs readings (step 2).
   - `archived body`: not a live reading;
   - `window unknown`;
   - `invalid`;
   - `unknown`.
5. **Output.** A table: resident, model, tokens, window, percent, last observed, age, state, note. `--json` gives machine output, and `--key` limits the run to one resident.
6. **Ledger.** One line per resident per run, appended to `Sessions/storage/gauges/ledger.jsonl` at mode 0600. The file is ignored by Git. `--no-ledger` skips the append.
7. **Lines.** The closeout begins at a fixed reserve of 50,000 tokens before the 70 percent line (`closeout.md`); at 70 the rotation is due (house guidance). In this version `gauge` only reports. A timer and the notification that the meter triggers each need Kevin's separate go, and a timer compares unrounded figures (649,960 of 1,000,000 prints as 65.0).
8. **Bodies.** Claude under `[host path 1]`. Codex under `[host path 2]`, its archived root and, where present, the VM-share Codex root. Copilot under `[host path 3]`. A partial id never matches as a suffix.

### Reviewed windows

Used only when neither the body nor the status line reports a window. Each row records where its figure came from and when it was observed. A model without a reviewed row stays "[words sha256=b23a6a8439c0dde5515893e7c90c1e3233b8616e634470f20dc4928bcf3609bc]".

```
[words sha256=41825676f51fdb967c2dec882b48e2f6c0b4efe2c441bff0f18df4812b91e6b0]
```

## Anecdotal Anchor

On 2026-10-30 this desk proposed rotating Claudio because his body was 78 MB. His meter read 32 percent: the file was large, not full. On the same day, the first run of `gauge` found what no estimate had flagged:
- Claudine was at 84.6 percent;
- Alan Codex was at 73.3 percent;
- George was at 60.3 percent and climbing.

It matched the desk's independent hand reading for Claudine, 845,588 tokens, to the token.

## Integrity Filter Warnings

- **Content.** Message content is never read into output, stored or printed. A Claude assistant row is parsed in memory only to take `usage`, `model` and `id`. A test plants a marker in content and finds it in 0 outputs.
- **Old readings.** An old reading is not an error. Only a later compaction or an archive makes it no longer current, and then the state says so.
- **Estimates.** A wake estimate made before a rotation is an estimate. The successor's first reading is the measurement, as with Joy's estimated 29 percent against her measured 39.
- **Window table.** A row needs a source and a date. Never add a window from memory or from a model's name.
- **Scope.** `gauge` changes nothing outside its ledger, `ledger.lock` and their directory. It installs no timer, sends no notification and touches no registry.
- **Boundary detection depends on two field values** (O1, resolved by the order-independent match in step 4). It no longer depends on field order or head length, but it still depends on Claude Code writing `type` `system` and `subtype` `compact_boundary`. Tests pin a boundary with extra leading fields, a side-conversation boundary that must not count, and a message whose content merely mentions the token. Re-check the two values on each Claude Code upgrade.
