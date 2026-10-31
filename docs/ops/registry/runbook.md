# Runbook Registry

Authoritative registry for operator-run procedures and the packet assets that carry them in Sessions. Framework: STELA (`Projects/STELA/docs/ops/registry/runbook.md`). A runbook is followed by a named writer with Kevin deciding at its stop points; it never redefines `DOCTRINE.md`. Updated 2026-10-30.

| ID | Name | File Path | Status | Notes |
| --- | --- | --- | --- | --- |
| RUNBOOK-01 | Rotation | docs/ops/specs/scripts/rotate.md | active by hand; script not written | Spec: `docs/ops/specs/scripts/rotate.md` (ported from Claudine Colbert's package runbook with Claudio's C11 to C13 and Kevin's decisions of 2026-10-30). Phases 0 to 9 with a stop point at each; tiers B (default), capsule-only and A; the writer's verified swap after Kevin's go, his `.NEW` swap as fallback; receipt `Receipts/<resident>-rotation-<n>-<date>.md`. Operator summary: `docs/MANUAL.md` sections 6 and 9. Automation: `ops/lib/scripts/rotate.py` (`SCRIPT-04`), [PLACEHOLDER: not written; writer named by Claude Shannon]. |
| RUNBOOK-02 | Resident Packet | ops/src/runbook/agent-input.yaml | spec written; asset placeholder | Spec: `docs/ops/specs/runbook/agent-input.md`. How a packet for a resident is written: to, from, owner, scope, authority, inputs, rules, stop condition, report. The asset file is `[PLACEHOLDER]` on 2026-10-30. [PLACEHOLDER: the paste-ready packet text in `ops/src/runbook/agent-input.yaml`; owner Claude Shannon.] |
