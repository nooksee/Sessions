# Technical Specification: identity

Script: `Sessions/ops/lib/scripts/identity.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_identity.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/check_identity_lock.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Verify that every resident's identity agrees in all four places it is written." (the file names no author; attributed to the file). The earliest receipt that names it is `Receipts/claudine-rotation-and-sanchez-retirement-20260805.md` (2026-08-05); 17 receipt(s) name it in all.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/check_identity_lock.py` (sha256 `f1b3c5cf1e67a5ebfc0f3d38a401bbf448f49f15b2d13a98bf38dcdd1d8ce896`) was copied to `ops/lib/scripts/identity.py` on 2026-11-01 with 1 edit(s): parents[1] -> parents[3] (1).
2. Command line: `python3 -I -B ops/lib/scripts/identity.py`. Options as the script declares them:
   - `--quiet`: print only problems
3. Reads and writes: as the docstring states (2716 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

`Receipts/claudine-rotation-and-sanchez-retirement-20260805.md` is the earliest of 17 receipt(s) naming `check_identity_lock.py`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "The launcher roster and host bindings must NOT name them, because the launcher rejects the whole roster when it meets a provider it does not support." "A provider this script does not know is reported as unsupported and incomplete, never scanned as Codex." "Any other value of "launcher" is a mismatch, never ignored, and so is "held" on a Copilot or unknown-provider row or with a session id that is not a string." "Read-only."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/check_identity_lock.py` until Control repoints them; this room's own documents name `ops/lib/scripts/identity.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Session Continuity Manager]

## The label leg's sources

Added 2026-11-06, after the update to PyCharm 2026.3. A Codex chat's label and its thread binding are read only from the newest `PyCharm<year>.<n>` folder under `~/.config/JetBrains`, by version number. An older folder is never read, so a chat that survives only there reports the label as not on disk and the leg as not compared; it does not read `ok`. The newest folder is assumed to be the running version's; a host rolled back to an older build would need a person's reading. A Claude session's label comes from the older title store when it holds one, and otherwise from the last `custom-title` row in its own body, reading that row type and its title only, never message content. The row is a different witness from the IDE's record, so the report names it: such a row carries `[label from the body's title row]`, the summary lists them, and a mismatch says `body title row` (CONSTRAINTS C07). A store and a row that disagree are left uncompared, as are two bodies with different titles, since the older store can hold a name the operator has since changed. Only a Claude row reads a body for its label.
