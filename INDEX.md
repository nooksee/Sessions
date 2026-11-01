# Sessions Index

## Start Here

- [DOCTRINE.md](DOCTRINE.md) — **the canonical method; read first**
- [NOW.md](NOW.md) — live board: current threads, numbers, open items
- [README.md](README.md) — charter, map, ground rules
- [Apprentice field guide](docs/session-continuity-apprentice-field-guide.md)
  — separates resident health, provider capacity, mechanism health, and
  activation authority

## Lanes

- [Archived/](Archived/README.md): retained raw payloads; JSONL ignored by git.
- [Attic/](Attic/README.md): staging lane for removals + AUDIT (offload, do not delete).
- [Candidates/](Candidates/README.md): historical transplant bodies + prime starter packet.
- [Evidence/](Evidence/README.md): generated measurements; append-only, stamped filenames.
- [Lab/](Lab/README.md): experiment workbench; JSONL ignored by git.
- [Plans/](Plans/README.md): superseded by DOCTRINE; provenance only.
- [Receipts/](Receipts/README.md): one receipt per action; append-only.
- [Resident-Center/](Resident-Center/README.md): Sessions-owned operator
  surface, imported lineage, tests, host profile, and productization gates.
- [Scripts/](Scripts/README.md): the toolbox.

## Current Surfaces

- Token health: `Scripts/check_codex_token_health.py` (run it; no stale report is authoritative)
- Session inventory: [Evidence/codex-session-assets-summary.txt](Evidence/codex-session-assets-summary.txt)
- Handoff: [Evidence/codex-session-handoff-current.txt](Evidence/codex-session-handoff-current.txt)
- Succession capsule: [Evidence/codex-succession-capsule-current.md](Evidence/codex-succession-capsule-current.md)
- George IX remote-control rotation handoff:
  [Evidence/george-ix-remote-control-rotation-handoff-20260723.md](Evidence/george-ix-remote-control-rotation-handoff-20260723.md)
- Remote-control and cross-surface standard:
  [../Decisions/codex-remote-control-and-cross-surface-standard.md](../Decisions/codex-remote-control-and-cross-surface-standard.md)
- Remote-control service-grade health and tray evidence:
  [../Inventory/codex-cli-remote-control/service-grade-health-and-tray-validation-20260723.md](../Inventory/codex-cli-remote-control/service-grade-health-and-tray-validation-20260723.md)
- Remote-control service-grade closeout receipt:
  [Receipts/codex-remote-control-service-grade-20260724.md](Receipts/codex-remote-control-service-grade-20260724.md)
- Remote-control unit source and lifecycle:
  [../Config/systemd-user/README.md](../Config/systemd-user/README.md)
- Joy Anne birth, enrollment, Personal jurisdiction, and current plant
  reconciliation:
  [Receipts/joy-anne-enrollment-and-shannon-plant-reconciliation-20260812.md](Receipts/joy-anne-enrollment-and-shannon-plant-reconciliation-20260812.md)
- Byte-identical Joy birth receipt from Shannon:
  [Receipts/joy-anne-home-advisor-birth-20260812.md](Receipts/joy-anne-home-advisor-birth-20260812.md)
- Codex claim-janitor source: `Scripts/codex_claim_janitor.py`; installed-unit
  source and lifecycle: [../Config/systemd-user/README.md](../Config/systemd-user/README.md)
- Resident Center Sessions transfer and current host cutover:
  [Resident-Center/TRANSFER.md](Resident-Center/TRANSFER.md)
- First accepted cross-provider ChatGPT-export-to-Codex transplant:
  [Receipts/control-room-gpt-to-codex-transplant-20260727.md](Receipts/control-room-gpt-to-codex-transplant-20260727.md)
- Current Control state-of-play reconciliation:
  [Receipts/control-state-of-play-reconciliation-20260728.md](Receipts/control-state-of-play-reconciliation-20260728.md)
- Current Control refresh and repository tidy:
  [Receipts/control-refresh-and-repository-tidy-20260729.md](Receipts/control-refresh-and-repository-tidy-20260729.md)
- **Clinic rounds (both wards, always-on):** `session-health-rounds.timer`
  (systemd --user, every 15 min) runs `Scripts/session_health_rounds.sh` →
  `Scripts/check_codex_token_health.py` (Codex tokens) +
  `Scripts/check_claude_session_health.py` (Claude bytes/images). Local-only
  output `Evidence/clinic-rounds-latest.txt` + `clinic-rounds.log` (untracked).
  Replaced the retired Codex-only `codex-session-size-watch.timer` on 2026-07-17.
  Public, versioned, identifier-free aggregate for external consumers such as
  Resident Center: `Evidence/clinic-aggregate.json`, contract in
  [docs/clinic-aggregate-contract.md](docs/clinic-aggregate-contract.md).
- Prime starter packet: [Candidates/prime/](Candidates/prime/)
- Retirement forensics for the April thread: [Receipts/codex-log-compaction-trigger-forensics-20260704.md](Receipts/codex-log-compaction-trigger-forensics-20260704.md)

## Hard Boundary

Session files are evidence. Repo canon remains authority. A loaded JSONL can
be useful continuity state, but it cannot override current operator
instruction, AGENTS rules, `STATUS.md`, or durable decisions.
