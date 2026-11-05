# Sessions operations: the continuity system, one map

Owner: Session Continuity Manager. Originally written 2026-10-30. Convention: STELA, the house convention, kept in the operator's Control tree and not in this repository. PoT 1.1 defines the filing boundaries; CONSTRAINTS C01 gives the filing mechanics. `storage/` carries named working cases, `var/tmp/` carries task scratch, `logs/` carries telemetry, and kept records belong in `archives/` or custody. Each tool has one word, a registered source path, specification and tests; imported shell tools retain `.sh`. Scratch mechanics are in `var/README.md` and the manual; clearing all working cases is not a cleanup procedure.

CONTEXT is the canonical read-in and domain-pointer inventory. CONSTRAINTS
contains human-consumed operating requirements delegated by PoT; neither
creates a compiler, hook or daemon reader. Each entry point must point readers
to these contracts. The map owns current locations, custody/Control ownership
and bounded migration holds; those holds do not create a permanent storage
state exception.

Paths in these documents use two tokens. `<control>` is the Control root on the
operator's host, and `<room>` is this room's root inside it, `<control>/Sessions`;
on a clone, the clone's root takes the place of `<room>`. The tools find the room
from their own location; code defaults and tests keep their literal paths.

## Foundational policy adoption

RoR-18 adopts the reviewed policy at SHA-256
`2dc41d8754189cbb52d65bca4bc387ba508eedf1cd2156f2e62f408b86eb21e7`
with its CONSTRAINTS/CONTEXT read-in contracts and entry-point wiring.
The private adoption receipt, `storage/active/pot-adoption-20261104/receipt.md` (not in this repository), records the actual source
head, application time, contract hashes, custody and checks. The preserved
proposal and clause map remain historical preparation evidence, not another
active policy. The gauge and mind-lock migration holds below ended with the state cutover
of 2026-11-04 16:57 (`archives/receipts/state-cutover-20261104.md`); the closeout hold
remains; the adoption itself moved no state.

## The system: four tools, one loop

```
 ops/etc/resident-identities.json      (the registry: who each resident is; the authority)
            |
            v
 [gauge]  reads each body's own API token count  -->  logs/gauges/ledger.jsonl (private telemetry)
            |   when: the closeout reserve before the rotation line (closeout spec)
            v
 [closeout]  hook puts the card in the resident's own context (Codex: the operator is notified)
            |   the resident parks work, writes its closing handoff,
            |   and proposes up to 3 mind entries in chat
            v
 the operator says yes in conversation
            |
            v
 [mind]  writes a new leaf  archives/MIND-<key>-<date>-<hash8>.md   (out of Git; custody-backed)
         and moves the pointer line in the room's root  MIND.md
            |
            v
 [rotate]  capsule = registry header + mind leaf + transition note + first-turn line,
           plus the donor's own summary and recent window, word for word
           -> static gates -> custody (two drives) -> the operator's go -> verified swap -> registry and binding
           -> labels (spares say "spare body, do not open") -> receipt in archives/receipts/
            |
            v
 [gauge]  the successor's first reading confirms the wake, and the loop begins again
```

## Where everything lives

| Piece | Path | Kind | Status |
| --- | --- | --- | --- |
| gauge | `ops/lib/scripts/gauge.py`, `docs/ops/specs/scripts/gauge.md`, `tools/test/test_gauge.py` | tool | built 10-30; Claudio reviews |
| gauge ledger | `logs/gauges/ledger.jsonl` by default | private telemetry | the history moved here in place on 2026-11-04 with its inodes (`archives/receipts/state-cutover-20261104.md`); `storage/gauges` is absent, and a recreated one would block default append; `--no-ledger` remains read-only |
| mind write lock | `<room>/logs/mind.lock` | shared room-wide exclusion | no legacy lock existed at the cutover of 2026-11-04, so the first authorized write creates this one; a legacy `<room>/storage/mind.lock` would block new writes; never a per-task lock |
| closeout | `ops/lib/scripts/closeout.py`, `docs/ops/specs/scripts/closeout.md`, `tools/test/test_closeout.py` | tool | implemented; synthetic coverage is not native delivery or installation proof |
| closeout state | `logs/closeout/` by default | private runtime state and diagnostics; unwired | legacy `storage/closeout` blocks default card delivery until reviewed migration; explicit state selection retains its interface |
| operator notice | `ops/lib/scripts/notice.py`, `docs/ops/specs/scripts/notice.md`, `tools/test/test_notice.py` | tool; source implemented, review and integration pending; unwired | consumes one exact gauge row using the shared closeout decision, submits only an operator notice; neither native context delivery nor display is proved |
| notice state | `logs/notices/<key>.json` and sibling `<key>.lock` | private runtime state, created only on an explicit accepted run | 0700/0600, hashed native binding, nonblocking flock and atomic state; separate from hook state, no existing state moved |
| mind | `ops/lib/scripts/mind.py`, `docs/ops/specs/scripts/mind.md` | tool | ported from the Candidates package, simplified to solicited input |
| mind pointer | `<room>/MIND.md`, one line per resident in the room | durable, out of Git | first one: `Sessions/MIND.md` |
| mind leaves | `<room>/archives/MIND-<key>-<date>-<hash8>.md` | durable, out of Git, two-drive custody | archives-root layout implemented; an actual write follows PoT 5.1 and the mind specification |
| rotate | `ops/lib/scripts/rotate.py`, `docs/ops/specs/scripts/rotate.md`, `tools/test/test_rotate.py` | tool | Joe's synthetic read-only phases 0 to 2 are implemented and source-reviewed; integration review pending; phases 3 to 9 remain unimplemented |
| Claude resident wrapper | `ops/bin/claude-resident`, `docs/ops/specs/scripts/claude-resident.md`, `tools/test/test_claude_resident.py` | binary | source implemented and reviewed; real form not yet proved against the provider; `cliPath` untouched |
| team room | `storage/handoff/{shannon,claudine,joe}.md`, and `storage/handoff/port.md` (the port writer's handoff, 2026-11-01) | private, ignored working notes | results are promoted to `archives/receipts/` or the office handoff |
| task scratch | `var/tmp/<owner>-<operation>.<unique>/`, skeleton described in `var/README.md` | ephemeral, ignored | owner-scoped; PoT 1.1.13; no persistent state or automatic purge |
| incoming payload | `storage/intake/` | working data; only `.gitkeep` admitted | payload ignored; awaiting classification, not executable installation or authority |
| active case payload | `storage/active/` | working data; only `.gitkeep` admitted | payload ignored; owner, operation and closeout; no operational code trees |
| mind project record | `archives/mind-manifest-20261101/` | durable, private and ignored | packed 2026-11-01; `MANIFEST.txt` holds every file's source and sha256; integrated by the port (`archives/receipts/mind-manifest-integration-20261101.md`, a private receipt); preservation does not imply Git admission |
| receipts | `archives/receipts/<what>-<date>.md` | durable; selective Git admission | original/private sources remain kept; only explicitly admitted redacted records enter Git, as `.gitignore` names them |
| custody | `<control>/Backup/Codex-Session-Preservation/<batch>/` (tier 1, /dev/sdb1), mirrored on hard_vol2 (tier 2, /dev/sdc1) | durable | hard_vol2 is failing and its replacement stays open (PoT 5.3.3): until a healthy second medium is chosen, each batch's third copy lives on the boot drive under the operator's home directory under `.local/state/` (tier 3, /dev/sda2, interim): `Sessions-Custody-Interim-20261104/<batch>/` holds the receipts, evidence and ledger-sources batches of 11-01 and 11-02; `Central-RoR-First-Render-20261104/` and `Sessions-State-Cutover-20261104/` hold the ledger render and the gauge-history preimages of 11-04, each with a sibling under `Backup/`; `sessions-history-20261104/` and `sessions-prerewrite-20261104/` hold the bundles of the repository before the history rewrite of 11-04 with the export of its pull requests, `sessions-identities-20261104/` the first public-gate repository before its re-creation with its four pull requests and the mailmap, and `sessions-port-110126-retired-20261104/` the porter's working copy of the room, retired from `Projects/` with its manifest beside it (receipt `archives/receipts/history-rewrite-20261104.md`) |
| help | `ops/bin/help`, `docs/ops/specs/binaries/help.md` | binary | adapted from STELA 10-30; read-only wayfinding (`docs/ops/registry/binaries.md`) |
| template | `ops/bin/template`, `docs/ops/specs/binaries/template.md` | binary | adapted from STELA 10-30; new tool skeleton (`docs/ops/registry/binaries.md`) |
| manual | `docs/MANUAL.md` | document | written 10-30; operator console for the loop |
| index | `docs/INDEX.md` | document | updated 11-03; maintained pointers to current docs and forms |
| registries | `docs/ops/registry/{scripts,binaries,test,runbook}.md` | document | maintained inventories; one row per tool, binary, test suite and runbook |

## What 2026-10-29 to 2026-11-01 left, and its place

- `archives/mind-manifest-20261101/`: the whole mind project as of 2026-11-01, packed by the Session Continuity Manager with a hash manifest: the v1 proposal and package, Claudio's audit, the v2 tool as it stands, the law, the handoff excerpts and the notes. It is the durable record. `storage/candidates/mind-manifest-20261029/` and `storage/lab/jojo-production/working-snapshots/claudio-20261030-mind-audit/` are its working duplicates, disposable.
- `storage/candidates/`, the build records of this office's rotations and capsules from 2026-07 to 2026-10, moved to custody on 2026-11-04 as batch `sessions-storage-candidates-20261104` (three roots, direct-read verified) and removed from the room at the operator's direction; `splice_window.py` and the gates, the ingredients of `rotate.py`, are in custody with them.
- `storage/lab/` (formerly the Lab folder): in custody entire as batch `sessions-storage-lab-20261104` (2026-11-04); this desk's folders removed from the room, the other residents' folders kept until their owners say, ignored by Git.

## Ported later (the operator: no side path now)

- `Scripts/`: ported 2026-11-01 to `ops/lib/scripts/`, one word each with a spec each (`docs/ops/specs/runbook/port.md`; its receipt, `archives/receipts/port-20261101.md`, is private); its two frozen remains are under `archives/legacy/Scripts/`.
- The retired folders Archived, Attic, Plans and Intake were frozen unchanged under `archives/legacy/` on 2026-11-01. `Resident-Center/`, `Config/` and the rest of `Scripts/` left the room in block 7 for Control's frozen runtime custody at `<control>/Control-Runtime/` (Control's decision; PoT 3.4).
- `HANDOFF.md`, `INDEX.md` and `START-HERE.md` became pointer-first root files on 2026-11-01; their former contents are at `archives/legacy/HANDOFF.md`, `archives/legacy/INDEX.md` and `docs/START-HERE.md`. `NOW.md` stays the present-state board. The root `START-HERE.md` pointer was retired on 2026-11-04 at the operator's direction; `docs/START-HERE.md` is the orientation. The same night the public gate completed: the history rewritten, the repository re-created under the name `nooksee/Sessions` and switched public, the receipt in `archives/receipts/`.

## Rules for every new file

1. Before creating a folder, find the existing base folder it belongs in.
2. One word per script; a spec with the same name; tests beside it in `tools/test`.
3. Apply PoT 1.1.4 and 1.1.13: the active case references its uniquely allocated `var/tmp/` scratch; use `mktemp -d` as shown in `var/README.md`. Kept results follow PoT 1.1.5 and 5.3 before the scratch is closed.
4. A root file is a pointer, not a document.

## Existing state consumers held for bounded migration

The source defaults below use `logs/`. The gauge and mind-lock migrations ran
on 2026-11-04 (`archives/receipts/state-cutover-20261104.md`); the closeout hold stands. No
source change itself moves an existing object.
The shared no-write legacy guard is `ops/lib/statepaths.py`, used lazily by
default gauge append and mind write locking. Closeout retains its own guard.
Each actual migration preserves the old inputs, exclusion and recovery path.

| Consumer / owner | Existing path | Hold or ending condition | Bounded migration action |
| --- | --- | --- | --- |
| `gauge.py`; tool writer; cutover performed by the Session Continuity Manager | `logs/gauges/ledger.jsonl` with sibling `ledger.lock`, moved in place from `storage/gauges/` on 2026-11-04 16:57 | Done (`archives/receipts/state-cutover-20261104.md`): history and lock inodes preserved, prefix verified, custody on two drives first. Any legacy node or unsafe ancestor still blocks default append; explicit custom output remains supported and grants no migration authority | Quiesce all ledger writers, inventory readers and both paths, verify custody and source stability, preserve the ledger prefix and shared lock inode during the reviewed cutover, verify ownership/privacy/identity, then prove one synthetic or separately authorized append preserves the prefix. No automatic copying or history reset. |
| `mind.py`; tool writer | `<room>/logs/mind.lock`, created by the first authorized write; no legacy lock existed at the cutover of 2026-11-04 (`archives/receipts/state-cutover-20261104.md`) | Done, nothing to move. Any legacy node or unsafe ancestor blocks a new write. The lock remains one shared object for every writer in the room | Close all old/new writers, preserve evidence, check OS lock ownership and retain the same inode if a legacy lock exists. Verify every active caller selects the new path before allowing writes. Do not copy an old lock into a second object, unlink a held inode, create a task-local replacement or mistake an absent pathname for proof of writer closure. This changes no mind content. |
| `closeout.py`; designated closeout tool writer | Legacy `storage/closeout/`; source default `logs/closeout/` (`state.json`, `log.jsonl`, lock and temporary state) | Tool remains unwired. Any legacy node, including a broken link, makes default delivery unknown; legacy bytes are neither copied nor replaced. The new location may record that diagnostic, never a delivered band. | Before wiring, inventory both actual paths and readers. Preserve/hash legacy state if present; stage and verify the reviewed private copy and deduplication state, then release the old canonical path under the named migration/custody operation. Explicit `--state-dir` remains supported. No automatic move, source activation or persistent state in `var/tmp/`. |

No persistent state moves to `var/tmp/`, and no consumer state is migrated as
a side effect of this source-only change. The new defaults and legacy guards
are source behavior; the gauge and mind-lock cutover ran on 2026-11-04
(`archives/receipts/state-cutover-20261104.md`); the closeout migration has not.

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
