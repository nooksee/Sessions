#!/usr/bin/env python3
"""Regression tests for the same-machine Codex rotation builder."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts" / "rotation.py"
SPEC = importlib.util.spec_from_file_location("build_codex_rotation", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def message(role: str, text: str, *, image: bool = False) -> dict:
    content = [{"type": "input_text", "text": text}]
    if image:
        content.append(
            {
                "type": "input_image",
                "image_url": "data:image/png;base64,not-real-image-data",
                "detail": "auto",
            }
        )
    return {
        "timestamp": "2026-08-08T12:00:00Z",
        "type": "response_item",
        "payload": {"type": "message", "role": role, "content": content},
    }


class RotationWindowTests(unittest.TestCase):
    def test_replacement_history_is_not_replayed(self) -> None:
        rows = [
            message("user", "old physical row"),
            {
                "timestamp": "2026-08-08T12:01:00Z",
                "type": "compacted",
                "payload": {
                    "window_number": 3,
                    "replacement_history": [
                        {"type": "message", "role": "user", "content": [
                            {"type": "input_text", "text": "retained but not replayable"},
                            {"type": "input_image", "image_url": "data:image/png;base64,large"},
                        ]},
                        {"type": "compaction", "encrypted_content": "sealed"},
                    ],
                },
            },
            message("user", "current question", image=True),
            message("assistant", "current answer"),
        ]

        window, counts = MODULE.donor_active_window(rows)
        blob = json.dumps(window)

        self.assertEqual(2, len(window))
        self.assertIn("current question", blob)
        self.assertIn("current answer", blob)
        self.assertNotIn("old physical row", blob)
        self.assertNotIn("retained but not replayable", blob)
        self.assertNotIn("encrypted_content", blob)
        self.assertNotIn("data:image", blob)
        self.assertIn(MODULE.IMAGE_MARKER, blob)
        self.assertEqual(1, counts["images_elided"])

    def test_synthetic_capsule_does_not_cut_the_window(self) -> None:
        rows = [
            message("user", "before synthetic capsule"),
            {"timestamp": "2026-08-08T12:01:00Z", "type": "compacted",
             "payload": {"message": "lineage", "replacement_history": []}},
            message("assistant", "after synthetic capsule"),
        ]
        window, _ = MODULE.donor_active_window(rows)
        blob = json.dumps(window)
        self.assertEqual(2, len(window))
        self.assertIn("before synthetic capsule", blob)
        self.assertIn("after synthetic capsule", blob)

    def test_injected_context_is_dropped(self) -> None:
        rows = [
            message("user", "<environment_context>stale host facts</environment_context>"),
            message("user", "operator dialogue"),
        ]
        window, counts = MODULE.donor_active_window(rows)
        self.assertEqual(1, len(window))
        self.assertEqual(1, counts["injected_context"])
        self.assertIn("operator dialogue", json.dumps(window))


class StructuralReidTests(unittest.TestCase):
    def test_only_structural_identifiers_change(self) -> None:
        donor = "000006fe-0000-4000-8000-0000000006fe"
        target = "000087f8-0000-4000-8000-0000000087f8"
        rows = [{
            "id": donor,
            "session_id": donor,
            "payload": {"thread_id": donor, "text": f"quoted {donor}"},
        }]
        changed, count = MODULE.reid(rows, donor, target)
        self.assertEqual(3, count)
        self.assertEqual(target, changed[0]["id"])
        self.assertEqual(target, changed[0]["session_id"])
        self.assertEqual(target, changed[0]["payload"]["thread_id"])
        self.assertEqual(f"quoted {donor}", changed[0]["payload"]["text"])


class CompleteBuildTests(unittest.TestCase):
    def test_build_includes_visible_capsule_and_only_active_dialogue(self) -> None:
        donor_id = "000006fe-0000-4000-8000-0000000006fe"
        target_id = "000087f8-0000-4000-8000-0000000087f8"
        donor = [
            {"timestamp": "2026-08-08T11:00:00Z", "type": "session_meta",
             "payload": {"id": donor_id, "session_id": donor_id}},
            {"timestamp": "2026-08-08T11:01:00Z", "type": "compacted",
             "payload": {"window_number": 1, "replacement_history": [
                 {"type": "message", "role": "user", "content": [
                     {"type": "input_text", "text": "must not return"}
                 ]}
             ]}},
            message("user", "live question"),
            message("assistant", "live answer"),
        ]
        target = [
            {"timestamp": "2026-08-08T12:00:00Z", "type": "session_meta",
             "payload": {"id": target_id, "session_id": target_id}},
            {"timestamp": "2026-08-08T12:00:01Z", "type": "turn_context",
             "payload": {"cwd": "/project"}},
            message("assistant", "fresh target response"),
        ]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            donor_path = root / "donor.jsonl"
            target_path = root / "target.jsonl"
            out_path = root / "out.jsonl"
            MODULE.dump(donor, donor_path)
            MODULE.dump(target, target_path)
            capsule_text = "LINEAGE MEMORY — TEST RESIDENT"
            out_rows, counts, replaced = MODULE.build_rotation(donor, target, capsule_text)
            MODULE.dump(out_rows, out_path)
            built, damaged = MODULE.load(out_path)

        blob = json.dumps(built, ensure_ascii=False)
        self.assertEqual(0, damaged)
        self.assertEqual(2, counts["kept"])
        self.assertEqual(0, replaced)
        self.assertEqual(target[0], built[0])
        self.assertEqual(1, sum(row.get("type") == "compacted" for row in built))
        self.assertEqual(2, blob.count(capsule_text))
        self.assertIn("live question", blob)
        self.assertIn("live answer", blob)
        self.assertIn("fresh target response", blob)
        self.assertNotIn("must not return", blob)


if __name__ == "__main__":
    unittest.main()
