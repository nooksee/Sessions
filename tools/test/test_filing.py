#!/usr/bin/env python3
"""Filing regressions: canonical source and synthetic Git-ignore fixtures only.

No session body, registry content, record or mind is read. Fixtures live in
the project's var/tmp and are removed by TemporaryDirectory, not a sweeper.
"""
import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


@contextmanager
def factory_room():
    with tempfile.TemporaryDirectory(prefix="filing-factory-",
                                     dir=ROOT / "var/tmp") as directory:
        room = Path(directory)
        (room / "ops/bin").mkdir(parents=True)
        shutil.copyfile(ROOT / "ops/bin/template", room / "ops/bin/template")
        shutil.copytree(ROOT / "ops/src", room / "ops/src")
        for relative in ("storage/active", "storage/intake", "var/tmp"):
            (room / relative).mkdir(parents=True)
        (room / "storage-alias").symlink_to(room / "storage", target_is_directory=True)
        yield room


def factory(room, *arguments):
    return subprocess.run(["bash", str(room / "ops/bin/template"), *arguments],
                          cwd=room, capture_output=True, text=True)


def packet_slots():
    arguments = ["packet"]
    for name in ("TO", "FROM", "RELAYED_BY", "OWNER", "SCOPE", "AUTHORITY",
                 "SOURCES", "RULES", "STOP_CONDITION", "POST_TO"):
        arguments.extend(("--slot", name + "=synthetic fixture"))
    return arguments


class FilingTest(unittest.TestCase):
    def test_storage_is_a_named_owned_case_not_general_scratch(self):
        clause = next(line for line in text("PoT.md").splitlines()
                      if line.startswith("- **1.1.4**"))
        for expected in ("named active cases", "one owner", "one operation",
                         "closeout condition", "not a general scratch"):
            self.assertIn(expected, clause)

    def test_scratch_has_owner_closeout_and_recovery_boundary(self):
        clause = next(line for line in text("PoT.md").splitlines()
                      if line.startswith("- **1.1.13**"))
        for expected in ("var/tmp/", "owning role and operation", "At closeout",
                         "promoted first", "not custody", "automatic purge"):
            self.assertIn(expected, clause)

    def test_filing_authority_paths_match_the_landed_shape(self):
        law = text("PoT.md")
        self.assertIn("- **1.1.6** [Retired]", law)
        self.assertIn("- **1.1.7** [Retired]", law)
        self.assertIn("- **1.1.12** `logs/`", law)
        self.assertIn("`ops/etc/resident-identities.json`: identity", law)
        self.assertIn("- **1.3.7** `archives/receipts/`", law)

    def test_amendment_process_is_not_permanently_waived(self):
        self.assertIn("- **7.3 Amendment:** a resident proposes in writing.",
                      text("PoT.md"))

    def test_script_factory_supplies_the_new_scratch_default(self):
        source = text("ops/src/scripts/script.py.tpl")
        self.assertIn('SCRATCH = SESSIONS / "var" / "tmp"', source)
        self.assertNotIn("Rebuildable output goes in storage/", source)

    def test_spec_factory_distinguishes_case_and_scratch(self):
        source = text("ops/src/docs/spec.md.tpl")
        self.assertIn("task scratch in `var/tmp/`", source)
        self.assertNotIn("rebuildable output in `storage/`", source)

    def test_packet_factory_names_the_scratch_mechanic(self):
        source = text("ops/src/reports/packet.md.tpl")
        self.assertIn("var/tmp/<owner>-<operation>.XXXXXX", source)
        self.assertIn("grants no cleanup or custody authority", source)

    def test_help_menu_exposes_both_lanes(self):
        result = subprocess.run(["bash", str(ROOT / "ops/bin/help")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("var/tmp/      owner-scoped task scratch", result.stdout)
        self.assertNotIn("empty it and the system still works", result.stdout)

    def test_binary_self_tests_default_to_project_scratch(self):
        for relative in ("ops/bin/help", "ops/bin/template"):
            with self.subTest(binary=relative):
                source = text(relative)
                self.assertIn("${TMPDIR:-${ROOM_ROOT}/var/tmp}", source)
                self.assertNotIn("${TMPDIR:-/tmp}", source)

    def test_git_admits_only_skeleton_not_temporary_payloads(self):
        with tempfile.TemporaryDirectory(prefix="filing-test-",
                                         dir=ROOT / "var/tmp") as directory:
            fixture = Path(directory)
            (fixture / "var/tmp").mkdir(parents=True)
            shutil.copyfile(ROOT / ".gitignore", fixture / ".gitignore")
            shutil.copyfile(ROOT / "var/tmp/.gitignore",
                            fixture / "var/tmp/.gitignore")
            subprocess.run(["git", "-c", "init.templateDir=", "init", "-q",
                            str(fixture)], check=True, capture_output=True)
            cases = {
                "var/README.md": False,
                "var/tmp/.gitignore": False,
                "var/tmp/.gitkeep": False,
                "var/other/output.txt": True,
                "var/tmp/worker-case/result.txt": True,
                "var/tmp/worker-case/nested/result.txt": True,
                "var/tmp/worker-case/.gitkeep": True,
                "var/tmp/worker-case/private.jsonl": True,
                "storage/handoff/example.md": True,
                "ops/etc/host-bindings.json": True,
                "MIND.md": True,
            }
            for path, expected_ignored in cases.items():
                with self.subTest(path=path):
                    result = subprocess.run(["git", "-C", str(fixture),
                                             "check-ignore", "-q", "--", path])
                    self.assertEqual(result.returncode,
                                     0 if expected_ignored else 1)

    def test_existing_operational_state_is_not_rerouted(self):
        self.assertIn('SESSIONS / "storage" / "gauges" / "ledger.jsonl"',
                      text("ops/lib/scripts/gauge.py"))
        self.assertIn('Path("storage") / "mind.lock"',
                      text("ops/lib/scripts/mind.py"))
        self.assertIn('SESSIONS / "storage" / "closeout"',
                      text("ops/lib/scripts/closeout.py"))

    def test_current_instructions_and_map_name_scratch(self):
        for relative in ("README.md", "AGENTS.md", "docs/ops/README.md",
                         "docs/MANUAL.md"):
            with self.subTest(document=relative):
                self.assertIn("var/tmp/", text(relative))
                self.assertTrue("storage/active/" in text(relative), relative)
                self.assertTrue("storage/intake/" in text(relative), relative)

    def test_report_refuses_storage_root_and_its_alias(self):
        for relative in ("storage/report.md", "storage/../storage/report.md",
                         "storage-alias/report.md"):
            with self.subTest(target=relative):
                with factory_room() as room:
                    result = factory(room, *packet_slots(), "--out", relative)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("storage root", result.stderr)
                    self.assertFalse((room / "storage/report.md").exists())

    def test_reports_use_active_or_intake(self):
        with factory_room() as room:
            for lane in ("active", "intake"):
                with self.subTest(lane=lane):
                    target = room / "storage" / lane / "case.md"
                    result = factory(room, *packet_slots(), "--out", str(target))
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue(target.is_file())

    def test_tool_generation_refuses_every_storage_descendant(self):
        for relative in ("storage", "storage/active", "storage/intake",
                         "storage-alias/active"):
            with self.subTest(target=relative):
                with factory_room() as room:
                    result = factory(room, "--root=" + str(room / relative), "sample")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("code under storage", result.stderr)
                    self.assertFalse(list((room / "storage").rglob("sample.py")))

    def test_tool_generation_allows_scratch_and_prefix_lookalike(self):
        with factory_room() as room:
            for relative in ("var/tmp/tool-check", "storage-lookalike"):
                with self.subTest(target=relative):
                    target = room / relative
                    target.mkdir(parents=True)
                    result = factory(room, "--root=" + str(target), "sample")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue((target / "ops/lib/scripts/sample.py").is_file())

        with factory_room() as room:
            target = room / "source-root"
            (target / "ops/lib").mkdir(parents=True)
            (target / "ops/lib/scripts").symlink_to(room / "storage/active",
                                                   target_is_directory=True)
            result = factory(room, "--root=" + str(target), "sample")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("code under storage", result.stderr)
            self.assertFalse((room / "storage/active/sample.py").exists())


if __name__ == "__main__":
    unittest.main()
