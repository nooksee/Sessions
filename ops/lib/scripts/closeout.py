#!/usr/bin/env python3
"""closeout: tell a resident, from its own body, that its closeout has begun. Standard library only.

A UserPromptSubmit hook. It reads the hook input on standard input, opens the
session's own transcript and nothing else, takes the newest usage reading the
way gauge does, and divides by the model's window. When 50,000 tokens or fewer
remain before the 70 percent line, it adds the closeout card to the resident's
context; otherwise it prints nothing.

Never in the way (Claudio section 131, C3): Claude Code erases the prompt when
a UserPromptSubmit hook exits with code 2. So every path here exits 0, every
error goes to the "unknown" path, no argument parser can exit on its own, and
the whole run is limited to 5 seconds.

Never message content: the prompt is not used, and the transcript is read only
as gauge reads it. The card's one source is the template
ops/src/reports/closeout.md.tpl; a template this hook cannot read or fill is
"unknown", never a fallback card. Nothing is wired: installing this hook, and the notification
to Kevin, each need Claudio's review and Kevin's named go.
Spec: docs/ops/specs/scripts/closeout.md.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True     # importing gauge must never leave bytecode beside it

import contextlib
import datetime as dt
import fcntl
import importlib.util
import json
import os
import re
import signal
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SESSIONS = HERE.parents[2]
GAUGE = HERE / "gauge.py"
DEFAULTS = {"room": SESSIONS,                       # whose Integrator and Contractors the card speaks of (tests name another)
            "registry": SESSIONS / "ops" / "etc" / "resident-identities.json",
            "spec": SESSIONS / "docs" / "ops" / "specs" / "scripts" / "gauge.md",
            "state-dir": SESSIONS / "logs" / "closeout",
            "template": SESSIONS / "ops" / "src" / "reports" / "closeout.md.tpl"}
LEGACY_STATE = SESSIONS / "storage" / "closeout"
LIMIT_SECONDS = 5.0
SOFT_SHARE = 0.9                   # at 90 percent of the limit the run turns to "unknown"; at the limit it exits 0
SOFT_MARGIN = 0.25                 # at least this long between the soft and the hard alarm, so the unknown is logged
MIN_LIMIT = 0.5                    # --limit-seconds (tests only) is kept between this and LIMIT_SECONDS
ASCII_SPACE = " \t\n\r\f\v"       # what ops/bin/template's [[:space:]] is in the C locale
RESERVE = 50_000                   # tokens left before the due line when the closeout begins
DUE = 0.70                         # the rotation is due at 70 percent
BAND = 0.05                        # the card repeats once per 5 points beyond the trigger
UNKNOWN_NOTICE = 3                 # consecutive unknowns before Kevin is told
SID_RE = re.compile(r"[0-9A-Za-z-]{8,64}")

CARD_SLOTS = ("PERCENT", "WINDOW", "READING_TIME", "ROTATION_WRITER")   # what this hook fills, no more and no less
INTEGRATOR_ROLE = "Integrator"                                          # runs every rotation but its own (PoT 4.1.3)
CONTRACTOR_ROLE = "Contractor"                                          # the one the operator assigns runs the Integrator's (PoT 4.1.4)
ASSIGNED_CONTRACTOR = "The Contractor the operator assigns"             # the card's words for it: the registry holds no assignment
MARKER_RE = re.compile(r"\{\{([^{}\n]*)\}\}")          # as grep -oE '\{\{[^{}]*\}\}', line by line
LEFTOVER_RE = re.compile(r"\{\{.*\}\}")                  # as check_rendered: any {{...}} on one line
WS = r"[ \t\r\f\v]"                    # [[:space:]] inside one line, in the C locale
FRONT_KEY = re.compile(r"([a-z_]+):" + WS + r"*(.*)")
SLOT_ITEM = re.compile(WS + r"+-" + WS + r"+([A-Z][A-Z0-9_]*)" + WS + r"*")
SLOT_NOTE = re.compile(WS + r"+([A-Z][A-Z0-9_]*):" + WS + r"+(.+)")


class Unknown(Exception):
    """No figure can be established: nothing for the resident, a line in the log."""


class Timeout(Exception):
    """The 5-second limit was reached."""


def pressure_band(tokens: int, window: int) -> int | None:
    """Shared reserve/band decision; None is below trigger, never unknown.

    Preserve the existing 70 percent line, 50,000-token reserve and 5-point
    bands. The hook and operator-only notice must call this one decision.
    """
    if (isinstance(tokens, bool) or not isinstance(tokens, int) or tokens < 0
            or isinstance(window, bool) or not isinstance(window, int) or window <= 0):
        raise Unknown("tokens and window must be valid integer counters")
    if tokens > window:
        raise Unknown("the reading exceeds the window")
    trigger = DUE * window - RESERVE
    if trigger <= 0:
        raise Unknown("the window is too small for the reserve rule")
    if tokens < trigger:
        return None
    return int((tokens - trigger) // (BAND * window))


ALARMS = [0]
PHASE = ["decide"]


def on_alarm(signum, frame):
    """During decide, the first alarm (the soft limit) raises, so the run turns to "unknown". Any other alarm,
    and any alarm once decide has returned, ends the run at once with exit 0: delivery is one small write, and a
    commit cut short only repeats the card on the next prompt."""
    ALARMS[0] += 1
    if ALARMS[0] > 1 or PHASE[0] != "decide":
        os._exit(0)
    raise Timeout(f"the {LIMIT_SECONDS:g}-second limit was reached")


def options(argv: list[str]) -> dict:
    """--name=value only; anything else is ignored, never an exit."""
    opts = dict(DEFAULTS)
    for arg in argv:
        if arg.startswith("--") and "=" in arg:
            name, value = arg[2:].split("=", 1)
            if name in ("room", "registry", "spec", "state-dir", "template"):
                opts[name] = Path(value)
            elif name in ("now", "limit-seconds"):
                opts[name] = value
    return opts


def utc_now(opts: dict) -> dt.datetime:
    if opts.get("now"):
        return dt.datetime.fromisoformat(opts["now"].replace("Z", "+00:00"))
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def load_gauge():
    spec = importlib.util.spec_from_file_location("gauge", GAUGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def own_transcript(provider: str, session_id: str, transcript_path) -> Path:
    """The hook input's transcript, only when its name is this session's own body."""
    if not isinstance(transcript_path, str) or not transcript_path:
        raise Unknown("the hook input names no transcript")
    path = Path(transcript_path)
    if provider == "claude":
        own = path.name == f"{session_id}.jsonl"
    elif provider == "codex":
        own = re.fullmatch(r"rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-" + re.escape(session_id) + r"\.jsonl", path.name)
    else:
        raise Unknown(f"no closeout route for provider {provider!r}")
    if not own:
        raise Unknown("the transcript is not this session's own body")
    if path.is_symlink() or not path.is_file():
        raise Unknown("the transcript is not a regular file")
    return path


# --------------------------------------------------------------------------
# The card: rendered from its template, with the rules ops/bin/template
# applies (docs/ops/specs/binaries/template.md). Any defect is "unknown".
# --------------------------------------------------------------------------
def card_template(path: Path) -> str:
    """The template's body, checked as ops/bin/template's load_template checks it, and against the four slots."""
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        raise Unknown("the card template is unreadable") from None
    lines = text.split("\n")
    if text.endswith("\n"):
        lines = lines[:-1]
    state, fields, required, notes, section, body = 0, {}, [], set(), None, []
    for n, line in enumerate(lines, 1):
        if state == 0:
            if line != "---":
                raise Unknown("the card template does not open with front matter")
            state = 1
        elif state == 1:
            key, item, note = FRONT_KEY.fullmatch(line), SLOT_ITEM.fullmatch(line), SLOT_NOTE.fullmatch(line)
            if line == "---":
                state = 2
            elif key:
                section = None
                if key.group(1) in ("requires_slots", "slot_notes"):
                    if key.group(2):
                        raise Unknown(f"the card template's {key.group(1)} takes a list, not a value")
                    section = key.group(1)
                else:
                    fields[key.group(1)] = key.group(2)
            elif section == "requires_slots" and item:
                if item.group(1) in required:
                    raise Unknown("the card template lists a slot twice")
                required.append(item.group(1))
            elif section == "slot_notes" and note:
                notes.add(note.group(1))
            elif line.strip(ASCII_SPACE) and not line.lstrip(ASCII_SPACE).startswith("#"):
                raise Unknown(f"the card template's front matter line {n} is not understood")
        else:
            body.append(line)
    if state != 2:
        raise Unknown("the card template's front matter is not closed")
    if (fields.get("template_type"), fields.get("template_id")) != ("report", "closeout") \
            or not re.fullmatch(r"[1-9][0-9]*", fields.get("template_version", "")):
        raise Unknown("the card template is not a closeout report template")
    if not required or set(required) != notes:
        raise Unknown("the card template's slots and slot notes do not agree")
    body_text = "".join(line + "\n" for line in body)
    used = set(MARKER_RE.findall(body_text))
    if any(not re.fullmatch(r"[A-Z][A-Z0-9_]*", slot) for slot in used):
        raise Unknown("the card template has a malformed marker")
    if used != set(required) or set(required) != set(CARD_SLOTS):
        raise Unknown("the card template's slots are not the four this hook fills")
    return body_text


def render_card(body: str, values: dict) -> str:
    """As ops/bin/template's render_body and check_rendered: one left-to-right pass, so a value is never
    searched for markers itself, and no {{...}} may remain on any line."""
    for slot, value in values.items():
        if not value.strip():
            raise Unknown(f"the card slot {slot} would be empty")
        if "[PLACEHOLDER" in value:
            raise Unknown(f"the card slot {slot} holds a placeholder")
    out, rest = [], body
    while "{{" in rest:
        head, rest = rest.split("{{", 1)
        out.append(head)
        m = re.match(r"([A-Z][A-Z0-9_]*)\}\}", rest)
        if m and m.group(1) in values:
            out.append(values[m.group(1)])
            rest = rest[m.end():]
        else:
            out.append("{{")
    text = "".join(out) + rest
    if LEFTOVER_RE.search(text):
        raise Unknown("a {{...}} marker would remain in the card")
    return text.rstrip("\n")


def named(entry: dict, what: str) -> tuple[str, str]:
    """(key, person) of a registry entry, both plain non-empty strings, or unknown."""
    key, person = entry.get("key"), entry.get("person")
    if not isinstance(key, str) or not key.strip() or not isinstance(person, str) or not person.strip():
        raise Unknown(f"the registry's {what} has no key or no name")
    return key, person.strip()


def in_room(entry, room: Path) -> bool:
    """Whether a registry entry is registered to this room: its room is an absolute path that resolves to this room's.
    The registry covers the whole host, and other rooms hold roles of the same names. A relative room would mean
    whatever folder the hook happens to run in, so it is no room."""
    value = entry.get("room") if isinstance(entry, dict) else None
    if not isinstance(value, str) or not Path(value).is_absolute():
        return False
    try:
        return Path(value).resolve() == room
    except (OSError, RuntimeError, ValueError):
        return False


def rotation_writer(identities: list, key: str, room: Path) -> str:
    """Who runs this resident's rotation, from the roles of this room in the registry. A writer is never the resident
    being moved.

    This room's Integrator runs every rotation but its own, whichever room the resident is registered to. Its own is
    run by the Contractor the operator assigns to it (PoT 4.1.4). The registry holds no such assignment, so the card
    says so and names nobody. With no Contractor in this room but the Integrator itself there is no one to assign,
    and that is unknown. An Integrator or a Contractor of another room is that room's and is not counted.
    """
    integrators = [i for i in identities if in_room(i, room) and i.get("role") == INTEGRATOR_ROLE]
    if len(integrators) != 1:
        raise Unknown("the registry does not name exactly one Integrator of this room")
    integrator_key, integrator = named(integrators[0], "Integrator")
    if integrator_key != key:
        return f"{integrator}'s desk"
    if not any(in_room(i, room) and i.get("role") == CONTRACTOR_ROLE and i.get("key") != key for i in identities):
        raise Unknown("the registry names no Contractor of this room to run the Integrator's rotation")
    return ASSIGNED_CONTRACTOR


# --------------------------------------------------------------------------
# State and log: ignored files under logs/closeout, keyed by session.
# Fresh state directories are 0700 and fresh files are 0600.
# A busy lock is skipped, never waited on.
# --------------------------------------------------------------------------
@contextlib.contextmanager
def state_lock(state_dir: Path):
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(state_dir / ".lock", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_state(state_dir: Path) -> dict:
    try:
        data = json.loads((state_dir / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_state(state_dir: Path, state: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=state_dir, prefix=".state.")
    try:
        os.write(fd, json.dumps(state, sort_keys=True).encode("utf-8"))
        os.close(fd)
        os.chmod(tmp, 0o600)
        os.replace(tmp, state_dir / "state.json")
    except BaseException:
        with contextlib.suppress(OSError):
            os.close(fd)
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def log(state_dir: Path, now: dt.datetime, **fields) -> None:
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    line = json.dumps({"at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), **fields}, sort_keys=True) + "\n"
    fd = os.open(state_dir / "log.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def update(state_dir: Path, session_id: str, change) -> dict | None:
    """Apply change(entry) to this session's entry under the lock; entry None removes it. Returns the old entry.
    Under the lock no other run is writing, so any temporary state file present was left by a run the hard
    limit ended mid-write, and is removed."""
    try:
        with state_lock(state_dir):
            for leftover in state_dir.glob(".state.*"):
                with contextlib.suppress(OSError):
                    leftover.unlink()
            state = read_state(state_dir)
            old = state.get(session_id)
            new = change(dict(old) if isinstance(old, dict) else {})
            if new is None:
                state.pop(session_id, None)
            else:
                state[session_id] = new
            if state.get(session_id) != old:
                write_state(state_dir, state)
            return old if isinstance(old, dict) else {}
    except BlockingIOError:
        return None


def record_unknown(opts: dict, now: dt.datetime, ctx: dict, why: str) -> None:
    """Nothing for the resident. A log line, and after 3 in a row, one notice for Kevin (not wired)."""
    sid, state_dir = ctx.get("session_id"), opts["state-dir"]
    who = {"key": ctx["key"]} if ctx.get("key") else {"session_id": sid}
    log(state_dir, now, event="unknown", why=why, **who)
    if not sid:
        return

    def bump(entry):
        entry["unknown"] = int(entry.get("unknown") or 0) + 1
        return entry
    old = update(state_dir, sid, bump)
    if old is not None and int(old.get("unknown") or 0) + 1 == UNKNOWN_NOTICE:
        log(state_dir, now, event="kevin-notice", delivered=False, why=f"{UNKNOWN_NOTICE} unknown readings in a row",
            note="notification not wired; needs Kevin's go", **who)


# --------------------------------------------------------------------------
# The decision.
# --------------------------------------------------------------------------
def decide(opts: dict, raw: bytes, now: dt.datetime):
    """(output or None, commit or None). The commit records the band and runs only after the card is delivered,
    so a failure after delivery repeats the card on the next prompt instead of losing it."""
    ctx: dict = {}
    try:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return None, None                             # unidentified: no session to key anything to
        session_id = data.get("session_id") if isinstance(data, dict) else None
        if not isinstance(session_id, str) or not SID_RE.fullmatch(session_id):
            return None, None
        ctx["session_id"] = session_id
        try:
            identities = json.loads(opts["registry"].read_text(encoding="utf-8"))["identities"]
        except (OSError, ValueError, KeyError, TypeError):
            raise Unknown("the registry is unreadable") from None
        matches = [i for i in identities if isinstance(i, dict) and i.get("session_id") == session_id]
        if not matches:
            return None, None                             # not a registered resident: always silent
        if len(matches) > 1:
            raise Unknown("the session is registered more than once")
        ctx["key"] = matches[0].get("key")
        if not isinstance(ctx["key"], str) or not ctx["key"].strip():
            raise Unknown("the session's registry entry has no key")
        if opts["state-dir"] == DEFAULTS["state-dir"]:
            try:
                LEGACY_STATE.lstat()
            except FileNotFoundError:
                # ENOENT also occurs through a dangling parent. Only a truly
                # absent parent or a searchable directory proves absence here.
                try:
                    LEGACY_STATE.parent.lstat()
                except FileNotFoundError:
                    pass
                except OSError:
                    raise Unknown("legacy closeout state parent cannot be inspected; reviewed migration is required") from None
                else:
                    if not LEGACY_STATE.parent.is_dir():
                        raise Unknown("legacy closeout state parent is not a readable directory; reviewed migration is required")
            except OSError:
                raise Unknown("legacy closeout state cannot be inspected; reviewed migration is required") from None
            else:
                raise Unknown("legacy closeout state requires reviewed migration before using the default destination")
        provider = matches[0].get("provider")
        transcript = own_transcript(provider, session_id, data.get("transcript_path"))
        gauge = load_gauge()
        reading = {"claude": gauge.read_claude, "codex": gauge.read_codex}[provider](transcript)
        if "tokens" not in reading:
            if reading.get("compaction_after"):
                return None, None                         # compacted, no reading since: silent, not unknown
            raise Unknown(reading.get("reason") or "no reading")
        if reading.get("compaction_after"):
            return None, None                             # the figure predates a compaction: silent until a fresh one
        gauge.resolve_window(reading, gauge.window_table(opts["spec"]), None)   # provider or reviewed table only
        tokens, window = reading["tokens"], reading.get("window")
        if not window:
            raise Unknown(reading.get("window_reason") or "no reviewed window")
        if tokens > window:
            raise Unknown("the reading exceeds the window")
        band = pressure_band(tokens, window)
        state_dir = opts["state-dir"]
        if band is None:
            old = update(state_dir, session_id, lambda entry: None)
            if old and old.get("band") is not None:
                log(state_dir, now, event="rearmed", key=ctx["key"], percent=round(100.0 * tokens / window, 3))
            return None, None
        percent = 100.0 * tokens / window
        when = gauge.parse_time(reading.get("reading_at"))
        card = render_card(card_template(opts["template"]), {    # first: a defect is unknown and uses up no band
            "PERCENT": f"{percent:.1f}", "WINDOW": f"{window:,} tokens",
            "READING_TIME": when.astimezone().strftime("%Y-%m-%d %H:%M %Z") if when else "an unknown time",
            "ROTATION_WRITER": rotation_writer(identities, ctx["key"], opts["room"].resolve())})
        told = read_state(state_dir).get(session_id)
        if isinstance(told, dict) and isinstance(told.get("band"), int) and band <= told["band"]:
            if told.get("unknown"):
                update(state_dir, session_id, lambda entry: {**entry, "unknown": 0})
            return None, None                             # already told within this band

        def commit():
            update(state_dir, session_id, lambda entry: {"band": band, "unknown": 0, "key": ctx["key"]})
            log(state_dir, now, event="card", key=ctx["key"], band=band, percent=round(percent, 3), tokens=tokens, window=window)
            log(state_dir, now, event="kevin-notice", key=ctx["key"], delivered=False,
                why=f"closeout card at {percent:.1f} percent", note="notification not wired; needs Kevin's go")
        return json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": card}}), commit
    except Exception as exc:                              # every failure, including the time limit, is unknown
        why = str(exc) if isinstance(exc, (Unknown, Timeout)) else f"error: {exc.__class__.__name__}"
        try:
            record_unknown(opts, now, ctx, why)
        except Exception:
            pass
        return None, None


def limit_of(value) -> float:
    """The run's limit: LIMIT_SECONDS unless a finite --limit-seconds (tests only) asks for less, never below MIN_LIMIT."""
    try:
        limit = float(value) if value is not None else LIMIT_SECONDS
    except ValueError:
        return LIMIT_SECONDS
    if limit != limit or limit <= 0 or limit > LIMIT_SECONDS:
        return LIMIT_SECONDS
    return max(limit, MIN_LIMIT)


def main() -> None:
    """Every path ends in os._exit(0), and nothing reaches standard error (Claudio section 131, C3)."""
    try:
        sys.stderr = open(os.devnull, "w")
        out = commit = None
        delivered = False
        try:
            opts = options(sys.argv[1:])
            limit = limit_of(opts.get("limit-seconds"))
            margin = max(limit * (1 - SOFT_SHARE), SOFT_MARGIN)
            signal.signal(signal.SIGALRM, on_alarm)
            signal.setitimer(signal.ITIMER_REAL, limit - margin, margin)
            now = utc_now(opts)
            out, commit = decide(opts, sys.stdin.buffer.read(), now)
            PHASE[0] = "deliver"
        except BaseException:
            out = commit = None
        PHASE[0] = "deliver"
        try:
            if out:
                sys.stdout.write(out + "\n")
            sys.stdout.flush()
            delivered = bool(out)
        except BaseException:
            delivered = False
        if delivered and commit:
            try:
                commit()                                  # after delivery: a failure here repeats the card, never loses it
            except BaseException:
                pass
    except BaseException:
        pass
    os._exit(0)


if __name__ == "__main__":
    main()
