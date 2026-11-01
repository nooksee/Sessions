#!/usr/bin/env python3
"""Reconcile known PyCharm AI-session surface residue without touching JSONL bodies.

The default mode is read-only. ``--preview-dir`` writes transformed workspace
copies for review. ``--apply`` requires PyCharm to be closed, updates only the
workspace XML presentation layer, and moves retired task-history files into a
caller-selected custody directory.

This tool deliberately does not archive, delete, move, or rewrite Codex or
Claude JSONL files. Codex archive state is handled by the supported Codex CLI.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path


GEORGE_VI_CHAT = "000098fc-0000-4000-8000-0000000098fc"
TEMP_OSAI_CHAT = "00009b5d-0000-4000-8000-000000009b5d"
LEGACY_CLAUDE_CHAT = "00008dac-0000-4000-8000-000000008dac"

SHELL_ONLY_STUBS = (
    "0000eb8d-0000-4000-8000-00000000eb8d",
    "0000ed3a-0000-4000-8000-00000000ed3a",
    "0000f4ee-0000-4000-8000-00000000f4ee",
    "0000ca56-0000-4000-8000-00000000ca56",
    "00003095-0000-4000-8000-000000003095",
    "0000b860-0000-4000-8000-00000000b860",
    "00001639-0000-4000-8000-000000001639",
    "0000e960-0000-4000-8000-00000000e960",
    "00000c3f-0000-4000-8000-000000000c3f",
    "00004b2f-0000-4000-8000-000000004b2f",
    "00001b23-0000-4000-8000-000000001b23",
    "0000f5e8-0000-4000-8000-00000000f5e8",
    "000028fa-0000-4000-8000-0000000028fa",
    "00004b15-0000-4000-8000-000000004b15",
    "00003566-0000-4000-8000-000000003566",
    "0000fe48-0000-4000-8000-00000000fe48",
    "00008f47-0000-4000-8000-000000008f47",
)

RETIRED_TASK_IDS = (*SHELL_ONLY_STUBS, TEMP_OSAI_CHAT, LEGACY_CLAUDE_CHAT)


def parse_args() -> argparse.Namespace:
    default_root = Path.home() / ".config/JetBrains/PyCharm2026.1"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-dir", type=Path, default=default_root / "workspace")
    parser.add_argument("--task-history", type=Path, default=default_root / "aia-task-history")
    parser.add_argument("--osai-workspace", default="3GTUEvWPa6t9rw2JOmeKUyiqhjR.xml")
    parser.add_argument("--control-workspace", default="3GTVEt3FvS6tW7Eou2gHkcfl6Gk.xml")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preview-dir", type=Path)
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--custody-dir", type=Path)
    return parser.parse_args()


def pycharm_processes() -> list[int]:
    found: list[int] = []
    own_pid = os.getpid()
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == own_pid:
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes().replace(b"\0", b" ").lower()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if b"/opt/pycharm" in cmdline or b"pycharm-2026.1" in cmdline:
            found.append(int(entry.name))
    return sorted(found)


def split_chat_blocks(lines: list[str]) -> list[tuple[int, int, str]]:
    blocks: list[tuple[int, int, str]] = []
    start: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "<SerializedChat>":
            if start is not None:
                raise ValueError("nested SerializedChat block")
            start = index
        elif stripped == "</SerializedChat>" and start is not None:
            blocks.append((start, index + 1, "".join(lines[start : index + 1])))
            start = None
    if start is not None:
        raise ValueError("unterminated SerializedChat block")
    return blocks


def transform_workspace(
    text: str,
    *,
    remove_chat_ids: set[str],
    repair_george_vi: bool,
) -> tuple[str, dict[str, int]]:
    lines = text.splitlines(keepends=True)
    remove_ranges: set[int] = set()
    removed_chats = 0
    model_repairs = 0
    title_repairs = 0
    george_vi_verified = 0

    for start, end, block in split_chat_blocks(lines):
        block_uids = {
            uid for uid in remove_chat_ids if f'<option name="uid" value="{uid}"' in block
        }
        if block_uids:
            remove_ranges.update(range(start, end))
            removed_chats += len(block_uids)
            continue
        if repair_george_vi and f'<option name="uid" value="{GEORGE_VI_CHAT}"' in block:
            old_model = 'value="agent_acp.registry.claude-acp"'
            new_model = 'value="agent_acp.registry.codex-acp"'
            if old_model in block:
                block = block.replace(old_model, new_model, 1)
                model_repairs += 1
            elif new_model not in block:
                raise ValueError("George VI chat has neither Claude nor Codex model assignment")
            old_title = '<option name="text" value="OSAI" />'
            new_title = '<option name="text" value="George VI — OSAI" />'
            if old_title in block:
                block = block.replace(old_title, new_title, 1)
                title_repairs += 1
            elif new_title not in block:
                raise ValueError("George VI chat title is not the expected OSAI title")
            if new_model in block and new_title in block:
                george_vi_verified += 1
            lines[start:end] = block.splitlines(keepends=True)

    map_ids = {*SHELL_ONLY_STUBS, *remove_chat_ids}
    removed_map_entries = 0
    output: list[str] = []
    for index, line in enumerate(lines):
        if index in remove_ranges:
            continue
        if any(f'<entry key="{uid}" ' in line for uid in map_ids):
            removed_map_entries += 1
            continue
        output.append(line)

    return "".join(output), {
        "removed_chats": removed_chats,
        "removed_map_entries": removed_map_entries,
        "model_repairs": model_repairs,
        "title_repairs": title_repairs,
        "george_vi_verified": george_vi_verified,
    }


def inspect_task_history(task_history: Path) -> dict[str, int]:
    shell_only_files = 0
    retired_full_files = 0
    task_ids_pending = 0
    task_ids_retired = 0
    deviations = 0
    for uid in SHELL_ONLY_STUBS:
        matches = sorted(task_history.glob(f"{uid}.*"))
        expected = [task_history / f"{uid}.agentsession"]
        if matches == expected:
            shell_only_files += 1
            task_ids_pending += 1
        elif not matches:
            task_ids_retired += 1
        else:
            deviations += 1
    for uid in (TEMP_OSAI_CHAT, LEGACY_CLAUDE_CHAT):
        matches = sorted(task_history.glob(f"{uid}.*"))
        suffixes = {path.suffix for path in matches}
        if suffixes == {".agentsession", ".events", ".lastid", ".usage"}:
            retired_full_files += len(matches)
            task_ids_pending += 1
        elif not matches:
            task_ids_retired += 1
        else:
            deviations += 1
    return {
        "shell_only_files": shell_only_files,
        "retired_full_files": retired_full_files,
        "task_ids_pending": task_ids_pending,
        "task_ids_retired": task_ids_retired,
        "task_history_deviations": deviations,
    }


def atomic_write(path: Path, text: str) -> None:
    mode = path.stat().st_mode
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    os.chmod(temp_path, mode)
    os.replace(temp_path, path)


def move_task_history(task_history: Path, custody_dir: Path) -> int:
    destination = custody_dir / "pycharm-task-history"
    destination.mkdir(parents=True, exist_ok=True)
    moved = 0
    for uid in RETIRED_TASK_IDS:
        for source in sorted(task_history.glob(f"{uid}.*")):
            target = destination / source.name
            if target.exists():
                raise FileExistsError(target)
            shutil.move(str(source), target)
            moved += 1
    return moved


def main() -> int:
    args = parse_args()
    if args.apply and args.custody_dir is None:
        raise SystemExit("--apply requires --custody-dir")
    if args.apply:
        pids = pycharm_processes()
        if pids:
            raise SystemExit(f"PyCharm must be closed; matching process IDs: {pids}")

    task_report = inspect_task_history(args.task_history)
    if task_report["task_history_deviations"]:
        raise SystemExit(json.dumps(task_report, indent=2))

    changed: dict[Path, str] = {}
    totals = {
        "workspace_files_scanned": 0,
        "workspace_files_changed": 0,
        "removed_chats": 0,
        "removed_map_entries": 0,
        "model_repairs": 0,
        "title_repairs": 0,
        "george_vi_verified": 0,
    }
    for path in sorted(args.workspace_dir.glob("*.xml")):
        original = path.read_text(encoding="utf-8")
        transformed, report = transform_workspace(
            original,
            remove_chat_ids={TEMP_OSAI_CHAT, LEGACY_CLAUDE_CHAT},
            repair_george_vi=path.name == args.osai_workspace,
        )
        totals["workspace_files_scanned"] += 1
        for key, value in report.items():
            totals[key] += value
        if transformed != original:
            changed[path] = transformed
            totals["workspace_files_changed"] += 1

    pending = (
        task_report["task_ids_pending"] == len(RETIRED_TASK_IDS)
        and task_report["task_ids_retired"] == 0
        and totals["removed_chats"] == 2
        and totals["model_repairs"] == 1
        and totals["title_repairs"] == 1
        and totals["george_vi_verified"] == 1
    )
    reconciled = (
        task_report["task_ids_pending"] == 0
        and task_report["task_ids_retired"] == len(RETIRED_TASK_IDS)
        and totals["removed_chats"] == 0
        and totals["removed_map_entries"] == 0
        and totals["model_repairs"] == 0
        and totals["title_repairs"] == 0
        and totals["george_vi_verified"] == 1
        and totals["workspace_files_changed"] == 0
    )
    if not pending and not reconciled:
        raise SystemExit(json.dumps({**task_report, **totals, "protocol_deviations": 1}, indent=2))
    totals["reconciliation_state"] = "pending" if pending else "reconciled"

    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        for source, transformed in changed.items():
            (args.preview_dir / source.name).write_text(transformed, encoding="utf-8")
    elif args.apply and pending:
        for path, transformed in changed.items():
            atomic_write(path, transformed)
        totals["task_history_files_moved"] = move_task_history(
            args.task_history, args.custody_dir
        )
    else:
        totals["task_history_files_moved"] = 0

    print(json.dumps({**task_report, **totals, "protocol_deviations": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
