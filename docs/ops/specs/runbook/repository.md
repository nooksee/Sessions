<!-- redact: public copy; source sha256 c66379c28d4fd08ca1fa35a968324bf6bad9cbb48982b00f2c70ca43cfe2cbe1; rules 8; mode history; words 1; sessions 0 whole, 0 truncated; host paths 3; decisions 0 -->
# Sessions repository

Kevin directed "[words sha256=e3c709e933b49ba138e26c6ee4788cbd3f446c8a8c0ddeb235ae305353ef38cf]" on 2026-10-31. George Friend owns this Git bootstrap. The repository root is [host path 1]; it is kept at the same filesystem path so existing room, launcher and runtime references continue to resolve. The GitHub home is private, nooksee/sessions.

## Versioned boundary

The first source snapshot contains the root canon and instructions, modern ops/, tools/ and docs/, the two existing constitutional snapshots and the bootstrap receipt. A root allowlist makes unclassified lanes ignored. Minds at MIND.md and archives/MIND-* are excluded, along with private bodies, working-storage payload, Candidates, Lab, generated Evidence, installed environments and editor state. W2a later admitted only storage/.gitignore, storage/README.md and the direct lane .gitkeep files; it did not admit case payload or handoffs. The current registry remains at its existing local path under Control ownership and is not duplicated into this Git history. A clone alone does not supply host custody or the live registry and is not an activated continuity installation.

## Control transition

This establishes Sessions Git and does not complete removal of Sessions paths from Control. Control currently tracks 1,084 Sessions paths. Some bootstrap paths overlap that legacy index; the bootstrap snapshot does not grant two independent writers authority over a shared file. George owns the present bootstrap and the Session Continuity Manager retains the existing room assignments outside its exact edits.

The parent has one active Process branch/PR #117 at f462451c8ec7ebcf2cf4ab7797a53606392558ff. It is preserved. Full separation requires its normal disposition and a separate Control branch/PR that reconciles the parent index and pointers, CI ownership and the frozen Resident Center custody contract. In particular, Control CI still runs Sessions/Scripts/tests, and the drift checker binds Sessions/Config/resident-center-relationship.json to accepted Control history. Removing every Sessions path from Control now would break those contracts.

This bootstrap changes neither the ratified PoT nor the pending amendments. Root README is rendered from the existing readme template; AGENTS' former shared-repository paragraph is corrected under Kevin's new direction. Existing Control history preserves their prior versions; immediate preimages are in ignored storage/repository-bootstrap-20261031/.

## Git lifecycle

The initial snapshot is committed on agent/repository-bootstrap-2026-10-31 and then established as main. The private remote receives that exact snapshot only after the allowlist and staged-file checks pass. Future changes use one assigned writer and a bounded agent branch with review before integration. This bootstrap grants no resident admission, body mutation, hook activation or production deployment.

## Recovery

Prior Sessions source history remains in Control; it is not rewritten or imported wholesale. Ignored and untracked host material stays in place. The local .git is new metadata. If this repository setup must be reversed, preserve its commits and the bootstrap receipt first, remove only the new Git boundary under an authorized rollback, and restore README and AGENTS from their recorded preimages after checking that no later writer changed them. Remote deletion requires its own named authority.

## Hosted checks

The current GitHub connection cannot upload workflow files. The proposed .github/workflows/sessions-gates.yml stays local and ignored, and the unpublished initial candidate is preserved by local tag bootstrap-with-ci-20261031. No hosted CI is installed by this bootstrap. Local Bash syntax, help self-test and privacy-boundary checks are recorded in the receipt. Enabling CI later needs a connection already authorized for workflow writes; this task changes no account permission.

## Current boundary after Block 7 - 2026-11-03

The bootstrap and transition sections above describe their original state.
The Block 7 landing moved the frozen `Scripts/`, `Config/` and
`Resident-Center/` runtime roots to `[host path 2]`.
Product source authority remains
`[host path 3]`. The canonical private
registry, roster and host-binding inputs remain under `Sessions/ops/etc/`;
they are not duplicated into Git.

At 2026-11-03 00:48 EST, local `main` was at
`714c588aa137c39a26bf4c431e9eb386a29e498f`, five commits ahead of private
`origin/main` at `bfbc83b7c1eb173d752edb21a01ec123e5ed13c2`. PRs #16 and #19
were still open. The accepted local join therefore remained unpublished to
hosted `main`; this readback does not claim a hosted merge, CI result or
remote synchronization.
