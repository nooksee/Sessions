# Technical Specification: myself

Script: `Sessions/ops/lib/scripts/myself.py` (original writer not recorded; port writer: Claude (Fable 5.1, that session), not a registered resident; shared-counter correction writer: Session Continuity Apprentice (Joe Codex)). Tests: `Sessions/tools/test/test_myself.py`. Original spec writer: the port writer; shared-counter spec correction: Session Continuity Apprentice (Joe Codex). Source status: shared gauge reader with synthetic coverage; independent review and integration are recorded in the owning change receipt. No hook, timer or service is installed by this source change. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Measure one resident's native identity and session health, without writes." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/resident-self-check-canary-20260809.md` (2026-08-09); 10 receipt(s) name it in all.

## Mechanics and Sequencing

1. Port provenance: `Scripts/check_myself.py` (sha256 `e4b2fad6d0d64d223fe904626374d5b3cbf993cafcbac876b336c2ed3baf3bc8`) was copied to `ops/lib/scripts/myself.py` on 2026-11-01 with one edit: parents[1] -> parents[3]. The later shared-counter correction replaces only the duplicated context-usage selection; identity, row/parse metrics and timestamp-cluster inspection keep their separate body analysis.
2. Command line: `python3 -I -B ops/lib/scripts/myself.py`; the script declares no argparse options (it reads its inputs from fixed paths or from the environment, as its docstring says).
3. Context selection loads the sibling `gauge.py` and calls its `read_codex` or `read_claude` on the exact selected body. The gauge specification owns the counter-selection and tail bound. Main-chain usage, incomplete final rows, zero usage and later compaction therefore use the same selection as gauge and closeout. The pressure leg reports unknown after compaction until a fresh complete reading; it does not reuse an older Codex window when the newest reading lacks one.
4. The existing Claude window source remains a model-matched identifier-free resource-state record, with its reported age; this correction does not replace it with gauge's reviewed-window table or claim parity when those capability sources disagree. The rotation threshold is unchanged. The pressure leg names the actual body, gauge source and, when used, resource-state surface.
5. Missing/unreadable gauge source or reader failure makes pressure undetermined, without a second reader fallback. Other identity/body-metric legs still run. A native Codex count above its reported window is undetermined, not a clean result. Repeated runs read current input; no pressure result is cached. No new output, state, registry, binding or body write is added.

## Anecdotal Anchor

`Receipts/resident-self-check-canary-20260809.md` is the earliest of 10 receipt(s) naming `check_myself.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Measure one resident's native identity and session health, without writes." "A working directory is never identity."
- Host consumer selection belongs to Control; this source change neither repoints nor restarts a consumer. The module and its sibling gauge reader must remain together in the source layout.
- The focused regression set covers eleven synthetic agreement/currentness cases plus reader failure, invalid-window and repeated-run checks. Those cases are not a live fleet or provider-version acceptance claim. Claude window-capability disagreement is an explicitly separate source contract, not silently calibrated here.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]
