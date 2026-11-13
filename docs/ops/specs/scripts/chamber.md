# Technical Specification: chamber

Script: `Sessions/ops/lib/scripts/chamber.py` (writer: not recorded in the file; port writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident). Tests: `Sessions/tools/test/test_chamber.py`. Spec writer: Claude (Fable 5.1, this session), by the operator's direction of 2026-11-01; not a registered resident. Status: ported on 2026-11-01 from `Scripts/build_codex_vm_loadtest_env.py`, which this tree no longer holds; built as it was, 1 edit(s) listed below; callers outside the room still name the legacy path; reviewer not yet named. Map: `docs/ops/README.md`.

## First Principles Rationale

Ported legacy tool. Its own docstring opens: "Build a local VM load-test chamber for a prepared Codex session sandbox." (the file names no author; attributed to the file). No receipt in `Receipts/` names it (0 of 304), so who asked for it, and when, is not recorded there.

## Mechanics and Sequencing

1. Behavior is the legacy script's, unchanged: `Scripts/build_codex_vm_loadtest_env.py` (sha256 `78e6ab31f6dc7b3fd183ec4ee90d41f1e1e4198e71f818a54a56b18224facb3e`) was copied to `ops/lib/scripts/chamber.py` on 2026-11-01 with 1 edit(s): parents[2] -> parents[4] (1).
2. Command line: `python3 -I -B ops/lib/scripts/chamber.py`. Options as the script declares them:
   - `--sandbox-run`: Prepared Sessions/Lab/Codex-Session-Sandbox/<run> directory.
   - `--stamp`: Stable output directory name. Default: current local timestamp.
   - `--output-root`: Parent output directory. Default: Sessions/Lab/VM-Load-Test.
   - `--disk-size`: Sparse qcow2 disk size to create. Default: 40G.
   - `--dry-run`: Print planned paths and checks without writing files.
   - `--prepare`: Create VM load-test chamber files. Does not launch the VM.
3. Reads and writes: as the docstring states (536 characters; the first paragraph is quoted above and the rest remains in the script). The port added no read and no write.

## Anecdotal Anchor

No receipt names `build_codex_vm_loadtest_env.py`. Its history before this port is in Control's Git history of `Sessions/Scripts/`. The port itself is receipted in `Receipts/port-20261101.md`.

## Integrity Filter Warnings

- Refusal and read-only statements in the docstring: "It does not edit production session files, copy auth material, promote JSONL candidates, or launch Codex."
- Callers outside this room (the rounds timer in Control, Control CI) still name `Scripts/build_codex_vm_loadtest_env.py` until Control repoints them; this room's own documents name `ops/lib/scripts/chamber.py`.
- [PLACEHOLDER: reviewer before this ported copy is relied on (PoT 4.2.2), owner: the Integrator]
