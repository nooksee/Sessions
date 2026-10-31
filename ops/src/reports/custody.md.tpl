---
template_type: report
template_id: custody
template_version: 1
source: PoT 1.2.9, 5.3 and 6.4.5 (a custody operation ends in a receipt)
requires_slots:
  - BATCH
  - DATE
  - WRITER
  - AUTHORITY
  - CONTENTS
  - TIER1
  - TIER2
  - VERIFICATION
  - EXCLUDED
  - COUNTS
  - DEVIATIONS
slot_notes:
  BATCH: the custody batch name, one word with its date, as the folder is named in both tiers
  DATE: the date and the clock span of the operation, read from a clock, not estimated
  WRITER: the one writer, as Role (Person) and registry key
  AUTHORITY: the operator decision this carries out, cited by its RoR.md entry
  CONTENTS: what was copied, as paths relative to the room, with file counts and bytes
  TIER1: the tier 1 path, its file count, and the sha256 of its SHA256SUMS file
  TIER2: the tier 2 path, its file count, and how each copy was verified there (a direct read for a medium known to be failing, PoT 5.3.3)
  VERIFICATION: each check run and its measured result, with counts of files that matched and did not match
  EXCLUDED: what was deliberately left out, and why
  COUNTS: protected or irreversible acts performed, as measured counts (PoT 6.4.5): files moved, deleted or modified at the source; session bodies read; credentials read
  DEVIATIONS: protocol deviations, counted, each with its correction
---
# Custody receipt: {{BATCH}}

- **Date:** {{DATE}}
- **Writer:** {{WRITER}}
- **Authority:** {{AUTHORITY}}

## Contents
{{CONTENTS}}

## Tiers
- **Tier 1:** {{TIER1}}
- **Tier 2:** {{TIER2}}

## Verification
{{VERIFICATION}}

## Excluded
{{EXCLUDED}}

## Counts
{{COUNTS}}

## Deviations
{{DEVIATIONS}}
