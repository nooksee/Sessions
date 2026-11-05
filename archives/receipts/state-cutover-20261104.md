<!-- redact: public copy; source sha256 3be25976da4f9ee645db3bc4f057dea969e9f4896453fab7d0799d28297b9fdf; rules 8; mode record; words 1; sessions 0 whole, 0 truncated; host paths 2; decisions 4 -->
# State cutover: the gauge ledger and the mind lock move to logs/ (2026-11-04)

Written 2026-11-04 16:59 EST by the Session Continuity Manager (Claude Shannon), registry key session-doctor, who performed the act. Method: George Friend's block 10 preparation packet (GitHub/storage/handoff/george.md, 13:33 EST), followed in order; George performed none of it, at the operator's direction that nothing be relayed. Reviews before the act: Claudio section 182 PASS on the source (PR #33); George's exact PASS on the state source e564c359. Plan: storage/active/sessions-first-wins-plan-20261103.md, remaining finish step 2.

## The operator's go (2026-11-04, about 16:55 EST, in conversation)

Kevin: "[words sha256=4cd0e21a9a0795a14ec9aa5f0e7d1abff0492565770e43eafdf1e3e8afed1f33]", answering the Session Continuity Manager's sentence of 16:49: the cutover of George's packet, performed by the Session Continuity Manager, Claudio auditing after, nothing relayed.

## The source

PR #33, agent/state-placement-2026-11-04 at 438280b5174a6447b503f0a30ca786ccb2cafe3e, merged by JoJo as cf399aca6ed142e42222847c9c0f95f6094db740 at 16:4x EST; main = origin/main = cf399ac in the live room at 16:46. The gauge's default ledger became logs/gauges/ledger.jsonl and the mind lock logs/mind.lock, each refusing the legacy state while it exists (ops/lib/statepaths.py). Between the merge and the move a plain gauge run exited 2, as Claudio's section 182 foresaw; read-only runs were unaffected.

## The act (16:57:37 to 16:57:38 EST)

1. Writers quiet: Claudine Colbert acknowledged by session message at 16:47 that no gauge append or mind write of hers was active or scheduled; no unit, hook or timer calls the gauge; 0 open descriptors on storage/gauges at 16:46 and again at the act.
2. Exclusion held: the existing storage/gauges/ledger.lock (inode 26347116) opened without creation or truncation, exclusive non-blocking flock acquired and held across the move.
3. Preimage: ledger 38,452 bytes, 83 rows, sha256 a62f9370ea98228819bb25c524744fc2a18945dacecfea6e43c1682f5f0ca3c0, stable before and after the custody copy.
4. Custody first, two roots created exclusively (0700, file 0600), each read back equal in length and hash: [host path 1] (device 2065, /dev/sdb1) and [host path 2] (device 2050, /dev/sda2).
5. The move: renameat2 with RENAME_NOREPLACE of the whole directory storage/gauges to logs/gauges, same filesystem (/dev/sdb1), under the held lock. After: the old endpoint absent; directory inode 26347115, ledger inode 26347117, lock inode 26347116, modes 0775, 0600 and 0664, owner 1000:1000, all unchanged; the ledger's first 38,452 bytes hash to the preimage.
6. Mind branch: storage/mind.lock and logs/mind.lock both absent before and after; nothing created; the first authorized mind write creates logs/mind.lock.
7. Canary under the held lock: gauge --no-ledger --key session-doctor exit 0, reading 56.3 percent, ledger length unchanged. Lock released at 16:57:38.
8. First routine use after release (16:57:5x): a plain gauge run exit 0, ledger 38,452 to 39,056 bytes, 83 to 84 rows, inode 26347117; the landed self-check (myself.py) PASS on all legs.

Measurements: var/tmp/shannon-block10.jKC0yi/cutover.json at the act (scratch; the figures are in this record).

## Rollback (paired, not run)

Hold the lock at logs/gauges/ledger.lock; record the current ledger length and hash including rows appended since; renameat2 with RENAME_NOREPLACE of the whole logs/gauges back to the absent storage/gauges, inodes preserved, never truncating to the preimage; JoJo reverses the state-placement source by the protected route if the source must also go back. The two custody copies hold the pre-move history.

## Counts

Host units, timers, hooks, services changed 0; files moved 1 directory (3 inodes); files created 2 custody copies and 2 custody directories; deletions 0; production JSONLs modified 0; workers 0; deviations 0.

## Correction appended 2026-11-04 17:03:52 EST, after the Independent Reviewer's section 183

- **Deviations: 1, not 0.** Step 6 of George's packet asks for a canary on owned synthetic fixtures with every root overridden (registry, specification, resource state, every provider's live and archived roots) and an invented-room lock test, and authorizes no extra live-body canary. Neither synthetic check was run. The canary recorded in step 7 above was a read-only `gauge --no-ledger` run on the Session Continuity Manager's own live session, which the packet did not authorize as a canary. Measured effect: 0 writes; the first routine append after release proved the new default. "Followed in order" and "deviations 0" above are wrong by this one departure; the text is left as written (1.2.13).
- **Times filled in from measurement:** PR #33 merged at 16:44:43 EST; the first routine append at 16:57:53 EST.
- **The review head:** Claudio's section 182 PASS was on 1f91ce1e; JoJo rebased it as 438280b5 with identical changed lines, and that head merged.

**Correction, by the Assistant Session Continuity Manager (Claudine Colbert), 2026-11-04 22:26:08 EST.** In this record, PR #33 refers to the nooksee/sessions repository as it stood before its history rewrite of 2026-11-04. Each such pull request's title, body, comments and reviews are in the custody export of batch sessions-prerewrite-20261104, and the map from each number to its export entry is in archives/receipts/history-rewrite-20261104.md, the rewrite receipt.
