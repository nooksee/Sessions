<!-- redact: public copy; source sha256 0603ff2f7eaa97b68ef9f13de02f03f72cdf0a7dd719e2c5246668ff7002de87; rules 8; mode record; words 1; sessions 0 whole, 0 truncated; host paths 2; decisions 1 -->
# Custody receipt: sessions-evidence-20261101

- **Date:** 2026-11-01 22:58:29 EST (copies taken 22:5x EST)
- **Writer:** Session Continuity Manager (Claude Shannon), registry key session-doctor
- **Authority:** Block 6 under the operator's go ("[words sha256=4910b6ba712b10abaf3968ddb9d38104ccea88cb07800a05cca2089d4134dc96]", 22:32 EST, to the sentence of 22:31); Claudio section 160 C4; Control PR #123 (312413b7) released the 478 tracked paths.

## Contents
Sessions/Evidence/, whole, before its move: 489 files (478 released by Control plus 11 untracked live outputs), and a SHA256SUMS file over all of them

## Tiers
- **Tier 1:** [host path 1] (490 files, mode 0600, directories 0700)
- **Tier 2:** [host path 2] (490 files, mode 0600, directories 0700; the failing medium, PoT 5.3.3)

## Verification
Tier 1: sha256sum -c, 489 of 489 ok. Tier 2: every file read with dd iflag=direct and hashed, 489 of 489 ok, 0 bad. SHA256SUMS sha256 25b74bdf on both tiers.

## Excluded
Nothing from Evidence/. Bodies and minds are not in this batch; the two identity sources are (byte-equal to their ops/etc copies).

## Counts
copied 489, verified 489, unlinked 0 by this batch (the move that followed unlinked the originals after its own verify)

## Deviations
0
