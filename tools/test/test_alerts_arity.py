#!/usr/bin/env python3
"""Regression tests for two clinic instruments that failed silently.

Both defects on 2026-09-08 were the same shape: an instrument that kept
reporting confidently after the thing it measured changed underneath it.
Neither raised an error, and that is what made them expensive.

1. `alerts.py` matched the Claude table with a fixed-arity pattern.
   A `cmp` column was added on 2026-08-05, after which group(1) bound `cmp`
   instead of the verdict. Every Claude verdict recorded thereafter was a string
   like "2/5", which is not in SEVERITY, so the diff skipped the row. The Claude
   ward could not raise a new or worsened flag for 34 days while a resident sat
   at CRITICAL.

2. `vitals.py` counted only one of the two media shapes a
   Claude body uses. It reported 100.6 MB where 170.1 MB was present -- blind to
   40.8 percent of the load. The same second shape had already been found and
   fixed in the externalizer eleven days earlier, so the tool that removes media
   could see more than the tool that looks for it.

The tests below add a column and add a shape, which are the two ways these
instruments have actually broken.
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), ROOT / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


diff = load("alerts.py")
health = load("vitals.py")


class ClaudeRowArityTests(unittest.TestCase):
    """The alert parser must key on the verdict, never on a column position."""

    HEADER = "     size   rows  imgMB  imgs     cmp  carry  verdict                     room / session"

    def test_parses_the_current_table(self):
        row = "     32MB  21138    0.0     0     2/5   1.2%  CRITICAL                    Personal / a124e1c3"
        got = diff.parse_claude(self.HEADER + "\n" + row)
        self.assertEqual(list(got.values()), ["CRITICAL"])

    def test_the_2026_08_05_regression_would_now_be_caught(self):
        """Before the fix this bound `cmp` and recorded the verdict as '2/5'."""
        row = "     32MB  21138    0.0     0     2/5   1.2%  CRITICAL                    Personal / a124e1c3"
        got = diff.parse_claude(row)
        for verdict in got.values():
            self.assertIn(verdict, diff.SEVERITY,
                          "a parsed verdict must be a real verdict, not another column")

    def test_survives_a_new_column_being_inserted(self):
        """The next column addition must not silence the ward again."""
        row = ("     32MB  21138    0.0     0     2/5   1.2%   9.9  CRITICAL"
               "                    Personal / a124e1c3")
        got = diff.parse_claude(row)
        self.assertEqual(list(got.values()), ["CRITICAL"])

    def test_every_verdict_in_the_vocabulary_parses(self):
        for verdict in diff.SEVERITY:
            row = f"      8MB   3354    0.0     0     0/1      -  {verdict}    Personal / 0000abc1"
            got = diff.parse_claude(row)
            self.assertEqual(list(got.values()), [verdict], f"failed on {verdict}")

    def test_a_row_with_no_real_verdict_does_not_match(self):
        """Failing loudly beats binding the wrong field quietly."""
        row = "     32MB  21138    0.0     0     2/5   1.2%  not-a-verdict   Personal / a124e1c3"
        self.assertEqual(diff.parse_claude(row), {})

    def test_label_is_captured_whole(self):
        row = "      0MB    237    0.0     0     0/0      -  healthy   Projects-STELA / 0000abc2"
        got = diff.parse_claude(row)
        self.assertEqual(list(got), ["claude:Projects-STELA / 0000abc2"])


class MediaShapeTests(unittest.TestCase):
    """The health checker must see both media shapes, as the externalizer does."""

    def test_counts_the_content_block_shape(self):
        acc = [0, 0]
        health.scan_images(
            {"message": {"content": [
                {"type": "image", "source": {"data": "A" * 400}}]}}, acc)
        self.assertEqual(acc, [1, 400])

    def test_counts_the_tool_result_shape(self):
        """The shape worth 69.5 MB on one resident that was never counted."""
        acc = [0, 0]
        health.scan_images(
            {"toolUseResult": {"type": "image", "file": {
                "filePath": "/home/nos4r2/Downloads/Septic Plan.pdf",
                "base64": "B" * 900, "originalSize": 1574967}}}, acc)
        self.assertEqual(acc, [1, 900])

    def test_counts_both_shapes_in_one_body(self):
        acc = [0, 0]
        health.scan_images(
            {"a": {"type": "image", "source": {"data": "A" * 100}},
             "b": {"file": {"base64": "B" * 200}}}, acc)
        self.assertEqual(acc, [2, 300])

    def test_an_externalized_placeholder_is_not_counted_as_media(self):
        """After treatment the payload is replaced by prose; it is not an image."""
        acc = [0, 0]
        health.scan_images(
            {"file": {"base64": "[media externalized 2026-09-08: image/png, 441,555 bytes, "
                                "preserved at hard_vol2/.../media/abc.png]"}}, acc)
        self.assertEqual(acc, [0, 0], "a placeholder must not be measured as media")

    def test_nested_and_listed_payloads_are_reached(self):
        acc = [0, 0]
        health.scan_images(
            [{"x": [{"file": {"base64": "C" * 500}}]}], acc)
        self.assertEqual(acc, [1, 500])


if __name__ == "__main__":
    unittest.main()
