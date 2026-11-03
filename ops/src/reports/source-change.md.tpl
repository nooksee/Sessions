---
template_type: report
template_id: source-change
template_version: 1
source: source/configuration change closeout; not a rotation receipt
requires_slots:
  - CHANGE
  - DATE
  - WRITER
  - AUTHORITY
  - SCOPE
  - BASE
  - CANDIDATE
  - DIFF
  - VALIDATION
  - REVIEW
  - INTEGRATION
  - DEVIATIONS
  - ROLLBACK
slot_notes:
  CHANGE: bounded change name and purpose
  DATE: measured start/end and timezone
  WRITER: sole source writer
  AUTHORITY: decision authorizing this exact scope
  SCOPE: exact changed paths or configuration surfaces
  BASE: immutable starting commit or configuration identity
  CANDIDATE: exact reviewed source head or resulting configuration identity
  DIFF: changed-path count and source diff/tree digest
  VALIDATION: named checks and measured outcomes
  REVIEW: independent reviewer and exact-head verdict
  INTEGRATION: PR, required checks, merge and synchronization evidence
  DEVIATIONS: counted deviations, or zero
  ROLLBACK: preserved recovery point and whether rollback ran
---
# Source/configuration change receipt: {{CHANGE}}

Date and clock: {{DATE}}.
Writer: {{WRITER}}.
Authority: {{AUTHORITY}}.

## Exact scope
{{SCOPE}}

## Source identity
- Base: {{BASE}}
- Candidate/result: {{CANDIDATE}}
- Diff: {{DIFF}}

## Validation and independent review
- Validation: {{VALIDATION}}
- Review: {{REVIEW}}

## Integration and recovery
- Integration: {{INTEGRATION}}
- Deviations: {{DEVIATIONS}}
- Rollback: {{ROLLBACK}}
