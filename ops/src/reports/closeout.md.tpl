---
template_type: report
template_id: closeout
template_version: 2
source: this template is the single source of the closeout card; ops/lib/scripts/closeout.py renders it (spec docs/ops/specs/scripts/closeout.md)
requires_slots:
  - PERCENT
  - WINDOW
  - READING_TIME
  - ROTATION_WRITER
slot_notes:
  PERCENT: the measured figure, in percent, from the resident's own body
  WINDOW: the model's context window, in tokens
  READING_TIME: the time of the reading the figure comes from
  ROTATION_WRITER: who runs the rotation; Shannon's desk, and for Shannon himself, Claudine
---
CLOSEOUT. Your context is {{PERCENT}} percent of {{WINDOW}}, measured from your own body at {{READING_TIME}}. It is time to close out, in this order:
1. Tell Kevin plainly that your closeout has begun, with the figure.
2. Finish the current step if it is short; otherwise stop at a clean point. Start nothing new and material.
3. Write your closing handoff: in flight, open promises, owners, first steps for your successor.
4. Propose up to three entries for your mind, in chat, for Kevin's yes: layer, text in your voice, event, fix, where it does not apply, source. Write nothing to the mind until he says yes; then it is written with his words and the date.
5. Tell Kevin you are ready for rotation. {{ROTATION_WRITER}} runs it.
