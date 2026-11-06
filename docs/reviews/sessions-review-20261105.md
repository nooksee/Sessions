<!-- redact: public copy; source sha256 d7f49ba1e280432f6bbea45546043bbaf5622a2b61d6fea6d90803b7ee681dfb; rules 8; mode record; words 0; sessions 0 whole, 0 truncated; host paths 0; decisions 11 -->
# Review of nooksee/sessions at `90c05f7` (2026-11-05)

Read-only. Written by Claude (Fable 5.1) for the Operator and the residents of the Sessions room. Nothing in the repository was changed; no push, no branch, no issue. Everything measured below was measured on a fresh shallow clone with 1,000 commits of history fetched (131 reachable from `main`).

> Admitted copy, 2026-11-05, by the Session Continuity Manager at the operator's direction. The received text is kept as intake with its SHA-256 67e2fa066dc2d0c2...; this copy differs from it in these ways and no other: the room's path and user tokens (`<room>`, `<control>`, `<user>`) in place of the host's literal names; the quotation marks removed from one sentence that quotes the room's own promise, so that the redact tool does not digest it as the operator's words; the Operator in place of the operator's name inside a quoted code line, as maintained documents do; item 11 reduced to one class-only line under PoT 5.1.4; one inner quoted term in item 3 named rather than printed under PoT 1.2.10; and two bracketed notes on a day count. Every item's disposition is in the Manager's record of 2026-11-05 at 23:43:55 EST.

## Verdict

The room took a port and made it a working office. The shape held (one word per tool, a spec and a suite beside each, the allowlist `.gitignore`, the ledger as a derived copy), and the team built on it instead of around it: the public gate, the redact tool, the notebook home, the launch wrapper, five phases of the rotate runner, an Auditor seated, and 131 commits in six days with every one of them passing the room's own gates. The law is short and amended by its own route. That is not what a failed port looks like.

Five things need repair now, two of them because the repository is public. Nothing needs to be redone from scratch. The biggest open risk is not in Git at all: PoT 5.3.3 is satisfied today only by a failing drive plus an interim copy on the boot drive, and it has been that way since 2026-10-30.

## What I ran

| Check | Result |
|---|---|
| Every suite, `python3 -I -B tools/test/test_*.py`, as a non-root user | 49 of 49 pass; `pytest -q tools/test`: 801 passed, 2 skipped, 820 subtests |
| The same suites as root | 48 of 49; `test_claude_resident.py` fails 1 of 39 because root ignores the `chmod 0o500` it relies on (test assumption, not a tool defect) |
| `ops/bin/help --test`, `ops/bin/template --test` | 14 of 14, 18 of 18 |
| PoT authorization gate, `constitution.py` on `HEAD~1..HEAD` | PASS |
| `ops/bin/help read` on the bare clone | 10 surfaces resolve; 3 honest `[PLACEHOLDER` lines in the manual |
| Fail-closed identity on a bare clone | `myself.py` reports UNDETERMINED caller identity; `claude-resident` prints usage and launches nothing |
| Tool, spec, suite parity | 43 tools, 43 specs, 43 suites |
| Contractions in maintained documents (AGENTS.md standard; DOCTRINE and archives excluded) | 0 |

## Blaring: repair now

**1. The public repository carries the host fingerprint in code and tests.** `<user>` or `<control>/...` occurs 30 times across 16 tracked files (`vitals.py` 7, `test_conflicts.py` 4, `test_media.py` 3, `test_identity.py` 3, `watch.py` 2, and one each in `alerts.py`, `capsule.py`, `estimate.py`, `gauge.py`, `miner.py`, `prime.py`, `retention.py`, `rounds.sh`, `telemetry.py`, `test_alerts_arity.py`, `test_successor.py`), plus 1 in the admitted record `archives/PoT-draft-v0-de5d6c0c.md`. `capsule.py` line 89 embeds the sentence "The operator is the Operator, user `<user>`. The working root for this repo is `<control>`" as capsule text. The documents adopted the `<room>` and `<control>` tokens; the map says "code defaults and tests keep their literal paths" and NOW.md defers the code-and-tests pass to a later programme. On a private repository that deferral was reasonable; on a public one it is the first fact an outsider learns about the host. The fix pattern already exists in the room: `pycharm.py` reads its identifiers from an ignored `ops/etc/pycharm-chats.json` and refuses without it. Do the same for the volume roots (the private `ops/etc/host-bindings.json` is the obvious home), fail closed when absent, and give the tests fixtures. Then re-admit or redact the draft PoT snapshot.

**2. The redact tool is unregistered.** `ops/lib/scripts/redact.py` and `tools/test/test_redact.py` appear in neither `docs/ops/registry/scripts.md` (43 rows for 44 files) nor `docs/ops/registry/test.md` (`test_redact.py` and `test_ror_join.py` missing, 47 of 49 registered) nor the map's "Where everything lives" table. This is the instrument of PoT 1.2.10 and of the whole public gate; it has a spec, so the registry rows are the only thing missing. Three rows.

**3. The redaction has a boundary defect that left a digest of nothing.** `[words sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855]` is the SHA-256 of the empty string. It occurs 3 times in tracked public copies: `RoR.md` line 158 and `archives/receipts/landing-stage-a-20261101.md` twice. At RoR.md:158 the operator's words contained an inner quoted term and the tool split the span at the inner quotes, so an inner quoted term sits in the clear between two digests. The exposed word is harmless; the rule is not, because the next inner quote could be anything. A rule for nested quotes (one span, outermost quotes) and a refusal to emit an empty-span digest, then re-render the two files from their sources, with the revision named in the header the way C6 revisions were.

**4. `docs/INDEX.md` is the front door and it is two days stale while claiming completeness.** "Every document in `Sessions/docs/`, one line each ... Updated 2026-11-03." Missing: `ops/specs/scripts/redact.md`, `notice.md`, `claude-resident.md`, `ops/specs/runbook/repository.md`, and 4 of the 8 test specs (`myself`, `notice`, `rotate`, `claude-resident`). Section 4 links five documents that the root allowlist excludes from the repository (`clinic-aggregate-contract.md`, `resource-state-contract.md`, the field guide, the review response, the `.patch`), so a public reader gets five dead links; section 1 links `../HANDOFF.md`, which is ignored. `docs/ops/specs/scripts/alerts.md` (a current spec) also points at `docs/clinic-aggregate-contract.md`. Either admit those documents or label them private where they are cited.

**5. The binary registry and the README disagree with `ops/bin/`.** `docs/ops/registry/binaries.md` has 2 rows and says "both binaries"; the README says "the two binaries"; `ops/bin/claude-resident` is the third, registered as `SCRIPT-45` in the script registry with its spec at `docs/ops/specs/scripts/claude-resident.md`, while the map calls it a binary. One home: `OPS-BIN-03` and `docs/ops/specs/binaries/`. The README's tool list also names a `custody` tool; 0 tools of that name exist.

## Needs tightening, not redoing

**6. NOW.md is a board with a history attached.** 448 lines; the live state is lines 16 to 96; lines 98 to 449 are dated boards from 2026-07-25 to 2026-11-03 carrying retired paths (`Receipts/`, `Evidence/`, `Backup/`, `../Decisions/`) and counts the file itself says are not current. The "Updated:" line is eight timestamps long. Every resident reads all 448 lines on wake (`help read`, step 7). PoT 1.3.3 and 1.2.12 make NOW.md orientation; move the dated boards into one admitted record (`archives/board-history-20261105.md`) and hold NOW.md under 100 lines with one Updated line and a pointer to the receipts.

**7. The map's rule 4 contradicts the root.** "A root file is a pointer, not a document," while the root holds DOCTRINE.md (642 lines), NOW.md (448), RoR.md (164) and README.md (41). PoT 1.1.9 and 1.3.12 name those surfaces at the root, so the rule is the thing that is wrong; amend it to name the four exceptions.

**8. `.gitignore` admits `ops/` whole and ignores only `/ops/etc/*.json` and `/ops/etc/notebooks/`.** A binding file in any other format dropped into `ops/etc/` would publish. Tighten to `/ops/etc/*` with `!/ops/etc/.gitkeep`. The rest of the allowlist, with its stated reasons, is the best `.gitignore` I have read this year.

**9. `test_claude_resident.py` assumes a non-root runner.** Guard the `chmod 0o500` case with `unittest.skipIf(os.geteuid() == 0, ...)` so a root reviewer gets 39 of 39 instead of a false failure.

**10. Commit subjects.** 30 non-merge commits since 2026-11-04; many subjects are paragraphs ("The board on the evening of 2026-11-05: the team formed and an Auditor seated, the wrapper's source passed review ..."). `git log --oneline` stops being a log. The body is where that text belongs; a subject under 72 characters. Style, not law. Merge style is also mixed (35 merge commits early, rebase merges later); pick one.

**11. Accepted exposure, recorded for completeness.** Commit metadata on `main` carries material of a class the operator designated private on 2026-11-05; the operator decided the same day that the history stands. Recorded by class only in this copy (PoT 5.1.4); the decision is the operator's to revisit.

## What is left (the room's own board, read against the port)

- W6: rotate phases 6 to 9 and the first real rotation; provider-native acceptance is unproved (PoT 4.4.7).
- W5: the provider route proof, seeding, the first projection and seal runs, the launch setting; each a named go.
- W4: the cadence go and the first real notification.
- The closeout migration hold (`storage/closeout` legacy) is open and closeout is unwired; the gauge and mind-lock cutovers are done.
- PoT 5.3.3, two independent verified copies on different drives: `hard_vol2` has been the failing second medium since 2026-10-30 (36 days [admission note: the received text says 36; the two dates it gives are 6 days apart]), with an interim third tier on the boot drive. The drive is bought; the swap is George's reviewed operation on the operator's word. Until it runs, the room's central promise, nothing is deleted, only copied, verified and retired, rests on a drive that is known to be failing. This outranks everything in Git.
- The 4.1.9 Auditor amendment under 7.3 review; the unresolved family of unregistered bodies; the six drift paths in Control's frozen runtime.
- `help curriculum` and the `PRESERVATION_MANIFEST.md` location remain honest placeholders.
- Of the port's eight lanes, all eight landed in some form: Scripts to `ops/lib/scripts/` (lane 1), the legacy lanes frozen, the runtime to Control (block 7), Evidence to `archives/legacy/Evidence/`, receipts admitted selectively after redaction, the mind manifest integrated, root pointers placed, the retired `START-HERE.md` pointer removed. The port's own handoff items are closed.

## Just fine, and said plainly

- 49 suites, 801 tests, 820 subtests, 0 failures as a non-root user; CI runs every suite, both self-tests and the PoT gate on every pull request and push, in 10 minutes or less.
- PoT.md: 226 lines, clause numbers permanent, 43 retired slots marked and never reused, 7.5 preservation map, 7.3 amendment route used three times after the first ratification (RoR-12, RoR-14, RoR-18) and the exception route used once and recorded as such (RoR-16).
- RoR.md as a derived copy with 26 word digests, attributed corrections instead of edits, and `constitution.py` refusing a PoT change without its authority record.
- 43 of 43 tools with a spec and a suite; the newest tools (`notice`, `redact`, `rotate`, `claude-resident`) arrived with test specs, which the ported ones never had.
- Fail-closed identity: `myself.py`, `claude-resident` and the mind tool refuse on a bare clone rather than guess; the mind tool verifies the nearest Git ancestor before any write (B1).
- `CLAUDE.md` appoints nobody, and says why, with the dates of the failure it prevents. That paragraph is worth more than most constitutions.
- `<room>` and `<control>` as path tokens in every maintained document; 0 contractions in maintained documents; `[PLACEHOLDER` lines where a tool does not exist yet instead of prose that pretends.

## Numbers

Files tracked: 220 (3.9 MB). Commits reachable from `main`: 131; since 2026-11-04: 30 non-merge plus merges. Tools 43, specs 43, suites 49, test specs 8. Registry gaps: 3 rows (redact script, redact test, ror_join test) plus 1 misfiled binary. Host-path occurrences in tracked files: 30 in 16 files plus 1 record. Empty-span digests: 3 in 2 files. Dead links from `docs/INDEX.md` for a public reader: 6. Days on a failing second custody medium: 36 [admission note: by the dates the review gives, 6]. Changes made by this review: 0.
