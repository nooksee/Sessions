<!-- redact: public copy; source sha256 0c0db3498cd8d707e94b16bc50b72daa87617f6de73aed55589eb7c078768a44; rules 8; mode record; words 0; sessions 0 whole, 0 truncated; host paths 2; decisions 0 -->
# Custody receipt: sessions-receipts-20261101

- **Date:** 2026-11-01 14:43:42 EST
- **Writer:** Session Continuity Manager (Claude Shannon), registry key session-doctor
- **Authority:** Claudine section 24 (2026-11-01 14:01), condition C2: 303 receipts live in no repository after Control PR #119 released them and the Sessions allowlist keeps them out until the redaction pass; a custody copy makes the live copy not the only working copy. Taken under the operator's deferral of 12:4x.

## Contents
Sessions/archives/receipts/, whole: 306 files (the 304 moved at stage D plus the two landing records), and a SHA256SUMS file over all of them

## Tiers
- **Tier 1:** [host path 1] (307 files, mode 0600, directories 0700)
- **Tier 2:** [host path 2] (307 files, mode 0600, directories 0700; hard_vol2 is the failing medium, PoT 5.3.3)

## Verification
Tier 1: sha256sum -c against SHA256SUMS, 306 of 306 ok. Tier 2: every file read with dd iflag=direct and hashed, 306 of 306 ok, 0 bad. SHA256SUMS sha256 c0f759a6 on both tiers.

## Excluded
Nothing from archives/receipts/. Bodies, minds, the registry and bindings are not in this batch.

## Counts
copied 306, verified 306, unlinked 0 (a custody copy; the live files stay in place)

## Deviations
0
