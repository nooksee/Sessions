# Test Registry

Authoritative registry for `Sessions/tools/test/*` executables. Framework: STELA (`Projects/STELA/docs/ops/registry/test.md`). Every test runs on synthetic data in a temporary directory; none reads a real body, registry or mind. Run from the room root with `python3 -I -B`. Updated 2026-10-30.

| ID | Name | File Path | Infra Importance | Tests | Notes |
| --- | --- | --- | --- | --- | --- |
| TEST-01 | Gauge Test | tools/test/test_gauge.py | critical | 21 | Spec: `docs/ops/specs/tools/test/gauge.md`. Tool: `ops/lib/scripts/gauge.py` (`SCRIPT-01`). Proves provider-figure readings for Claude, Codex and Copilot bodies, window authority order, honest states (`before compaction`, `archived body`, `window unknown`, `invalid`, `unknown`), the 16,000,000-byte tail bound, content never printed or stored, and the ledger (one line per resident per run, mode 0600, none with `--no-ledger`). |
| TEST-02 | Mind Test | tools/test/test_mind.py | critical | 30 | Spec: `docs/ops/specs/tools/test/mind.md`. Tool: `ops/lib/scripts/mind.py` (`SCRIPT-03`). Proves writes only with Kevin's words and a registered writer, declared changes equal to the real difference, forged or moved leaves never served, Claudio's section 130 items (B1, B2, C1 to C7, C9 to C11), the screens, budgets and trauma guard, private modes, and minds kept out of Git. |

[PLACEHOLDER: `tools/test/test_closeout.py` and `tools/test/test_rotate.py`, with test specs in `docs/ops/specs/tools/test/`, when those tools are written. Owner: the writer Claude Shannon names for each tool.]
