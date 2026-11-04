<!-- redact: public copy; source sha256 b8323289c20b363c7690952a515b1f26965cd8c806ed1bb1a0f92e497e935648; rules 8; mode history; words 24; sessions 0 whole, 0 truncated; host paths 2; decisions 0 -->
# Sessions operations: the continuity system, one map

Owner: Session Continuity Manager. Originally written 2026-10-30. Convention: STELA (`Projects/STELA`). PoT 1.1 defines the filing boundaries; CONSTRAINTS C01 gives the filing mechanics. `storage/` carries named working cases, `var/tmp/` carries task scratch, `logs/` carries telemetry, and kept records belong in `archives/` or custody. Each tool has one word, a registered source path, specification and tests; imported shell tools retain `.sh`. Scratch mechanics are in `var/README.md` and the manual; clearing all working cases is not a cleanup procedure.

CONTEXT is the canonical read-in and domain-pointer inventory. CONSTRAINTS
contains human-consumed operating requirements delegated by PoT; neither
creates a compiler, hook or daemon reader. Each entry point must point readers
to these contracts. The map owns current locations, custody/Control ownership
and bounded migration holds; those holds do not create a permanent storage
state exception.

## Foundational policy adoption

RoR-18 adopts the reviewed policy at SHA-256
`2dc41d8754189cbb52d65bca4bc387ba508eedf1cd2156f2e62f408b86eb21e7`
with its CONSTRAINTS/CONTEXT read-in contracts and entry-point wiring.
`storage/active/pot-adoption-20261104/receipt.md` records the actual source
head, application time, contract hashes, custody and checks. The preserved
proposal and clause map remain historical preparation evidence, not another
active policy. Existing operational-state migration holds below remain in
force until their separately assigned cutover; this adoption moves no state.

## The system: four tools, one loop

```
 [words sha256=d6174139de04261e6caf388fa3aa3e61ff86814b6a6bb4c9898757acbfa3f227]
            [words sha256=cbe5cfdf7c2118a9c3d78ef1d684f3afa089201352886449a06a6511cfef74a7]
            [words sha256=4c94485e0c21ae6c41ce1dfe7b6bfaceea5ab68e40a2476f50208e526f506080]
 [words sha256=19a95362122aa1c3c7d4b6ae84dde626db47d730fbe9586cbaf1fa78bf2c1fe8]
            [words sha256=82d948504cac87dae1b1a071ec6ddd1677cef65547013d936625a379232df39c]
            [words sha256=4c94485e0c21ae6c41ce1dfe7b6bfaceea5ab68e40a2476f50208e526f506080]
 [words sha256=3c7bc975a4ca71b4f167de9427f9b2d2075be04ad484f23d765f2b47a9cfe976]
            [words sha256=7cc8c27c66bfc149da0aa8c802b1007d4a8870a93a61d8bc4a1ac7c4bbb21237]
            [words sha256=daef9073a7ce22875840b70f33bb3e2af4585916f697c5363d9a760987ee1684]
            [words sha256=4c94485e0c21ae6c41ce1dfe7b6bfaceea5ab68e40a2476f50208e526f506080]
 [words sha256=64323b40d5c620029cabcd43947bf4254d330dc5fe64e3ac4ce031637ef03655]
            [words sha256=cbe5cfdf7c2118a9c3d78ef1d684f3afa089201352886449a06a6511cfef74a7]
            [words sha256=4c94485e0c21ae6c41ce1dfe7b6bfaceea5ab68e40a2476f50208e526f506080]
 [words sha256=8cdd8d8c7578390804c9d639f0da8a56ba97d34b9c5eda9aa85d0532a6aee593]
         [words sha256=5b0e52261aaf0f76b262c0b8a004e1d74090f607ffb023f31187203e7bf4474d]
            [words sha256=cbe5cfdf7c2118a9c3d78ef1d684f3afa089201352886449a06a6511cfef74a7]
            [words sha256=4c94485e0c21ae6c41ce1dfe7b6bfaceea5ab68e40a2476f50208e526f506080]
 [words sha256=d54ac852d42183f6ce8cfbb46583a132a0f4ef2cd16ce81090df62d596c6023c]
           [words sha256=89f593150cb849af6ccb1b91a6cb9f25648dfe149e91215b0ef4849177b73791]
           [words sha256=06b22146f801977093248d4a3a97bca67d44cca3e4d9f0cfbfaf91908d09c266]
           [words sha256=c07e7bc6fe6369153d60deae715c8a7a8342aeb1cbca94d6a22e929963dd9eec]
            [words sha256=cbe5cfdf7c2118a9c3d78ef1d684f3afa089201352886449a06a6511cfef74a7]
            [words sha256=4c94485e0c21ae6c41ce1dfe7b6bfaceea5ab68e40a2476f50208e526f506080]
 [words sha256=e9466bb9118b563b4b262af14a51b81b586ffa6a221f1d9eba2207c859a46f44]
```

## Where everything lives

| Piece | Path | Kind | Status |
| --- | --- | --- | --- |
| gauge | `ops/lib/scripts/gauge.py`, `docs/ops/specs/scripts/gauge.md`, `tools/test/test_gauge.py` | tool | built 10-30; Claudio reviews |
| gauge ledger | `logs/gauges/ledger.jsonl` by default | private telemetry | legacy `storage/gauges` blocks default append until reviewed history/lock cutover; `--no-ledger` remains read-only |
| mind write lock | `<room>/logs/mind.lock` | shared room-wide exclusion | legacy `<room>/storage/mind.lock` blocks new writes until reviewed inode-preserving cutover; never a per-task lock |
| closeout | `ops/lib/scripts/closeout.py`, `docs/ops/specs/scripts/closeout.md`, `tools/test/test_closeout.py` | tool | implemented; synthetic coverage is not native delivery or installation proof |
| closeout state | `logs/closeout/` by default | private runtime state and diagnostics; unwired | legacy `storage/closeout` blocks default card delivery until reviewed migration; explicit state selection retains its interface |
| mind | `ops/lib/scripts/mind.py`, `docs/ops/specs/scripts/mind.md` | tool | ported from the Candidates package, simplified to solicited input |
| mind pointer | `<room>/MIND.md`, one line per resident in the room | durable, out of Git | first one: `Sessions/MIND.md` |
| mind leaves | `<room>/archives/MIND-<key>-<date>-<hash8>.md` | durable, out of Git, two-drive custody | archives-root layout implemented; an actual write follows PoT 5.1 and the mind specification |
| rotate | `ops/lib/scripts/rotate.py` (to write), `docs/ops/specs/scripts/rotate.md` (from the package runbook) | tool | next |
| team room | `storage/handoff/{shannon,claudine,joe}.md`, and `storage/handoff/port.md` (the port writer's handoff, 2026-11-01) | private, ignored working notes | results are promoted to `archives/receipts/` or the office handoff |
| task scratch | `var/tmp/<owner>-<operation>.<unique>/`, skeleton described in `var/README.md` | ephemeral, ignored | owner-scoped; PoT 1.1.13; no persistent state or automatic purge |
| incoming payload | `storage/intake/` | working data; only `.gitkeep` admitted | payload ignored; awaiting classification, not executable installation or authority |
| active case payload | `storage/active/` | working data; only `.gitkeep` admitted | payload ignored; owner, operation and closeout; no operational code trees |
| mind project record | `archives/mind-manifest-20261101/` | durable, private and ignored | packed 2026-11-01; `MANIFEST.txt` holds every file's source and sha256; integrated by the port (`archives/receipts/mind-manifest-integration-20261101.md`); preservation does not imply Git admission |
| receipts | `archives/receipts/<what>-<date>.md` | durable; selective Git admission | original/private sources remain kept; only explicitly admitted redacted records enter Git, as `.gitignore` names them |
| custody | `[host path 1]>/` mirrored on hard_vol2 | durable | hard_vol2 is failing; a replacement is pending |
| help | `ops/bin/help`, `docs/ops/specs/binaries/help.md` | binary | adapted from STELA 10-30; read-only wayfinding (`docs/ops/registry/binaries.md`) |
| template | `ops/bin/template`, `docs/ops/specs/binaries/template.md` | binary | adapted from STELA 10-30; new tool skeleton (`docs/ops/registry/binaries.md`) |
| manual | `docs/MANUAL.md` | document | written 10-30; operator console for the loop |
| index | `docs/INDEX.md` | document | updated 11-03; maintained pointers to current docs and forms |
| registries | `docs/ops/registry/{scripts,binaries,test,runbook}.md` | document | maintained inventories; one row per tool, binary, test suite and runbook |

## What the last two days left, and its place

- `archives/mind-manifest-20261101/`: the whole mind project as of 2026-11-01, packed by the Session Continuity Manager with a hash manifest: the v1 proposal and package, Claudio's audit, the v2 tool as it stands, the law, the handoff excerpts and the notes. It is the durable record. `storage/candidates/mind-manifest-20261029/` and `storage/lab/jojo-production/working-snapshots/claudio-20261030-mind-audit/` are its working duplicates, disposable.
- `storage/candidates/joy-anne-rotation-20261030/` and `shannon-rebuild-20261029/`: build records of two rotations. `splice_window.py` and the gates are the ingredients of `rotate.py`. The large intermediate bodies are rebuildable from custody.
- `storage/lab/` (formerly the Lab folder): existing working snapshots, ignored by Git. Required audit evidence stays until classified and kept; new task scratch goes to `var/tmp/`. Existing contents await the assigned retention pass, not a blind move or purge.

## Ported later (Kevin: no side path now)

- `Scripts/`: ported 2026-11-01 to `ops/lib/scripts/`, one word each with a spec each (`docs/ops/specs/runbook/port.md`, `archives/receipts/port-20261101.md`); its two frozen remains are under `archives/legacy/Scripts/`.
- The retired folders Archived, Attic, Plans and Intake were frozen unchanged under `archives/legacy/` on 2026-11-01. `Resident-Center/`, `Config/` and the rest of `Scripts/` left the room in block 7 for Control's frozen runtime custody at `[host path 2]` (Control's decision; PoT 3.4).
- `HANDOFF.md`, `INDEX.md` and `START-HERE.md` became pointer-first root files on 2026-11-01; their former contents are at `archives/legacy/HANDOFF.md`, `archives/legacy/INDEX.md` and `docs/START-HERE.md`. `NOW.md` stays the present-state board.

## Rules for every new file

1. Before creating a folder, find the existing base folder it belongs in.
2. One word per script; a spec with the same name; tests beside it in `tools/test`.
3. Apply PoT 1.1.4 and 1.1.13: the active case references its uniquely allocated `var/tmp/` scratch; use `mktemp -d` as shown in `var/README.md`. Kept results follow PoT 1.1.5 and 5.3 before the scratch is closed.
4. A root file is a pointer, not a document.

## Existing state consumers held for bounded migration

The source defaults below now use `logs/`; actual prior state remains held
until its assigned cutover. No source change itself moves an existing object.
The shared no-write legacy guard is `ops/lib/statepaths.py`, used lazily by
default gauge append and mind write locking. Closeout retains its own guard.
Each actual migration preserves the old inputs, exclusion and recovery path.

| Consumer / owner | Existing path | Hold or ending condition | Bounded migration action |
| --- | --- | --- | --- |
| `gauge.py`; assigned tool writer and actual cutover owner | Legacy `storage/gauges/`; source default `logs/gauges/ledger.jsonl` with sibling `ledger.lock` | Preserve history and exclusion. Any legacy node or unsafe ancestor blocks default append; explicit custom output remains supported and grants no migration authority | Quiesce all ledger writers, inventory readers and both paths, verify custody and source stability, preserve the ledger prefix and shared lock inode during the reviewed cutover, verify ownership/privacy/identity, then prove one synthetic or separately authorized append preserves the prefix. No automatic copying or history reset. |
| `mind.py`; assigned tool writer and actual cutover owner | Legacy `<room>/storage/mind.lock`; source default `<room>/logs/mind.lock` | Any legacy node or unsafe ancestor blocks a new write. The lock remains one shared object for every writer in the room | Close all old/new writers, preserve evidence, check OS lock ownership and retain the same inode if a legacy lock exists. Verify every active caller selects the new path before allowing writes. Do not copy an old lock into a second object, unlink a held inode, create a task-local replacement or mistake an absent pathname for proof of writer closure. This changes no mind content. |
| `closeout.py`; designated closeout tool writer | Legacy `storage/closeout/`; source default `logs/closeout/` (`state.json`, `log.jsonl`, lock and temporary state) | Tool remains unwired. Any legacy node, including a broken link, makes default delivery unknown; legacy bytes are neither copied nor replaced. The new location may record that diagnostic, never a delivered band. | Before wiring, inventory both actual paths and readers. Preserve/hash legacy state if present; stage and verify the reviewed private copy and deduplication state, then release the old canonical path under the named migration/custody operation. Explicit `--state-dir` remains supported. No automatic move, source activation or persistent state in `var/tmp/`. |

No persistent state moves to `var/tmp/`, and no consumer state is migrated as
a side effect of this source-only change. The new defaults and legacy guards
are source behavior; they do not prove that the assigned live cutover ran.

## Case routing mechanics

New incoming data uses `storage/intake/`; accepted working-case payloads use
`storage/active/`. No new loose files go on the storage root. Existing named
handoffs remain private working notes. Git admits only `storage/.gitignore`,
`storage/README.md` and the direct lane `.gitkeep` files; payload is denied by
default, including nested notes and code. Check the exact staged path set
before any commit; do not rely on ignore rules to constrain a forced add.
Operational state consumers remain only under the bounded migration holds
above and CONSTRAINTS C01; the current location is recorded here, not in law.
Operational code belongs in `ops/bin/`, `ops/lib/scripts/`, `ops/src/` or
`tools/test/`, with its specifications and operator guidance in `docs/`.
Independent product code stays in its project repository. STELA's map makes
the same distinction between operational assets, project code and payload.
The generator refuses root-level storage report output and tool generation
beneath storage, including resolved aliases. `var/tmp/` remains the home for
synthetic code checkouts, probes and intermediates, not a retained deployment.
