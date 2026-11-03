# Local scratch layout

Introduced: 2026-11-03 00:55:13 EST (-0500) / 2026-11-03 05:55:13 UTC.
Writer: Session Continuity Apprentice (Joe Codex), joe-codex.
Filing authority: PoT 1.1.4, 1.1.12 and 1.1.13. The initial introduction is
recorded privately in archives/receipts/project-var-tmp-introduction-20261103.md;
the immediate policy/default integration is recorded in RoR-16 and its receipt.
There is no new automatic purge policy.

## Homes

| Path | Current purpose |
| --- | --- |
| `var/tmp/` | Ephemeral task-local scratch: temporary clones, extracted test trees, disposable probes and intermediate build output. |
| `storage/intake/` | Incoming material awaiting classification, handled as data rather than installed code. |
| `storage/active/` | Named active case payloads: drafts, review packets and working evidence; not operational software trees. |
| Existing named `storage/` lanes | Current handoffs and enumerated legacy state, preserved only under the bounded migration holds in `docs/ops/README.md`; no new tool state or loose storage-root files. |
| `logs/` | Machine-generated telemetry and diagnostics. |
| `archives/` and verified external custody | Kept records, accepted evidence and retained recovery material, under their existing privacy and retention rules. |

Borrowed design: Projects/STELA/PoT.md, Filing Doctrine; Projects/STELA/docs/MAP.md,
base layout; Projects/STELA/.gitignore, local runtime roots. The STELA repository
was read, not modified. This port does not import STELA's other governance or tools.

## Using the scratch directory

From the Sessions project root:

```sh
mktemp -d "$PWD/var/tmp/joe-task.XXXXXX"
```

Use a task/resident-specific prefix. Only the skeleton files in var/tmp are
versionable; its generated contents stay ignored. The host directory is mode
0700. A fresh checkout gets the skeleton from Git once the owning Git writer
integrates it; verify the private mode before writing sensitive working data.
No global TMPDIR or system /var/tmp setting is changed by this layout.

The storage working case points to its temporary scratch only while that case
is active. A sole-copy record or required rollback is not scratch merely
because it was produced during a task; its kept copy belongs in the existing
private record/custody lane. See PoT 1.2.9, 5.1 and 5.3, and Control's
Decisions/backup-quarantine-and-retirement-retention-standard.md.

## Existing material and closeout

Existing operational state paths are unchanged. The help and template self-tests
now default to project-local var/tmp, while retaining an explicit TMPDIR override.
Existing data classification and migration belong to the separately requested final
retention pass. This is not a renamed storage dump or a second evidence archive.
There is no automatic purge, age-based sweep, system tmpfiles rule or service.
Active work, custody, minds, registered bodies and unique review evidence are
not removed by introducing this directory. No historical path is silently moved.

Current integration status is in storage/handoff/joe.md and the owning Git
writer's handoff; this dated introduction is not a claim of remote merge.
