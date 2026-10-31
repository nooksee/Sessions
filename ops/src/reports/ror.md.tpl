---
template_type: report
template_id: ror
template_version: 1
source: PoT 1.2.10 (the decision ledger), 7.1 and 7.6; ledger RoR.md
requires_slots:
  - ENTRY
  - KIND
  - GIVEN
  - WORDS
  - ACT
  - RECORD
  - ENTERED_BY
slot_notes:
  ENTRY: the next entry number in RoR.md; numbers are permanent and never reused
  KIND: ratification, amendment, decision, standing direction, exception, acting holder, or anomaly
  GIVEN: when the operator gave it, and that time's source
  WORDS: the operator's exact words, verbatim (PoT 4.3.4); material under PoT 5.1.4 is redacted with a note
  ACT: the act and target the words authorize; for a standing direction, its scope and the event that ends it
  RECORD: the record of the act (receipt, mind leaf, or archived text), with its sha256
  ENTERED_BY: the role and registry key of the resident who entered it, and the clock time of the entry
---
### RoR-{{ENTRY}}: {{KIND}}

- **Given:** {{GIVEN}}
- **Words:** "{{WORDS}}"
- **Act:** {{ACT}}
- **Record:** {{RECORD}}
- **Entered by:** {{ENTERED_BY}}
