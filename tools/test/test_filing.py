#!/usr/bin/env python3
"""Filing regressions: canonical source and synthetic Git-ignore fixtures only.

No session body, registry content, record or mind is read. Fixtures live in
the project's var/tmp and are removed by TemporaryDirectory, not a sweeper.
"""
import ast
import re
import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]


def text(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def filing_contracts():
    """The current law chooses its named contracts; missing files never pass."""
    law = text("PoT.md")
    canon = next(line for line in law.splitlines() if line.startswith("- **1.3.8**"))
    if "ops/lib/manifests/CONSTRAINTS.md" in canon:
        constraints = text("ops/lib/manifests/CONSTRAINTS.md")
        filing = re.search(r"^## C01\n(.*?)(?=^## |\Z)", constraints, re.M | re.S)
        if filing is None:
            raise ValueError("the delegated filing contract is missing C01")
        return law, filing.group(1), text("ops/lib/manifests/CONTEXT.md")
    filing = "\n".join(next(line for line in law.splitlines() if line.startswith(f"- **{number}**"))
                       for number in ("1.1.4", "1.1.13"))
    return law, filing, law


def assigned(relative, name, expression):
    """Compare executable assignments, not a matching comment or docstring."""
    tree = ast.parse(text(relative))
    matches = [node.value for node in tree.body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    return len(matches) == 1 and ast.dump(matches[0]) == ast.dump(ast.parse(expression, mode="eval").body)


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
    def test_resident_packet_form_has_every_required_field(self):
        source = text("ops/src/runbook/agents/agent-input.yaml")
        for field in ("to", "from", "owner", "scope", "authority", "inputs",
                      "rules", "stop_condition", "report"):
            self.assertIn(f"  {field}:", source)
        self.assertNotIn("[PLACEHOLDER]", source)

    def test_storage_is_a_named_owned_case_not_general_scratch(self):
        law, contract, _ = filing_contracts()
        clause = next(line for line in law.splitlines()
                      if line.startswith("- **1.1.4**"))
        self.assertIn("storage/", clause)
        for pattern in (r"(?:one owner|one owner, operation)", r"(?:one operation|operation and closeout)",
                        r"closeout condition", r"(?:not a general scratch|No loose-root dump)"):
            self.assertRegex(contract, pattern)

    def test_scratch_has_owner_closeout_and_recovery_boundary(self):
        law, contract, _ = filing_contracts()
        clause = next(line for line in law.splitlines()
                      if line.startswith("- **1.1.13**"))
        self.assertIn("var/tmp/", clause)
        self.assertRegex(clause, r"not custody")
        self.assertRegex(contract, r"(?:owning role and operation|owned var/tmp scratch)")
        self.assertIn("At closeout", contract)
        self.assertRegex(contract, r"(?:promoted first|promote acceptance/recovery/record material before)")
        self.assertIn("automatic purge", contract)

    def test_filing_authority_paths_match_the_landed_shape(self):
        law, _, context = filing_contracts()
        self.assertIn("- **1.1.6** [Retired]", law)
        self.assertIn("- **1.1.7** [Retired]", law)
        self.assertIn("- **1.1.12** `logs/`", law)
        self.assertIn("ops/etc/resident-identities.json", context)
        self.assertIn("archives/receipts/", context)

    def test_amendment_process_is_not_permanently_waived(self):
        clause = next(line for line in text("PoT.md").splitlines()
                      if re.match(r"^- \*\*7\.3(?:\*\*| Amendment:\*\*)", line))
        self.assertRegex(clause, r"(?:resident proposes in writing|written amendment)")
        self.assertIn("ratif", clause.lower())
        self.assertIn("review", clause.lower())

    def test_declared_contract_cannot_be_missing_or_lack_its_filing_section(self):
        original = filing_contracts.__globals__["text"]
        law = "- **1.3.8** `ops/lib/manifests/CONSTRAINTS.md` is delegated\n"
        for contract in (None, "# Constraints without the declared section\n"):
            def fake(relative):
                if relative == "PoT.md":
                    return law
                if relative.endswith("CONSTRAINTS.md"):
                    if contract is None:
                        raise FileNotFoundError("synthetic missing contract")
                    return contract
                return original(relative)
            with self.subTest(contract=contract), mock.patch.dict(filing_contracts.__globals__, {"text": fake}):
                with self.assertRaises((FileNotFoundError, ValueError)):
                    filing_contracts()

    def test_filing_owner_cannot_be_satisfied_by_an_unrelated_clause(self):
        original = filing_contracts.__globals__["text"]
        sources = {p: original(p) for p in ("PoT.md",)}
        if "ops/lib/manifests/CONSTRAINTS.md" in sources["PoT.md"]:
            sources["ops/lib/manifests/CONSTRAINTS.md"] = original("ops/lib/manifests/CONSTRAINTS.md")
        sources = {p: value.replace("one owner", "missing-owner-proof") for p, value in sources.items()}
        with mock.patch.dict(filing_contracts.__globals__, {"text": lambda p: sources[p] if p in sources else original(p)}):
            with self.assertRaises(AssertionError):
                self.test_storage_is_a_named_owned_case_not_general_scratch()

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

    def test_git_admits_only_storage_skeleton_not_payloads(self):
        with tempfile.TemporaryDirectory(prefix="filing-test-",
                                         dir=ROOT / "var/tmp") as directory:
            fixture = Path(directory)
            (fixture / "storage").mkdir(parents=True)
            shutil.copyfile(ROOT / ".gitignore", fixture / ".gitignore")
            shutil.copyfile(ROOT / "storage/.gitignore",
                            fixture / "storage/.gitignore")
            subprocess.run(["git", "-c", "init.templateDir=", "init", "-q",
                            str(fixture)], check=True, capture_output=True)
            cases = {
                "storage/.gitignore": False,
                "storage/README.md": False,
                "storage/active/.gitkeep": False,
                "storage/intake/.gitkeep": False,
                "storage/handoff/.gitkeep": False,
                "storage/loose.md": True,
                "storage/.gitkeep": True,
                "storage/active/README.md": True,
                "storage/active/case.md": True,
                "storage/active/case/nested.txt": True,
                "storage/active/case/.gitkeep": True,
                "storage/intake/incoming.txt": True,
                "storage/intake/nested/private.jsonl": True,
                "storage/active/.gitignore": True,
                "storage/active/intake/README.md": True,
                "storage/active/intake/.gitignore": True,
                "storage/active/handoff/README.md": True,
                "storage/active/handoff/.gitignore": True,
                "storage/intake/handoff/README.md": True,
                "storage/intake/handoff/.gitignore": True,
                "storage/handoff/jojo.md": True,
                "storage/handoff/nested/.gitkeep": True,
                "storage/handoff/nested/review.md": True,
                "storage-lookalike/payload.txt": True,
                "ops/etc/host-bindings.json": True,
                "MIND.md": True,
            }
            self.assertEqual(len(cases), 26)
            nested_paths = tuple(path for path in cases
                                 if path.count("/") == 3 and
                                 path.endswith(("README.md", ".gitignore")))
            self.assertEqual(len(nested_paths), 6)
            for path in nested_paths:
                nested_file = fixture / path
                nested_file.parent.mkdir(parents=True, exist_ok=True)
                nested_file.write_text("synthetic private payload\n",
                                       encoding="utf-8")
            for path, expected_ignored in cases.items():
                with self.subTest(path=path):
                    result = subprocess.run(["git", "-C", str(fixture),
                                             "check-ignore", "-q", "--", path])
                    self.assertEqual(result.returncode,
                                     0 if expected_ignored else 1)
            status = subprocess.run(
                ["git", "-C", str(fixture), "status", "--porcelain",
                 "--untracked-files=all"], check=True, capture_output=True,
                text=True)
            for path in nested_paths:
                with self.subTest(untracked_path=path):
                    self.assertNotIn(path, status.stdout)

    def test_runtime_defaults_use_logs_and_retain_legacy_cutover_guards(self):
        self.assertTrue(assigned("ops/lib/scripts/gauge.py", "LEDGER",
                                 'SESSIONS / "logs" / "gauges" / "ledger.jsonl"'))
        self.assertTrue(assigned("ops/lib/scripts/mind.py", "LOCK", 'Path("logs") / "mind.lock"'))
        self.assertTrue(assigned("ops/lib/scripts/mind.py", "LEGACY_LOCK", 'Path("storage") / "mind.lock"'))
        self.assertTrue(assigned("ops/lib/scripts/closeout.py", "LEGACY_STATE",
                                 'SESSIONS / "storage" / "closeout"'))
        for path in ("ops/lib/scripts/gauge.py", "ops/lib/scripts/mind.py"):
            self.assertIn("require_absent_legacy", text(path))

    def test_current_instructions_and_map_name_scratch(self):
        canonical_map = text("docs/ops/README.md")
        for relative in ("README.md", "AGENTS.md", "docs/ops/README.md",
                         "docs/MANUAL.md"):
            with self.subTest(document=relative):
                source = text(relative)
                self.assertIn("var/tmp/", source)
                for lane in ("storage/active/", "storage/intake/"):
                    if relative == "AGENTS.md" and lane not in source:
                        self.assertIn("ops/lib/manifests/CONSTRAINTS.md", source)
                        self.assertIn("docs/ops/README.md", source)
                        self.assertIn("## C01", text("ops/lib/manifests/CONSTRAINTS.md"))
                        self.assertIn(lane, canonical_map)
                    else:
                        self.assertIn(lane, source, relative)

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
