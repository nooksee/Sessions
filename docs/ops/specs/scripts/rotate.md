# Technical Specification: rotate

Script: `Sessions/ops/lib/scripts/rotate.py` (Claude-first synthetic runner). Spec writer: Claude Shannon, 2026-10-30. It is ported from Claudine Colbert's runbook (`storage/candidates/mind-manifest-20261029/package/docs/ops/specs/runbook/transition.md`) and adds:
- Claudio Freeman's conditions C11 to C13 (`claudio.md` section 130);
- The operator's decisions of 2026-10-30, and the install decision Shannon made under his deferral.

Map: `docs/ops/README.md`.

Status: synthetic phases 0 to 9 implemented, dry-run only, with Claude-only
window/build rehearsal and disposable custody, install, acceptance and close.
The fixture path has no live rotation or persistent recovery. Slice 6 adds
an explicitly gated disposable operation engine and persistent checkpoints;
it has no provider driver and no actual native-load or operator-acceptance proof.

Slice 5 adds explicit Claude adapter preparation on synthetic fixtures only,
through phase 5; native phases 6 to 9 refuse before reading evidence.

## First Principles Rationale

The operator, 2026-10-30: the rotation had never been formalized, and to him it always felt haphazard and awkward and was never carried out the same way twice. The craft existed in the Sessions doctrine: a native destination, a lineage capsule and the resident's own active window. But every rotation was assembled by hand from loose pieces, and the slips happened at the joins. In Joy's rotation 6, three of them came from hand-glued steps:
- a path passed where text was meant;
- an image pointer that led nowhere;
- a chmod in the wrong order.

`rotate` performs the same phases in the same order every time. It stops at fixed points, refuses on any failed gate, and drafts its own receipt. The art stays where it belongs, in where the window is cut and what the transition note says.

## Mechanics and Sequencing

### Claude adapter preparation (slice 5)

Select `--adapter claude --adapter-plan fixtures/adapter.json`, in addition
to the existing explicit synthetic-room and phase inputs. The default
`--adapter fixture` retains the earlier rehearsal unchanged, including its
temporary model phases 6 to 9. Neither selection admits native JSONL.

The adapter plan is a private, bounded `rotate-claude-adapter/1` object.
Its `kind` must be `registered-fixture`; `key`, `writer`, hashed `binding`,
`gauge_sha256`, `closeout_sha256` and `destination_sha256` must match phase 0.
`provider_version` is a nonblank string of at most 64 characters, a supplied
fixture label, not an installed-version observation. Each reference below
uses the existing exact `{path, sha256}` contract and confinement.

| Phase | Implementation and stop | Design realization or remaining limit |
| --- | --- | --- |
| 0 | Existing trigger plus plan binding and `process_model`; all holders absent and the model observable | Separate Claude preparation path, with no host process or native admission claim |
| 1 | Existing hash-bound closing record and the mind index it closed with | No handoff or approval is authored by the adapter |
| 2 | Existing mind verifier | The checked index is the room's mind; the room keeps the provider's auto memory off, so the provider carries nothing beside it |
| 3 | Existing spare metadata plus `destination_metadata` equality and `pristine` reference | Exactly one custom-title row and an inert user/assistant exchange; exact room, spare label, synthetic IDs, distinct linked message IDs and times from creation through build. User text is the source's `FIRST_PROMPT`, assistant text is `READY`. No container is created |
| 4 | `compaction` reference, then existing window selection against its post-compaction reading | `rotate-compaction-fixture/1` requires `actor: operator`, `method: supported-interface`, `before_gauge_sha256`, zoned `at`, and `after_gauge` reference. Compaction follows the initial due reading and precedes closeout; post-reading is at or after compaction and no later than closeout, with unchanged measured window. Actual fixture boundary time matches `at`; summary precedes the selected prompt. This fixes the earlier rehearsal's same-reading assumption without fabricating a new trigger |
| 5 | Existing in-process builder, externalizer and static gates; temporary artifacts removed at return | No whole native donor is imported, no capsule enters an external command line, no candidate is installed |
| 6 | Refuse with `named-native-custody-go-required-native-unimplemented` | Physical copies, real holds, daily-batch joins and final durable media fixity are not implemented here |
| 7 | Refuse with `post-custody-replacement-go-required-native-unimplemented` | No native swap, registry/binding write, `.NEW` publication or native inverse |
| 8 | Refuse with `named-native-load-go-required-native-unimplemented` | No provider launch, append, native reading or operator acceptance |
| 9 | Refuse with `named-donor-disposition-go-required-native-unimplemented` | No native receipt or donor disposition |

The fixture prompt is invented input, not operator words. Compaction records
are declarations only; the adapter never compacts or authenticates a person.
The pre-compaction due snapshot remains the reported trigger; the separately
validated post-compaction snapshot selects the carried window. Native card
delivery and installed-version evidence still need their accepted instruments.

`--native-action` explicitly requests a refused act: `disposable-exercise`,
`compact`, `rotation`, `hold`, `custody`, `install`, `load`, `rollback` or
`donor-disposition`. Every refusal names the corresponding go, except
compaction, which names its operator-only boundary. No supplied go enables
these paths. `--adapter codex` refuses with
`codex-summary-active-window-and-loader-proof-required`, even at phase 0;
the default fixture mode's earlier Codex metadata checks remain unchanged.

Design limits retained, not silently claimed built: unregistered disposable
admission, real closed-writer/ownership proof, persistent checkpoints and
restart, native W5 joins, physical custody, durable media paths, native
promotion/load/rollback and both named live exercises. The Manager owns the
separate custody-tool disk check. Safe roots, F1 registry privacy and C09
remain required. This slice creates no runtime map entry or live capability.

### Disposable operation engine (slice 6)

This separate path is selected only by `--native-apply --adapter claude --native-plan PATH
--native-plan-sha256 SHA --native-action ACTION --native-go PATH
--native-go-sha256 SHA --native-proof PATH --native-proof-sha256 SHA`.
Without a native plan all earlier fixture refusals remain unchanged. Actions
are `disposable-exercise` (admission only), `custody`, `install`, `load`
(a reader, never a provider launch), and `rollback`. Resident rotation,
compaction, launcher hold and donor disposition remain refused. There is
no default plan, go, proof, store, body or custody root.
An explicit `--dry-run` forbids this path even when `--native-apply` is also
given. Omitting `--native-apply` refuses before reading any native input.

These are execution-capable source interfaces, not installation authority.
Go files record an externally supplied named authorization; a digest proves
bytes, not the identity of the author. A reviewed operation packet and the
operator's separate live words remain mandatory. The engine triggers no
compaction, provider, launcher, registry update or notification. All
validation of this slice uses invented objects behind masked2.

The bounded private plan is `rotate-disposable/1`: `operation` is one plain
lowercase name, `provider` is `claude`, `provider_version` is a nonblank
label of at most 64 characters, and `writer` is exactly one registered key
in this room. `room`, `project`, `store` and `records_dir` are absolute, unlinked paths;
project and store are distinct existing 0700 owner directories; records_dir
is also an existing 0700 owner directory. No resident
has the disposable project as its room. `registry` is a hash-bound reference
to the canonical room registry, regular single-link 0600 of its accepted
owner, never a shadow registry. `donor` and `destination` each name `path`,
`session_id` and closed `sha256`; their two distinct identifiers must be
unregistered and their exact `<identifier>.jsonl` files are the only bodies
in the named store. The engine never discovers or enrolls a container.

The plan lives directly in `<room>/storage/active/<operation>/`, 0700.
Its separately named go and instrument-proof files live there too.
`candidate` is a `{path, sha256}` reference under that case; `artifacts`
is a list of unique `{name, path, sha256}` references there, including
`capsule`, `gates` and `window`, plus any durable media and supporting
records. Artifact names cannot shadow donor, destination or candidate.
Every file is regular, single-link, owner-only 0600, without linked
ancestors; reads are bounded to 64 MiB per body/artifact and 1 MiB per
record. A bracketed read checks identity, size, mtime and ctime before and
after. Larger inputs refuse; the bound is not an inferred native capacity.

`gates` is a `rotate-native-gates/1` phase-5 record binding
`donor_sha256`, `pristine_sha256` and `candidate_sha256`. Its `gates` object
names `trigger`, `closeout`, `operator_compaction`, `window`, `static` and
`media`. All six must be true. This is a required upstream evidence join,
not a native phase-0-to-5 producer or an authentication of the operator.
The engine additionally parses the bodies, checks identity/parent/tool
structure, the pristine inert first exchange, the candidate boundary, and
structural donor residue. The accepted builder and complete static-gate
evidence remain required; this reader does not replace them with a load flag.

`custody_roots` names two to four existing private roots outside the room,
project and store; `date` is YYYYMMDD. The engine calls custody.py in process
with its real physical-disk checks and without the synthetic same-device
override. The writer/day batch is the canonical `sessions-<writer>-<date>`.
Aliases are `<operation>-donor`, `-destination`, `-candidate`, `-preimages`
and `-<artifact-name>`. Open MANIFEST rows and direct full reads bind the
operation members; the engine does not require or rewrite a shared daily
batch as an exclusive whole-root SHA256SUMS inventory. Closing the day and
its audit remain the writer's separate closeout, not an automatic side effect.

The mapped runtime home is `<room>/logs/rotate/<operation>/`, private 0700,
with `operation.lock`, immutable `preimages.json` and atomic `state.json`
at 0600. The lock is nonblocking. State pins the plan and preimages, actual
root/file identities and known staging/postimages. It never grants a go.
Unknown state, a leftover `.state.NEW`, changed plan/preimages or an
unrecorded stage refuses; no unknown file is swept away. Interrupted
recorded renames can resume by matching the exact staged inode and bytes.

Every `rotate-native-go/1` binds `operation`, `plan_sha256`, `writer`,
`action` and a zoned `at` no more than one hour old. Install also binds
`pristine_sha256`, `candidate_sha256`, `custody_manifest_sha256` and
`inverse: restore-pristine-and-stop`; its time must follow custody.
Rollback names the observed `destination_sha256`; absent-donor restoration
requires explicit `restore_absent_donor: true`. An unchanged donor is never
rewritten. The whole process remains stopped while partial joins are held.

Each `rotate-native-proof/1` binds the same operation/plan/action and has
`quiescence`: exactly two observations at least one second apart, no more
than 60 seconds old. Each observation contains the actual donor/destination
snapshot (type, dev, ino, size, sha256, mode, uid, gid, mtime_ns, ctime_ns,
nlink), project dev/ino, `same_user_observable: true`, and integer-zero
`holders`, `session_records`, `argument_holders`, `locks`, `unreadable` and
`foreign_processes`. Missing observations are unknown, never zero. These
are external-instrument records, not a substitute for I1's real process
inspection. The present interface permits no accepted-foreign-process
exception; a live packet needing one requires a reconciled contract.

The proof's `instruments` object binds the actual observer inputs and outputs.
Each binding is exactly `{packet: {path, sha256}, record: {path, sha256}}`,
all directly in the operation's case. `I1` is a two-element list of bindings,
with distinct fresh output inodes; each output is the actual reader's
`{held: [], own_unreadable: 0, foreign_unreadable: 0}` shape. These records
join the two timed observations; neither timestamp nor digest authenticates
the writer. The adapter additionally refuses unreadable foreign processes,
stricter than I1's standalone verdict. I2's recorded objects, listing and
directory identity must equal actual preimages before admission. Its bound
packet and record remain pinned in state throughout the operation.

Before install, `custody_audit` in that proof binds the member-manifest
digest, a distinct registered `auditor` with role `Auditor`, `verdict: PASS`
and a hash-bound `review` under the case. That `rotate-custody-audit/1`
record binds operation, plan digest, member digest, auditor and verdict.
The engine also re-reads
every required copy. The first install call writes one 0600 same-directory
`.NEW`, fsyncs it, records its identity and returns `install-prepared` without
renaming. The independent I3B reader then inspects that inode. A second
install call requires the exact bound I3B output and unchanged target,
atomically renames, fsyncs the directory, verifies the known postimage and
returns `install-renamed`. A third requires I3A's actual postimage before
returning `installed`. All three use the same post-custody go. Only this recorded
stage can be resumed or removed by the authorized inverse.
Go, plan and instrument bytes, go age and fresh quiescence are rechecked at
the rename boundary, not only before the potentially lengthy custody read.

Load reads an actual append after the installed prefix, requires the same
inode, intact prefix, terminated linked rows, destination identities,
unique message IDs, paired tools and an assistant reply. Its canonical
`gauge.read_claude` result must equal proof `first_gauge` for tokens, model,
reading_at and call; actual I4 output must also match the counted complete
append. Recognition is not inferred; operator_accepted remains
false. Rollback retains appended destination bytes under a NEW custody
alias before restore and requires proof `appended_sha256`. Unknown edits
refuse. Whole rollback compares the store/project listings and file type,
size, hash, mode, uid and gid with the preimages; replacement inode changes
are recorded rather than mistaken for data loss. Restore returns
`rollback-restored`, not a completed inverse. A further call with the same
rollback go, fresh post-restore I1 readings and I5's zero-difference record
alone returns `rolled-back`. Both I1 output files must postdate the saved
restore timestamp. An explicitly authorized absent-donor restore has an
additional `rollback-donor-pending` stop after the destination is restored;
fresh I1 evidence is required before the second target is written.

**Instrument join:** source interface matched to the reviewed instruments
SHA-256 `5c1ea1bc6ac84e0d3b2271527cc5df3f2036051b44fa4e649c4ef299770e6793`
and the revision-4 design pin
`0bf4def343117144e5506b988818e3a1d2ee710b844b4460b0097d7c5f9c252d`.
The private `instrument-packets.json` index points to immutable hash-bound
I1/I2 and phase-specific I3B/I3A/I4/I5 packets. I1 is an explicit two-packet
array with distinct exclusive result names, at least one second apart by
output-file mtime as well as the observation envelope. Every export uses
fresh output names without replacing earlier observations. Initial
`--native-export-instruments` under the disposable-exercise go exports only
I1/I2, before admission or state creation. On an existing operation,
the export flag loads the checked checkpoint under its lock and exports
the phase-specific readers without applying the action. Re-export is inert;
the adapter never runs an observer. After each later stop it exports the
next reader's packet. No supplied packet or result is a live go.

Every packet includes `evidence` and `record_name`; synthetic plans also
name `synthetic_root`. Reader source requires `destination_token` for I3B
and I3A despite its omission from ADAPTER_OUTPUTS; both packets supply it.
I1's `project` is the private working cwd, correcting the table's ambiguous
store-folder description. I2/I3/I5 use the provider-store folder for listings.
I3A emits `{postimage: ...}`, but I4 reads flat metadata plus `uuids`; the
adapter retains the exact I3A output and explicitly derives a separate
hash-bound I4 input from that postimage and the installed candidate's IDs.
It never labels the derived object as an observer output. I5 receives actual
I2 objects/listing, every retained-append custody copy and the newly exported
second I1 output path, never the pre-restore record.
These interface differences require joint review before live use. Paths and identifiers
remain only in the private case/checkpoint; stdout reports reason codes,
hashes and phase names. Mind, notebook and launcher joins report
`NOT APPLICABLE`, never passed. No resident route or real exercise is
claimed by this source implementation.

### Implemented synthetic slices: one dry-run stop at a time

The specification below describes the complete intended rotation. The first
runner checks supplied synthetic evidence, rechecks earlier gates on each
invocation, and stops after the requested phase. The third slice implements
the disposable phases 6 to 9 described below; it is not a native adapter
or authority to operate on a real launcher, registry, store or custody root.
Donor handling still follows CONSTRAINTS C09, not an unconditional restore.

Invocation uses the configured interpreter with `-I -B`:

```text
ops/lib/scripts/rotate.py --room SYNTHETIC_ROOM --key fixture-resident \
  --writer fixture-writer --destination INVENTED_SPARE --phase 2 \
  --gauge-row logs/gauge.json \
  --closeout-state logs/closeout/state.json \
  --closing-record storage/active/closing.json
```

`--phase` defaults to 0. `--dry-run` is the default and the only mode;
there is no apply mode. The room is mandatory, existing, 0700, owned by the
effective user, with no linked path components. It is not the source room.
It contains `.rotate-synthetic.json`, exactly
`{"schema":"rotate-synthetic/1","synthetic":true}`. This marker declares
fixture intent; it authenticates no operator and grants no live authority.
Registry bindings must use invented `0000`-prefix identifiers. No default
native store or real body is opened, and `.jsonl` input paths are refused.
Phases 4 and 5 accept only hash-bound `.fixture` synthetic-body inputs,
with invented session/message identifiers, inside that same private room.
The source room is the executing checkout; this is a cooperating-writer
fixture boundary, not permission to copy or inspect a real body in a clone.

All evidence paths are relative to this room, confined against parent/final
symlinks and `..`; regular 0600 owner files with one link are required.
The registry is `ops/etc/resident-identities.json`. JSON uses the existing
strict duplicate/nonfinite parser; input limits are 1 MiB, or 64 KiB for
the gauge snapshot, closing record, handoff/approval references and pointer.
Evidence is rechecked for content and identity changes before a successful
stop. Existing inputs, their modes, locks and progress records are never
written. Phases 5 to 9 create and remove private temporary fixture
artifacts as described below. Parents
above the private fixture root retain the trusted cooperating-writer bound;
this is not hostile same-user descriptor confinement.

0. **Trigger.** Reuse `notice.measurement`, which validates the gauge/1
   snapshot against the unique registry binding and calls the shared
   closeout pressure rule. Require a live-body, last-observed snapshot at
   the existing closeout.DUE line, using unrounded counters, not rounded
   display percent. The named writer must be a different registered key;
   the recipient's registry room must match. A declared, invented
   `--destination` must differ from every registered container. Its digest
   is reported, but no body is opened and native/spare admission remains
   unimplemented. Tier B is the only admitted tier in this slice.
   Claude and Codex metadata
   preflight are supported, not native rotation parity. Require the exact
   session's existing closeout state entry: matching key, integer band no
   greater than the snapshot band, and integer unknown=0. Preserve the
   snapshot reading/measuring times, age and window provenance. A pending
   `.state.*` sibling refuses without removal. This is
   recorded closeout-state evidence, not independent native-delivery proof.
1. **Donor closing checks.** Read the explicit `rotate-closing/1` record.
   It binds `key`, `writer`, tier `B`, the same hashed `binding` returned
   by notice, `destination_sha256`, and `gauge_sha256` / `closeout_sha256`
   to phase 0's exact bytes. `closed_at` is zoned and no earlier than the usage reading.
   `handoff` is a nonempty retained `{path, sha256}` reference. `mind` is
   exactly `{"index_sha256": <digest or null>}`: the SHA-256 of the room's
   `MIND.md` as the donor closed, or null when the room has no index. Any
   other shape refuses (`mind-index-unproved`); this runner writes no mind.
   These are hash-bound declarations, not authenticated operator authorship.
2. **Mind readiness.** Read `MIND.md` and each live leaf it points at as
   private evidence, then run the mind tool's own verifier (`mind.verify`,
   read-only, no Git) with the explicit synthetic room and registry; any
   blocking failure refuses (`mind-check-refused`). The index's SHA-256
   must equal the closing record's (`closing-mind-mismatch`), so a leaf
   written after the close is caught. The result names the index digest
   and the count of the resident's own leaves. No mind content, handoff
   text or native identifier is printed.
3. **Synthetic destination.** Require `--build-plan`, a bounded
   `rotate-build/1` JSON object binding `key`, `writer`, the phase-0 hashed
   `binding`, and `closing_sha256` to the exact closing record. Its
   `destination` is a retained `{path, sha256}` reference to
   `rotate-spare/1` metadata: exact provider, `session_id`, `room`, `cwd`,
   the registry's plain label plus ` - spare body, do not open`, an
   EXPLICIT `owner: null`, literal `fresh: true`, and integer `work_rows: 0`.
   `created_at` is zoned and no earlier than closeout. A missing owner is
   unknown, not unowned. The plan's zoned `built_at` must follow spare
   creation. This verifies supplied synthetic metadata, not
   native creation, labeling or human authorship. The existing `gate.holders`
   reader checks the exact fixture file, preceded by a same-user process
   observability check. Inaccessible same-user descriptor evidence refuses;
   it is not silently an empty holder list. Other privileged users and a
   writer opening after the last check are outside the cooperating-writer
   boundary. Tests use an explicit synthetic process model; no real host
   holder clearance is inferred from them. A `.rotate-build.*` sibling is
   preserved and blocks this phase, never adopted as prior completion.
4. **Synthetic window.** `donor` is a hash-bound `.fixture` reference,
   at most 1 MiB and 4,096 strictly parsed, terminated JSONL rows. Every row
   must carry the exact invented donor session; nonfixture identifiers,
   including those in prose, refuse. Call the existing `gauge.read_claude`
   on that confined file: tokens, model and reading time must equal phase 0,
   with no later compaction. This reuses gauge usage extraction; it does
   not calibrate a model window. The window remains the validated supplied
   gauge snapshot's value/provenance. Require the last compact boundary
   and exactly one compact-summary row before the chosen cut.

   `cut` names integer zero-based `user_row` and `exchange_row`, retained
   `{path, sha256}` `reason`, and a referenced `estimate` object. The cut and
   substantive exchange must be ordinary user-role rows: no summary, side
   chain, metadata, tool result, known injected prefix or slash command.
   A non-metadata, main-chain assistant reply must follow the exchange.
   That is a structural synthetic-prompt check, not proof a human authored
   native conversation. Splice the boundary, its summary and the tail;
   reparent only the cut row to that summary, leaving prose unchanged.

   `rotate-estimate/1` binds `donor_sha256`, `cut_row`, `window`, positive
   integer `tokens` no greater than 20 percent of that window, and a
   nonempty `method`. This is a retained SUPPLIED wake estimate and target
   check, not a calculated or measured native wake. No token estimator or
   pressure formula is invented. Codex window/build remains refused as
   `provider-window-build-unsupported`: its accepted ingredient omits the
   native compaction summary. It needs its own reviewed design and load test.
5. **Temporary synthetic build and gates.** `transition` is a nonempty
   retained text reference in the build plan, not a path substituted for
   text. Assemble the four capsule parts here: registry header, the
   resident's own index lines and the hint to open a leaf with `mind.py read`,
   transition, first-turn line.
   The legacy six-question Codex capsule generator is not this composer.

   Recheck all evidence and fixture holders, then create one 0700
   `.rotate-build.<unique>` directory directly inside the synthetic room.
   No output path is selected by the caller. Invoke the actual existing
   Claude `successor.main` on the selected private fixture, including its
   field-scoped re-ID and native orientation construction. Use the existing
   `media.Externalizer` on both supported payload shapes. Append the plain
   custom-title/agent-name pair; these are fixture records, not native labels.
   Only the new orientation and label rows receive `built_at`; no historical
   donor timestamp is changed, and the builder's old orientation-date literal
   is not carried into the new row.
   All temporary files are 0600 independently of the caller's umask.

   Run and record each applicable static predicate: termination, strict
   parse and row equality, exact destination identities, structural donor
   residue, unique message IDs and non-dangling parent chain, boundary head,
   matched/unique tool uses and results, one exact capsule orientation,
   named destination, orientation cwd, final plain label pair, zero inline
   media, orientation privacy, media-file fixity and pointer linkage, and
   carried window length/text. A media pointer must name the actual private
   staged file, not merely a matching short digest somewhere else.
   Recheck inputs and holders again before success. Always remove this
   invocation's temporary directory through its own context manager. This
   rehearses real construction/gates but retains no successor or media.
   A killed process can leave staging; the next phase-3-or-later attempt
   refuses it without cleanup or inferred ownership. It is not durable
   recovery or a candidate ready for custody.

### W6 third-slice implementation details: disposable phases 6 to 9

These are explicitly synthetic implementation details, not changes to the
target workflow below. No persistent runner state, automatic resume,
provider adapter or native authorization is introduced. Each invocation
rechecks phases 0 to 5 and performs only through its requested stop in one
private staging context. The supplied room is unchanged when it returns.
Fixture timestamps describe the rehearsal; they do not prove that a real
operator spoke or that a prior invocation completed. A go's declared time
is checked against declared custody time; actual temporary custody copies
are verified again before that go is used.

For phases 6 to 9, `--operation-plan` names private relative JSON evidence.
`rotate-operation/1` binds `key`, `writer`, phase 0's `binding`, and
`build_sha256` to exact build-plan bytes. Its other fields are:

- `process_model`: a retained `{path, sha256}` reference to
  `rotate-process/1`, literal `observable: true`, and lists `holders` and
  `session_records` of confined relative fixture paths. It is loaded before
  phase 3. These phases never inspect the host process table. Unobservable
  or malformed evidence refuses, not an empty clearance. This model is not
  native holder proof or a guarantee against a later cooperating writer.
- `pristine`: a reference to a destination `.fixture` under the selected
  invented identity, in the room, with its exact spare title.
- `donor_store`: a `.fixture` reference byte-identical by hash to the checked
  donor, never an actual provider store.
- `binding_preimage`: a reference to `rotate-binding/1` containing exact
  `key`, old `session_id`, provider `claude` and `root` equal to the room.
- `launcher`: a reference to `rotate-launcher/1` containing exact `key` and
  literal `hold: false`. This file-backed model is not a launcher call.
- zoned `custody_at`, no earlier than `built_at`; `go`, `load` and
  `acceptance` references for later phases; positive integer `rotation`,
  nonnegative integer `deviations`, and `donor_preference: removed` for close.

6. **Synthetic custody and hold.** Create runtime copies of the pristine
   destination, registry, binding, donor store and launcher. Set and read
   back the model hold. Copy donor, pristine destination, successor, capsule,
   gates, registry/binding preimages, launcher and every media file into two
   private synthetic roots with `SHA256SUMS`. Read every member directly
   in each root and verify its hash, exact inventory and manifest. This
   proves two fixture copies, not two independent drives. Stop without
   reading any later word.
7. **Go and synthetic install.** `rotate-go/1` names exact `key`, `writer`,
   `container`, `room`, integer pristine `size`, its `custody_sha256`,
   `rollback: restore-pristine-and-hold`, integer `after_phase: 6`, literal
   `word: go`, and zoned `at` strictly after `custody_at`. Wrong targets,
   early words and refusals do not authorize install. Recheck unchanged
   inputs and both custody roots. Verify the runtime destination against
   pristine custody bytes and consult only the process model.

   If held, stage `destination.fixture.NEW`, retain the hold, and report
   next phase 7 with only 0 to 6 completed. No binding changes or operator
   swap are inferred; requesting acceptance while held refuses. Because
   this is disposable, no `.NEW` survives and no later call adopts it.
   Otherwise stage beside the runtime destination at 0600, hash it, rename
   and verify; switch only the model registry identity and binding. The
   canonical identity-registry privacy contract below applies to preimage,
   staging and postimage, including accepted uid/gid. Measure all six
   agreements. Stop without reading load or acceptance.

   C12 operates only on temporary copies. Refusal, failed step, load failure
   and ordinary interruption reassert and verify the known hold first, then
   restore all four preimages from directly verified custody. A missing
   donor is restored only after the bound rollback go was validated.
   Unexpected/newer bytes or identity stop restoration, never overwrite
   them; report rollback unknown, never success. Staging is still disposed,
   since no supplied input or real surface was changed.
8. **Synthetic serve and acceptance.** `rotate-load/1` binds `key` and
   `container`, literal `loaded: true`, zoned `served_at` no earlier than the go, and
   `readback` equal to the key, registered person and room. Release the model
   hold and append its hash-bound `.fixture` rows. Check a first assistant
   reply, exact session identities, strict parse, termination, unique message
   IDs, parent linkage and matched tool pairs. `gauge` references a snapshot
   validated by notice against the switched model registry; the existing
   gauge reader must extract the same tokens, model and time from the
   appended file, with no later compaction or reading before serve.

   A separate `rotate-acceptance/1` fixture names exact key and container,
   literal `word: recognize`, and zoned `at` no earlier than the reading.
   The load record also requires `mind_confirmed: true`. These are declared
   fixture recognition/readback and confirmation, not semantic or native
   proofs. Correct status or a load flag alone is insufficient.
   Named detail: the synthetic runner requires that confirmation fixture at phase 8
   as a stricter model prerequisite; the target workflow still places the
   resident's actual confirmation at phase 9. No native step is resequenced.
9. **Synthetic close.** Invoke existing `ops/bin/template receipt` with its
   actual 17 slots, bounded timeout and minimal environment; no shell
   interpolation or caller-selected command. Write its receipt privately
   under staging `archives/receipts/`. It carries cut/reason, actual gates
   and custody, mind digest, estimate beside extracted wake, counted
   deviations and timed fixture acceptance. Reverify custody and the
   unchanged donor entry, then unlink only the disposable runtime donor
   copy for preference `removed`. Both custody copies and the supplied
   donor remain intact. Report receipt size/hash, not content. No real kept
   receipt is created.

Exit 0 means only that the requested dry-run gate stopped successfully;
output lists `completed`, `next_phase` and `needs`, never whole-rotation
acceptance. A refusal or unsupported phase exits 2. Every output states
dry-run, no native-load proof and no operator acceptance. `writes` is zero
through phase 4; phases 5 to 9 report the number of temporary file artifacts
present for cleanup (not total creations or syscall count), their write scope
and successful removal. Phase 9 can already have removed its model donor.
No input or persistent state is changed, and no artifact content is printed.
For phases 6 to 9 `rehearsal` reports measured copy counts, hashes, agreements,
hold/rollback state, fixture wake and receipt metadata. Even phase 9 leaves
`native_load_proved` and `operator_accepted` false. Native operations and
physical custody remain unimplemented, not demonstrated by this model.
An interruption leaves no runner state to adopt: repeat the same phase
with unchanged evidence, or supply corrected evidence and recheck from 0.
There is no inferred persisted completion, automatic resume or journal.

Tests: `tools/test/test_rotate.py`; test contract:
`docs/ops/specs/tools/test/rotate.md`. The existing template generator
supplied the initial script/test skeleton while preserving this spec.

### Complete resident target workflow (not implemented by the disposable engine)

**Roles.**
- **The operator:** chooses the tier, creates the destination container, gives the go, accepts or does not.
- **Writer:** exactly one, named before work starts, never the resident being moved. Builds, gates, takes custody, installs, writes the receipt.
- **Donor:** closes well; never builds its own successor.
- **Auditor:** the audit afterwards, read-only.

**Tiers, declared in writing before work starts.**
- **B, transplant:** the default. The capsule plus the donor's compaction summary and a measured slice of its own window, word for word.
- **Capsule-only:** only when a window build fails to load, on the operator's go.
- **A, reseed:** a fresh session reads the handoff. Only on the operator's explicit choice, recorded as Tier A and never called a rotation.

**The capsule.** It is appended as the orientation row, as text, never as a path, in four parts:
1. **Header,** from the registry: person, role, room, destination container.
2. **The mind:** this resident's own pointer lines from the room's `MIND.md`, pointers only, never a leaf's body, and the hint to open a leaf with `mind.py read <id>`; the index's SHA-256 is recorded in the receipt.
3. **Transition note,** written by the writer:
   - the window range not carried, and the handoff sections that cover it;
   - work in flight, the hold, the owners;
   - anything after the donor's last row.
4. **First turn:** "the room's status in a few lines, then speak as yourself."

The mind supplies part 2 only. Identifiers and live state belong in parts 1 and 3. The window always travels too; the mind is added to it and never replaces it. (C11: the capsule is assembled by `rotate` from these four parts. No mind command produces it.)

**Phases.** Each ends at a stop point; the writer reports and does not run ahead.

0. **Trigger.** The gauge reading crosses the resident's line, and the closeout card has run (`closeout.md`). The writer records the tier, donor, writer, destination and the gauge reading in the handoff.
1. **The donor closes well,** by the card:
   - a closing handoff;
   - any idea it learned that stays true, written as a leaf with `mind.py add`, no approval asked;
   - the closing record names the index it closed with.
2. **The mind is ready.** `mind check` passes, and the index hash matches the closing record.
3. **The destination.** the operator opens a fresh chat in the resident's room. The writer labels it `<Role (Person)> - spare body, do not open` at once. The writer then verifies:
   - the room and working directory are right;
   - the container is not registered to anyone else and carries no "old", "spare of another" or "do not resume" label;
   - no process holds it.
4. **The window.** Measure the donor from its own usage figures, by the gauge method. Choose the cut at a genuine operator prompt, so the measured wake estimate leaves the resident well inside its runway: a target of about 20 percent. Shannon's rebuild of 2026-10-29 woke at 32.8 percent, which spent a third of the window before the first word and brought his next closeout line within one heavy day. Carry at least one exchange with the operator beyond procedure. Record the reason for the cut.
5. **Build and static gates.**
   - Splice: boundary, summary, tail.
   - Re-identify by identity field at any depth, never by text.
   - Externalize media, with each pointer naming its custody path.
   - Append the capsule text as the orientation row, then a fresh label pair with the plain name.
   - Run the gates: final line terminated, 0 parse errors, every session id the new one, 0 structural donor ids, 0 dangling parents, the head is the boundary, tool pairs matched, exactly one orientation row, its identity matching the registry, the new container named, the room's working directory, the plain label last, 0 inline media, and no medical words in the orientation.
6. **Custody and serve-safety.**
   - `launcher stop <key>` writes the hold.
   - The donor's closed copy, unmodified, goes to both tiers, checked against `SHA256SUMS` (tier 2 by direct read).
   - So do the pristine destination, the successor, the capsule, the gates, the media, and the registry and binding before the change.

6 to 7. **The operator's go,** for this replacement. The writer names the container, room, size and custody hash about to be replaced, and the rollback, then waits. A go given at phase 0 does not count.

7. **Install.**
   - **Default, the writer's verified swap:**
     - check that the destination still equals its custody copy and that no process or session record holds it;
     - write the successor beside it, hash it, rename it over atomically at mode 0600, and verify it;
     - switch the registry key and the launcher binding;
     - check that six things agree: registry id, binding id, body `sessionId`, binding root against body working directory, registry room, body label.
   - **Fallback, the operator's `.NEW` swap:** when a process still holds the file, or when the operator prefers it. The writer leaves `<id>.jsonl.NEW` beside the original; the operator closes the app and swaps it.
   - **Rollback (C12).** It runs on the operator's refusal, and also on any failed install step or failed load:
     - restore the pristine destination;
     - restore the registry and binding;
     - put the donor's store file back from custody;
     - keep the hold.

**Canonical identity-registry privacy.** Registry-value updates, creation,
replacement and restoration of `ops/etc/resident-identities.json` require
mode 0600, preserving its accepted uid and gid, regular single-link type
and no symbolic link in its path. This is distinct from the launcher roster
and binding pair. An in-place content update preserves the existing private
mode; a newly staged file must explicitly have 0600 before publication.
Verify both the staged object and the canonical postimage; do not rely on
umask or copy defaults. A preimage/postimage mismatch or unexpected
ownership, type, link count or path change stops the affected operation
instead of overwriting newer state. A separate metadata-only correction
names its own go, preimage and bounded inverse; it changes no registry values
and grants no enrollment, body-replacement or activation authority.

8. **Acceptance, in two parts.**
   - **Mechanical.** `launcher serve <key>`, which also releases the hold and is the load test. The first reply gives the room's status and then speaks as itself. Its first gauge reading is recorded beside the wake estimate. (C13) A clean native append: after that turn the body still parses, Claude Code's own new rows carry the new session id, and tool pairs match.
   - **The operator's.** the operator states that he recognizes her, or him, as the resident. A correct status alone is not acceptance.
9. **Close.**
   - Write the receipt `archives/receipts/<resident>-rotation-<n>-<date>.md`: tier, cut and reason, gates, custody, mind index hash, estimate against the measured wake, deviations counted, acceptance and its time.
   - Handle the donor's store entry. After its custody is verified by hash in both tiers, the entry is either relabeled "<Role (Person)> - donor, rotated <date>, do not resume" or removed from the list, as the operator prefers. His standing preference since 2026-10-29: removed. The custody copy is the donor of record.
   - The new resident reads its own leaves and confirms they still hold.

**Codex residents** (Joe Codex, 2026-10-30): `ops/lib/scripts/rotation.py` carries messages after the last native compaction but not the compaction summary. A Codex rotation under this spec waits for a Codex-specific design and a loader test.

## Anecdotal Anchor

2026-10-29:
- the 19:12 rotation was Tier A run as a rotation, and woke as a resident the operator did not recognize as his doctor (his words, paraphrased);
- the 23:34 rebuild passed its gates but carried a briefing for a self, and the operator found that something was missing from it;
- the 00:04 rebuild carried a real self and Shannon's own window, and he woke as himself.

On 2026-10-30, Joy's rotation 6 followed these phases by hand and woke as herself, with her wire printed by 08:57. Its three hand-made slips are what this tool removes.

Think of a hospital transfer: the chart travels with the patient, the receiving doctor reads it before the first word, and nobody signs the transfer until the patient answers to their own name.

## Integrity Filter Warnings

- **Three separate things.** Static valid is not loader valid, and loader valid is not accepted.
- **No serving in between.** The background timer never serves a resident between custody and acceptance; the hold stays.
- **The donor is never modified.** Its closed copy is the record. The store entry is relabeled or removed only after custody is verified.
- **Text, not path.** The orientation is text. A capsule path is a gate failure.
- **No identifiers in the mind.** Identity stays in the registry.
- **One writer,** never the resident being moved.
- **A wake estimate is an estimate.** The first gauge reading is the measurement.
