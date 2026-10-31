---
template_type: report
template_id: packet
template_version: 1
source: docs/ops/specs/runbook/agent-input.md
requires_slots:
  - TO
  - FROM
  - RELAYED_BY
  - OWNER
  - SCOPE
  - AUTHORITY
  - SOURCES
  - RULES
  - STOP_CONDITION
  - POST_TO
slot_notes:
  TO: the resident by Role (Person) and registry key; never a session identifier
  FROM: the packet's real author; relayed words carry their real author
  RELAYED_BY: who carries the packet into the resident's own chat (usually Kevin), or none
  OWNER: the single writer of the work; review grants no write authority
  SCOPE: the exact files or surfaces the owner may write, as a list of paths
  AUTHORITY: whose decision this carries out, quoted with date, and what still needs a further go
  SOURCES: the paths to read first, in order, beginning with the room's own instructions
  RULES: the house rules that apply, stated, not assumed
  STOP_CONDITION: the deliverable, the time box, and the point at which the owner stops and reports
  POST_TO: where the result goes, for the Sessions team the owner's own file in storage/handoff/
---
# Packet for {{TO}}

- **To:** {{TO}}
- **From:** {{FROM}}
- **Relayed by:** {{RELAYED_BY}}
- **Owner (the single writer):** {{OWNER}}

## Scope
The owner may write only these; everything else is read-only.
{{SCOPE}}

## Authority
{{AUTHORITY}}

## Read first, in order
{{SOURCES}}

## Rules
{{RULES}}

## Stop condition
{{STOP_CONDITION}}

## Report
Post to: {{POST_TO}}
The report contains: files written with sizes, what is real and what is placeholder, tests run, deviations counted, and the release of the writer claim.

This packet carries the decision named under Authority and creates none. It is delivered only when it is pasted into the recipient's own chat. Form: `ops/src/reports/packet.md.tpl` (spec `docs/ops/specs/runbook/agent-input.md`).
