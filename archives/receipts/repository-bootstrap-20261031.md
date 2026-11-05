<!-- redact: public copy; source sha256 3d8168a2c666195d0ec36408470f128d2da8d8dde95e1e5040c0f6d7426c3c15; rules 8; mode record; words 0; sessions 0 whole, 0 truncated; host paths 1; decisions 0 -->
# Sessions repository bootstrap

Owner: Desktop Continuity Manager (George Friend). Written 2026-10-31T05:45:04.554Z. Convention: STELA (`Projects/STELA`).

## Purpose
Kevin directed creation of Sessions as a repository. A new Git root now exists in place; a private GitHub repository nooksee/sessions has been created. This is a narrow source bootstrap, with the remaining Control ownership split stated explicitly.

## Structure
docs/ops/specs/runbook/repository.md

## Entry Point
git -C [host path 1] status

## Constraints
Measured checks: 20 ignore cases passed, help self-test 14/14 passed, Bash syntax passed for both binaries. An independent boundary reviewer found 0 material issues in the initial 53-path seed and 4 edits. Python suites were not run locally: the configured-interpreter lookup failed twice on Control lost+found; the new CI runs the existing synthetic suites. A command using a redundant Sessions relative directory also failed harmlessly and was corrected. No tool implementation changed. Protocol deviations: 0; unavailable local Python test gate is reported as untested, not passed.

Private source boundary: no bodies, minds, registry, credentials, editor state, working notes or frozen runtime custody are imported. Body mutations, registry edits, service changes, file moves and permanent deletions: 0 each. Two root instruction/navigation files were edited; exact preimages are in ignored storage/repository-bootstrap-20261031. Parent Control still tracks legacy Sessions paths, and its Process branch and PR remain intact. The source manifest and final Git identifiers are retained in the same storage lane and George handoff. The initial branch is used for the source snapshot and then becomes main; future work uses reviewed branches.

## Canonical Pointer
PoT.md and RoR.md; repository scope and remaining work in docs/ops/specs/runbook/repository.md

Bootstrap measurement update by George Friend at 2026-10-31T05:46:03.581Z: 5 legacy docs remain unchanged in Control and are excluded from this seed. The initial whitespace check found pre-existing whitespace in 2 of those documents; after applying the modern-doc boundary, the staged whitespace check passes without an exception or source-byte cleanup. Final independent workflow and boundary reviews report 0 material findings.

Publication correction by George Friend at 2026-10-31T05:46:42.907Z: GitHub rejected the initial push because the existing OAuth connection lacks workflow scope. No remote branch was created by that attempt. The proposed workflow is retained locally, ignored, and in local tag bootstrap-with-ci-20261031 at 553b637. It is omitted from the published root snapshot. The earlier statement that the new CI runs is therefore superseded: no hosted CI is installed or claimed as passed. No account permission was changed.
