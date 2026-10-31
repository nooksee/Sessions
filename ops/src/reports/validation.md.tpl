---
template_type: report
template_id: validation
template_version: 1
source: PoT 6.1.5 (a live validation on bodies created for it is its own named operation) and 6.4.5
requires_slots:
  - TEST
  - DATE
  - WRITER
  - AUTHORITY
  - SUBJECT
  - SETUP
  - STEPS
  - VERDICT
  - TEARDOWN
  - REVIEW
  - COUNTS
  - DEVIATIONS
slot_notes:
  TEST: the test name, one word with its number, as the runbook names it
  DATE: the date and the clock span, read from a clock, not estimated
  WRITER: the one writer accountable for the test thread, as Role (Person) and registry key
  AUTHORITY: the RoR.md entry and the operator's named go, quoted, naming folder, settings file, command and frozen hashes
  SUBJECT: each tool and template under test, with its frozen sha256
  SETUP: the folder, the settings file and its sha256, the command string, and the fixtures, each with its sha256
  STEPS: each step as runbook step, prompt or action, expected outcome, observed outcome (measured), and pass or fail
  VERDICT: PASS or FAIL for the test as a whole, with the measured basis
  TEARDOWN: what was removed or kept afterwards, and where any kept evidence lives
  REVIEW: the independent review before the go, and the audit after, cited by section
  COUNTS: protected or irreversible acts performed, as measured counts (PoT 6.4.5): real bodies touched, registry changes, settings changed outside the test folder, credentials read
  DEVIATIONS: protocol deviations, counted, each with its correction
---
# Live validation receipt: {{TEST}}

- **Date:** {{DATE}}
- **Writer:** {{WRITER}}
- **Authority:** {{AUTHORITY}}

## Subject
{{SUBJECT}}

## Setup
{{SETUP}}

## Steps
{{STEPS}}

## Verdict
{{VERDICT}}

## Teardown
{{TEARDOWN}}

## Review
{{REVIEW}}

## Counts
{{COUNTS}}

## Deviations
{{DEVIATIONS}}
