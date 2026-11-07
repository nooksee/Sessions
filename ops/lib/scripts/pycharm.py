#!/usr/bin/env python3
"""Reconcile known PyCharm AI-session surface residue without touching JSONL bodies.

The default mode is read-only. ``--preview-dir`` writes transformed workspace
copies for review. ``--apply`` requires PyCharm to be closed, updates only the
workspace XML presentation layer, and moves retired task-history files into a
caller-selected custody directory.

This tool deliberately does not archive, delete, move, or rewrite Codex or
Claude JSONL files. Codex archive state is handled by the supported Codex CLI.

The IDE chat identifiers are host data and are not kept in this file. They are
read from the chats file, by default ``ops/etc/pycharm-chats.json`` in the room,
or from the path given by ``--chats``. The tool reads that file before anything
else and refuses with one message and a nonzero exit when it is absent or
malformed.

The IDE's folders default to the live settings folder, the highest PyCharm
version present, by the rule ``identity.py`` uses. It refuses when there is none,
or when two folders read as the same version, unless ``--workspace-dir`` and
``--task-history`` are both given. It is never pinned to a version: on 2026-11-06
a pin left ``--apply`` aimed at a folder two versions behind the running IDE.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOM = Path(__file__).resolve().parents[3]
CHATS = ROOM / "ops" / "etc" / "pycharm-chats.json"
CHAT_KEYS = ("george_vi_chat", "temp_osai_chat", "legacy_claude_chat", "shell_only_stubs")
CHAT_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


class ChatsError(ValueError):
    """The chats file is absent, unreadable, or malformed."""


@dataclass(frozen=True)
class Chats:
    george_vi_chat: str
    temp_osai_chat: str
    legacy_claude_chat: str
    shell_only_stubs: tuple[str, ...]

    @property
    def retired_task_ids(self) -> tuple[str, ...]:
        return (*self.shell_only_stubs, self.temp_osai_chat, self.legacy_claude_chat)


def _kind(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "a boolean"
    if isinstance(value, (int, float)):
        return "a number"
    if isinstance(value, str):
        return "a string"
    if isinstance(value, list):
        return "a list"
    return "an object"


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    seen: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise ChatsError(f"repeats the key {key!r}")
        seen[key] = value
    return seen


def load_chats(path: Path) -> Chats:
    """Read and validate the chats file; raise ChatsError naming the one fault."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ChatsError("does not exist") from None
    except UnicodeDecodeError:
        raise ChatsError("is not UTF-8 text") from None
    except OSError as exc:
        raise ChatsError(f"cannot be read ({exc.strerror or type(exc).__name__})") from None
    except ValueError as exc:
        raise ChatsError(f"cannot be read ({exc})") from None
    try:
        data = json.loads(text, object_pairs_hook=_unique_keys)
    except json.JSONDecodeError as exc:
        raise ChatsError(f"is not valid JSON ({exc.msg}, line {exc.lineno} column {exc.colno})") from None
    if not isinstance(data, dict):
        raise ChatsError(f"holds {_kind(data)}, not an object")
    missing = [key for key in CHAT_KEYS if key not in data]
    if missing:
        raise ChatsError(f"lacks the key(s) {', '.join(missing)}")
    extra = sorted(key for key in data if key not in CHAT_KEYS)
    if extra:
        raise ChatsError(f"has the unexpected key(s) {', '.join(repr(key) for key in extra)}")
    places: list[tuple[str, str]] = []
    for key in CHAT_KEYS[:3]:
        if not isinstance(data[key], str):
            raise ChatsError(f"gives {key} as {_kind(data[key])}, not a string")
        places.append((key, data[key]))
    stubs = data["shell_only_stubs"]
    if not isinstance(stubs, list):
        raise ChatsError(f"gives shell_only_stubs as {_kind(stubs)}, not a list of strings")
    for index, value in enumerate(stubs):
        if not isinstance(value, str):
            raise ChatsError(f"gives shell_only_stubs[{index}] as {_kind(value)}, not a string")
        places.append((f"shell_only_stubs[{index}]", value))
    first: dict[str, str] = {}
    for place, value in places:
        if not CHAT_ID.fullmatch(value):
            raise ChatsError(
                f"gives {place} a value that is not a 36-character lowercase hyphenated hex identifier"
            )
        if value in first:
            raise ChatsError(f"repeats one identifier at {first[value]} and {place}")
        first[value] = place
    return Chats(
        george_vi_chat=data["george_vi_chat"],
        temp_osai_chat=data["temp_osai_chat"],
        legacy_claude_chat=data["legacy_claude_chat"],
        shell_only_stubs=tuple(stubs),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-dir", type=Path, help="default: workspace in the live settings folder")
    parser.add_argument("--task-history", type=Path, help="default: aia-task-history in the live settings folder")
    parser.add_argument("--osai-workspace", default="3GTUEvWPa6t9rw2JOmeKUyiqhjR.xml")
    parser.add_argument("--control-workspace", default="3GTVEt3FvS6tW7Eou2gHkcfl6Gk.xml")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preview-dir", type=Path)
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--custody-dir", type=Path)
    parser.add_argument(
        "--chats",
        type=Path,
        default=CHATS,
        help="the chats file of IDE chat identifiers (default: ops/etc/pycharm-chats.json in the room)",
    )
    return parser.parse_args()


def live_root() -> Path:
    """The live settings folder by identity.py's rule, or a refusal. Reads folder names only."""
    spec = importlib.util.spec_from_file_location("pycharm_identity", Path(__file__).with_name("identity.py"))
    if spec is None or spec.loader is None:
        raise SystemExit("pycharm.py refuses: identity.py could not be loaded for the live folder rule. Nothing else was read or written.")
    identity = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(identity)
    newest = identity.newest_pycharm_folders()
    if len(newest) != 1:
        found = "no PyCharm<year>.<n> folder" if not newest else f"{len(newest)} folders of the same version"
        raise SystemExit(
            f"pycharm.py refuses: {found} under ~/.config/JetBrains, so there is no one live folder; "
            "give --workspace-dir and --task-history. Nothing else was read or written."
        )
    return newest[0]


def is_pycharm(exe: str, cmdline: bytes) -> bool:
    """The IDE by its resolved executable, with no version in the rule and no argv substring alone.

    The launcher itself, or the JVM an older launcher starts. An IDE updated in
    place while it runs has an executable that reads as deleted, and it is still
    the IDE. A command line that merely mentions the IDE, as this tool's own does,
    is not.
    """
    name = Path(exe.removesuffix(" (deleted)")).name
    return name in ("pycharm", "pycharm.sh") or (name == "java" and b"com.intellij.idea.main" in cmdline.lower())


def pycharm_processes(proc: Path = Path("/proc")) -> list[int]:
    found: list[int] = []
    own_pid = os.getpid()
    for entry in proc.iterdir():
        if not entry.name.isdigit() or int(entry.name) == own_pid:
            continue
        try:
            cmdline = (entry / "cmdline").read_bytes()
        except OSError:
            continue                                  # the process has gone
        try:
            exe = os.readlink(entry / "exe")
        except OSError:
            if b"pycharm" in cmdline.lower():         # its executable cannot be read, so it cannot be ruled out
                found.append(int(entry.name))
            continue
        if is_pycharm(exe, cmdline):
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
    chats: Chats,
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
        if repair_george_vi and f'<option name="uid" value="{chats.george_vi_chat}"' in block:
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

    map_ids = {*chats.shell_only_stubs, *remove_chat_ids}
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


def inspect_task_history(task_history: Path, chats: Chats) -> dict[str, int]:
    shell_only_files = 0
    retired_full_files = 0
    task_ids_pending = 0
    task_ids_retired = 0
    deviations = 0
    for uid in chats.shell_only_stubs:
        matches = sorted(task_history.glob(f"{uid}.*"))
        expected = [task_history / f"{uid}.agentsession"]
        if matches == expected:
            shell_only_files += 1
            task_ids_pending += 1
        elif not matches:
            task_ids_retired += 1
        else:
            deviations += 1
    for uid in (chats.temp_osai_chat, chats.legacy_claude_chat):
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


def move_task_history(task_history: Path, custody_dir: Path, chats: Chats) -> int:
    destination = custody_dir / "pycharm-task-history"
    destination.mkdir(parents=True, exist_ok=True)
    moved = 0
    for uid in chats.retired_task_ids:
        for source in sorted(task_history.glob(f"{uid}.*")):
            target = destination / source.name
            if target.exists():
                raise FileExistsError(target)
            shutil.move(str(source), target)
            moved += 1
    return moved


def main() -> int:
    args = parse_args()
    try:
        chats = load_chats(args.chats)
    except ChatsError as exc:
        raise SystemExit(
            f"pycharm.py refuses: the chats file {args.chats} {exc}. Nothing else was read or written."
        ) from None
    if args.apply and args.custody_dir is None:
        raise SystemExit("--apply requires --custody-dir")
    if args.workspace_dir is None or args.task_history is None:
        root = live_root()
        args.workspace_dir = args.workspace_dir or root / "workspace"
        args.task_history = args.task_history or root / "aia-task-history"
    if args.apply:
        pids = pycharm_processes()
        if pids:
            raise SystemExit(f"PyCharm must be closed; matching process IDs: {pids}")

    task_report = inspect_task_history(args.task_history, chats)
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
            chats=chats,
            remove_chat_ids={chats.temp_osai_chat, chats.legacy_claude_chat},
            repair_george_vi=path.name == args.osai_workspace,
        )
        totals["workspace_files_scanned"] += 1
        for key, value in report.items():
            totals[key] += value
        if transformed != original:
            changed[path] = transformed
            totals["workspace_files_changed"] += 1

    pending = (
        task_report["task_ids_pending"] == len(chats.retired_task_ids)
        and task_report["task_ids_retired"] == 0
        and totals["removed_chats"] == 2
        and totals["model_repairs"] == 1
        and totals["title_repairs"] == 1
        and totals["george_vi_verified"] == 1
    )
    reconciled = (
        task_report["task_ids_pending"] == 0
        and task_report["task_ids_retired"] == len(chats.retired_task_ids)
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
            args.task_history, args.custody_dir, chats
        )
    else:
        totals["task_history_files_moved"] = 0

    print(json.dumps({**task_report, **totals, "protocol_deviations": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
