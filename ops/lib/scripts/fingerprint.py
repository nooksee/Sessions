#!/usr/bin/env python3
"""Read the private host fingerprint: the volume roots this host's tools run under.

The repository is public, so a host path has no place in tracked code. This reads
the private ``ops/etc/host-fingerprint.json``, which the ignore rule covers, and
refuses with one message and a nonzero exit when the file is absent, unreadable,
not private, or not exactly the expected keys. Nothing else is read or written on a
refusal, and a refusal names the path and the fault and never a value.

No tool reads this yet. A later slice of the programme moves each tool onto it.
"""

from __future__ import annotations

import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

ROOM = Path(__file__).resolve().parents[3]
FILE = ROOM / "ops" / "etc" / "host-fingerprint.json"
SCHEMA = "host-fingerprint/1"
KEYS = {"schema_version", "volume_roots"}
ROOTS = {"working", "archive"}
PLAIN_PATH = re.compile(r"/[A-Za-z0-9._/@+-]*")


class FingerprintError(Exception):
    """The file is absent, unreadable, not private or malformed. Its text names one fault and no value."""


@dataclass(frozen=True)
class Fingerprint:
    working: str
    archive: str


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    if len(set(keys)) != len(keys):
        raise FingerprintError("repeats a key")
    return dict(pairs)


def _root(roots: dict[str, object], name: str) -> str:
    value = roots[name]
    if not isinstance(value, str) or not PLAIN_PATH.fullmatch(value):
        raise FingerprintError(f"has a volume root {name} that is not an absolute path of plain characters")
    if os.path.normpath(value) != value or value == "/":
        raise FingerprintError(f"has a volume root {name} that is not in its plain form")
    return value


def read_fingerprint(path: Path = FILE) -> Fingerprint:
    """The fingerprint, or FingerprintError naming the one fault."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        raise FingerprintError("does not exist") from None
    except OSError as exc:
        raise FingerprintError(f"cannot be opened as a file, not a link ({exc.strerror or type(exc).__name__})") from None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise FingerprintError("is not a regular file")
        if st.st_uid != os.getuid():
            raise FingerprintError("is not owned by this user")
        if stat.S_IMODE(st.st_mode) != 0o600:
            raise FingerprintError("is not private: its mode must be 0600")
        raw = b""
        try:
            while chunk := os.read(fd, 65536):
                raw += chunk
        except OSError as exc:
            raise FingerprintError(f"cannot be read ({exc.strerror or type(exc).__name__})") from None
    finally:
        os.close(fd)
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_keys)
    except UnicodeDecodeError:
        raise FingerprintError("is not UTF-8 text") from None
    except json.JSONDecodeError as exc:
        raise FingerprintError(f"is not valid JSON (line {exc.lineno} column {exc.colno})") from None
    if not isinstance(data, dict):
        raise FingerprintError("does not hold an object")
    if set(data) != KEYS:
        raise FingerprintError(f"must have exactly the keys {', '.join(sorted(KEYS))}")
    if data["schema_version"] != SCHEMA:
        raise FingerprintError(f"is not schema {SCHEMA}")
    roots = data["volume_roots"]
    if not isinstance(roots, dict) or set(roots) != ROOTS:
        raise FingerprintError(f"must have exactly the volume roots {', '.join(sorted(ROOTS))}")
    return Fingerprint(working=_root(roots, "working"), archive=_root(roots, "archive"))


def refuse(tool: str, path: Path, error: FingerprintError) -> SystemExit:
    """The one refusal, for a tool to raise. It exits 1, in the manner of pycharm.py."""
    return SystemExit(f"{tool} refuses: the host fingerprint file {path} {error}. Nothing else was read or written.")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args:
        raise SystemExit("usage: fingerprint.py (it takes no argument, and prints no value)")
    try:
        read_fingerprint(FILE)
    except FingerprintError as exc:
        raise refuse("fingerprint.py", FILE, exc) from None
    print(f"the host fingerprint file {FILE} reads whole")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
