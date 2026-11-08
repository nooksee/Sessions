#!/usr/bin/env python3
"""Custody by day: one batch per writer per day, the same bytes on every root.

A batch is named sessions-<writer>-<date>. It is opened by its first add, takes
items one file at a time, and is closed once, at the writer's closing handoff.
Each root holds the same files and the same append-only MANIFEST; close writes
SHA256SUMS, README.txt and CLOSED, and nothing is added after. verify compares
every root with its own record. Roots are given on the command line and are
never read from a file, so the tool names no host. It reads file bytes only to
copy and hash them; it opens no session content.

Filing authority: PoT 1.1.4 and 1.1.13; custody before render, CONSTRAINTS C02.
Exit codes: 0 done, 1 a mismatch found by verify, 2 refused.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

WRITER = re.compile(r"[a-z0-9][a-z0-9-]{0,47}\Z")
DATE = re.compile(r"20[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])\Z")
BATCH = re.compile(r"sessions-[a-z0-9][a-z0-9-]{0,47}-20[0-9]{6}\Z")
ITEM = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
RESERVED = {"MANIFEST", "SHA256SUMS", "README.txt", "CLOSED"}
SYS = Path("/sys")


class Refused(Exception):
    pass


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def direct_sha(path: Path) -> str:
    done = subprocess.run(
        ["dd", f"if={path}", "bs=1M", "iflag=direct,noatime", "status=none"],
        capture_output=True, check=False,
    )
    if done.returncode:
        raise Refused(f"direct read failed: {path}")
    return hashlib.sha256(done.stdout).hexdigest()


def batch_name(writer: str, date: str) -> str:
    if not WRITER.fullmatch(writer):
        raise Refused(f"writer key is not a plain key: {writer!r}")
    if not DATE.fullmatch(date):
        raise Refused(f"date is not YYYYMMDD: {date!r}")
    return f"sessions-{writer}-{date}"


def root_device(p: Path) -> int:
    return p.stat().st_dev


def disks(dev: int, sys_root: Path | None = None) -> frozenset[str]:
    """The physical disks under a device number, read from sysfs.

    A partition resolves to its parent disk; a stacked device (dm, LVM, md)
    to the disks under its slaves. A device with no block entry, such as
    tmpfs, overlay, FUSE or a btrfs subvolume, cannot be placed on a disk,
    so it is refused.
    """
    root = SYS if sys_root is None else sys_root
    major, minor = os.major(dev), os.minor(dev)
    entry = root / "dev" / "block" / f"{major}:{minor}"
    if major == 0 or not entry.exists():
        raise Refused(f"device {major}:{minor} has no disk this tool can name")
    return _disks_of(entry.resolve(), root, 0)


def _disks_of(node: Path, root: Path, depth: int) -> frozenset[str]:
    if depth > 8:
        raise Refused(f"device stack too deep at {node.name}")
    if (node / "partition").exists():
        node = node.parent
    slaves = node / "slaves"
    names = sorted(os.listdir(slaves)) if slaves.is_dir() else []
    if not names:
        return frozenset({node.name})
    out: set[str] = set()
    for name in names:
        out |= _disks_of((slaves / name).resolve(), root, depth + 1)
    return frozenset(out)


def check_roots(roots: list[str], same_device_ok: bool) -> list[Path]:
    if len(roots) < 2:
        raise Refused("at least two roots are required")
    paths = []
    for raw in roots:
        p = Path(raw)
        if not p.is_absolute() or ".." in p.parts:
            raise Refused(f"root is not a plain absolute path: {raw}")
        if p.is_symlink() or not p.is_dir():
            raise Refused(f"root is not a directory: {raw}")
        paths.append(p)
    if len({str(p) for p in paths}) != len(paths):
        raise Refused("a root is named twice")
    if same_device_ok:
        return paths
    devices = [root_device(p) for p in paths]
    if len(set(devices)) != len(devices):
        raise Refused("two roots share a device, so they are one copy, not two")
    seen: dict[str, Path] = {}
    for p, dev in zip(paths, devices):
        for disk in sorted(disks(dev)):
            if disk in seen:
                raise Refused(f"roots {seen[disk]} and {p} share the disk {disk}, so they are one copy, not two")
            seen[disk] = p
    return paths


def direct_set(direct: list[str] | None, roots: list[Path]) -> set[str]:
    resolved = {str(r.resolve()) for r in roots}
    out = set()
    for raw in direct or []:
        r = str(Path(raw).resolve())
        if r not in resolved:
            raise Refused(f"--direct names no --root: {raw}")
        out.add(r)
    return out


def state(batch: Path) -> str:
    if not os.path.lexists(batch):
        return "absent"
    if batch.is_symlink() or not batch.is_dir():
        raise Refused(f"batch path is not a directory: {batch}")
    return "closed" if os.path.lexists(batch / "CLOSED") else "open"


def manifest_rows(batch: Path) -> list[str]:
    m = batch / "MANIFEST"
    return m.read_text(encoding="ascii").splitlines() if m.exists() else []


def agree(batches: list[Path]) -> str:
    states = {state(b) for b in batches}
    if len(states) != 1:
        raise Refused(f"roots disagree on the batch's state: {sorted(states)}")
    s = states.pop()
    if s != "absent":
        rows = {tuple(manifest_rows(b)) for b in batches}
        if len(rows) != 1:
            raise Refused("roots hold different manifests")
    return s


def write_private(path: Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="ascii") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())


def cmd_add(a: argparse.Namespace) -> int:
    name = batch_name(a.writer, a.date)
    roots = check_roots(a.root, a.same_device_ok)
    direct = direct_set(a.direct, roots)
    batches = [r / name for r in roots]
    s = agree(batches)
    if s == "closed":
        raise Refused(f"{name} is closed; nothing is added after close")
    have = {row.split("  ")[1] for row in manifest_rows(batches[0])} if s == "open" else set()
    items = []
    for raw in a.files:
        src = Path(raw)
        if src.is_symlink() or not src.is_file():
            raise Refused(f"item is not a regular file: {raw}")
        item = a.as_name if a.as_name else src.name
        if len(a.files) > 1 and a.as_name:
            raise Refused("--as names one file only")
        if not ITEM.fullmatch(item) or item in RESERVED or item in have:
            raise Refused(f"item name refused or already in the batch: {item}")
        have.add(item)
        items.append((src, item, sha(src)))
    for b in batches:
        if s == "absent":
            b.mkdir(mode=0o700)
            os.chmod(b, 0o700)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    for src, item, digest in items:
        placed: list[Path] = []
        try:
            for b in batches:
                tmp = b / f".{item}.part"
                shutil.copyfile(src, tmp)
                os.chmod(tmp, 0o600)
                got = direct_sha(tmp) if str(b.parent.resolve()) in direct else sha(tmp)
                if got != digest:
                    os.unlink(tmp)
                    raise Refused(f"copy of {item} on {b.parent} does not match its source")
                os.replace(tmp, b / item)
                placed.append(b / item)
            if sha(src) != digest:
                raise Refused(f"source {src} changed while it was copied")
        except BaseException:
            for p in placed:
                with contextlib.suppress(OSError):
                    p.unlink()
            for b in batches:
                with contextlib.suppress(OSError):
                    (b / f".{item}.part").unlink()
            raise
        for b in batches:
            m = b / "MANIFEST"
            if not m.exists():
                write_private(m, "")
            with open(m, "a", encoding="ascii") as f:
                f.write(f"{digest}  {item}  {stamp}\n")
                f.flush()
                os.fsync(f.fileno())
        print(f"added {item} {digest[:16]} to {name} on {len(batches)} roots")
    agree(batches)
    return 0


def recorded(batch: Path) -> dict[str, str]:
    source = batch / ("SHA256SUMS" if state(batch) == "closed" else "MANIFEST")
    out = {}
    for row in source.read_text(encoding="ascii").splitlines():
        digest, item = row.split("  ")[:2]
        out[item] = digest
    return out


def check_batch(batch: Path, direct: bool) -> list[str]:
    faults = []
    want = recorded(batch)
    present = {p.name for p in batch.iterdir()} - RESERVED
    for item in sorted(present - set(want)):
        faults.append(f"unlisted {item}")
    for item, digest in sorted(want.items()):
        p = batch / item
        if not p.is_file() or p.is_symlink():
            faults.append(f"missing {item}")
            continue
        if (direct_sha(p) if direct else sha(p)) != digest:
            faults.append(f"mismatch {item}")
    return faults


def cmd_close(a: argparse.Namespace) -> int:
    name = batch_name(a.writer, a.date)
    roots = check_roots(a.root, a.same_device_ok)
    direct = direct_set(a.direct, roots)
    batches = [r / name for r in roots]
    if agree(batches) != "open":
        raise Refused(f"{name} is not open on every root")
    for b in batches:
        faults = check_batch(b, str(b.parent.resolve()) in direct)
        if faults:
            raise Refused(f"{name} on {b.parent} is not whole: {faults[:3]}")
    rows = manifest_rows(batches[0])
    sums = "".join(f"{r.split('  ')[0]}  {r.split('  ')[1]}\n" for r in sorted(rows, key=lambda r: r.split("  ")[1]))
    readme = a.readme.strip() + "\n"
    if not readme.isascii() or len(readme) > 4000:
        raise Refused("README text must be ASCII and under 4,000 characters")
    for b in batches:
        write_private(b / "README.txt", readme)
        write_private(b / "SHA256SUMS", sums)
        write_private(b / "CLOSED", hashlib.sha256(sums.encode()).hexdigest() + "\n")
    print(f"closed {name}: {len(rows)} items on {len(batches)} roots, SHA256SUMS {hashlib.sha256(sums.encode()).hexdigest()[:16]}")
    return 0


def cmd_verify(a: argparse.Namespace) -> int:
    if not BATCH.fullmatch(a.batch):
        raise Refused(f"batch name is not sessions-<writer>-<date>: {a.batch!r}")
    roots = check_roots(a.root, a.same_device_ok)
    direct = direct_set(a.direct, roots)
    batches = [r / a.batch for r in roots]
    s = agree(batches)
    if s == "absent":
        raise Refused(f"{a.batch} is on no root")
    bad = 0
    for b in batches:
        faults = check_batch(b, str(b.parent.resolve()) in direct)
        print(f"{b.parent}: {s}, {len(recorded(b))} items, {'0 faults' if not faults else faults}")
        bad += len(faults)
    return 1 if bad else 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="custody", description="custody by day: one batch per writer per day on every root")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("add", "close", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--root", action="append", required=True, help="a custody root; give each root once")
        p.add_argument("--direct", action="append", help="a root to read back with O_DIRECT, such as a failing medium")
        p.add_argument("--same-device-ok", action="store_true", help="synthetic tests only: allow roots on one device")
        if name in ("add", "close"):
            p.add_argument("--writer", required=True)
            p.add_argument("--date", required=True)
        if name == "add":
            p.add_argument("--as", dest="as_name", help="store the one file under this name")
            p.add_argument("files", nargs="+")
        if name == "close":
            p.add_argument("--readme", required=True, help="what the batch holds and why, ASCII")
        if name == "verify":
            p.add_argument("batch")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    try:
        return {"add": cmd_add, "close": cmd_close, "verify": cmd_verify}[a.cmd](a)
    except Refused as exc:
        print(f"custody refuses: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"custody refuses: {exc.strerror or exc} ({exc.filename})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
