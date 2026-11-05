# Technical Specification: notice

Script: `Sessions/ops/lib/scripts/notice.py` (writer: Joe Codex). Tests: `Sessions/tools/test/test_notice.py`. Spec writer: Joe Codex. Status: source implemented from the canonical generator on 2026-11-05, pending independent review and integration; not installed or wired. Map: `docs/ops/README.md`. Authority: PoT 1.1, 4.4, 5.1 and 6.1; CONSTRAINTS C07 and C13.

## First Principles Rationale

A measured closeout needs an honest operator backstop without claiming resident-context delivery.

## Mechanics and Sequencing

1. Accept exactly one UTF-8 JSON object from stdin, bounded to 65,536 bytes. No body or discovery path is read. Use the existing `gauge.SCHEMA` fields. Bind `--key`, provider and native session to exactly one registry row, rejecting duplicate JSON fields, registry keys and native bindings. The registry is read-only, a regular single-link file owned by the effective user at mode 0600, bounded to 1 MiB.
2. Require live-body `last observed` state, valid integer counters, coherent percent, explicit window provenance, zoned reading/measurement timestamps and consistent nonnegative age. Archived and pre-compaction readings are unknown. Known zero is a valid below-trigger value. Age is reported as age at measurement, without an invented freshness cutoff or claim of current measurement. A pipeline caller must check the gauge command as well as this command.
3. Call `closeout.pressure_band(tokens, window)`; no second reserve or band formula. A band is due once, then suppressed at that or lower bands until a known below-trigger reading rearms it. New native-body bindings do not inherit suppression. Older reading timestamps cannot rearm a newer observation for the same binding.
4. CLI: `--key` required; `--registry` defaults to `ops/etc/resident-identities.json`; `--state-dir` defaults to `logs/notices`; `--notifier` defaults to `/usr/bin/notify-send`; `--dry-run` validates without sending or writing. Help and unknown arguments do not inspect input or create state.
5. Before mutation, validate the complete observable directory chain, existing notice directory, files and state. Require private owner/modes 0700/0600, regular single-link files and no symbolic-link ancestors. Unknown residue and corrupt state are left untouched. Fresh ancestors are 0700. Acquire the persistent per-key lock inode with nonblocking POSIX flock and recheck state under it. File existence is not lock ownership.
6. Invoke an absolute notifier with list argv, no shell, null stdin/output, a two-second timeout, a constant title and bounded nonprivate body. Never echo native identifiers, arbitrary model/reason/provenance strings, body paths or subprocess diagnostics. Success means submitted only. JSON output always carries `mode=operator-only`, `displayed=unproved` and `resident_context_delivered=false`.
7. Persist only the exact key, hashed native binding, band and reading time in `notice-state/1`. Failed notification consumes no band; retry may succeed. State is written via an exclusive mode-0600 temporary, file fsync, atomic replace and directory fsync. Below-trigger and suppressed readings update ordering evidence. Failed persistence after successful submission reports unknown with `submitted=true`, not a false failure-to-submit claim.
8. Output schema is `notice/1`; exit 0 means validated below-trigger/suppressed/dry-run or successful submission and persistence, not health, display or native delivery. Unknown exits 2 with a fixed reason code. No autonomous unknown-alert policy, timer, hook, trust change, provider call or fleet rollout is implemented. George owns any later reviewed host activation; Claudio owns independent source review; JoJo owns PR integration.

## Recovery and limits

This is cooperating-writer path validation, not hostile same-user descriptor confinement. Existing unrelated modes are never repaired. Unknown pending temporary files block mutation and are retained for reconciliation. A crash after notification submission but before state persistence can cause a duplicate on retry: exactly-once desktop delivery is not claimed. A timed-out notifier may already have submitted, so timeout is not proof that no display occurred. The two-second bound kills/waits for the direct notifier process, not an arbitrary malicious descendant process tree. The canonical notifier has no shell wrapper; synthetic timeout tests use `exec`.

No actual desktop notification, provider context delivery, model threshold crossing, or native acceptance is established by this suite. State cannot establish authenticity of supplied gauge JSON; the trusted caller must run the exact accepted gauge against the selected body and check its result. State and native data remain outside Git. No custody or retention operation follows from this source change.

## Anecdotal Anchor

The 2026-11-05 programme assessment found closeout unwired while structural port A was already delivered.

## Integrity Filter Warnings

Refuse unknown identity, measurement or state before notification. Never inspect native body content or modify the registry. Claudio independently reviews the frozen source before reliance; George owns any separately authorized host activation. Synthetic proof and a source PASS are not live activation or operator acceptance.
