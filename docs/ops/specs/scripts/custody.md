# Technical Specification: custody

Script: `ops/lib/scripts/custody.py`. Tests: `tools/test/test_custody.py`. Spec writer: Claude Shannon (Session Continuity Manager), 2026-11-08. Status: built, first slice; proposal P5.3 of the review plan of 2026-11-07, accepted by the operator.

## First Principles Rationale

Custody kept every private source safe, one act at a time: by 2026-11-07 tier 1 held 25 batches from four days, each written by its own one-off script in the Manager's scratch, eight such scripts in all, none of them a maintained tool, and each batch took its own audit. A rule that the tool enforces is safer than a rule each script restates: the same bytes on every root, an append-only record, private modes, and a close after which nothing is added.

## Mechanics and Sequencing

1. **One batch per writer per day,** named `sessions-<writer>-<date>`: the writer a plain registry key, the date `YYYYMMDD`. It is opened by its first `add` and closed once by `close`, at the writer's closing handoff.
2. **Roots are arguments, never a file.** Each `--root` names one custody root; at least two; none named twice; each a plain absolute directory, not a link. **Two roots on one device are refused,** since they are one copy, not two. `--same-device-ok` exists for the synthetic suite only. The tool names no host, so the count of names (`fingerprint.md`) holds.
3. **`add`** takes regular files only, never a link or a folder. Every item is checked before any root is written, so one refused item writes nothing. Each copy goes to a hidden `.part` name at 0600, is hashed in full, compared with the source's hash, and only then renamed into place. A copy that does not match is removed and the run refuses. The source is hashed again after the copies, and a change refuses. Then one row, `sha256  name  time`, is appended to `MANIFEST` on every root, with an fsync. Names are plain, never `MANIFEST`, `SHA256SUMS`, `README.txt` or `CLOSED`, and never a name already in the batch. `--as` stores one file under another name.
4. **The roots must agree** before and after every act: the same state (absent, open or closed) and byte-equal manifests. A disagreement refuses.
5. **`close`** first checks every root whole against its manifest, then writes `README.txt` (the writer's ASCII text, required), `SHA256SUMS` sorted by name, and `CLOSED` holding the hash of `SHA256SUMS`, each 0600 by exclusive create. After that, `add` and `close` refuse.
6. **`verify BATCH`** checks every root against its own record, `SHA256SUMS` once closed and `MANIFEST` while open, and reports each missing, mismatched or unlisted item. Exit 1 on any fault.
7. **`--direct ROOT`** reads that root's copies back with `O_DIRECT`, for a failing medium, as the earlier batches did.
8. **Exit codes:** 0 done, 1 a fault found by `verify`, 2 refused. A refusal prints `custody refuses: <reason>` on standard error. An operating-system error, such as a full disk, is a refusal, 2, never a traceback.
9. **A refused `add` leaves no stray copy:** the item's copies already placed on earlier roots are removed, before any manifest row is written for it.
10. **Recovery from a `close` cut off between roots:** the roots then disagree, some closed and some open, and every later act refuses. Recover by hand: confirm with `sha256sum -c SHA256SUMS` that each closed root is whole, then copy the three closing files, byte-equal, onto each open root. Nothing else is touched.
11. **`--direct` must name one of the `--root`s,** compared by resolved path, so a different spelling cannot drop the direct read silently. `verify` takes only a name of the form `sessions-<writer>-<date>`.
12. **Items are single regular files.** A tree, such as the rollbacks batch, is not a day item: it stays a batch of its own, made and audited as before.

What it does not do: it opens no session content, reads no live root in its tests, and never deletes or rewrites an item. A batch made by an earlier script stays as it is; this tool does not adopt it.

## Interim roots, 2026-11-08

On the operator's word the interim tier 2 is a folder on the large external drive, while the failing medium is being imaged and its replacement is delayed. The roots are given on each call, so the swap to the new drive changes the command, not the tool.

## Anecdotal Anchor

Proposal P5.3 (`storage/active/review-20261107/p5-3-custody-by-day.md`, passed by the Auditor at 4e08f68d), and the Auditor's condition on it: a release that rests on audited custody waits for the batch's close or for an audit of that one item.
