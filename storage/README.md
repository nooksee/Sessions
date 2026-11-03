# Sessions working storage

The tracked directory skeleton follows the nested ignore policy. Its content
admission list is storage/.gitignore; there is no second parallel allowlist.
The filing authority is PoT 1.1.4 and 1.1.13; the operational map is
docs/ops/README.md and the operator mechanics are docs/MANUAL.md.

- intake/: incoming data awaiting classification.
- active/: named case data with an owner, operation and closeout condition.
- handoff/: existing resident work-in-flight notes.

Only this README, the ignore file and the three lane .gitkeep files are
admitted. Case payload, handoffs, nested code, bodies, private data and
generated output remain ignored. Git ignore is not protection against a
forced add or a substitute for review. Before committing storage changes,
verify the exact staged path set contains only the declared skeleton.

Reusable code, specifications, tests and kept records have their canonical
homes outside this working lane. The map records existing state held for
migration; introducing this skeleton moves or removes none of it. Scratch
uses the project-local var/tmp/ lane, not storage/.
