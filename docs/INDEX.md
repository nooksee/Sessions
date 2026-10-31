# Documentation Index (Front Door)

Every document in `Sessions/docs/`, one line each, and the root files that point into them. Framework: STELA (`Projects/STELA/docs/INDEX.md`). Updated 2026-10-30. Status of each tool lives in its registry, not here.

## 0. Primary Read-in (Start Here)
* [MANUAL.md](MANUAL.md): the operations manual; people and roles, the four-tool loop, reading a gauge, closeout, minds, rotation, custody, labels, the operator's card, the rules for new files, glossary.
* [ops/README.md](ops/README.md): the map; the four tools in one loop, where everything lives, and the rules for every new file.
* [INDEX.md](INDEX.md): this index.

## 1. Root Files (pointers into the room)
* [../DOCTRINE.md](../DOCTRINE.md): the method; four identities, failure taxonomy, the transplant recipe, custody tiers. It wins over the manual.
* [../AGENTS.md](../AGENTS.md): room instructions for every agent; ownership, required reading, hard safety boundary.
* [../CLAUDE.md](../CLAUDE.md): instructions for the resident Claude; who you are on wake, and where identity is decided (the registry).
* [../START-HERE.md](../START-HERE.md): five-minute orientation for a newcomer; pointers only.
* [../README.md](../README.md): the room charter and its older map of lanes.
* [../INDEX.md](../INDEX.md): the room's catalog of lanes and current surfaces.
* [../NOW.md](../NOW.md): the live board of residents and open items (last updated 2026-10-19).
* [../HANDOFF.md](../HANDOFF.md): the resident's durable handoff and wake note.
* `../MIND.md`: the room's mind pointer, one line per resident; written only by `mind.py`, out of Git. Not yet created on 2026-10-30.

Per the map, `HANDOFF.md`, `NOW.md`, `INDEX.md` and `START-HERE.md` are to become pointer-first root files.

## 2. Operations: Registries
* [ops/registry/scripts.md](ops/registry/scripts.md): the tools in `ops/lib/scripts/` (gauge, closeout, mind, rotate) and their status.
* [ops/registry/binaries.md](ops/registry/binaries.md): the entry points in `ops/bin/` (help, template) and their status.
* [ops/registry/test.md](ops/registry/test.md): the test suites in `tools/test/` and their counts.
* [ops/registry/runbook.md](ops/registry/runbook.md): operator-run procedures (rotation, the resident packet).

## 3. Operations: Specifications
Scripts (STELA's sections: rationale, mechanics, anchor, warnings):
* [ops/specs/scripts/gauge.md](ops/specs/scripts/gauge.md): how full each resident is, from the provider's own token figures; states, window authority, the reviewed window table, the ledger.
* [ops/specs/scripts/closeout.md](ops/specs/scripts/closeout.md): the signal from inside a resident at its reserve, and the closeout card (design only).
* [ops/specs/scripts/mind.md](ops/specs/scripts/mind.md): the mind as a chain of immutable leaves, written only with Kevin's words; commands, gates, screens, and Claudio's section 130 dispositions.
* [ops/specs/scripts/rotate.md](ops/specs/scripts/rotate.md): the rotation, phase by phase with stop points; tiers, capsule, custody, install, acceptance, close.

Binaries:
* [ops/specs/binaries/help.md](ops/specs/binaries/help.md): spec for `ops/bin/help`, the command-line wayfinding entry point.
* [ops/specs/binaries/template.md](ops/specs/binaries/template.md): spec for `ops/bin/template`, the template rendering router.

Runbook:
* [ops/specs/runbook/agent-input.md](ops/specs/runbook/agent-input.md): how a packet for a resident is written; to, from, owner, scope, authority, inputs, rules, stop condition, report.

Tests:
* [ops/specs/tools/test/gauge.md](ops/specs/tools/test/gauge.md): what `tools/test/test_gauge.py` proves, test by test (21).
* [ops/specs/tools/test/mind.md](ops/specs/tools/test/mind.md): what `tools/test/test_mind.py` proves, test by test (30).

## 4. Contracts and Guides (earlier clinic work)
* [clinic-aggregate-contract.md](clinic-aggregate-contract.md): the public clinic health file (`Evidence/clinic-aggregate.json`) for consumers outside Sessions.
* [resource-state-contract.md](resource-state-contract.md): the Resource Governor state file (`Evidence/resource-state.json`) written by the status-line collector; gauge's last-resort window source.
* [session-continuity-apprentice-field-guide.md](session-continuity-apprentice-field-guide.md): orientation for apprentices and reviewers; separates resident health, provider capacity, mechanism health and activation authority.
* [session-clinic-integration-review-response.md](session-clinic-integration-review-response.md): the clinic's 2026-07-24 answer to OSAI's integration review request; ownership split and adapter contract.
* [tray-session-clinic-watchdog-20260724.patch](tray-session-clinic-watchdog-20260724.patch): a 2026-07-24 diff adding clinic status to the Control remote-control tray script; a record, not a document to apply.

## 5. Templates (not documents; listed so they are found)
* `../ops/src/docs/spec.md.tpl`: the spec template. `[PLACEHOLDER]` on 2026-10-30.
* `../ops/src/runbook/agent-input.yaml`: the resident packet template. `[PLACEHOLDER]` on 2026-10-30.
