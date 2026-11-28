# Technical Specification: capsule

Script: `ops/lib/scripts/capsule.py`. Tests: `tools/test/test_capsule.py`.
Builds a six-question succession capsule from room canon and inventory evidence.

## Mechanics and Sequencing

The root is three parents above the script. Inventory defaults to the room logs directory. CANON_FILES follows help read: AGENTS, PoT, CONTEXT, CONSTRAINTS, class-specific identity guidance, RoR, NOW, INDEX, system map and manual. The closing instruction repeats that list. No parent canon or Dropbox folder is read or named.

Active-work excerpts come from NOW.md and docs/ops/README.md. Inventory summaries and room Git metadata supply evidence; absent evidence is labelled. Options --inventory-dir and --output select the evidence and output. The tool writes a dated and a current capsule, not a live session.

## Tests and limits

Synthetic inventory, mocked canon excerpts and Git metadata pin room anchoring and successor instructions. This tool grants no succession or deployment authority.
