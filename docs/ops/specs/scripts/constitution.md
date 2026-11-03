<!-- redact: public copy; source sha256 846f1d8f59b1725eb327000fcc178e7cb08868b7b24cc4e2aaabcca3dc4286de; rules 8; mode history; words 1; sessions 0 whole, 0 truncated; host paths 0; decisions 0 -->
# Technical Specification: constitution

Script: `ops/lib/scripts/constitution.py`. Tests:
`tools/test/test_constitution.py`. Status: built; 10 synthetic Git contract
tests pass locally; hosted CI and independent exact-head review remain pending.
Map: `docs/ops/README.md`.

## First Principles Rationale

A PoT edit is a constitutional change, not an ordinary document update. A
textual "[words sha256=2687f86ed6784b8a5fca36e6c468e12aa44dc3c7e8137e3160d1a95079bdcd02]" marker cannot establish that the exact candidate was
authorized, and a previous decision cannot authorize a different policy hash.
This gate enforces exact base/head coupling in the repository's normal private
pull-request route.

## Mechanics and Sequencing

1. Run `python3 -I -B ops/lib/scripts/constitution.py --base <accepted-base> --head <candidate-head>`.
   Both local checks and CI use this same interface and exact commit pair.
2. The gate requires a clean candidate checkout, resolves both revisions,
   verifies that base is an ancestor, and reads only regular tracked files
   from Git objects; policy, ledger and evidence paths cannot be symlinks.
3. If `PoT.md` is byte-identical at base and head, the result is an ordinary
   pass and no decision evidence is required.
4. If `PoT.md` changes, it must be modified in place. The candidate must add
   `archives/PoT-<hash8>.md` byte-identical to the candidate law and
   `archives/PoT-authority-<hash8>.md`, where `hash8` is the prefix of the
   exact SHA-256 of that law.
5. In the same candidate, `RoR.md` must be append-only and include a newly
   appended latest operator-decision entry scoped to `PoT.md`. Its full target
   hash, private-words digest, snapshot and sanitized authority leaf must
   agree exactly. A standalone approval word, old decision, unrelated entry,
   stale hash or missing record fails.
6. This is a structural and consistency check. It cannot authenticate who
   supplied the operator decision or whether protected review occurred.
   Those facts depend on the independent protected review/operator
   provenance in the private Git process; this script does not install or
   prove GitHub branch protection.
7. The gate reads no private `archives/RoR-words.md`, bodies, registry,
   receipts or host state; it writes nothing. Task scratch for synthetic
   tests is created under `var/tmp/` (PoT 1.1.13) and each test removes only
   its own temporary repository.

## Anecdotal Anchor

The 2026-11-03 filing alignment is intended to close a permanent
storage-state exception while preserving the existing gauge ledger, mind lock,
and closeout state paths for later bounded migration. The exact current
inventory and holds are in `docs/ops/README.md`; this gate is independent of
those consumers.

## Integrity Filter Warnings

- Refuses dirty checkouts, invalid revisions, unrelated base/head histories,
  symlinked or executable policy/evidence files,
  deleted or renamed law, missing or overwritten hash snapshots, missing
  sanitized authority leaf, non-appended ledger history, stale/wrong hashes,
  mismatched decision scope, and inconsistent private-source digests.
- An unchanged PoT is an ordinary pass; a malformed or absent PoT is not
  treated as unchanged.
- The authority leaf and ledger structure are not proof of human identity or
  cryptographic operator authenticity. Independent review, the delivered
  operator direction and repository protection remain outside this checker.
- No session body, private record content, credentials, host state, or
  session identity is read or written.
