#!/usr/bin/env python3
"""Tests for field-scoped re-identification in `successor.py`.

Every case here is drawn from a real body measured on 2026-08-10, not invented.
The regression case is Claudio Freeman's, whose carried history was rewritten by
whole-text replacement into a false claim binding one resident's identity
sentence to another resident's identifier.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops" / "lib" / "scripts"))

from successor import count_residue, reid_rows  # noqa: E402

DONOR = "00009fee-0000-4000-8000-000000009fee"
NEW = "0000f2f2-0000-4000-8000-00000000f2f2"


class TestIdentityFields(unittest.TestCase):
    def test_rewrites_top_level_camel_case(self):
        rows = [{"sessionId": DONOR, "type": "user"}]
        self.assertEqual(reid_rows(rows, DONOR, NEW), 1)
        self.assertEqual(rows[0]["sessionId"], NEW)

    def test_rewrites_top_level_snake_case(self):
        """The exact leg an earlier walker missed by assuming it was nested.

        Measured on a real donor: 104 of 741 identity fields were top-level
        `session_id`. A depth assumption would have corrected 0 of them.
        """
        rows = [{"session_id": DONOR, "type": "user"}]
        self.assertEqual(reid_rows(rows, DONOR, NEW), 1)
        self.assertEqual(rows[0]["session_id"], NEW)

    def test_rewrites_both_fields_on_one_row(self):
        rows = [{"sessionId": DONOR, "session_id": DONOR}]
        self.assertEqual(reid_rows(rows, DONOR, NEW), 2)

    def test_rewrites_when_deeply_nested(self):
        rows = [{"message": {"content": [{"input": {"session_id": DONOR}}]}}]
        self.assertEqual(reid_rows(rows, DONOR, NEW), 1)
        self.assertEqual(
            rows[0]["message"]["content"][0]["input"]["session_id"], NEW)

    def test_leaves_a_different_identifier_alone(self):
        other = "0000a3a3-0000-4000-8000-00000000a3a3"
        rows = [{"sessionId": other}]
        self.assertEqual(reid_rows(rows, DONOR, NEW), 0)
        self.assertEqual(rows[0]["sessionId"], other)

    def test_requires_exact_value_not_substring(self):
        rows = [{"sessionId": DONOR + "-suffix"}]
        self.assertEqual(reid_rows(rows, DONOR, NEW), 0)


class TestPreservedEvidence(unittest.TestCase):
    """The three kinds of history that must survive re-identification."""

    def test_conversation_prose_is_untouched(self):
        text = f"I measured my own container and it returned {DONOR}."
        rows = [{"type": "assistant", "message": {"content": text}}]
        self.assertEqual(reid_rows(rows, DONOR, NEW), 0)
        self.assertEqual(rows[0]["message"]["content"], text)

    def test_file_snippet_is_untouched(self):
        """`attachment.snippet` records what a file contained when read."""
        snippet = f'56\t  "person": "Claude Shannon",\n58\t  "session_id": "{DONOR}",'
        rows = [{"attachment": {"snippet": snippet}}]
        self.assertEqual(reid_rows(rows, DONOR, NEW), 0)
        self.assertEqual(rows[0]["attachment"]["snippet"], snippet)

    def test_recorded_command_is_untouched(self):
        """`input.command` records what was actually run."""
        cmd = f"B=/home/nos4r2/.claude/projects/-media/{DONOR}.jsonl"
        rows = [{"message": {"content": [{"input": {"command": cmd}}]}}]
        self.assertEqual(reid_rows(rows, DONOR, NEW), 0)
        self.assertEqual(
            rows[0]["message"]["content"][0]["input"]["command"], cmd)


class TestClaudioFreemanRegression(unittest.TestCase):
    """Whole-text replacement bound one resident's identity to another's id.

    Claudio Freeman's body, row 2, was rewritten to read "I am Claude Shannon,
    Session Continuity Manager, session 61685fad" -- a sentence true of the
    donor with the donor's identifier, and false of Claudio with his.
    """

    def test_identity_sentence_in_prose_is_not_rebound(self):
        sentence = (f"I am **Claude Shannon, Session Continuity Manager**, "
                    f"session `{DONOR}`.")
        rows = [{"sessionId": DONOR,
                 "type": "user",
                 "message": {"content": sentence}}]
        self.assertEqual(reid_rows(rows, DONOR, NEW), 1)
        self.assertEqual(rows[0]["sessionId"], NEW,
                         "the identity field must be rewritten")
        self.assertEqual(rows[0]["message"]["content"], sentence,
                         "the historical sentence must survive verbatim")
        self.assertNotIn(NEW, rows[0]["message"]["content"],
                         "the new identifier must never appear in carried prose")


class TestResidueReporting(unittest.TestCase):
    def test_clean_build_reports_zero_structural(self):
        rows = [{"sessionId": DONOR, "message": {"content": f"ran {DONOR}"}}]
        reid_rows(rows, DONOR, NEW)
        structural, preserved = count_residue(rows, DONOR)
        self.assertEqual(structural, 0)
        self.assertEqual(preserved, 1)

    def test_incomplete_build_is_visible_as_structural(self):
        rows = [{"sessionId": DONOR}]
        structural, preserved = count_residue(rows, DONOR)
        self.assertEqual(structural, 1)
        self.assertEqual(preserved, 0)

    def test_two_numbers_separate_defect_from_history(self):
        """The point of the split: a raw total cannot tell these apart."""
        rows = [{"sessionId": DONOR, "message": {"content": f"saw {DONOR}"}}]
        structural, preserved = count_residue(rows, DONOR)
        self.assertEqual((structural, preserved), (1, 1))
        self.assertNotEqual(structural, structural + preserved)


if __name__ == "__main__":
    unittest.main(verbosity=2)
