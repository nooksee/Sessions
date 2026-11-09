# Documentation Index (Front Door)

Every document in `Sessions/docs/`, one line each, and the root files that point into them. Framework: STELA (`Projects/STELA/docs/INDEX.md`). Updated 2026-11-05. Status of each tool lives in its registry, not here.

## 0. Primary Read-in (Start Here)
* [../PoT.md](../PoT.md): the local constitution; the only current Sessions law.
* [../ops/lib/manifests/CONTEXT.md](../ops/lib/manifests/CONTEXT.md): canonical read-in order, reader classes and domain pointers.
* [../ops/lib/manifests/CONSTRAINTS.md](../ops/lib/manifests/CONSTRAINTS.md): delegated operational requirements; not a second constitution or a daemon parser.
* [MANUAL.md](MANUAL.md): the operations manual; people and roles, the four-tool loop, reading a gauge, closeout, minds, rotation, custody, labels, the operator's card, the rules for new files, glossary.
* [ops/README.md](ops/README.md): the map; the four tools in one loop, where everything lives, and the rules for every new file.
* [INDEX.md](INDEX.md): this index.

## 1. Root Files (pointers into the room)
* [../PoT.md](../PoT.md): Sessions law; Control policy remains higher.
* [../AGENTS.md](../AGENTS.md): room routing and parent authority; filing mechanics are in CONSTRAINTS C01.
* [../CLAUDE.md](../CLAUDE.md): Claude entry instructions; identity/read-in follow CONTEXT X01 and the native session and registry.
* [../ops/lib/manifests/CONTEXT.md](../ops/lib/manifests/CONTEXT.md): required reader context and canonical domain pointers.
* [../ops/lib/manifests/CONSTRAINTS.md](../ops/lib/manifests/CONSTRAINTS.md): human-consumed operating contract.
* [START-HERE.md](START-HERE.md): five-minute orientation for a newcomer; pointers only.
* [../README.md](../README.md): the room charter and its older map of lanes.
* [../INDEX.md](../INDEX.md): the room's catalog of lanes and current surfaces.
* [../NOW.md](../NOW.md): current room state and open items; no rules.
* [../HANDOFF.md](../HANDOFF.md): the resident's durable handoff and wake note (private: ignored by the repository, present on the host only).
* `../MIND.md`: the room's mind pointer, one line per resident; written only by `mind.py`, out of Git. Not yet created on 2026-10-30.

The former broad method document is preserved in place as historical source;
current craft and mechanics are in the manual and specifications.

## 2. Operations: Registries
* [ops/registry/scripts.md](ops/registry/scripts.md): the tools in `ops/lib/scripts/` and their status.
* [ops/registry/binaries.md](ops/registry/binaries.md): the entry points in `ops/bin/` (help, template) and their status.
* [ops/registry/test.md](ops/registry/test.md): the test suites in `tools/test/` and their counts.
* [ops/registry/runbook.md](ops/registry/runbook.md): operator-run procedures (rotation, the resident packet).

## 3. Operations: Specifications
Scripts (STELA's sections: rationale, mechanics, anchor, warnings):
* [ops/specs/scripts/gauge.md](ops/specs/scripts/gauge.md): how full each resident is, from the provider's own token figures; states, window authority, the reviewed window table, the ledger.
* [ops/specs/scripts/closeout.md](ops/specs/scripts/closeout.md): implemented closeout hook behavior, reserve, privacy limits and separate installation gates.
* [ops/specs/scripts/mind.md](ops/specs/scripts/mind.md): the mind as a chain of immutable leaves, written only with the operator's words; commands, gates, screens, and Claudio's section 130 dispositions.
* [ops/specs/scripts/rounds.md](ops/specs/scripts/rounds.md): clinic report and separate Control source-drift wrapper behavior; no deployment authority.
* [ops/specs/scripts/rotate.md](ops/specs/scripts/rotate.md): the rotation, phase by phase with stop points; tiers, capsule, custody, install, acceptance, close.
* [ops/specs/scripts/constitution.md](ops/specs/scripts/constitution.md): the PoT authorization gate; a changed law needs its coupled ledger entry, snapshot and authority leaf.
* [ops/specs/scripts/redact.md](ops/specs/scripts/redact.md): the public-copy renderer; digests the operator's words, placeholders host paths and session identifiers, fails closed on the unclassified.
* [ops/specs/scripts/notice.md](ops/specs/scripts/notice.md): the operator-only closeout notice from one gauge row; dry run writes no state.

Ported from `Scripts/` on 2026-11-01 (`docs/ops/specs/runbook/port.md`), each spec opening with the script's own first line:
* [ops/specs/scripts/pressure.md](ops/specs/scripts/pressure.md): ported from `Scripts/analyze_codex_compact_context_pressure.py`; Gate copied Codex JSONL candidates for compact/context pressure.
* [ops/specs/scripts/items.md](ops/specs/scripts/items.md): ported from `Scripts/analyze_codex_response_item_pressure.py`; Analyze Codex JSONL response-item pressure without rewriting sessions.
* [ops/specs/scripts/bloat.md](ops/specs/scripts/bloat.md): ported from `Scripts/analyze_codex_session_bloat.py`; Analyze Codex session JSONL pressure without modifying session files.
* [ops/specs/scripts/estimate.md](ops/specs/scripts/estimate.md): ported from `Scripts/analyze_codex_token_context_pressure.py`; Estimate Codex JSONL context pressure in tokens.
* [ops/specs/scripts/archive.md](ops/specs/scripts/archive.md): ported from `Scripts/archive_codex_session.py`; Archive selected Codex session files into root Backup.
* [ops/specs/scripts/successor.md](ops/specs/scripts/successor.md): ported from `Scripts/build_claude_resident.py`; Build a new Claude resident from a donor body.
* [ops/specs/scripts/rotation.md](ops/specs/scripts/rotation.md): ported from `Scripts/build_codex_rotation.py`; Rotate a Codex resident into a fresh provider-created container.
* [ops/specs/scripts/dossier.md](ops/specs/scripts/dossier.md): ported from `Scripts/build_codex_session_handoff.py`; Build a deterministic Codex session handoff packet.
* [ops/specs/scripts/reid.md](ops/specs/scripts/reid.md): ported from `Scripts/build_codex_session_reid_candidate.py`; Build a derivative Codex JSONL with structural session IDs rewritten.
* [ops/specs/scripts/sandbox.md](ops/specs/scripts/sandbox.md): ported from `Scripts/build_codex_session_sandbox.py`; Prepare an isolated Codex session JSONL sandbox without launching Codex.
* [ops/specs/scripts/capsule.md](ops/specs/scripts/capsule.md): ported from `Scripts/build_codex_succession_capsule.py`; Build a six-question Codex succession capsule from repo canon and evidence.
* [ops/specs/scripts/chamber.md](ops/specs/scripts/chamber.md): ported from `Scripts/build_codex_vm_loadtest_env.py`; Build a local VM load-test chamber for a prepared Codex session sandbox.
* [ops/specs/scripts/prime.md](ops/specs/scripts/prime.md): ported from `Scripts/build_prime_session_candidate_packet.py`; Build a prime session candidate packet without copying raw sessions.
* [ops/specs/scripts/tablet.md](ops/specs/scripts/tablet.md): ported from `Scripts/build_tablet_codex_successor.py`; Build a current-version, CLI-native Codex successor from a copied session body.
* [ops/specs/scripts/vitals.md](ops/specs/scripts/vitals.md): ported from `Scripts/check_claude_session_health.py`; Report health for Claude Code session JSONL files.
* [ops/specs/scripts/conflicts.md](ops/specs/scripts/conflicts.md): ported from `Scripts/check_codex_thread_writer_conflicts.py`; Detect the active-writer condition that can hang a chat on "Initializing".
* [ops/specs/scripts/telemetry.md](ops/specs/scripts/telemetry.md): ported from `Scripts/check_codex_token_health.py`; Report token health for Codex rollout JSONL files.
* [ops/specs/scripts/identity.md](ops/specs/scripts/identity.md): ported from `Scripts/check_identity_lock.py`; Verify that every resident's identity agrees in all four places it is written.
* [ops/specs/scripts/myself.md](ops/specs/scripts/myself.md): ported from `Scripts/check_myself.py`; Measure one resident's native identity and session health, without writes.
* [ops/specs/scripts/drift.md](ops/specs/scripts/drift.md): ported from `Scripts/check_resident_center_drift.py`; Detect drift between the frozen Sessions runtime donor and the product source. (no spec in this room; Control's tool, SCRIPT-24.)
* [ops/specs/scripts/retention.md](ops/specs/scripts/retention.md): ported from `Scripts/check_session_retention.py`; Report, and on explicit request enforce, the official session-folder policy.
* [ops/specs/scripts/gate.md](ops/specs/scripts/gate.md): ported from `Scripts/check_writer_gate.py`; Verify the single-writer gate before any session-body write.
* [ops/specs/scripts/alerts.md](ops/specs/scripts/alerts.md): ported from `Scripts/clinic_alert_diff.py`; Edge-triggered alert layer for the clinic rounds report.
* [ops/specs/scripts/janitor.md](ops/specs/scripts/janitor.md): ported from `Scripts/codex_claim_janitor.py`; Release writer claims the remote daemon is squatting on, automatically.
* [ops/specs/scripts/condense.md](ops/specs/scripts/condense.md): ported from `Scripts/condense_codex_compacted_history.py`; Condense old Codex compacted-history rows in copied JSONL candidates.
* [ops/specs/scripts/transcripts.md](ops/specs/scripts/transcripts.md): ported from `Scripts/condense_codex_tool_transcripts.py`; Condense old Codex tool transcript rows in copied JSONL candidates.
* [ops/specs/scripts/elide.md](ops/specs/scripts/elide.md): ported from `Scripts/elide_codex_tool_outputs.py`; Elide oversized Codex tool-call outputs while preserving every turn.
* [ops/specs/scripts/media.md](ops/specs/scripts/media.md): ported from `Scripts/externalize_claude_image_payloads.py`; Move base64 media out of a Claude session body into files, losslessly.
* [ops/specs/scripts/images.md](ops/specs/scripts/images.md): ported from `Scripts/externalize_codex_image_payloads.py`; Build an analysis-only Codex JSONL copy with oldest image payloads externalized.
* [ops/specs/scripts/history.md](ops/specs/scripts/history.md): ported from `Scripts/inspect_compacted_history.py`; Inspect Codex compacted-history rows without modifying session files.
* [ops/specs/scripts/inventory.md](ops/specs/scripts/inventory.md): ported from `Scripts/inventory_codex_sessions.py`; Inventory local Codex session assets without modifying them.
* [ops/specs/scripts/workers.md](ops/specs/scripts/workers.md): ported from `Scripts/inventory_worker_threads.py`; Classify Codex sessions into residents, worker threads, and unknowns.
* [ops/specs/scripts/miner.md](ops/specs/scripts/miner.md): ported from `Scripts/mine_codex_logs_compaction_events.py`; Read-only Codex log miner for compact and context failure evidence.
* [ops/specs/scripts/pycharm.md](ops/specs/scripts/pycharm.md): retired from routine use 2026-11-07; ported from `Scripts/reconcile_pycharm_ai_surfaces.py`; Reconcile known PyCharm AI-session surface residue without touching JSONL bodies.
* [ops/specs/scripts/resources.md](ops/specs/scripts/resources.md): ported from `Scripts/resident_resource_collector.py`; Resident Resource Governor -- collector.
* [ops/specs/scripts/limits.md](ops/specs/scripts/limits.md): ported from `Scripts/validate_codex_session_loader_limits.py`; Validate copied Codex JSONL candidates against observed loader limits.
* [ops/specs/scripts/watch.md](ops/specs/scripts/watch.md): ported from `Scripts/watch_codex_session_size.py`; Watch Codex sessions and emit operator-visible warnings.

Binaries:
* [ops/specs/binaries/help.md](ops/specs/binaries/help.md): spec for `ops/bin/help`, the command-line wayfinding entry point.
* [ops/specs/binaries/template.md](ops/specs/binaries/template.md): spec for `ops/bin/template`, the template rendering router.

Runbook:
* [ops/specs/runbook/agent-input.md](ops/specs/runbook/agent-input.md): how a packet for a resident is written; to, from, owner, scope, authority, inputs, rules, stop condition, report.
* [ops/specs/runbook/port.md](ops/specs/runbook/port.md): the port of the room's legacy lanes to the STELA base, every lane, with the path map and what Control must still repoint.
* [ops/specs/runbook/repository.md](ops/specs/runbook/repository.md): the repository's boundary, Git lifecycle, recovery and hosted checks.

Tests:
* [ops/specs/tools/test/gauge.md](ops/specs/tools/test/gauge.md): what `tools/test/test_gauge.py` proves, test by test (21).
* [ops/specs/tools/test/mind.md](ops/specs/tools/test/mind.md): what `tools/test/test_mind.py` proves, test by test (43).
* [ops/specs/tools/test/closeout.md](ops/specs/tools/test/closeout.md): synthetic behavior and non-deployment limits of `tools/test/test_closeout.py`.
* [ops/specs/tools/test/rounds.md](ops/specs/tools/test/rounds.md): syntax and static-integrity checks in `tools/test/test_rounds.py`.
* [ops/specs/tools/test/myself.md](ops/specs/tools/test/myself.md): the self-check's suite.
* [ops/specs/tools/test/notice.md](ops/specs/tools/test/notice.md): the notice's suite.
* [ops/specs/tools/test/rotate.md](ops/specs/tools/test/rotate.md): the rotate runner's suite, synthetic dry-run phases 0 to 9.

## 4. Contracts and Guides (earlier clinic work)
* [clinic-aggregate-contract.md](clinic-aggregate-contract.md): the public clinic health file (`logs/clinic-aggregate.json`) for consumers outside Sessions. (private: not in the repository; on the host only.)
* [resource-state-contract.md](resource-state-contract.md): the Resource Governor state file (`logs/resource-state.json`) written by the status-line collector; gauge's last-resort window source. (private: not in the repository; on the host only.)
* [session-continuity-apprentice-field-guide.md](session-continuity-apprentice-field-guide.md): historical orientation for apprentices and reviewers; its legacy authority wording is not current policy. (private: not in the repository; on the host only.)
* [session-clinic-integration-review-response.md](session-clinic-integration-review-response.md): the clinic's 2026-07-24 answer to OSAI's integration review request; ownership split and adapter contract. (private: not in the repository; on the host only.)
* [tray-session-clinic-watchdog-20260724.patch](tray-session-clinic-watchdog-20260724.patch): a 2026-07-24 diff adding clinic status to the Control remote-control tray script; a record, not a document to apply. (private: not in the repository; on the host only.)

## 5. Templates (not documents; listed so they are found)
* `../ops/src/docs/spec.md.tpl`: the spec template used by `ops/bin/template`.
* `../ops/src/runbook/agents/agent-input.yaml`: resident packet form fields and delivery boundary.
* `../ops/src/reports/source-change.md.tpl`: bounded source/configuration change receipt, distinct from rotation and custody receipts.

## 6. Reviews (read-only reviews of the repository, admitted as public copies)
* [reviews/sessions-review-20261105.md](reviews/sessions-review-20261105.md): the port's writer's review of the room at 90c05f7e, 2026-11-05: verdict, repairs, what is left; admitted through the redact tool with the room's path tokens.
