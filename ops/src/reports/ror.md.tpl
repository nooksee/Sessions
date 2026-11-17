---
template_type: report
template_id: ror
template_version: 1
source: PoT 1.2.10 (Record of Record), 7.1 and 7.6; RoR.md
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
  KIND: ratification or amendment of PoT, scoped packet addendum, or design choice
  GIVEN: when the operator gave it, and that time's source
  WORDS: private source words under PoT 1.2.10; publish only their verified digest; protected material follows 5.1.4
  ACT: the ratification, packet addendum or design choice; its clause or packet and scope; no rule binds from this record
  RECORD: the clause or packet and the act's receipt or archived text, with its sha256
  ENTERED_BY: the role and registry key of the resident who entered it, and the clock time of the entry
---
### RoR-{{ENTRY}}: {{KIND}}

- **Given:** {{GIVEN}}
- **Words:** "{{WORDS}}"
- **Act:** {{ACT}}
- **Record:** {{RECORD}}
- **Entered by:** {{ENTERED_BY}}
