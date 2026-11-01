"""Tests for held, registry-only claude and codex residents in identity.py.

Kevin decided on 2026-10-23 that Gordon Bell (codex) and Grace Hopper (claude)
are to be admitted registry-only at first, held from the launcher until the launcher
diagnosis returns. A registry row marks that with "[words sha256=ec9a6e9fe278eb1a471fbab6f40367d8548078b651d9c71581c57c2a6ca379e0]": "[words sha256=c20dea4d876b5b8fb0a1814b43017030cea6d4ac30b2d9ae71b404d2faba49b5]".

Standard library only, because control-gates runs `python3 -m unittest
discover` with nothing installed. Every fixture lives in a temporary folder,
so the tests do not depend on this host's homes, registry or bindings.

Optional review gate: set LIVE to the pre-change script to compare it byte for
byte with the candidate on this host's real registry (skipped otherwise).
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(os.environ.get(
    "CANDIDATE", Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "identity.py"))
LIVE = os.environ.get("LIVE")
GRACE_SID = "00002ba4-0000-4000-8000-000000002ba4"
GORDON_SID = "0000e583-0000-4000-8000-00000000e583"
GRACE_LABEL = "GitHub Reviewer (Grace Hopper)"
GORDON_LABEL = "GitHub Assistant (Gordon Bell)"
HELD_NOTE = "although the registry holds it from the launcher"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mod, *argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with mock.patch("sys.argv", ["identity.py", *argv]), \
            contextlib.redirect_stdout(buf):
        code = mod.main()
    return code, buf.getvalue()


def grace(**over) -> dict:
    row = {"key": "grace-hopper", "role": "GitHub Reviewer", "person": "Grace Hopper",
           "provider": "claude", "session_id": GRACE_SID, "room": "/office",
           "verified": "kevin", "[words sha256=ec9a6e9fe278eb1a471fbab6f40367d8548078b651d9c71581c57c2a6ca379e0]": "[words sha256=c20dea4d876b5b8fb0a1814b43017030cea6d4ac30b2d9ae71b404d2faba49b5]"}
    row.update(over)
    return row


def gordon(**over) -> dict:
    row = {"key": "gordon-bell", "role": "GitHub Assistant", "person": "Gordon Bell",
           "provider": "codex", "session_id": GORDON_SID, "room": "/office",
           "verified": "kevin", "[words sha256=ec9a6e9fe278eb1a471fbab6f40367d8548078b651d9c71581c57c2a6ca379e0]": "[words sha256=c20dea4d876b5b8fb0a1814b43017030cea6d4ac30b2d9ae71b404d2faba49b5]"}
    row.update(over)
    return row


def served() -> dict:
    return {"key": "claude-one", "role": "Lead", "person": "Claude One", "provider": "claude",
            "session_id": "0000849d-0000-4000-8000-00000000849d", "room": "/x",
            "verified": "kevin"}


class House:
    """A hermetic registry, roster and bindings, with bodies and labels faked."""

    def __init__(self, base: Path):
        self.base = base
        self.roster = {"residents": [{"key": "claude-one", "display_name": "Lead (Claude One)"}]}
        self.bindings = {"residents": [{"key": "claude-one",
                                        "session_id": "0000849d-0000-4000-8000-00000000849d"}]}
        self.bodies = {GRACE_SID: "Grace Hopper", GORDON_SID: "Gordon Bell",
                       "0000849d-0000-4000-8000-00000000849d": "Claude One"}
        self.labels = {GRACE_SID: GRACE_LABEL, GORDON_SID: GORDON_LABEL,
                       "0000849d-0000-4000-8000-00000000849d": "Lead (Claude One)"}
        self.mod = load(SCRIPT, "cand_held")
        self.mod.REGISTRY = base / "registry.json"
        self.mod.ROSTER = base / "roster.json"
        self.mod.BINDINGS = base / "bindings.json"

    def body(self, ident: dict):
        name = self.bodies.get(ident["session_id"])
        return (name, "test body") if name else (None, "container missing")

    def run(self, *rows, argv=()) -> tuple[int, str]:
        (self.base / "registry.json").write_text(json.dumps({"identities": list(rows)}))
        (self.base / "roster.json").write_text(json.dumps(self.roster))
        (self.base / "bindings.json").write_text(json.dumps(self.bindings))
        return self.rerun(argv=argv)

    def rerun(self, argv=()) -> tuple[int, str]:
        """Run the checker again on the fixture files as they now stand."""
        with mock.patch.object(self.mod, "body_identity", side_effect=self.body), \
                mock.patch.object(self.mod, "pycharm_titles", return_value=dict(self.labels)), \
                mock.patch.object(self.mod, "copilot_body", side_effect=AssertionError), \
                mock.patch.object(self.mod, "agent_dock_title", side_effect=AssertionError):
            return run(self.mod, *argv)


class HeldTest(unittest.TestCase):
    def house(self) -> House:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return House(Path(tmp.name))


class HeldIsClean(HeldTest):
    def test_held_claude_absent_from_launcher_is_clean(self):
        h = self.house()
        code, out = h.run(served(), grace())
        self.assertNotIn("MISMATCH", out)
        self.assertNotIn("absent from", out)
        self.assertIn(f"  ok  grace-hopper               {GRACE_LABEL}   [held from launcher]\n", out)
        self.assertIn("identities: 2   mismatches: 0   unverified: 0   incomplete: 0   "
                      "PyCharm leg compared: 2/2   held from launcher: 1\n", out)
        self.assertEqual(code, 0)

    def test_held_codex_absent_from_launcher_is_clean(self):
        h = self.house()
        code, out = h.run(served(), gordon())
        self.assertNotIn("MISMATCH", out)
        self.assertIn(f"  ok  gordon-bell                {GORDON_LABEL}   [held from launcher]\n", out)
        self.assertEqual(code, 0)

    def test_both_held_counted(self):
        h = self.house()
        code, out = h.run(served(), grace(), gordon())
        self.assertIn("held from launcher: 2\n", out)
        self.assertEqual(code, 0)

    def test_quiet_prints_no_rows(self):
        h = self.house()
        code, out = h.run(served(), grace(), argv=("--quiet",))
        self.assertNotIn("grace-hopper", out)
        self.assertIn("held from launcher: 1\n", out)
        self.assertEqual(code, 0)


class HeldMismatches(HeldTest):
    def test_held_present_in_launcher(self):
        # Both providers: Claudio's delta review found every lock mismatch test
        # used only the Claude row.
        for make, key, sid, label in ((grace, "grace-hopper", GRACE_SID, GRACE_LABEL),
                                      (gordon, "gordon-bell", GORDON_SID, GORDON_LABEL)):
          for where in ("roster", "bindings"):
            with self.subTest(key=key, where=where):
                h = self.house()
                getattr(h, where)["residents"].append(
                    {"key": key, "display_name": label, "session_id": sid})
                code, out = h.run(served(), make())
                self.assertIn(f"MISMATCH  {key}: present in {where} {HELD_NOTE} (in both "
                              f"roster and bindings the launcher would serve it; in one alone "
                              f"it rejects the whole roster)\n", out)
                self.assertNotIn("before launcher support", out)
                self.assertEqual(code, 1)

    def test_unknown_launcher_value_fails_closed(self):
        for value in ("served", "", None, "Held", " held", 1, True):
            with self.subTest(value=value):
                h = self.house()
                code, out = h.run(served(), grace(launcher=value))
                self.assertIn(f"MISMATCH  grace-hopper: registry launcher value {value!r} "
                              f"is not 'held'", out)
                # Not held, so the ordinary launcher legs apply.
                self.assertIn("MISMATCH  grace-hopper: absent from roster", out)
                self.assertIn("MISMATCH  grace-hopper: absent from bindings", out)
                self.assertNotIn("held from launcher", out)
                self.assertEqual(code, 1)

    def test_held_on_unsupported_provider_fails_closed(self):
        # An unknown provider here; the copilot case is in the copilot tests.
        for provider in ("gemini",):
            for where in (None, "roster", "bindings"):
                with self.subTest(provider=provider, where=where):
                    h = self.house()
                    if where:
                        getattr(h, where)["residents"].append(
                            {"key": "grace-hopper", "display_name": GRACE_LABEL,
                             "session_id": GRACE_SID})
                    code, out = h.run(served(), grace(provider=provider))
                    self.assertIn("MISMATCH  grace-hopper: registry launcher value 'held' "
                                  "applies only to a claude or codex row, not provider "
                                  f"{provider!r}\n", out)
                    if where:
                        self.assertIn(f"MISMATCH  grace-hopper: present in {where} before "
                                      f"launcher support for provider {provider!r} (the "
                                      f"launcher rejects the whole roster)\n", out)
                    self.assertNotIn(HELD_NOTE, out)
                    self.assertNotIn("held from launcher", out)
                    self.assertEqual(code, 1)

    def test_held_session_bound_under_another_key(self):
        for make, key, sid in ((grace, "grace-hopper", GRACE_SID),
                               (gordon, "gordon-bell", GORDON_SID)):
            with self.subTest(key=key):
                h = self.house()
                h.bindings["residents"].append({"key": "an-alias", "session_id": sid})
                code, out = h.run(served(), make())
                self.assertIn(f"MISMATCH  {key}: held session {sid[:13]} is bound under "
                              "launcher key 'an-alias' (with a roster row of that key the "
                              "launcher would serve it; without one it rejects the whole "
                              "roster)\n", out)
                self.assertEqual(code, 1)

    def test_malformed_alias_key_is_reported_not_a_crash(self):
        # Claudio, PR #112 condition 4: a mixed-type bindings key sharing the
        # held session must be reported, not abort the run with a TypeError.
        h = self.house()
        h.bindings["residents"] += [{"key": 7, "session_id": GRACE_SID},
                                    {"key": "zeta", "session_id": GRACE_SID},
                                    {"key": "alpha", "session_id": GRACE_SID}]
        code, out = h.run(served(), grace())
        self.assertIn("identities: 2", out)
        lines = [l for l in out.splitlines() if "is bound under launcher key" in l]
        self.assertEqual([l.split("launcher key ")[1].split(" ")[0] for l in lines],
                         ["'alpha'", "'zeta'", "7"])
        self.assertEqual(code, 1)

    def test_non_string_held_session_is_reported_not_a_crash(self):
        # Claudio, PR #112 condition 4: a non-string held session id, of any
        # type and on either provider, is reported and the run continues. The
        # body and label legs are skipped as uncompared. (An unheld row keeps
        # its older behaviour, which aborts on main as well.)
        for make, key in ((grace, "grace-hopper"), (gordon, "gordon-bell")):
            for sid in (12345, 1.5, True, None, ["x"], {"a": 1}):
                with self.subTest(key=key, sid=sid):
                    h = self.house()
                    h.bindings["residents"].append({"key": "alias", "session_id": sid})
                    code, out = h.run(served(), make(session_id=sid))
                    self.assertIn(f"MISMATCH  {key}: registry session_id {sid!r} is not a "
                                  f"string; its body and label legs are not compared\n", out)
                    self.assertIn("body identity unreadable (session_id is not a string)", out)
                    self.assertIn("PyCharm label NOT compared: session_id is not a string", out)
                    self.assertIn("identities: 2", out)
                    self.assertEqual(code, 1)

    def test_held_body_still_compared(self):
        h = self.house()
        h.bodies[GRACE_SID] = "Claude Shannon"
        code, out = h.run(served(), grace())
        self.assertIn("MISMATCH  grace-hopper: body says 'Claude Shannon'", out)
        self.assertEqual(code, 1)

    def test_held_label_still_compared(self):
        h = self.house()
        h.labels[GRACE_SID] = "Session Continuity Manager (Claude Shannon)"
        code, out = h.run(served(), grace())
        self.assertIn("MISMATCH  grace-hopper: PyCharm label", out)
        self.assertEqual(code, 1)

    def test_held_label_uncompared_is_incomplete_not_mismatch(self):
        # Kevin's decision 4: Grace's label leg is reported "[words sha256=685adafbc232105246930042f8b3fcd88bf04a56ff050a8f634352a7bdf1c930]", a
        # disclosed coverage exception, never a pass and never a mismatch.
        h = self.house()
        del h.labels[GRACE_SID]
        code, out = h.run(served(), grace())
        self.assertIn("mismatches: 0", out)
        self.assertIn("incomplete: 1", out)
        self.assertIn(f"  ?   grace-hopper               {GRACE_LABEL}   [held from launcher]\n"
                      "        PyCharm label not on disk; this leg was NOT compared\n", out)
        self.assertEqual(code, 1)

    def test_held_body_missing_is_incomplete(self):
        h = self.house()
        del h.bodies[GRACE_SID]
        code, out = h.run(served(), grace())
        self.assertIn("body identity unreadable (container missing)", out)
        self.assertIn("mismatches: 0", out)
        self.assertEqual(code, 1)


class RealCodexStore(unittest.TestCase):
    """Claudio's delta review of PR #112: exercise the real Codex body lookup.

    The House harness mocks body_identity, so it cannot see a crash inside it.
    Here the Codex session store holds a real .jsonl file and nothing on the
    body path is mocked; only the PyCharm/ACP label files are emptied.
    """

    def test_non_string_held_session_with_populated_codex_store(self):
        for provider, make, key in (("codex", gordon, "gordon-bell"),
                                    ("claude", grace, "grace-hopper")):
            for sid in (12345, 1.5, True, None, ["x"], {"a": 1}):
                with self.subTest(provider=provider, sid=sid):
                    tmp = tempfile.TemporaryDirectory()
                    self.addCleanup(tmp.cleanup)
                    base = Path(tmp.name)
                    for d in ("claude", "codex/2026/10/24", "copilot", "dock"):
                        (base / d).mkdir(parents=True)
                    (base / "codex/2026/10/24/rollout-2026-10-24T00-00-00-"
                             "00000e4f-0000-4000-8000-000000000e4f.jsonl").write_text(
                        json.dumps({"type": "compacted",
                                    "payload": {"message": "You are `X (Y)`."}}) + "\n")
                    mod = load(SCRIPT, "cand_real_codex")
                    mod.REGISTRY = base / "registry.json"
                    mod.ROSTER = base / "roster.json"
                    mod.BINDINGS = base / "bindings.json"
                    mod.CLAUDE_PROJECTS = base / "claude"
                    mod.CODEX_SESSIONS = base / "codex"
                    mod.COPILOT_SESSIONS = base / "copilot"
                    mod.AGENT_DOCK_PROJECTS = base / "dock"
                    mod.acp_titles = lambda: {}
                    mod.REGISTRY.write_text(json.dumps({"identities": [make(session_id=sid)]}))
                    mod.ROSTER.write_text(json.dumps({"residents": []}))
                    mod.BINDINGS.write_text(json.dumps({"residents": []}))
                    code, out = run(mod)
                    self.assertIn(f"MISMATCH  {key}: registry session_id {sid!r} is not a "
                                  f"string; its body and label legs are not compared\n", out)
                    self.assertIn("identities: 1   mismatches: 1", out)
                    self.assertEqual(code, 1)

    def test_string_held_codex_session_reads_real_body(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        for d in ("claude", "codex/2026/10/24", "copilot", "dock"):
            (base / d).mkdir(parents=True)
        (base / f"codex/2026/10/24/rollout-2026-10-24T00-00-00-{GORDON_SID}.jsonl").write_text(
            json.dumps({"type": "compacted",
                        "payload": {"message": f"You are `{GORDON_LABEL}`, a resident."}}) + "\n")
        mod = load(SCRIPT, "cand_real_codex_ok")
        mod.REGISTRY, mod.ROSTER, mod.BINDINGS = (base / "registry.json", base / "roster.json",
                                                  base / "bindings.json")
        mod.CLAUDE_PROJECTS, mod.CODEX_SESSIONS = base / "claude", base / "codex"
        mod.COPILOT_SESSIONS, mod.AGENT_DOCK_PROJECTS = base / "copilot", base / "dock"
        mod.acp_titles = lambda: {}
        mod.REGISTRY.write_text(json.dumps({"identities": [gordon()]}))
        mod.ROSTER.write_text(json.dumps({"residents": []}))
        mod.BINDINGS.write_text(json.dumps({"residents": []}))
        code, out = run(mod)
        self.assertNotIn("MISMATCH", out)
        self.assertNotIn("body identity unreadable", out)
        self.assertIn("gordon-bell", out)
        self.assertIn("held from launcher: 1", out)


class ExistingRowsUnchanged(HeldTest):
    def test_rows_unchanged_by_inserting_held(self):
        for at in (0, 1):
            with self.subTest(at=at):
                h = self.house()
                _, base = h.run(served())
                rows = [served()]
                rows.insert(at, grace())
                _, out = h.run(*rows)

                def strip(text):
                    return [l for l in text.splitlines()
                            if not l.startswith("identities:") and "grace-hopper" not in l]
                self.assertEqual(strip(out), strip(base))

    def test_no_held_rows_no_summary_suffix(self):
        h = self.house()
        _, out = h.run(served())
        self.assertNotIn("held from launcher", out)

    @unittest.skipUnless(LIVE and Path(LIVE).is_file(), "set LIVE to the pre-change script")
    def test_live_byte_identical(self):
        live, cand = load(Path(LIVE), "live_held"), load(SCRIPT, "cand_held_live")
        cand.REGISTRY, cand.ROSTER, cand.BINDINGS = live.REGISTRY, live.ROSTER, live.BINDINGS
        for argv in ((), ("--quiet",)):
            with self.subTest(argv=argv):
                self.assertEqual(run(live, *argv), run(cand, *argv))


class ReadOnly(HeldTest):
    def test_no_file_changes(self):
        h = self.house()
        h.run(served(), grace(), gordon())

        def snap():
            return {p.name: (p.stat().st_mtime_ns, p.read_bytes()) for p in h.base.iterdir()}
        before = snap()
        for argv in ((), ("--quiet",)):
            h.rerun(argv=argv)
        self.assertEqual(snap(), before)
        self.assertEqual(set(before), {"registry.json", "roster.json", "bindings.json"})


if __name__ == "__main__":
    unittest.main()
