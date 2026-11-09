#!/usr/bin/env python3
"""Measure one resident's native identity and session health, without writes.

Run this script with no arguments. It identifies the caller only from a
provider-bound native session signal. A working directory is never identity.

The tool rules out only the known identity, coverage, context-pressure,
native-body, compaction-count, and timestamp-cluster failure classes that it
measures. It proves nothing about unknown failure classes and grants repair
authority 0.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import re
import stat
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
LABEL_RE = re.compile(r"You are\s+`([^`]+?)\s*\(([^`()]+)\)`", re.IGNORECASE)
ORIENTATION_TAG = "<session_clinic_orientation>"
IDE_NOTICE_RE = re.compile(r"\s*<(ide_opened_file|ide_selection)>.*?</\1>", re.DOTALL)
IDE_NOTICE_CLOSE_RE = re.compile(r"</(?:ide_opened_file|ide_selection)>")
ORIENTATION_IDENTITY_RE = re.compile(
    r"(?:^|\n)\s*You are\s+(.+?)(?:\.|\n|$)",
    re.IGNORECASE,
)
ROMAN_ROLE_SUFFIX_RE = re.compile(r"\s+[IVXLCDM]+$", re.IGNORECASE)
ROTATION_PERCENT = 70.0
TIMESTAMP_CLUSTER_MINIMUM = 20
EXPECTED_LEGS = 10
AUTO_MEMORY_SWITCH = "CLAUDE_CODE_DISABLE_AUTO_MEMORY"
SWITCH_OFF_VALUES = ("", "0", "false")   # any other value reads as the switch: a wrong finding costs less than a wrong pass
AUTO_MEMORY_KEY = "autoMemoryEnabled"
ROOM_SETTINGS = (".claude/settings.local.json", ".claude/settings.json")   # the room's own scopes, local over project
SETTINGS_LIMIT = 65_536
GAUGE_PATH = Path(__file__).resolve().with_name("gauge.py")
LIMIT_TEXT = (
    "This tool rules out only the known identity, coverage, context-pressure, "
    "native-body, compaction-count, and timestamp-cluster failure classes "
    "that it measures. It proves nothing about unknown failure classes and "
    "grants repair authority 0. Claude token usage is caller-body native; its "
    "model window is the gauge's reviewed table row for the caller's own model, "
    "reported with the row's source and observation date, and is not caller-bound "
    "telemetry."
)


@dataclass(frozen=True)
class CheckPaths:
    registry: Path
    roster: Path
    bindings: Path
    codex_lock_root: Path
    proc_root: Path = Path("/proc")
    window_spec: Path | None = None      # the gauge's reviewed window table; None is the gauge's own SPEC
    room: Path | None = None             # the room whose own settings turn auto memory off; None leaves that leg unknown

    @classmethod
    def live(cls) -> "CheckPaths":
        sessions = Path(__file__).resolve().parents[3]
        return cls(
            registry=sessions / "ops/etc/resident-identities.json",
            roster=sessions / "ops/etc/residents.json",
            bindings=sessions / "ops/etc/host-bindings.json",
            codex_lock_root=Path.home() / ".codex/thread-writer-locks",
            room=sessions,
        )


@dataclass(frozen=True)
class CallerSignal:
    provider: str
    session_id: str
    surface: str


@dataclass
class Leg:
    name: str
    status: str
    detail: str
    surfaces: tuple[str, ...]


@dataclass
class Report:
    legs: list[Leg] = field(default_factory=list)
    duplicates: int = 0
    source_failures: list[str] = field(default_factory=list)

    def add(
        self,
        name: str,
        status: str,
        detail: str,
        *surfaces: str,
    ) -> None:
        if status not in {"pass", "finding", "undetermined"}:
            raise ValueError(f"unsupported leg status: {status}")
        self.legs.append(Leg(name, status, detail, tuple(surfaces)))

    @property
    def unresolved(self) -> int:
        return sum(leg.status == "undetermined" for leg in self.legs)

    @property
    def findings(self) -> int:
        return sum(leg.status == "finding" for leg in self.legs)

    @property
    def exit_code(self) -> int:
        complete = len(self.legs) == EXPECTED_LEGS and self.unresolved == 0
        clean = self.findings == 0 and not self.source_failures
        return 0 if complete and clean else 1


@dataclass(frozen=True)
class BodyIdentityClaim:
    kind: str
    line_number: int
    person: str | None = None
    role: str | None = None
    display: str | None = None


@dataclass
class BodyAnalysis:
    path: Path
    provider: str
    size: int
    rows: int = 0
    parse_errors: int = 0
    native_compactions: int = 0
    message_rows: int = 0
    missing_message_timestamps: int = 0
    timestamp_counts: Counter[str] = field(default_factory=Counter)
    identity_rows_seen: int = 0
    identity_claims: list[BodyIdentityClaim] = field(default_factory=list)
    latest_identity_line: int | None = None
    latest_identity_claim: BodyIdentityClaim | None = None
    native_session_id: str | None = None
    native_cwd: str | None = None
    context_tokens: int | None = None
    context_window: int | None = None
    context_observed_at: str | None = None
    model_id: str | None = None
    context_unavailable_reason: str | None = None


def _surface(path: Path) -> str:
    return str(path.resolve(strict=False))


def _parse_timestamp(value: object) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=dt.timezone.utc)
    return stamp.astimezone(dt.timezone.utc)


def _load_json(path: Path) -> tuple[object | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _environment_signals(environ: Mapping[str, str]) -> tuple[list[CallerSignal], list[str]]:
    signals: list[CallerSignal] = []
    errors: list[str] = []
    mapping = {
        "CODEX_THREAD_ID": "codex",
        "CLAUDE_CODE_SESSION_ID": "claude",
        "CLAUDE_SESSION_ID": "claude",
    }
    for key, provider in mapping.items():
        value = environ.get(key)
        if value is None:
            continue
        if not UUID_RE.fullmatch(value):
            errors.append(f"/proc/self/environ::{key} is not a native UUID")
            continue
        signals.append(
            CallerSignal(provider, value, f"/proc/self/environ::{key}")
        )
    return signals, errors


def _read_proc_tokens(proc_root: Path, pid: int) -> tuple[list[str], str | None]:
    path = proc_root / str(pid) / "cmdline"
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [], f"{_surface(path)}: {type(exc).__name__}: {exc}"
    return [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part], None


def _read_ppid(proc_root: Path, pid: int) -> int | None:
    path = proc_root / str(pid) / "status"
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("PPid:"):
                return int(line.split(":", 1)[1].strip())
    except (OSError, ValueError):
        return None
    return None


def _command_provider(tokens: Sequence[str]) -> str | None:
    if not tokens:
        return None
    launch_tokens = tokens[:2]
    marker = " ".join(Path(token).name.lower() for token in launch_tokens)
    joined = " ".join(token.lower() for token in launch_tokens)
    if "claude" in marker or "/claude" in joined:
        return "claude"
    if "codex" in marker or "/codex" in joined:
        return "codex"
    return None


def _resume_id(tokens: Sequence[str], provider: str) -> str | None:
    if provider == "codex":
        markers = {"resume"}
    else:
        markers = {"--resume", "--session-id", "-r"}
    for index, token in enumerate(tokens):
        if token in markers and index + 1 < len(tokens):
            value = tokens[index + 1]
            if UUID_RE.fullmatch(value):
                return value
        for marker in markers:
            prefix = marker + "="
            if token.startswith(prefix):
                value = token[len(prefix):]
                if UUID_RE.fullmatch(value):
                    return value
    return None


def _ancestry_signals(
    proc_root: Path,
    start_pid: int | None,
    maximum_depth: int = 16,
) -> tuple[
    list[CallerSignal],
    list[str],
    dict[str, list[tuple[int, str]]],
    list[str],
]:
    if start_pid is None:
        return [], [], {}, []
    signals: list[CallerSignal] = []
    errors: list[str] = []
    provider_processes: dict[str, list[tuple[int, str]]] = {}
    inspected_surfaces: list[str] = []
    pid = start_pid
    seen: set[int] = set()
    for _ in range(maximum_depth):
        if pid <= 1 or pid in seen:
            break
        seen.add(pid)
        inspected_surfaces.extend(
            [
                _surface(proc_root / str(pid) / "cmdline"),
                _surface(proc_root / str(pid) / "status"),
            ]
        )
        tokens, error = _read_proc_tokens(proc_root, pid)
        if error is not None:
            errors.append(error)
            break
        provider = _command_provider(tokens)
        if provider is not None:
            surface = _surface(proc_root / str(pid) / "cmdline")
            provider_processes.setdefault(provider, []).append((pid, surface))
            session_id = _resume_id(tokens, provider)
            if session_id is not None:
                signals.append(
                    CallerSignal(
                        provider,
                        session_id,
                        surface,
                    )
                )
        parent = _read_ppid(proc_root, pid)
        if parent is None or parent == pid:
            break
        pid = parent
    return signals, errors, provider_processes, inspected_surfaces


def _codex_writer_lock_evidence(
    lock_root: Path,
    session_id: str,
    proc_root: Path,
    provider_processes: Sequence[tuple[int, str]],
) -> tuple[list[str], str | None]:
    lock_path = (lock_root / f"{session_id}.lock").resolve(strict=False)
    if not lock_path.is_file():
        return [_surface(lock_path)], "exact Codex writer lock is absent"
    for pid, _ in provider_processes:
        fd_root = proc_root / str(pid) / "fd"
        try:
            descriptors = list(fd_root.iterdir())
        except OSError:
            continue
        for descriptor in descriptors:
            try:
                target = os.readlink(descriptor)
            except OSError:
                continue
            if Path(target).resolve(strict=False) == lock_path:
                return [_surface(lock_path), str(descriptor.absolute())], None
    return (
        [_surface(lock_path)],
        "exact Codex writer lock is not held by a caller-ancestor Codex process",
    )


def resolve_caller(
    environ: Mapping[str, str],
    proc_root: Path,
    start_pid: int | None,
    codex_lock_root: Path,
) -> tuple[CallerSignal | None, tuple[str, ...], list[str]]:
    env_signals, env_errors = _environment_signals(environ)
    (
        process_signals,
        process_errors,
        provider_processes,
        inspected_surfaces,
    ) = _ancestry_signals(proc_root, start_pid)
    accepted_environment: list[CallerSignal] = []
    support_surfaces: list[str] = []
    for signal in env_signals:
        processes = provider_processes.get(signal.provider, [])
        if not processes:
            env_errors.append(
                f"{signal.surface} has no matching {signal.provider} process "
                "in the caller ancestry"
            )
            continue
        surfaces = [surface for _, surface in processes]
        if signal.provider == "codex":
            lock_surfaces, lock_error = _codex_writer_lock_evidence(
                codex_lock_root,
                signal.session_id,
                proc_root,
                processes,
            )
            surfaces.extend(lock_surfaces)
            if lock_error is not None:
                env_errors.append(f"{signal.surface}: {lock_error}")
                continue
        else:
            exact_process_ids = {
                item.session_id
                for item in process_signals
                if item.provider == "claude"
            }
            if signal.session_id not in exact_process_ids:
                env_errors.append(
                    f"{signal.surface} has no matching exact Claude session "
                    "identifier in the caller process ancestry"
                )
                continue
        accepted_environment.append(signal)
        support_surfaces.extend(surfaces)
    all_signals = accepted_environment + process_signals
    unique = {(item.provider, item.session_id) for item in all_signals}
    surfaces = tuple(
        dict.fromkeys(
            [item.surface for item in all_signals] + support_surfaces
            + inspected_surfaces
        )
    )
    errors = env_errors + process_errors
    if len(unique) != 1:
        if not unique:
            errors.append("no provider-bound native session signal was found")
        else:
            errors.append(f"caller signals disagree across {len(unique)} native identities")
        return None, surfaces, errors
    provider, session_id = next(iter(unique))
    chosen = CallerSignal(provider, session_id, surfaces[0])
    return chosen, surfaces, errors


def _canonical_label(text: object) -> str | None:
    if not isinstance(text, str):
        return None
    match = LABEL_RE.search(text)
    if match is None:
        return None
    role = " ".join(match.group(1).split())
    person = " ".join(match.group(2).split())
    return f"{role} ({person})"


def _display_claim(text: object, line_number: int) -> BodyIdentityClaim | None:
    display = _canonical_label(text)
    if display is None:
        return None
    match = re.fullmatch(r"(.+?)\s*\(([^()]+)\)", display)
    if match is None:
        return None
    return BodyIdentityClaim(
        kind="lineage capsule",
        line_number=line_number,
        role=" ".join(match.group(1).split()),
        person=" ".join(match.group(2).split()),
        display=display,
    )


def _orientation_text(content: object) -> str | None:
    """The row's text from the orientation tag on, or None when the tag does not begin it.

    A message typed in the GUI while a file is open begins with an IDE notice,
    so leading notices, these two by name, are passed over first. Nothing else
    is: other leading text, another wrapper or a tool result leaves the tag not
    beginning the row. A notice can hold anything the operator selected, this
    tag included, so a notice's own text is never returned, and a row whose
    notices were passed over counts only when no notice's closing tag stands
    after them, since that means the first closing tag was quoted text.
    """
    if not isinstance(content, str):
        return None
    rest, passed = content, False
    notice = IDE_NOTICE_RE.match(rest)
    while notice:
        rest, passed = rest[notice.end():], True
        notice = IDE_NOTICE_RE.match(rest)
    rest = rest.lstrip()
    if not rest.startswith(ORIENTATION_TAG):
        return None
    if passed and IDE_NOTICE_CLOSE_RE.search(rest):
        return None
    return rest


def _orientation_claim(text: object, line_number: int) -> BodyIdentityClaim | None:
    text = _orientation_text(text)
    if text is None:
        return None
    match = ORIENTATION_IDENTITY_RE.search(text)
    if match is None:
        return None
    clauses = [" ".join(part.strip(" `").split()) for part in match.group(1).split(",")]
    clauses = [part for part in clauses if part]
    if not clauses:
        return None
    return BodyIdentityClaim(
        kind="session-clinic orientation",
        line_number=line_number,
        person=clauses[0],
        role=clauses[1] if len(clauses) > 1 else None,
    )


def _normalized(value: str) -> str:
    return " ".join(value.split()).casefold()


def _normalized_role(value: str) -> str:
    return _normalized(ROMAN_ROLE_SUFFIX_RE.sub("", value.strip()))


def _compare_body_identity(
    claim: BodyIdentityClaim,
    expected_role: str,
    expected_person: str,
) -> tuple[str, str]:
    expected_display = f"{expected_role} ({expected_person})"
    if claim.display is not None:
        agreement = _normalized(claim.display) == _normalized(expected_display)
        return (
            ("pass", "canonical display agrees with registry")
            if agreement
            else (
                "finding",
                f"body_identity={claim.display!r}; registry_identity={expected_display!r}",
            )
        )

    if claim.person is None:
        return "undetermined", "orientation contains no parseable person claim"
    person_claim = _normalized(claim.person)
    expected_person_normalized = _normalized(expected_person)
    if person_claim == expected_person_normalized:
        role_note = (
            f"; orientation_role={claim.role!r} is mutable registry-owned context"
            if claim.role
            else ""
        )
        return "pass", f"durable person identity agrees with registry{role_note}"

    expected_first = expected_person_normalized.split()[0]
    if person_claim == expected_first and claim.role is not None:
        if _normalized_role(claim.role) == _normalized_role(expected_role):
            return (
                "pass",
                "provider-name and role identity agree with registry; "
                "the orientation omits the durable surname",
            )
        return (
            "undetermined",
            "orientation gives only a provider-name claim and its role does not "
            "corroborate the registry",
        )
    return (
        "finding",
        f"body_person={claim.person!r}; registry_person={expected_person!r}",
    )


def _record_message_timestamp(analysis: BodyAnalysis, row: dict[str, Any]) -> None:
    analysis.message_rows += 1
    stamp = row.get("timestamp")
    if isinstance(stamp, str) and stamp:
        analysis.timestamp_counts[stamp] += 1
    else:
        analysis.missing_message_timestamps += 1


def _load_gauge():
    """Load the sibling canonical counter reader without invoking its CLI."""
    spec = importlib.util.spec_from_file_location("myself_gauge", GAUGE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError("canonical gauge reader is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _context_from_gauge(analysis: BodyAnalysis) -> BodyAnalysis:
    """Share selection/currentness with gauge; keep identity/metrics independent."""
    try:
        gauge = _load_gauge()
        reader = {"codex": gauge.read_codex, "claude": gauge.read_claude}[analysis.provider]
        reading = reader(analysis.path)
        if reading.get("compaction_after"):
            analysis.context_unavailable_reason = (
                "native usage is before compaction; the next complete native reading is required"
            )
            return analysis
        if "tokens" not in reading:
            analysis.context_unavailable_reason = reading.get("reason") or "no native context reading"
            return analysis
        analysis.context_tokens = reading["tokens"]
        analysis.context_window = reading.get("window")
        analysis.model_id = reading.get("model")
        if analysis.provider == "claude" and (
            not isinstance(analysis.model_id, str) or not analysis.model_id
        ):
            analysis.context_unavailable_reason = "native Claude usage names no verified model"
            return analysis
        stamp = reading.get("reading_at")
        analysis.context_observed_at = stamp if isinstance(stamp, str) else None
        if analysis.context_window and analysis.context_tokens > analysis.context_window:
            analysis.context_unavailable_reason = "native token count exceeds its reported window"
    except Exception as exc:
        analysis.context_unavailable_reason = f"canonical gauge reader unavailable: {type(exc).__name__}"
    return analysis


def analyze_codex_body(path: Path) -> BodyAnalysis:
    analysis = BodyAnalysis(path=path, provider="codex", size=path.stat().st_size)
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                analysis.parse_errors += 1
                continue
            if not isinstance(row, dict):
                analysis.parse_errors += 1
                continue
            analysis.rows += 1
            row_type = row.get("type")
            payload = row.get("payload")
            if line_number == 1 and row_type == "session_meta" and isinstance(payload, dict):
                value = payload.get("id")
                cwd = payload.get("cwd")
                analysis.native_session_id = value if isinstance(value, str) else None
                analysis.native_cwd = cwd if isinstance(cwd, str) else None
            if row_type == "compacted" and isinstance(payload, dict):
                if isinstance(payload.get("window_number"), int):
                    analysis.native_compactions += 1
                claim = _display_claim(payload.get("message"), line_number)
                if claim is not None:
                    analysis.identity_rows_seen += 1
                    analysis.identity_claims.append(claim)
                    analysis.latest_identity_line = line_number
                    analysis.latest_identity_claim = claim
            if row_type == "response_item" and isinstance(payload, dict):
                if payload.get("type") == "message":
                    _record_message_timestamp(analysis, row)
    return _context_from_gauge(analysis)


def analyze_claude_body(path: Path) -> BodyAnalysis:
    analysis = BodyAnalysis(path=path, provider="claude", size=path.stat().st_size)
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                analysis.parse_errors += 1
                continue
            if not isinstance(row, dict):
                analysis.parse_errors += 1
                continue
            analysis.rows += 1
            session_id = row.get("sessionId")
            cwd = row.get("cwd")
            if isinstance(session_id, str):
                analysis.native_session_id = session_id
            if isinstance(cwd, str):
                analysis.native_cwd = cwd
            row_type = row.get("type")
            if row_type in {"user", "assistant"}:
                _record_message_timestamp(analysis, row)
            if row.get("subtype") == "compact_boundary":
                analysis.native_compactions += 1
            if row_type == "user":
                message = row.get("message")
                content = message.get("content") if isinstance(message, dict) else None
                orientation = _orientation_text(content)
                if orientation is not None:
                    analysis.identity_rows_seen += 1
                    analysis.latest_identity_line = line_number
                    claim = _display_claim(orientation, line_number) or _orientation_claim(
                        orientation,
                        line_number,
                    )
                    analysis.latest_identity_claim = claim
                    if claim is not None:
                        analysis.identity_claims.append(claim)
    return _context_from_gauge(analysis)


def _candidate_bodies(
    provider: str,
    session_id: str,
    session_root: Path,
) -> list[Path]:
    if provider == "codex":
        root = (session_root / "sessions").resolve(strict=False)
        pattern = f"*{session_id}*.jsonl"
        raw = root.rglob(pattern) if root.is_dir() else []
    else:
        root = session_root.resolve(strict=False)
        pattern = f"*/{session_id}.jsonl"
        raw = root.glob(pattern) if root.is_dir() else []
    matches: list[Path] = []
    for path in raw:
        try:
            resolved = path.resolve(strict=True)
        except OSError:
            continue
        if not resolved.is_file():
            continue
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        matches.append(resolved)
    return sorted(set(matches))


def _claude_window(analysis: BodyAnalysis, window_spec: Path | None) -> tuple[int | None, str, Path | None]:
    """The window for the caller's own model, from the gauge's reviewed table through gauge.resolve_window.

    Strict unknown when the table cannot be read or has no row for the model. The shared status-line
    record, which whichever session last ran writes, is never consulted: it is passed to resolve_window
    as absent. Returns (window, detail, the table path read)."""
    try:
        gauge = _load_gauge()
        spec = window_spec if window_spec is not None else gauge.SPEC
        table = gauge.window_table(spec)
    except Exception as exc:
        return None, f"the gauge's window table is unavailable: {type(exc).__name__}", window_spec
    if not table:
        return None, "the gauge's reviewed window table is unreadable or has no rows", spec
    reading = {"model": analysis.model_id}
    gauge.resolve_window(reading, table, None)
    if not isinstance(reading.get("window"), int) or reading["window"] <= 0:
        return None, (f"window unknown: {reading.get('window_reason') or 'no reviewed window'}; "
                      "the shared status-line record is not used"), spec
    return reading["window"], (
        f"model={analysis.model_id}; tokens_source=caller-native-body; "
        f"window_source=gauge {reading['window_source']}"
    ), spec


def _identity_rows(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("identities"), list):
        return []
    return [row for row in payload["identities"] if isinstance(row, dict)]


def _resident_rows(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("residents"), list):
        return []
    return [row for row in payload["residents"] if isinstance(row, dict)]


def _resident_collection_is_whole(payload: object) -> bool:
    """True only for a {"residents": [objects]} payload.

    _resident_rows() drops what it cannot read, which is safe when a row must
    be found. For a held resident, absence is the passing state, so a missing,
    non-list or partly unreadable collection must not count as verified absence.
    """
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("residents"), list)
        and all(isinstance(row, dict) for row in payload["residents"])
    )


def _private_mode_discrepancy(path: Path) -> str | None:
    try:
        mode = path.stat().st_mode & 0o777
    except OSError:
        mode = None
    if mode != 0o600:
        return f"private binding mode={oct(mode) if mode is not None else 'unreadable'}"
    return None


def _launch_process(proc_root: Path, start_pid: int | None, session_id: str) -> tuple[int, list[str]] | None:
    """The nearest Claude process in the ancestry whose own arguments name this session."""
    _, _, processes, _ = _ancestry_signals(proc_root, start_pid)
    for pid, _surface_name in processes.get("claude", []):
        tokens, error = _read_proc_tokens(proc_root, pid)
        if error is None and _resume_id(tokens, "claude") == session_id:
            return pid, tokens
    return None


def _settings_values(tokens: Sequence[str]) -> list[str]:
    """Every settings source a launch's own arguments give, up to its own --."""
    values: list[str] = []
    arguments = list(tokens[1:])
    for index, token in enumerate(arguments):
        if token == "--":
            break
        if token == "--settings" and index + 1 < len(arguments):
            values.append(arguments[index + 1])
        elif token.startswith("--settings="):
            values.append(token.split("=", 1)[1])
    return values


def _switch_is_on(proc_root: Path, pid: int) -> bool:
    """Whether the launch's own environment, as the kernel holds it, carries the auto-memory switch. Raises OSError."""
    prefix = f"{AUTO_MEMORY_SWITCH}=".encode()
    for item in (proc_root / str(pid) / "environ").read_bytes().split(b"\0"):
        if item.startswith(prefix):
            return item[len(prefix):].decode("utf-8", "replace").lower() not in SWITCH_OFF_VALUES
    return False


def _auto_memory_setting(source: str) -> tuple[str, Any]:
    """One settings source: a file path, or inline JSON as the provider's --settings also takes it.
    Returns ('set', value), ('unset', None), ('absent', None) or ('broken', None). Never follows a link."""
    if source.lstrip().startswith("{"):
        data = source.encode("utf-8", "replace")
    else:
        try:
            fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return "absent", None
        except OSError:
            return "broken", None
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                return "broken", None
            data = os.read(fd, SETTINGS_LIMIT + 1)
        except OSError:
            return "broken", None
        finally:
            os.close(fd)
    if len(data) > SETTINGS_LIMIT:
        return "broken", None
    try:
        payload = json.loads(data)
    except ValueError:
        return "broken", None
    if not isinstance(payload, dict):
        return "broken", None
    if AUTO_MEMORY_KEY not in payload:
        return "unset", None
    return "set", payload[AUTO_MEMORY_KEY]


def _auto_memory(
    paths: CheckPaths,
    identity: dict[str, Any] | None,
    caller: CallerSignal | None,
    start_pid: int | None,
) -> tuple[str, str, tuple[str, ...]]:
    """Whether this launch runs with the provider's auto memory off, as this room requires: a Claude resident of
    this room wakes from its own mind and handoff, never from a memory the provider shares across the room. Read
    from the launch's own environment and settings arguments, then the room's local and project settings, in the
    provider's order of precedence. It sees what the launch carried, not what the provider then loaded."""
    registry = (_surface(paths.registry),)
    if caller is None or identity is None:
        return "undetermined", "caller identity or its registry row is unavailable", registry
    if caller.provider != "claude":
        return "pass", "not a Claude row: auto memory does not apply", registry
    if paths.room is None:
        return "undetermined", "no room is configured", registry
    row_room = identity.get("room")
    if not isinstance(row_room, str) or not row_room:
        return "undetermined", "the registry row names no room", registry
    if os.path.realpath(row_room) != os.path.realpath(paths.room):
        return "pass", "a row of another room: this room's setting does not apply", registry
    launch = _launch_process(paths.proc_root, start_pid, caller.session_id)
    if launch is None:
        return "undetermined", "no Claude process in the ancestry names this session", registry
    pid, tokens = launch
    room_files = [(paths.room / rel, rel) for rel in ROOM_SETTINGS]
    surfaces = (_surface(paths.proc_root / str(pid) / "cmdline"), _surface(paths.proc_root / str(pid) / "environ"),
                *(_surface(path) for path, _ in room_files))
    try:
        if _switch_is_on(paths.proc_root, pid):
            return "pass", f"auto memory is off by the launch's environment ({AUTO_MEMORY_SWITCH})", surfaces
    except OSError:
        return "undetermined", "the launch's own environment cannot be read", surfaces
    sources = [(value, "a --settings argument of the launch") for value in _settings_values(tokens)]
    sources += [(str(path), rel) for path, rel in room_files]
    for source, label in sources:
        state, value = _auto_memory_setting(source)
        if state == "broken":
            return "undetermined", f"{label} cannot be read as a settings object", surfaces
        if state != "set":
            continue
        if value is False:
            return "pass", f"auto memory is off by {label}", surfaces
        if value is True:
            return "finding", (f"auto memory is on by {label}: every resident of this room would share one "
                               "provider memory"), surfaces
        return "finding", f"{label} sets {AUTO_MEMORY_KEY} to a value that is not true or false", surfaces
    return "finding", (f"nothing turns auto memory off: {ROOM_SETTINGS[1]} needs \"{AUTO_MEMORY_KEY}\": false, "
                       "or the launch loads the provider's shared memory"), surfaces


def run_check(
    paths: CheckPaths,
    *,
    environ: Mapping[str, str],
    start_pid: int | None,
    now: dt.datetime | None = None,
) -> Report:
    report = Report()                    # now is accepted for callers; no leg reads the clock
    caller, signal_surfaces, signal_errors = resolve_caller(
        environ, paths.proc_root, start_pid, paths.codex_lock_root
    )
    if caller is None:
        report.add(
            "caller identity",
            "undetermined",
            "; ".join(signal_errors),
            *(signal_surfaces or ("/proc/self/environ",)),
        )
    elif signal_errors:
        report.source_failures.extend(signal_errors)
        report.add(
            "caller identity",
            "finding",
            f"provider={caller.provider}; native_session={caller.session_id}; "
            + "; ".join(signal_errors),
            *signal_surfaces,
        )
    else:
        report.add(
            "caller identity",
            "pass",
            f"provider={caller.provider}; native_session={caller.session_id}",
            *signal_surfaces,
        )

    registry_payload, registry_error = _load_json(paths.registry)
    roster_payload, roster_error = _load_json(paths.roster)
    bindings_payload, bindings_error = _load_json(paths.bindings)
    for path, error in (
        (paths.registry, registry_error),
        (paths.roster, roster_error),
        (paths.bindings, bindings_error),
    ):
        if error is not None:
            report.source_failures.append(f"{_surface(path)}: {error}")

    identity: dict[str, Any] | None = None
    expected_display: str | None = None
    expected_role: str | None = None
    expected_person: str | None = None
    if caller is None or registry_error is not None:
        report.add(
            "identity registry",
            "undetermined",
            registry_error or "caller identity is unavailable",
            _surface(paths.registry),
        )
    else:
        matches = [
            row
            for row in _identity_rows(registry_payload)
            if row.get("session_id") == caller.session_id
            and row.get("provider") == caller.provider
        ]
        if len(matches) != 1:
            report.duplicates += max(0, len(matches) - 1)
            report.add(
                "identity registry",
                "undetermined",
                f"expected one exact caller row; observed={len(matches)}",
                _surface(paths.registry),
            )
        else:
            identity = matches[0]
            role = identity.get("role")
            person = identity.get("person")
            key = identity.get("key")
            if not all(isinstance(value, str) and value for value in (role, person, key)):
                report.add(
                    "identity registry",
                    "undetermined",
                    "the exact row lacks key, role, or person",
                    _surface(paths.registry),
                )
                identity = None
            else:
                expected_role = role
                expected_person = person
                expected_display = f"{expected_role} ({expected_person})"
                report.add(
                    "identity registry",
                    "pass",
                    f"key={key}; registry_identity={expected_display}",
                    _surface(paths.registry),
                )

    # Registry-only claude or codex resident held from the launcher (the operator,
    # 2026-10-23): absence from roster and bindings is then the correct state.
    # The launcher serves a resident only when both files carry its key, and
    # presence in one alone makes it reject the whole roster.
    held = identity is not None and identity.get("launcher") == "held"
    roster_row: dict[str, Any] | None = None
    if identity is None or roster_error is not None:
        report.add(
            "launcher roster",
            "undetermined",
            roster_error or "registry key is unavailable",
            _surface(paths.roster),
        )
    else:
        rows = [row for row in _resident_rows(roster_payload) if row.get("key") == identity["key"]]
        if "launcher" in identity and not held:
            report.add(
                "launcher roster",
                "finding",
                f"registry launcher value {identity['launcher']!r} is not 'held'",
                _surface(paths.registry),
            )
        elif held and not _resident_collection_is_whole(roster_payload):
            report.add(
                "launcher roster",
                "undetermined",
                "resident collection is missing or malformed, so absence cannot be verified",
                _surface(paths.roster),
            )
        elif held:
            report.add(
                "launcher roster",
                "finding" if rows else "pass",
                "present although the registry holds it from the launcher (in both roster "
                "and bindings the launcher would serve it; in one alone it rejects the "
                "whole roster); "
                f"observed={len(rows)}"
                if rows else "registry-only: held from the launcher and absent as required",
                _surface(paths.roster),
            )
        elif len(rows) != 1:
            report.duplicates += max(0, len(rows) - 1)
            report.add(
                "launcher roster",
                "undetermined",
                f"expected one exact key; observed={len(rows)}",
                _surface(paths.roster),
            )
        else:
            roster_row = rows[0]
            discrepancies = []
            if roster_row.get("display_name") != expected_display:
                discrepancies.append(
                    f"display_name={roster_row.get('display_name')!r}"
                )
            if roster_row.get("provider_id") != caller.provider:
                discrepancies.append(
                    f"provider_id={roster_row.get('provider_id')!r}"
                )
            if roster_row.get("enabled") is not True:
                discrepancies.append(f"enabled={roster_row.get('enabled')!r}")
            report.add(
                "launcher roster",
                "finding" if discrepancies else "pass",
                "; ".join(discrepancies) if discrepancies else "key, label, provider, and enabled state agree",
                _surface(paths.roster),
            )

    binding_row: dict[str, Any] | None = None
    session_root: Path | None = None
    if caller is not None and isinstance(bindings_payload, dict):
        providers = bindings_payload.get("providers")
        provider_config = providers.get(caller.provider) if isinstance(providers, dict) else None
        root_value = provider_config.get("session_root") if isinstance(provider_config, dict) else None
        if isinstance(root_value, str) and root_value:
            session_root = Path(root_value).expanduser()
    if identity is None or bindings_error is not None:
        report.add(
            "host bindings",
            "undetermined",
            bindings_error or "registry key is unavailable",
            _surface(paths.bindings),
        )
    else:
        rows = [
            row
            for row in _resident_rows(bindings_payload)
            if row.get("key") == identity["key"]
        ]
        if held and not _resident_collection_is_whole(bindings_payload):
            report.add(
                "host bindings",
                "undetermined",
                "resident collection is missing or malformed, so absence cannot be verified",
                _surface(paths.bindings),
            )
        elif held:
            # Holding changes which rows may exist, not the file's privacy. A
            # bindings row under another key that carries the held session
            # would be served under that key if the roster has it too, and
            # alone makes the launcher reject the whole roster.
            discrepancies = []
            if rows:
                discrepancies.append(
                    "present although the registry holds it from the launcher (in both roster "
                    "and bindings the launcher would serve it; in one alone it rejects the "
                    "whole roster); "
                f"observed={len(rows)}"
                )
            aliases = sorted(
                str(row.get("key"))
                for row in _resident_rows(bindings_payload)
                if row.get("key") != identity["key"]
                and row.get("session_id") == identity.get("session_id")
            )
            if aliases:
                discrepancies.append(
                    "held session is bound under launcher key " + ", ".join(aliases)
                    + " (with a roster row of that key the launcher would serve it;"
                    " without one it rejects the whole roster)"
                )
            mode_problem = _private_mode_discrepancy(paths.bindings)
            if mode_problem is not None:
                discrepancies.append(mode_problem)
            report.add(
                "host bindings",
                "finding" if discrepancies else "pass",
                "; ".join(discrepancies)
                if discrepancies
                else "registry-only: held from the launcher, absent as required, and mode 0600",
                _surface(paths.bindings),
            )
        elif len(rows) != 1:
            report.duplicates += max(0, len(rows) - 1)
            report.add(
                "host bindings",
                "undetermined",
                f"expected one exact key; observed={len(rows)}",
                _surface(paths.bindings),
            )
        else:
            binding_row = rows[0]
            discrepancies = []
            if binding_row.get("session_id") != caller.session_id:
                discrepancies.append("session_id mismatch")
            if binding_row.get("provider_id") != caller.provider:
                discrepancies.append("provider_id mismatch")
            if binding_row.get("project_root") != identity.get("room"):
                discrepancies.append("project_root does not match registry room")
            mode_problem = _private_mode_discrepancy(paths.bindings)
            if mode_problem is not None:
                discrepancies.append(mode_problem)
            if session_root is None:
                discrepancies.append("provider session_root is unavailable")
            report.add(
                "host bindings",
                "finding" if discrepancies else "pass",
                "; ".join(discrepancies) if discrepancies else "key, provider, session, room, and mode 0600 agree",
                _surface(paths.bindings),
            )

    analysis: BodyAnalysis | None = None
    body_paths: list[Path] = []
    if caller is None or session_root is None:
        report.add(
            "native session body",
            "undetermined",
            "caller identity or provider session root is unavailable",
            _surface(paths.bindings),
        )
    else:
        body_paths = _candidate_bodies(caller.provider, caller.session_id, session_root)
        if len(body_paths) != 1:
            report.duplicates += max(0, len(body_paths) - 1)
            report.add(
                "native session body",
                "undetermined",
                f"expected one exact live native body; observed={len(body_paths)}",
                _surface(session_root),
            )
        else:
            body_path = body_paths[0]
            try:
                analysis = (
                    analyze_codex_body(body_path)
                    if caller.provider == "codex"
                    else analyze_claude_body(body_path)
                )
            except (OSError, UnicodeDecodeError) as exc:
                report.source_failures.append(
                    f"{_surface(body_path)}: {type(exc).__name__}: {exc}"
                )
                report.add(
                    "native session body",
                    "undetermined",
                    f"native body could not be read: {type(exc).__name__}: {exc}",
                    _surface(body_path),
                )
            else:
                discrepancies = []
                comparison_gaps = []
                if analysis.native_session_id != caller.session_id:
                    discrepancies.append("body-native session identifier mismatch")
                expected_root = (
                    binding_row.get("project_root")
                    if binding_row is not None
                    and isinstance(binding_row.get("project_root"), str)
                    else identity.get("room")
                    if held and isinstance(identity.get("room"), str)
                    else None
                )
                if expected_root is None:
                    comparison_gaps.append(
                        "working-directory comparison unavailable because an "
                        "exact binding project_root is unavailable"
                    )
                elif analysis.native_cwd is None:
                    discrepancies.append("body-native working directory is absent")
                elif Path(analysis.native_cwd).resolve() != Path(expected_root).resolve():
                    discrepancies.append("body-native working directory mismatch")
                if comparison_gaps:
                    status = "undetermined"
                    detail = "; ".join(discrepancies + comparison_gaps)
                elif discrepancies:
                    status = "finding"
                    detail = "; ".join(discrepancies)
                else:
                    status = "pass"
                    detail = (
                        "one exact live body; native session identifier and "
                        "working directory agree"
                    )
                report.add(
                    "native session body",
                    status,
                    detail,
                    _surface(body_path),
                    _surface(paths.bindings),
                )

    if analysis is None:
        report.add(
            "body identity",
            "undetermined",
            "native body analysis is unavailable",
            *([_surface(body_paths[0])] if body_paths else [_surface(paths.registry)]),
        )
    elif analysis.latest_identity_claim is None:
        report.add(
            "body identity",
            "undetermined",
            "latest canonical capsule or session-clinic orientation has no "
            "parseable identity; "
            f"identity_rows_seen={analysis.identity_rows_seen}; "
            f"latest_identity_line={analysis.latest_identity_line or 'none'}",
            _surface(analysis.path),
        )
    elif expected_role is None or expected_person is None:
        report.add(
            "body identity",
            "undetermined",
            "a canonical body identity was observed but registry role or person "
            "comparison is unavailable",
            _surface(analysis.path),
        )
    else:
        claim = analysis.latest_identity_claim
        status, comparison = _compare_body_identity(
            claim,
            expected_role,
            expected_person,
        )
        report.add(
            "body identity",
            status,
            f"selected={claim.kind}; line={claim.line_number}; "
            f"identity_rows_seen={analysis.identity_rows_seen}; {comparison}",
            _surface(analysis.path),
            _surface(paths.registry),
        )

    if analysis is None or analysis.context_tokens is None or analysis.context_unavailable_reason:
        report.add(
            "context pressure",
            "undetermined",
            (analysis.context_unavailable_reason if analysis else None)
            or "caller-native context telemetry is unavailable",
            *([_surface(analysis.path), _surface(GAUGE_PATH)] if analysis else [_surface(paths.bindings)]),
        )
    else:
        context_surfaces = [_surface(analysis.path), _surface(GAUGE_PATH)]
        context_detail = ""
        if analysis.provider == "claude":
            window, context_detail, table_path = _claude_window(analysis, paths.window_spec)
            if table_path is not None:
                context_surfaces.append(_surface(table_path))
            analysis.context_window = window
        if analysis.context_window is None or analysis.context_window <= 0:
            report.add(
                "context pressure",
                "undetermined",
                context_detail or "model context window is unavailable",
                *context_surfaces,
            )
        else:
            percentage = 100.0 * analysis.context_tokens / analysis.context_window
            above = percentage >= ROTATION_PERCENT
            detail = (
                f"tokens={analysis.context_tokens}; window={analysis.context_window}; "
                f"pressure={percentage:.1f}%; rotation_line={ROTATION_PERCENT:.1f}%; "
                f"observed_at={analysis.context_observed_at or 'undetermined'}"
            )
            if context_detail:
                detail += f"; {context_detail}"
            report.add(
                "context pressure",
                "finding" if above else "pass",
                detail,
                *context_surfaces,
            )

    if analysis is None:
        report.add(
            "body metrics",
            "undetermined",
            "native body analysis is unavailable",
            _surface(paths.bindings),
        )
    else:
        detail = (
            f"bytes={analysis.size}; rows={analysis.rows}; "
            f"native_compactions={analysis.native_compactions}; "
            f"parse_errors={analysis.parse_errors}"
        )
        if analysis.parse_errors:
            report.source_failures.append(
                f"{_surface(analysis.path)}: JSON parse errors={analysis.parse_errors}"
            )
        report.add(
            "body metrics",
            "finding" if analysis.parse_errors else "pass",
            detail,
            _surface(analysis.path),
        )

    if analysis is None:
        report.add(
            "timestamp cluster",
            "undetermined",
            "native body analysis is unavailable",
            _surface(paths.bindings),
        )
    elif analysis.message_rows == 0 or analysis.missing_message_timestamps:
        report.add(
            "timestamp cluster",
            "undetermined",
            f"message_rows={analysis.message_rows}; missing_timestamps={analysis.missing_message_timestamps}",
            _surface(analysis.path),
        )
    else:
        clusters = [
            (stamp, count)
            for stamp, count in analysis.timestamp_counts.items()
            if count >= TIMESTAMP_CLUSTER_MINIMUM
        ]
        clusters.sort()
        maximum = max(analysis.timestamp_counts.values(), default=0)
        detail = (
            f"clusters={len(clusters)}; maximum_exact_timestamp_messages={maximum}; "
            f"threshold={TIMESTAMP_CLUSTER_MINIMUM}"
        )
        if clusters:
            detail += "; detected=" + ",".join(
                f"{stamp}:{count}" for stamp, count in clusters
            )
        report.add(
            "timestamp cluster",
            "finding" if clusters else "pass",
            detail,
            _surface(analysis.path),
        )

    memory_status, memory_detail, memory_surfaces = _auto_memory(paths, identity, caller, start_pid)
    report.add("auto memory", memory_status, memory_detail, *memory_surfaces)

    return report


def render(report: Report) -> str:
    lines = ["Resident self-check", f"LIMIT: {LIMIT_TEXT}", ""]
    labels = {
        "pass": "PASS",
        "finding": "FINDING",
        "undetermined": "UNDETERMINED",
    }
    for leg in report.legs:
        lines.append(f"[{labels[leg.status]}] {leg.name}: {leg.detail}")
        for surface in leg.surfaces:
            lines.append(f"  surface: {surface}")
    resolved = len(report.legs) - report.unresolved
    lines.extend(
        [
            "",
            (
                f"coverage: observed={len(report.legs)}/{EXPECTED_LEGS}; "
                f"resolved={resolved}/{EXPECTED_LEGS}; unresolved={report.unresolved}; "
                f"findings={report.findings}; "
                f"duplicates={report.duplicates}; "
                f"source_failures={len(report.source_failures)}"
            ),
        ]
    )
    for failure in report.source_failures:
        lines.append(f"  source failure: {failure}")
    lines.append("result: PASS" if report.exit_code == 0 else "result: FAIL-CLOSED")
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 1:
        print("check_myself.py accepts no arguments", file=sys.stderr)
        return 2
    report = run_check(
        CheckPaths.live(),
        environ=os.environ,
        start_pid=os.getppid(),
    )
    print(render(report), end="")
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
