#!/usr/bin/env python3
"""notice: submit an operator-only closeout notice from one exact gauge row.

Generated with ops/bin/template, then implemented by Joe Codex. Standard
library only. Reads bounded stdin and the registry, never a session body.
Writes private suppression state under --state-dir. No resident-context
delivery, provider prompt, hook or timer. Spec: docs/ops/specs/scripts/notice.md.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import math
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOM = Path(__file__).resolve().parents[3]
LIMIT = 65_536
REGISTRY_LIMIT = 1_048_576
KEY = re.compile(r"[a-z][a-z0-9-]{1,63}")
SID = re.compile(r"[A-Za-z0-9-]{8,64}")
STATE_SCHEMA = "notice-state/1"
OUTPUT_SCHEMA = "notice/1"
NOTIFIER_TIMEOUT = 2.0


class Refused(Exception):
    """A bounded reason code, never caller-controlled error text."""


def sibling(name):
    spec = importlib.util.spec_from_file_location("notice_" + name, Path(__file__).with_name(name + ".py"))
    if spec is None or spec.loader is None:
        raise Refused("dependency-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refused("duplicate-json-key")
        result[key] = value
    return result


def bad_constant(_):
    raise Refused("nonfinite-json")


def decode(raw):
    try:
        value = json.loads(raw, object_pairs_hook=unique, parse_constant=bad_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise Refused("invalid-json") from None
    if not isinstance(value, dict):
        raise Refused("json-object-required")
    return value


def stamp(value):
    if (not isinstance(value, str) or len(value) > 40
            or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)", value, re.ASCII)):
        raise Refused("invalid-reading-time")
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise Refused("invalid-reading-time") from None
    if result.tzinfo is None:
        raise Refused("unzoned-reading-time")
    return result


def private_node(path, directory=False):
    node = path.lstat()
    kind = stat.S_ISDIR(node.st_mode) if directory else stat.S_ISREG(node.st_mode)
    if (not kind or node.st_uid != os.geteuid()
            or stat.S_IMODE(node.st_mode) != (0o700 if directory else 0o600)
            or (not directory and node.st_nlink != 1)):
        raise Refused("unsafe-private-node")
    return node


def read_private(path, limit):
    expected = private_node(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        observed = os.fstat(handle.fileno())
        if (observed.st_dev, observed.st_ino) != (expected.st_dev, expected.st_ino):
            raise Refused("private-node-replaced")
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise Refused("oversized-private-file")
    return decode(raw)


def measurement(raw, registry, key):
    if len(raw) > LIMIT:
        raise Refused("oversized-gauge-row")
    row = decode(raw)
    gauge, closeout = sibling("gauge"), sibling("closeout")
    if row.get("schema") != gauge.SCHEMA:
        raise Refused("unsupported-gauge-schema")
    identities = read_private(registry, REGISTRY_LIMIT).get("identities")
    if not isinstance(identities, list) or not identities:
        raise Refused("invalid-registry")
    keys, bindings, selected = set(), set(), None
    for item in identities:
        if not isinstance(item, dict):
            raise Refused("invalid-registry-row")
        k, provider, session = (item.get(f) for f in ("key", "provider", "session_id"))
        if (not isinstance(k, str) or not KEY.fullmatch(k)
                or provider not in ("codex", "claude", "copilot")
                or not isinstance(session, str) or not SID.fullmatch(session)):
            raise Refused("invalid-registry-identity")
        if k in keys or (provider, session) in bindings:
            raise Refused("ambiguous-registry")
        keys.add(k)
        bindings.add((provider, session))
        if k == key:
            selected = item
    if selected is None or any(row.get(f) != selected.get(f) for f in ("key", "provider", "session_id")):
        raise Refused("identity-mismatch")
    if row.get("state") != "last observed" or row.get("body") != "live":
        raise Refused("measurement-not-current-body")
    try:
        band = closeout.pressure_band(row.get("tokens"), row.get("window"))
    except closeout.Unknown:
        raise Refused("unknown-pressure") from None
    reading, measured = stamp(row.get("reading_at")), stamp(row.get("measured_at"))
    age = row.get("age_seconds")
    if (type(age) is not int or age < 0 or (measured - reading).total_seconds() < 0
            or abs((measured - reading).total_seconds() - age) >= 1):
        raise Refused("invalid-reading-age")
    percent = row.get("percent")
    expected = round(100.0 * row["tokens"] / row["window"], 1)
    if (isinstance(percent, bool) or not isinstance(percent, (int, float))
            or not math.isfinite(percent) or percent != expected):
        raise Refused("inconsistent-percent")
    provenance = row.get("window_source")
    if not isinstance(provenance, str) or not provenance.strip() or len(provenance) > 4096:
        raise Refused("unknown-window-source")
    identity = json.dumps([key, row["provider"], row["session_id"]], separators=(",", ":"))
    binding = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return row, band, binding


def parent_chain(path):
    """Read-only preflight; hostile same-user replacement is outside scope."""
    for parent in reversed((path, *path.parents)):
        try:
            node = parent.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISDIR(node.st_mode):
            raise Refused("unsafe-state-parent")


class Store:
    def __init__(self, directory, key):
        if ".." in directory.parts:
            raise Refused("unsafe-state-parent")
        self.directory = Path(os.path.abspath(directory))
        self.key = key
        self.path = self.directory / (key + ".json")
        self.lock = self.directory / (key + ".lock")

    def inspect(self):
        parent_chain(self.directory)
        if not os.path.lexists(self.directory):
            return None
        private_node(self.directory, True)
        for entry in self.directory.iterdir():
            if not re.fullmatch(r"[a-z][a-z0-9-]{1,63}\.(json|lock)", entry.name):
                raise Refused("unrecognized-state-residue")
            private_node(entry)
        if not os.path.lexists(self.path):
            return None
        state = read_private(self.path, LIMIT)
        if (set(state) != {"schema", "key", "binding", "band", "reading_at"}
                or state["schema"] != STATE_SCHEMA or state["key"] != self.key
                or not isinstance(state["binding"], str)
                or not re.fullmatch("[0-9a-f]{64}", state["binding"])
                or (state["band"] is not None and (type(state["band"]) is not int or state["band"] < 0))):
            raise Refused("corrupt-notice-state")
        stamp(state["reading_at"])
        return state

    @contextlib.contextmanager
    def locked(self):
        self.inspect()
        missing, parent = [], self.directory
        while not parent.exists():
            missing.append(parent)
            parent = parent.parent
        for node in reversed(missing):
            node.mkdir(mode=0o700)
        private_node(self.directory, True)
        fd = os.open(self.lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            expected, observed = private_node(self.lock), os.fstat(fd)
            if (expected.st_dev, expected.st_ino) != (observed.st_dev, observed.st_ino):
                raise Refused("lock-identity-changed")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Refused("notice-state-busy") from None
            yield self.inspect()
        finally:
            os.close(fd)

    def write(self, binding, band, reading_at):
        state = {"schema": STATE_SCHEMA, "key": self.key, "binding": binding,
                 "band": band, "reading_at": reading_at}
        raw = (json.dumps(state, sort_keys=True) + "\n").encode("utf-8")
        fd, name = tempfile.mkstemp(prefix=".notice-", dir=self.directory)
        pending = Path(name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(pending, self.path)
            directory_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if pending.exists():
                pending.unlink()  # Only this invocation's exclusively created temporary.


def output(key, status, submitted=False, **values):
    result = {"schema": OUTPUT_SCHEMA, "key": key, "mode": "operator-only", "status": status,
              "submitted": submitted, "displayed": "unproved", "resident_context_delivered": False}
    result.update(values)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notice", description=__doc__.split("\n")[0])
    parser.add_argument("--key", required=True)
    parser.add_argument("--registry", type=Path, default=ROOM / "ops/etc/resident-identities.json")
    parser.add_argument("--state-dir", type=Path, default=ROOM / "logs/notices")
    parser.add_argument("--notifier", type=Path, default=Path("/usr/bin/notify-send"))
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv=None, stream=None) -> int:
    args = build_parser().parse_args(argv)
    submitted = False
    safe_key = args.key if KEY.fullmatch(args.key) else None
    try:
        if safe_key is None:
            raise Refused("invalid-key")
        if not args.notifier.is_absolute():
            raise Refused("notifier-must-be-absolute")
        source = sys.stdin.buffer if stream is None else stream
        row, band, binding = measurement(source.read(LIMIT + 1), args.registry, safe_key)
        store = Store(args.state_dir, safe_key)
        prior = store.inspect()

        def decide(prior):
            if prior is not None and prior["binding"] == binding:
                if stamp(row["reading_at"]) < stamp(prior["reading_at"]):
                    raise Refused("out-of-order-reading")
                if band is not None and prior["band"] is not None and band <= prior["band"]:
                    return "suppressed"
            return "below-trigger" if band is None else "due"

        status = decide(prior)
        info = {"band": band, "percent": row["percent"], "reading_at": row["reading_at"],
                "age_seconds": row["age_seconds"], "measurement": "last observed"}
        if args.dry_run:
            result = output(safe_key, "dry-run", would=status, **info)
        else:
            with store.locked() as prior:
                status = decide(prior)
                if status == "due":
                    body = (f"Resident {safe_key}: last observed {row['percent']:.1f} percent at "
                            f"{row['reading_at']} (age at measurement {row['age_seconds']} s). "
                            "Closeout is due. Operator notice only; resident context is not delivered.")
                    try:
                        process = subprocess.run([str(args.notifier), "--app-name=Sessions", "--",
                                                  "Resident closeout", body], stdin=subprocess.DEVNULL,
                                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                                 timeout=NOTIFIER_TIMEOUT, check=False)
                    except subprocess.TimeoutExpired:
                        raise Refused("notifier-timeout") from None
                    except OSError:
                        raise Refused("notifier-unavailable") from None
                    if process.returncode != 0:
                        raise Refused("notifier-failed")
                    submitted, status = True, "submitted"
                store.write(binding, band if status != "suppressed" else prior["band"], row["reading_at"])
            result = output(safe_key, status, submitted=submitted, **info)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Refused as exc:
        result = output(safe_key, "unknown", submitted=submitted, reason=str(exc))
    except (OSError, ValueError, TypeError, OverflowError, RecursionError):
        result = output(safe_key, "unknown", submitted=submitted, reason="input-or-state-failure")
    print(json.dumps(result, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
