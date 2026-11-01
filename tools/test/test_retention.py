#!/usr/bin/env python3
"""The retention classifier must recognise every rollback scaffold suffix the
house actually writes. On 2026-10-08 nine .PRE-UNSWAP / .PRE-SEAT / .PRE-RESEAT
files from the 2026-08-08 container reversal were found still on the field,
classed active for two months because their names carried a registered id and
the suffix list did not know them."""
from __future__ import annotations
import importlib.util, tempfile, unittest
from pathlib import Path
SPEC = importlib.util.spec_from_file_location("ret", Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "retention.py")
ret = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(ret)
SID = "0000d0d0-0000-4000-8000-00000000d0d0"

class ScaffoldSuffixTests(unittest.TestCase):
    def classify_one(self, name: str) -> str:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / name; p.write_text('{"payload": {}}\n')
            out = ret.classify(Path(d), {SID: "Someone (Codex)"}, {})
            return out[0]["kind"]
    def test_every_house_scaffold_suffix_is_a_scaffold_even_with_a_registered_id(self):
        for suf in (".PRE-ROTATION", ".PRE-ORIENTATION", ".PRE-RESEED", ".PRE-UNSWAP", ".PRE-SEAT", ".PRE-RESEAT", ".bak", ".NEW", ".tmp"):
            self.assertEqual(self.classify_one(f"rollout-2026-08-08T00-01-21-{SID}.jsonl{suf}"), "scaffold", suf)
    def test_a_registered_body_without_a_scaffold_suffix_is_active(self):
        self.assertEqual(self.classify_one(f"rollout-2026-08-08T00-01-21-{SID}.jsonl"), "active")


class LiveHolderGuardTests(unittest.TestCase):
    """A sweep must refuse to move anything a running process holds open.
    On 2026-10-08 the sweep moved three live Claude agent transcripts and a
    workflow journal from under their processes; they were unregistered and
    unbound, so the classifier was right that they were movable later and
    wrong that they were movable then."""
    def test_open_file_under_root_is_reported_with_our_pid(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve(); f = root / "sub" / "live.jsonl"; f.parent.mkdir()
            with f.open("w") as fh:
                fh.write("x\n"); fh.flush()
                held = ret.held_open_under([root])
                self.assertIn(f, held); self.assertIn(os.getpid(), held[f])
            self.assertNotIn(f, ret.held_open_under([root]))
    def test_file_outside_roots_is_ignored(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as other:
            f = Path(other) / "x.jsonl"
            with f.open("w"):
                self.assertNotIn(f.resolve(), ret.held_open_under([Path(d)]))


class LiveClaudeSessionRecordTests(unittest.TestCase):
    """A served or GUI-driven Claude session holds no descriptor on its body;
    its ~/.claude/sessions/<pid>.json record is the truth. Measured 2026-10-08."""
    def test_live_record_marks_its_body_held(self):
        import json, os
        with tempfile.TemporaryDirectory() as d:
            rec = Path(d) / "sessions"; rec.mkdir(); proj = Path(d) / "projects" / "-room"; proj.mkdir(parents=True)
            body = proj / "00008b12-0000-4000-8000-000000008b12.jsonl"; body.write_text("{}\n")
            dead = proj / "00006ea5-0000-4000-8000-000000006ea5.jsonl"; dead.write_text("{}\n")
            (rec / "1.json").write_text(json.dumps({"pid": os.getpid(), "sessionId": body.stem}))
            (rec / "2.json").write_text(json.dumps({"pid": 2**22 - 1, "sessionId": dead.stem}))
            held = ret.live_claude_session_bodies(rec, Path(d) / "projects")
            self.assertIn(body.resolve(), held); self.assertEqual(held[body.resolve()], os.getpid())
            self.assertNotIn(dead.resolve(), held)


if __name__ == "__main__":
    unittest.main()
