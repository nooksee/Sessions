# Technical Specification: prime

Script: `Sessions/ops/lib/scripts/prime.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_prime.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/build_prime_session_candidate_packet.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Build a prime session candidate packet without copying raw sessions." (the file names no author; attributed to the file). No receipt in `Receipts/` names it (0 of 304), so who asked for it, and when, is not recorded there.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/build_prime_session_candidate_packet.py` (sha256 `171fbea738967d266f26e72bc72d4a232c1fd7c05162a8829ec2b04468e70a8f`) was copied to `ops/lib/scripts/prime.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1). One change since, W8's second slice of 2026-11-07: the live-USB marker names the tool's own `ROOT`, not a literal. It reads no private file.
2. Command line: `python3 -I -B ops/lib/scripts/prime.py`. Options as the script declares them:
   - `--profile`: Candidate packet profile to build.
   - `--stamp`: (no help text in the script)
   - `--current-only`: Refresh only current-<profile> packet directories without retaining stamped packet directories.
3. Reads and writes: as the docstring states (68 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

No receipt names `build_prime_session_candidate_packet.py`. Its history before this port is in Control's Git history of `Sessions/Scripts/`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "Build a prime session candidate packet without copying raw sessions."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/build_prime_session_candidate_packet.py` until Control repoints them; this room's own documents name `ops/lib/scripts/prime.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
