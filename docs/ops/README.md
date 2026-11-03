<!-- redact: public copy; source sha256 9b40097aeb196b6361ba97964f3cfacd42afe4e4dbd2c41e73d7fce982b0058b; rules 8; mode history; words 24; sessions 0 whole, 0 truncated; host paths 2; decisions 0 -->
# Sessions operations: the continuity system, one map

Owner: Claude Shannon. Written 2026-10-30 at Kevin's request for a 30,000-foot view. Convention: STELA (`Projects/STELA`). Base folders and root files are the base; no new specialty folders. Each script is one word, in `ops/lib/scripts/<word>.py`, with a spec of the same name in `docs/ops/specs/scripts/<word>.md` and tests in `tools/test/test_<word>.py`. `storage/` is disposable: empty it and the system still works. Durable records live in `archives/` and `archives/receipts/`, or in custody.

## The system: four tools, one loop

```
 [words sha256=d6174139de04261e6caf388fa3aa3e61ff86814b6a6bb4c9898757acbfa3f227]
            [words sha256=cbe5cfdf7c2118a9c3d78ef1d684f3afa089201352886449a06a6511cfef74a7]
            [words sha256=4c94485e0c21ae6c41ce1dfe7b6bfaceea5ab68e40a2476f50208e526f506080]
 [words sha256=52be09371af6f365a61af20815d93b5450fdedb2f308870ddf5f74b3047db559]
            [words sha256=82d948504cac87dae1b1a071ec6ddd1677cef65547013d936625a379232df39c]
            [words sha256=4c94485e0c21ae6c41ce1dfe7b6bfaceea5ab68e40a2476f50208e526f506080]
 [words sha256=3c7bc975a4ca71b4f167de9427f9b2d2075be04ad484f23d765f2b47a9cfe976]
            [words sha256=7cc8c27c66bfc149da0aa8c802b1007d4a8870a93a61d8bc4a1ac7c4bbb21237]
            [words sha256=daef9073a7ce22875840b70f33bb3e2af4585916f697c5363d9a760987ee1684]
            [words sha256=4c94485e0c21ae6c41ce1dfe7b6bfaceea5ab68e40a2476f50208e526f506080]
 [words sha256=64323b40d5c620029cabcd43947bf4254d330dc5fe64e3ac4ce031637ef03655]
            [words sha256=cbe5cfdf7c2118a9c3d78ef1d684f3afa089201352886449a06a6511cfef74a7]
            [words sha256=4c94485e0c21ae6c41ce1dfe7b6bfaceea5ab68e40a2476f50208e526f506080]
 [words sha256=ab6455e0e05338ce2051b8faabc1f5a1af0989d914d527ff8c8df86755b15562]
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
| gauge ledger | `storage/gauges/ledger.jsonl` | disposable | rebuildable from bodies |
| closeout | `ops/lib/scripts/closeout.py`, `docs/ops/specs/scripts/closeout.md` | tool | designed 10-30 |
| mind | `ops/lib/scripts/mind.py`, `docs/ops/specs/scripts/mind.md` | tool | ported from the Candidates package, simplified to solicited input |
| mind pointer | `<room>/MIND.md`, one line per resident in the room | durable, out of Git | first one: `Sessions/MIND.md` |
| mind leaves | `<room>/archives/surfaces/MIND-<key>-<date>-<hash8>.md` | durable, out of Git, two-drive custody | first: Shannon's v2, after Kevin's yes |
| rotate | `ops/lib/scripts/rotate.py` (to write), `docs/ops/specs/scripts/rotate.md` (from the package runbook) | tool | next |
| team room | `storage/handoff/{shannon,claudine,joe}.md`, and `storage/handoff/port.md` (the port writer's handoff, 2026-11-01) | working notes | results are promoted to `archives/receipts/` or the office handoff |
| mind project record | `archives/mind-manifest-20261101/` | durable, tracked | packed 2026-11-01; `MANIFEST.txt` holds every file's source and sha256; integrated by the port (`archives/receipts/mind-manifest-integration-20261101.md`) |
| receipts | `archives/receipts/<what>-<date>.md` | durable, tracked | unchanged |
| custody | `[host path 1]>/` mirrored on hard_vol2 | durable | hard_vol2 is failing; a replacement is pending |
| help | `ops/bin/help`, `docs/ops/specs/binaries/help.md` | binary | adapted from STELA 10-30; read-only wayfinding (`docs/ops/registry/binaries.md`) |
| template | `ops/bin/template`, `docs/ops/specs/binaries/template.md` | binary | adapted from STELA 10-30; new tool skeleton (`docs/ops/registry/binaries.md`) |
| manual | `docs/MANUAL.md` | document | written 10-30; operator console for the loop |
| index | `docs/INDEX.md` | document | written 10-30; every document in `docs/` plus the root files |
| registries | `docs/ops/registry/{scripts,binaries,test,runbook}.md` | document | written 10-30 for Sessions; one row per tool, binary, test suite and runbook |

## What the last two days left, and its place

- `archives/mind-manifest-20261101/`: the whole mind project as of 2026-11-01, packed by the Session Continuity Manager with a hash manifest: the v1 proposal and package, Claudio's audit, the v2 tool as it stands, the law, the handoff excerpts and the notes. It is the durable record. `storage/candidates/mind-manifest-20261029/` and `storage/lab/jojo-production/working-snapshots/claudio-20261030-mind-audit/` are its working duplicates, disposable.
- `storage/candidates/joy-anne-rotation-20261030/` and `shannon-rebuild-20261029/`: build records of two rotations. `splice_window.py` and the gates are the ingredients of `rotate.py`. The large intermediate bodies are rebuildable from custody.
- `storage/lab/` (formerly the Lab folder): working snapshots, ignored by Git. Claudio's audit evidence lives there. It is scratch, not a home.

## Ported later (Kevin: no side path now)

- `Scripts/`: ported 2026-11-01 to `ops/lib/scripts/`, one word each with a spec each (`docs/ops/specs/runbook/port.md`, `archives/receipts/port-20261101.md`); its two frozen remains are under `archives/legacy/Scripts/`.
- The retired folders Archived, Attic, Plans and Intake were frozen unchanged under `archives/legacy/` on 2026-11-01. `Resident-Center/`, `Config/` and the rest of `Scripts/` left the room in block 7 for Control's frozen runtime custody at `[host path 2]` (Control's decision; PoT 3.4).
- `HANDOFF.md`, `INDEX.md` and `START-HERE.md` became pointer-first root files on 2026-11-01; their former contents are at `archives/legacy/HANDOFF.md`, `archives/legacy/INDEX.md` and `docs/START-HERE.md`. `NOW.md` stays the present-state board.

## Rules for every new file

1. Before creating a folder, find the existing base folder it belongs in.
2. One word per script; a spec with the same name; tests beside it in `tools/test`.
3. Working notes and rebuildable output go in `storage/`. Anything that cannot be rebuilt goes in `archives/`, `archives/receipts/` or custody, never in `storage/`.
4. A root file is a pointer, not a document.
