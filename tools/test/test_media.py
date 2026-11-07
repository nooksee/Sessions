#!/usr/bin/env python3
"""Tests for the two media and tool-output reducers.

Every case here is drawn from a real body measured on 2026-08-28. One case's prose
is invented text of the same shape, because the original held the operator's own
words, which are never published (PoT 1.2.10).
Both tools shipped a defect that day, and both defects were the same shape: the
tool knew one of the provider's two payload layouts and silently did nothing
about the other. `elide.py` reported `0` characters saved on
a `69 MB` session; the first pass of `media.py`
moved `64%` and left `199.8 MB` behind. Neither raised an error. The regression
cases below exist so that a future shape change fails a test instead of quietly
reporting a believable zero.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts"))

from media import Externalizer  # noqa: E402
from elide import output_blocks, OUTPUT_TYPES  # noqa: E402

PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
) * 8


class TestClaudeMediaShapes(unittest.TestCase):
    """A Claude body carries media two ways; both must move."""

    def setUp(self):
        self.tmp = Path(__file__).parent / "_tmp_media"
        self.tmp.mkdir(exist_ok=True)
        self.ex = Externalizer(self.tmp, "custody", "2026-09-08")

    def tearDown(self):
        for f in self.tmp.glob("*"):
            f.unlink()
        self.tmp.rmdir()

    def test_moves_content_block_source_data(self):
        row = {"message": {"content": [
            {"type": "image", "source": {"type": "base64",
                                         "media_type": "image/png",
                                         "data": PNG_B64}}]}}
        self.assertTrue(self.ex.walk(row))
        block = row["message"]["content"][0]
        self.assertEqual(block["type"], "text")
        self.assertIn("media externalized", block["text"])
        self.assertNotIn(PNG_B64, json.dumps(row))

    def test_moves_tool_result_file_base64(self):
        """The shape the first pass missed, worth 199.8 MB on one body."""
        row = {"toolUseResult": {"type": "image", "file": {
            "filePath": "/home/example/Downloads/Septic Plan.pdf",
            "base64": PNG_B64, "originalSize": 1574967}}}
        self.assertTrue(self.ex.walk(row))
        self.assertNotIn(PNG_B64, json.dumps(row))

    def test_tool_result_keeps_operator_metadata(self):
        """Clearing the node destroyed filePath on 17 rows; it must survive."""
        row = {"toolUseResult": {"type": "image", "file": {
            "filePath": "/home/example/Downloads/Soil Evaluation Report.pdf",
            "base64": PNG_B64, "originalSize": 1574967}}}
        self.ex.walk(row)
        f = row["toolUseResult"]["file"]
        self.assertEqual(f["filePath"],
                         "/home/example/Downloads/Soil Evaluation Report.pdf")
        self.assertEqual(f["originalSize"], 1574967)
        self.assertIn("externalized_to", f)

    def test_identical_payloads_collapse_to_one_file(self):
        for _ in range(3):
            self.ex.walk({"message": {"content": [
                {"type": "image", "source": {"media_type": "image/png",
                                             "data": PNG_B64}}]}})
        self.assertEqual(self.ex.written, 1)
        self.assertEqual(self.ex.deduped, 2)

    def test_prose_that_is_not_base64_is_left_alone(self):
        """Row 758 of Joy Anne's body: `data` that held Kevin's own words.

        The prose here is invented text of the same shape: one plain sentence
        that ends in a non-ASCII dash, repeated, which base64 cannot decode.
        """
        prose = "I took a few notes on the garden shed and wanted you to have them \u2014 " * 12
        row = {"message": {"content": [{"source": {"data": prose}}]}}
        self.assertFalse(self.ex.walk(row))
        self.assertEqual(row["message"]["content"][0]["source"]["data"], prose)
        self.assertEqual(self.ex.failed, 1)

    def test_placeholder_carries_the_run_date_not_the_authoring_date(self):
        """The stamp was a string literal until 2026-09-08.

        A second run on the same resident then wrote "media externalized
        2026-08-28" beside a path from the later run -- the placeholder is the
        resident's only record of what happened to her own pictures, and it was
        misdated by eleven days. A tool that stamps the day it was written
        rather than the day it ran tells one small lie and then repeats it
        forever.
        """
        ex = Externalizer(self.tmp, "custody", "2026-12-25")
        row = {"message": {"content": [
            {"type": "image", "source": {"media_type": "image/png", "data": PNG_B64}}]}}
        ex.walk(row)
        text = row["message"]["content"][0]["text"]
        self.assertIn("media externalized 2026-12-25", text)
        self.assertNotIn("2026-08-28", text)

    def test_short_values_are_not_treated_as_media(self):
        row = {"source": {"data": "short"}}
        self.assertFalse(self.ex.walk(row))


class TestCodexOutputShapes(unittest.TestCase):
    """A Codex tool result carries output two ways; both must be elidable."""

    def test_older_string_output(self):
        blocks = output_blocks({"type": "function_call_output", "output": "x" * 500})
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][1], "x" * 500)

    def test_current_block_list_output(self):
        """The shape that made the tool report 0 chars saved on 69 MB."""
        payload = {"type": "custom_tool_call_output",
                   "output": [{"type": "output_text", "text": "y" * 900}]}
        blocks = output_blocks(payload)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][1], "y" * 900)

    def test_both_shapes_are_recognised_types(self):
        self.assertIn("function_call_output", OUTPUT_TYPES)
        self.assertIn("custom_tool_call_output", OUTPUT_TYPES)

    def test_setter_replaces_only_the_text(self):
        payload = {"type": "custom_tool_call_output", "output": [
            {"type": "output_text", "text": "z" * 900},
            {"type": "output_image", "image_url": "data:image/png;base64,AAAA"}]}
        setter, _ = output_blocks(payload)[0]
        setter("[elided]")
        self.assertEqual(payload["output"][0]["text"], "[elided]")
        self.assertEqual(payload["output"][1]["image_url"],
                         "data:image/png;base64,AAAA")

    def test_image_blocks_are_never_offered_for_elision(self):
        """Eliding an image destroys it; externalization owns that lane."""
        payload = {"type": "custom_tool_call_output", "output": [
            {"type": "output_image", "image_url": "data:image/png;base64,AAAA"}]}
        self.assertEqual(output_blocks(payload), [])

    def test_multiple_text_blocks_all_returned(self):
        payload = {"type": "custom_tool_call_output", "output": [
            {"text": "a" * 400}, {"text": "b" * 400}]}
        self.assertEqual(len(output_blocks(payload)), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
