# Technical Specification: test_notice.py

Tool: `ops/lib/scripts/notice.py`. Test: `tools/test/test_notice.py`.
Writer: Joe Codex. Scope: synthetic data and fake notifiers only.

## Purpose and invocation

Run the configured Python with `-I -B tools/test/test_notice.py`. All inputs
are temporary registry/measurement/state fixtures. No production body,
registry, notifier, mind, hook, settings or service is used. The shared
pressure helper is tested by interception as well as boundary cases.

## Proofs

Exact identity and uniqueness; malformed, duplicate, oversized and multiple
JSON rows; zero/invalid counters; archived/compacted/unknown readings;
window provenance, percent and timestamp coherence; source-age labeling;
band boundaries, suppression, rearm, changed-body and out-of-order cases;
dry-run absence of writes; bounded argv and content nonleakage; notifier
failure/timeout and retry; honest post-submission persistence failure;
0700/0600 creation under an open umask; unsafe modes, symlinks, hardlinks,
FIFO and corrupt/pending evidence preservation; nonblocking actual flock
contention; stable lock inode; process help/argument/submission/timeout
smokes using only invented local executable fixtures.

## Not proved

No actual popup, native context delivery, installed automation, hostile
same-user confinement, exactly-once crash delivery or full continuity loop.
The canonical source specification states recovery limits explicitly.
