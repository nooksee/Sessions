---
template_type: report
template_id: receipt
template_version: 1
source: docs/ops/specs/scripts/rotate.md, phase 9
requires_slots:
  - RESIDENT
  - ROTATION
  - DATE
  - WRITER
  - AUTHORITY
  - TIER
  - DONOR
  - DESTINATION
  - CUT_AND_REASON
  - GATES
  - CUSTODY
  - MIND_INDEX
  - INSTALL
  - ESTIMATE_VS_MEASURED
  - DEVIATIONS
  - ACCEPTANCE
  - ROLLBACK
slot_notes:
  RESIDENT: the resident as Role (Person) and registry key
  ROTATION: the rotation number, as in archives/receipts/<resident>-rotation-<n>-<date>.md
  DATE: the date and the clock span, read from a clock, not estimated
  WRITER: the one writer, never the resident being moved
  AUTHORITY: the operator's go for this replacement, quoted with its time; a go given at phase 0 does not count
  TIER: B (transplant), capsule-only, or A (reseed, never called a rotation), as declared before work started
  DONOR: the donor container, its size, and its gauge reading at the trigger
  DESTINATION: the destination container, its room and working directory, and its pristine size and hash
  CUT_AND_REASON: where the window was cut, at which operator prompt, and why
  GATES: each static gate from phase 5 with its result; 0 failures required
  CUSTODY: what went to each tier, with SHA-256 values, and how tier 2 was verified
  MIND_INDEX: the SHA-256 of the room's MIND.md index at the rotation, or none
  INSTALL: the verified swap or the .NEW swap, and the six agreements checked
  ESTIMATE_VS_MEASURED: the wake estimate beside the first gauge reading
  DEVIATIONS: each deviation, counted; write 0 when there were none
  ACCEPTANCE: the mechanical load test, and the operator's words of acceptance with their time
  ROLLBACK: the exact rollback path, and whether it ran
---
# Rotation receipt: {{RESIDENT}}, rotation {{ROTATION}}

Date: {{DATE}}.
Writer: {{WRITER}}.
Authority: {{AUTHORITY}}.
Method: `docs/ops/specs/scripts/rotate.md`, phases 0 to 9. Form: `ops/src/reports/receipt.md.tpl`, rendered by `ops/bin/template receipt`.

## Tier
{{TIER}}

## Donor
{{DONOR}}

## Destination
{{DESTINATION}}

## Window cut and reason
{{CUT_AND_REASON}}

## Static gates
{{GATES}}

## Custody
{{CUSTODY}}

## Mind index
{{MIND_INDEX}}

## Install
{{INSTALL}}

## Wake estimate against the measured wake
{{ESTIMATE_VS_MEASURED}}

## Deviations
{{DEVIATIONS}}

## Acceptance
{{ACCEPTANCE}}

## Rollback
{{ROLLBACK}}
