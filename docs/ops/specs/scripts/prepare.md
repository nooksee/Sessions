# Technical Specification: prepare

Script: `ops/lib/scripts/prepare.py` (writer: Claudine Colbert, `claudine-colbert`). Tests: `tools/test/test_prepare.py`. Spec writer: Claudine Colbert, 2026-11-09. Status: built, W6 slice 7, disposable variant only. Design: `storage/active/continuity-loop-w5w6-20261105/w6-slice7-producer-design.md` revision 1 (d0fa31cf), passed by the Auditor in bernard.md section 253.

## First Principles Rationale

Slice 6's engine (`rotate.py`, the native disposable route) consumes a phase-5 `rotate-native-gates/1` record, a built candidate, a capsule and a window as supplied files. It produces none of them, and `rotate.py`'s own phases 0 to 5 take fixture bodies only. The Auditor's G1 (bernard.md section 251): nothing implemented makes those files, so the procedure's E1 and the run packet had no producer. The Manager's ruling was a builder slice, reviewed like every other, with no hand-built set (packet `packet-claudine-slice7.md`, 3ee1694a). This tool is that producer. It is joined to the engine only through the files the engine already reads, and it never touches `rotate.py`.

## Mechanics and Sequencing

1. **The request.** `--request` names `rotate-native-prepare/1` in the operation's evidence folder E = `<room>/storage/active/<operation>/` (0700), bound by `--request-sha256`. It names the room, the operation, the project folder W, the donor D and the destination T (each with path, `session_id` and `sha256`), the phase-0 record and the cut reason (each with path and hash, in E), and `built_at`. Every path is plain and absolute, and W may not overlap the room.
2. **No resident.** A D or T whose `session_id` is any registered resident's in `ops/etc/resident-identities.json` is refused before anything but the request and the registry is read (the Manager's O1 ruling, condition 3).
3. **No overwrite.** Any output already present in E is a refusal.
4. **T** is hashed only, bracketed by two lstat readings, and must equal the request.
5. **D** is read in one streaming pass, bracketed the same way and hashed whole. It may be at most 64 MiB (the engine's own limit), with each line terminated and at most 16 MiB. Every `sessionId` and `session_id` must be D's, and every `cwd` W's. Only the rows after the boundary are kept, at most 4,096 rows and 8 MiB. Before the boundary, only the last usage reading is kept, read as `gauge.read_claude` reads it: a non-sidechain assistant row, input plus cache read plus cache creation.
6. **Phase 4, the window** (rotate's `window_ready`, written fresh; design O2):
   - exactly one boundary, with `compactMetadata.trigger` `manual`;
   - a pre-boundary reading whose model has a reviewed window in the gauge's table, at or above 70 percent of it (`trigger`);
   - its pressure band not None (`closeout`, disposable variant);
   - the phase-0 record equal to that reading, field by field;
   - the reading before the boundary;
   - exactly one `isCompactSummary` row;
   - the cut at the first genuine user prompt after it, by rotate's `user_prompt`, followed by a non-meta, non-sidechain assistant reply;
   - leading IDE notices (`<ide_opened_file>`, `<ide_selection>`, myself.py's exact shape) are passed over before that test, so a prompt sent while a file is open in the editor is still genuine. A notice with nothing after it, or with a closing notice tag left after it, is not. The engine's own `user_prompt` takes the same strip in the Apprentice's correction slice (packet 37, item 4a), so the two agree on the cut only when both are merged (claudine.md section 234; bernard.md section 286).
   - tool calls and results paired within the window;
   - `built_at` no earlier than D's last row.

   The selection is the boundary, the summary, then the cut to the end, and only the cut is reparented to the summary. The wake estimate is the window's last usage reading plus the capsule's bytes, as an upper bound on its tokens; it must be at most a fifth of the window.
7. **Phase 5, the build:**
   - E is checked Git-private by `mind.git_exposed`.
   - `window.jsonl` is written, then `successor.main` runs in process on it alone: field-only re-identification to T and the orientation, with `cwd` W. Its output is captured into `builder-output.txt`, which is private.
   - The orientation's time becomes `built_at`.
   - `media.Externalizer` writes into `E/media`, so every pointer names its final path.
   - Two labels close the candidate, "W6 disposable destination".
   - rotate's static list (`static_gates`, written fresh) and the media checks run before `candidate.jsonl`, `capsule.txt`, `window.json` and `gates.json` are written.
   - The build runs under umask 0077, and each file is made by exclusive create at 0600.
8. **The gates record**, as the engine reads it (rotate.py e7d926af, lines 1517 to 1528):
   - `schema` and `phase` 5;
   - `donor_sha256`, `pristine_sha256` and `candidate_sha256`;
   - `gates`: exactly `trigger`, `closeout`, `operator_compaction`, `window`, `static` and `media`, each `true`.

   A failed check is a refusal, never a `false`. Beside the record: `detail` holds each sub-check, and `provenance.closeout` says `"evidence": "band reading"`, with tokens, window, band and the reading's source (row, time, phase-0 hash), states the overlap with `trigger`, and gives `"delivered_card": "NOT APPLICABLE"`.
9. **The report** prints the plan fragment: the `candidate`, and the `artifacts` `window`, `capsule`, `gates` and `window-rows`, plus one `media-<sha12>` per file, each with path and hash. It prints no session identifier. `--dry-run` runs step 6 and everything before it, and writes nothing.
10. **Exit codes:** 0 done; 2 refused (`prepare: refused: <reason>`, nothing written); 3 a refusal or failure after the build began. Exit 3 prints `failed` and the outputs present, and removes nothing. `gates.json` is always written last, so an engine never meets a record from a failed run.

## Anecdotal Anchor

- The Auditor's G1, bernard.md section 251 (2026-11-09 18:41 EST).
- The design's PASS, sections 252 and 253.
- The Manager's O1 ruling, recorded in claudine.md section 215 and its addition.
- The engine was read from slice 6's frozen postimages (FROZEN.md c135737f, `rotate.py` e7d926af).
- The suite's integration test runs the engine's own `native_rows` on the candidate, from that frozen file.

## Integrity Filter Warnings

- It refuses, without writing:
  - a registered resident's session;
  - a request not in E, or not matching its hash;
  - E not private, or an output present;
  - a hash mismatch for D or T, or either changing during its read;
  - a foreign session or another project in D, or a line unbounded or unterminated;
  - not exactly one manual boundary, or not exactly one summary;
  - a reading below the due line, or one not equal to the phase-0 record, or after the boundary;
  - a model with no reviewed window;
  - no genuine cut, no reply after it, unpaired tool calls, a window over its bound, or an estimate over a fifth;
  - `built_at` before D's end;
  - E exposed to Git.
- After the build begins, any static or media failure, a payload left inline under the Externalizer's 256-character floor, or more than 64 artifacts (four fixed and one per media file, counted before `candidate.jsonl` and `gates.json` are created) stops with exit 3, and no record is written.
- **What it reads:** for the live exercise, it reads the donor's text and writes it into E, under the operation's content authorization, which the run packet's go must carry (the Auditor's N1). Its tests read only synthetic bodies.
- **What it never does:** write outside E, read another resident's body, change D or T, or touch a production JSONL.
- **What it is not:** the resident route. The delivered closeout card, the registry, the launcher and the mind (phases 0 to 2 for a resident) are out of its scope, and the band never stands in for the card.
