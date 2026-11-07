#!/usr/bin/env python3
"""Read-only Codex log miner for compact and context failure evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Iterable


DEFAULT_DB = Path.home() / ".codex" / "logs_2.sqlite"
SESSIONS = Path(__file__).resolve().parents[3]   # the room, resolved as gauge.py does
DEFAULT_OUT = SESSIONS / "logs" / "codex-log-compaction-events-20260704.md"

PATTERNS = [
    ("auto_compact", "auto_compact"),
    ("compact", "compact"),
    ("remote_compact_task", "remote compact task"),
    ("context_window", "context window"),
    ("out_of_room", "out of room"),
    ("ran_out_of_room", "ran out of room"),
    ("response_completed", "response.completed"),
    ("websocket", "websocket"),
    ("maximum_context", "maximum context"),
    ("context_length", "context_length"),
    ("array_too_long", "array too long"),
    ("invalid_input", "Invalid 'input'"),
    ("token", "token"),
    ("tokens", "tokens"),
]

TEXT_TYPES = ("TEXT", "CHAR", "CLOB", "JSON", "VARCHAR")
SCHEMA_CLUE_PARTS = (
    "token",
    "compact",
    "context",
    "error",
    "response",
    "websocket",
    "input",
)


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def connect_read_only(db: Path) -> sqlite3.Connection:
    uri = f"file:{db.resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.execute("PRAGMA query_only = ON")
    return conn


def get_objects(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    rows = conn.execute(
        """
        SELECT name, type
        FROM sqlite_master
        WHERE type IN ('table', 'view')
          AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        """
    ).fetchall()
    return [(str(name), str(kind)) for name, kind in rows]


def get_columns(conn: sqlite3.Connection, object_name: str) -> list[dict[str, object]]:
    rows = conn.execute(f"PRAGMA table_info({quote_identifier(object_name)})").fetchall()
    columns: list[dict[str, object]] = []
    for cid, name, col_type, notnull, default_value, primary_key in rows:
        columns.append(
            {
                "cid": cid,
                "name": str(name),
                "type": str(col_type or ""),
                "notnull": notnull,
                "default": default_value,
                "primary_key": primary_key,
            }
        )
    return columns


def is_text_column(column: dict[str, object]) -> bool:
    col_type = str(column["type"]).upper()
    name = str(column["name"]).lower()
    if any(part in col_type for part in TEXT_TYPES):
        return True
    if not col_type and any(part in name for part in SCHEMA_CLUE_PARTS):
        return True
    return False


def is_numeric_clue(column: dict[str, object]) -> bool:
    name = str(column["name"]).lower()
    col_type = str(column["type"]).upper()
    if not any(part in name for part in ("token", "context")):
        return False
    return any(part in col_type for part in ("INT", "REAL", "NUM", "DEC", "DOUBLE", "FLOAT"))


def safe_count(
    conn: sqlite3.Connection, object_name: str, column_name: str, needle: str
) -> int | None:
    object_sql = quote_identifier(object_name)
    column_sql = quote_identifier(column_name)
    try:
        row = conn.execute(
            f"SELECT COUNT(*) FROM {object_sql} WHERE {column_sql} LIKE ?",
            (f"%{needle}%",),
        ).fetchone()
        return int(row[0]) if row is not None else 0
    except sqlite3.Error:
        return None


def sample_hits(
    conn: sqlite3.Connection,
    object_name: str,
    column_name: str,
    needle: str,
    limit: int,
) -> list[dict[str, object]]:
    object_sql = quote_identifier(object_name)
    column_sql = quote_identifier(column_name)
    samples: list[dict[str, object]] = []
    try:
        rows = conn.execute(
            f"SELECT rowid, {column_sql} FROM {object_sql} "
            f"WHERE {column_sql} LIKE ? LIMIT ?",
            (f"%{needle}%", limit),
        ).fetchall()
    except sqlite3.Error:
        try:
            rows = conn.execute(
                f"SELECT NULL, {column_sql} FROM {object_sql} "
                f"WHERE {column_sql} LIKE ? LIMIT ?",
                (f"%{needle}%", limit),
            ).fetchall()
        except sqlite3.Error:
            return samples

    for rowid, value in rows:
        if isinstance(value, str):
            raw = value.encode("utf-8", "replace")
        elif isinstance(value, bytes):
            raw = value
        else:
            raw = str(value).encode("utf-8", "replace")
        samples.append(
            {
                "rowid": rowid,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return samples


def numeric_summary(
    conn: sqlite3.Connection, object_name: str, column_name: str
) -> dict[str, object] | None:
    object_sql = quote_identifier(object_name)
    column_sql = quote_identifier(column_name)
    try:
        row = conn.execute(
            f"SELECT COUNT({column_sql}), MIN({column_sql}), MAX({column_sql}) "
            f"FROM {object_sql} WHERE {column_sql} IS NOT NULL"
        ).fetchone()
    except sqlite3.Error:
        return None
    if row is None:
        return None
    count, minimum, maximum = row
    return {"count": int(count or 0), "min": minimum, "max": maximum}


def markdown_table(headers: Iterable[str], rows: Iterable[Iterable[object]]) -> list[str]:
    header_list = list(headers)
    out = ["| " + " | ".join(header_list) + " |"]
    out.append("| " + " | ".join(["---"] * len(header_list)) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(value) for value in row) + " |")
    return out


def write_report(
    db: Path,
    out_path: Path,
    objects_scanned: int,
    text_columns_scanned: int,
    schema_clues: list[tuple[str, str, str, str]],
    numeric_clues: list[tuple[str, str, str, object, object]],
    hit_counts: dict[tuple[str, str, str], int],
    pattern_totals: dict[str, int],
    samples: list[tuple[str, str, str, object, int, str]],
) -> None:
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    token_schema_clues = [
        clue for clue in schema_clues if "token" in clue[2].lower() or "token" in clue[3].lower()
    ]
    compact_schema_clues = [
        clue for clue in schema_clues if "compact" in clue[2].lower() or "compact" in clue[3].lower()
    ]

    lines: list[str] = []
    lines.append("# Codex Log Compaction Event Forensics")
    lines.append("")
    lines.append(f"- Generated: `{now}`")
    lines.append(f"- Source database: `{db}`")
    lines.append(f"- Source database bytes: `{db.stat().st_size if db.exists() else 0}`")
    lines.append(f"- Objects scanned: `{objects_scanned}`")
    lines.append(f"- Text columns scanned: `{text_columns_scanned}`")
    lines.append(f"- Raw log snippets written: `0`")
    lines.append("")
    lines.append("## Pattern Totals")
    lines.extend(
        markdown_table(
            ["pattern", "matches"],
            [(name, pattern_totals.get(name, 0)) for name, _needle in PATTERNS],
        )
    )
    lines.append("")
    lines.append("## Table And Column Hits")
    hit_rows = [
        (table, column, pattern, count)
        for (table, column, pattern), count in sorted(
            hit_counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1], item[0][2])
        )
        if count
    ]
    if hit_rows:
        lines.extend(markdown_table(["table", "column", "pattern", "matches"], hit_rows[:80]))
    else:
        lines.append("No pattern hits were found.")
    lines.append("")
    lines.append("## Sample Evidence Handles")
    if samples:
        lines.extend(
            markdown_table(
                ["table", "column", "pattern", "rowid", "bytes", "sha256"],
                samples[:80],
            )
        )
    else:
        lines.append("No sample handles were collected.")
    lines.append("")
    lines.append("## Schema Clues")
    if schema_clues:
        lines.extend(
            markdown_table(
                ["object_type", "table", "column", "type"],
                schema_clues[:120],
            )
        )
    else:
        lines.append("No compact, context, token, response, or error column names were found.")
    lines.append("")
    lines.append("## Numeric Token Or Context Clues")
    if numeric_clues:
        lines.extend(
            markdown_table(
                ["table", "column", "count", "min", "max"],
                numeric_clues[:80],
            )
        )
    else:
        lines.append("No numeric token or context columns were found in the scanned schema.")
    lines.append("")
    lines.append("## Interpretation")
    if token_schema_clues or numeric_clues:
        lines.append(
            "- The log schema exposes at least one token or context clue. "
            "Use the table and column names above for the next focused query."
        )
    else:
        lines.append(
            "- The scanned log schema does not expose obvious numeric token counters. "
            "The local log may record failure surface text without the remote compact token budget."
        )
    if compact_schema_clues or pattern_totals.get("remote_compact_task", 0):
        lines.append(
            "- Compact-related evidence is present locally. "
            "This supports a focused event timeline pass before another JSONL candidate load test."
        )
    else:
        lines.append(
            "- Compact-related evidence was not found in the bounded scan. "
            "The next pass should inspect extension host logs or VS Code logs."
        )
    lines.append("")
    lines.append("## Counters")
    lines.append("- Production session edits: `0`")
    lines.append("- Source session rewrites: `0`")
    lines.append("- JSONL promotions: `0`")
    lines.append("- Automatic Codex launches: `0`")
    lines.append("- Raw log snippets written: `0`")
    lines.append("- Protocol deviations: `0`")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mine Codex SQLite logs for compact and context failure evidence."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--sample-limit", type=int, default=3)
    args = parser.parse_args()

    db = args.db
    if not db.exists():
        raise SystemExit(f"database not found: {db}")

    conn = connect_read_only(db)
    objects = get_objects(conn)
    objects_scanned = 0
    text_columns_scanned = 0
    schema_clues: list[tuple[str, str, str, str]] = []
    numeric_clues: list[tuple[str, str, str, object, object]] = []
    hit_counts: dict[tuple[str, str, str], int] = {}
    pattern_totals: dict[str, int] = defaultdict(int)
    samples: list[tuple[str, str, str, object, int, str]] = []

    for object_name, object_type in objects:
        objects_scanned += 1
        columns = get_columns(conn, object_name)
        for column in columns:
            column_name = str(column["name"])
            column_type = str(column["type"])
            lower_blob = f"{column_name} {column_type}".lower()
            if any(part in lower_blob for part in SCHEMA_CLUE_PARTS):
                schema_clues.append((object_type, object_name, column_name, column_type))
            if is_numeric_clue(column):
                summary = numeric_summary(conn, object_name, column_name)
                if summary and summary["count"]:
                    numeric_clues.append(
                        (
                            object_name,
                            column_name,
                            str(summary["count"]),
                            summary["min"],
                            summary["max"],
                        )
                    )
            if not is_text_column(column):
                continue
            text_columns_scanned += 1
            for pattern_name, needle in PATTERNS:
                count = safe_count(conn, object_name, column_name, needle)
                if count is None:
                    continue
                if count:
                    hit_counts[(object_name, column_name, pattern_name)] = count
                    pattern_totals[pattern_name] += count
                    for sample in sample_hits(
                        conn, object_name, column_name, needle, args.sample_limit
                    ):
                        samples.append(
                            (
                                object_name,
                                column_name,
                                pattern_name,
                                sample["rowid"],
                                int(sample["bytes"]),
                                str(sample["sha256"]),
                            )
                        )

    write_report(
        db=db,
        out_path=args.out,
        objects_scanned=objects_scanned,
        text_columns_scanned=text_columns_scanned,
        schema_clues=schema_clues,
        numeric_clues=numeric_clues,
        hit_counts=hit_counts,
        pattern_totals=pattern_totals,
        samples=samples,
    )
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
