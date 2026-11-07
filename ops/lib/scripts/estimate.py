#!/usr/bin/env python3
"""Estimate Codex JSONL context pressure in tokens.

This is a read-only lab tool. It does not edit session files, promote
derivatives, copy authentication files, or launch Codex.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import tiktoken
except Exception as exc:  # pragma: no cover - user-facing dependency check
    raise SystemExit(
        "Missing dependency: tiktoken. Use Sessions/.venv/bin/python or install tiktoken."
    ) from exc


SESSIONS = Path(__file__).resolve().parents[3]   # the room, resolved as gauge.py does
EVIDENCE_DIR = SESSIONS / "logs"

ACTIVE_CONTEXT_PROXY_KEYS = {
    "proxy_response_message_tokens",
    "proxy_reasoning_summary_tokens",
    "proxy_session_instruction_tokens",
    "proxy_compacted_message_tokens",
}

STORAGE_DIAGNOSTIC_PROXY_KEYS = {
    "proxy_tool_call_tokens",
    "proxy_tool_output_tokens",
    "proxy_compacted_replacement_tokens",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def nested_get(value: Any, keys: tuple[str, ...]) -> Any:
    cur = value
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def classify_row(payload: Any) -> tuple[str, str]:
    if not isinstance(payload, dict):
        return "other", "unknown"

    row_type = str(payload.get("type") or payload.get("kind") or "")
    payload_type = str(
        payload.get("payload", {}).get("type")
        if isinstance(payload.get("payload"), dict)
        else payload.get("payload_type") or ""
    )
    item_type = str(
        payload.get("item", {}).get("type")
        if isinstance(payload.get("item"), dict)
        else ""
    )

    joined = " ".join(part for part in (row_type, payload_type, item_type) if part).lower()
    if "response_item" in joined:
        return "response_item", payload_type or item_type or row_type or "unknown"
    if "compact" in joined or "compacted" in compact_json(payload).lower()[:2000]:
        return "compacted", payload_type or item_type or row_type or "unknown"
    if "turn_context" in joined:
        return "turn_context", payload_type or item_type or row_type or "unknown"
    if "session" in joined:
        return "session_meta", payload_type or item_type or row_type or "unknown"
    if "event" in joined or "message" in joined or "msg" in joined:
        return "event_msg", payload_type or item_type or row_type or "unknown"
    return row_type or "other", payload_type or item_type or "unknown"


def count_content_text_chars(value: Any) -> int:
    total = 0
    stack = [value]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for key, child in cur.items():
                if key in {"text", "content", "input_text", "output_text"} and isinstance(child, str):
                    total += len(child)
                else:
                    stack.append(child)
        elif isinstance(cur, list):
            stack.extend(cur)
    return total


def token_len(enc: Any, text: str) -> int:
    if not text:
        return 0
    return len(enc.encode(text))


def iter_content_text(value: Any) -> list[str]:
    """Return user-visible text from Codex message content containers."""
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []

    texts: list[str] = []
    for item in value:
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str):
                texts.append(text)
    return texts


def compact_proxy_token_breakdown(payload: dict[str, Any], enc: Any) -> dict[str, int]:
    """Estimate tokens likely relevant to hosted compact input.

    Raw JSONL includes UI event rows, encrypted reasoning blobs, metadata wrappers,
    and duplicated message records. This proxy counts visible response content and
    compacted-history summaries separately from raw row JSON so that working
    controls do not fail only because their storage representation is large.
    """
    row_type = payload.get("type")
    inner = payload.get("payload")
    if not isinstance(inner, dict):
        inner = {}

    parts: dict[str, int] = defaultdict(int)

    if row_type == "response_item":
        payload_type = inner.get("type")
        if payload_type == "message":
            for text in iter_content_text(inner.get("content")):
                parts["proxy_response_message_tokens"] += token_len(enc, text)
        elif payload_type in {"function_call", "custom_tool_call"}:
            name = inner.get("name")
            if isinstance(name, str):
                parts["proxy_tool_call_tokens"] += token_len(enc, name)
            arguments = inner.get("arguments")
            if isinstance(arguments, str):
                parts["proxy_tool_call_tokens"] += token_len(enc, arguments)
            call_input = inner.get("input")
            if isinstance(call_input, str):
                parts["proxy_tool_call_tokens"] += token_len(enc, call_input)
        elif payload_type in {"function_call_output", "custom_tool_call_output", "tool_search_output"}:
            output = inner.get("output")
            if isinstance(output, str):
                parts["proxy_tool_output_tokens"] += token_len(enc, output)
        elif payload_type == "reasoning":
            for summary in inner.get("summary") or []:
                if isinstance(summary, dict):
                    text = summary.get("text")
                    if isinstance(text, str):
                        parts["proxy_reasoning_summary_tokens"] += token_len(enc, text)
                elif isinstance(summary, str):
                    parts["proxy_reasoning_summary_tokens"] += token_len(enc, summary)
            encrypted = inner.get("encrypted_content")
            if isinstance(encrypted, str):
                parts["storage_encrypted_reasoning_chars"] += len(encrypted)
        elif payload_type in {"web_search_call", "tool_search_call"}:
            # Call metadata is small and useful for chronology, but not raw JSON wrappers.
            action = inner.get("action")
            if isinstance(action, dict):
                query = action.get("query")
                if isinstance(query, str):
                    parts["proxy_tool_call_tokens"] += token_len(enc, query)

    elif row_type == "compacted":
        message = inner.get("message")
        if isinstance(message, str):
            parts["proxy_compacted_message_tokens"] += token_len(enc, message)
        replacement_history = inner.get("replacement_history")
        if isinstance(replacement_history, list):
            for item in replacement_history:
                if isinstance(item, str):
                    parts["proxy_compacted_replacement_tokens"] += token_len(enc, item)
                elif isinstance(item, dict):
                    for text in iter_content_text(item.get("content")):
                        parts["proxy_compacted_replacement_tokens"] += token_len(enc, text)

    elif row_type == "session_meta":
        for key in ("base_instructions", "instructions"):
            text = inner.get(key)
            if isinstance(text, str):
                parts["proxy_session_instruction_tokens"] += token_len(enc, text)

    elif row_type == "event_msg":
        message = inner.get("message")
        if isinstance(message, str):
            parts["diagnostic_event_message_tokens"] += token_len(enc, message)

    elif row_type == "turn_context":
        text_chars = count_content_text_chars(inner)
        parts["diagnostic_turn_context_text_chars"] += text_chars

    return dict(parts)


def analyze_file(path: Path, encoding_name: str, top_rows: int) -> dict[str, Any]:
    enc = tiktoken.get_encoding(encoding_name)
    row_type_counts: Counter[str] = Counter()
    row_type_tokens: Counter[str] = Counter()
    payload_type_counts: Counter[str] = Counter()
    payload_type_tokens: Counter[str] = Counter()
    parse_errors: list[dict[str, Any]] = []
    largest_rows: list[dict[str, Any]] = []
    total_tokens = 0
    compact_active_message_tokens = 0
    compact_storage_proxy_tokens = 0
    compact_proxy_tokens_all = 0
    compact_proxy_parts: Counter[str] = Counter()
    rows = 0
    content_text_chars = 0

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.rstrip("\n")
            if not raw:
                continue
            rows += 1
            try:
                payload = json.loads(raw)
            except Exception as exc:
                parse_errors.append({"line": line_no, "error": str(exc), "bytes": len(raw.encode("utf-8", "replace"))})
                continue

            rendered = compact_json(payload)
            token_count = len(enc.encode(rendered))
            row_type, payload_type = classify_row(payload)
            text_chars = count_content_text_chars(payload)
            byte_count = len(raw.encode("utf-8", "replace"))
            proxy_parts = compact_proxy_token_breakdown(payload, enc)
            active_token_count = sum(proxy_parts.get(key, 0) for key in ACTIVE_CONTEXT_PROXY_KEYS)
            all_proxy_token_count = sum(value for key, value in proxy_parts.items() if key.startswith("proxy_"))
            storage_token_count = max(0, all_proxy_token_count - active_token_count)

            total_tokens += token_count
            compact_active_message_tokens += active_token_count
            compact_storage_proxy_tokens += storage_token_count
            compact_proxy_tokens_all += all_proxy_token_count
            compact_proxy_parts.update(proxy_parts)
            content_text_chars += text_chars
            row_type_counts[row_type] += 1
            row_type_tokens[row_type] += token_count
            payload_type_counts[payload_type] += 1
            payload_type_tokens[payload_type] += token_count

            entry = {
                "line": line_no,
                "tokens": token_count,
                "bytes": byte_count,
                "row_type": row_type,
                "payload_type": payload_type,
                "content_text_chars": text_chars,
            }
            largest_rows.append(entry)
            largest_rows.sort(key=lambda item: item["tokens"], reverse=True)
            if len(largest_rows) > top_rows:
                largest_rows.pop()

    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "encoding": encoding_name,
        "rows": rows,
        "parse_errors": parse_errors,
        "raw_json_tokens": total_tokens,
        "total_tokens": compact_active_message_tokens,
        "compact_active_message_tokens": compact_active_message_tokens,
        "compact_storage_proxy_tokens": compact_storage_proxy_tokens,
        "compact_proxy_tokens": compact_active_message_tokens,
        "compact_proxy_tokens_all": compact_proxy_tokens_all,
        "compact_proxy_parts": dict(compact_proxy_parts),
        "active_context_proxy_keys": sorted(ACTIVE_CONTEXT_PROXY_KEYS),
        "storage_diagnostic_proxy_keys": sorted(STORAGE_DIAGNOSTIC_PROXY_KEYS),
        "content_text_chars": content_text_chars,
        "row_type_counts": dict(row_type_counts),
        "row_type_tokens": dict(row_type_tokens),
        "payload_type_counts": dict(payload_type_counts),
        "payload_type_tokens": dict(payload_type_tokens),
        "largest_rows": largest_rows,
        "safety": {
            "production_session_edits": 0,
            "source_session_rewrites": 0,
            "jsonl_derivatives_promoted": 0,
            "auth_file_copies": 0,
            "automatic_codex_launches": 0,
            "permanent_deletes": 0,
        },
        "limits_note": (
            "This report separates raw JSONL token storage from a compact-input proxy. "
            "Raw JSONL tokens and storage/tool/replacement proxy tokens are diagnostic only; "
            "the status gate uses compact_active_message_tokens."
        ),
    }


def status_for(total_tokens: int, warn_total: int, max_total: int, hard_trigger: int, parse_errors: int) -> str:
    if parse_errors:
        return "fail_parse"
    if total_tokens >= hard_trigger:
        return "fail_hard_trigger"
    if total_tokens > max_total:
        return "fail_target"
    if total_tokens > warn_total:
        return "warn"
    return "pass"


def write_evidence(results: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, str]:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    stem = args.evidence_stem or f"codex-token-context-pressure-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    json_path = EVIDENCE_DIR / f"{stem}.json"
    summary_path = EVIDENCE_DIR / f"{stem}-summary.md"
    top_rows_path = EVIDENCE_DIR / f"{stem}-top-rows.csv"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": {
            "warn_total_tokens": args.warn_total_tokens,
            "max_total_tokens": args.max_total_tokens,
            "hard_trigger_tokens": args.hard_trigger_tokens,
        },
        "results": results,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with top_rows_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["file", "line", "tokens", "bytes", "row_type", "payload_type", "content_text_chars"],
            lineterminator="\n",
        )
        writer.writeheader()
        for result in results:
            for row in result["largest_rows"]:
                writer.writerow({"file": result["path"], **row})

    lines = [
        "# Codex Token Context Pressure",
        "",
        f"Generated: `{payload['generated_at']}`",
        "",
        "This is a read-only local proxy for hosted Codex context pressure. It does not edit session files.",
        "",
        "## Thresholds",
        "",
        f"- Warn active compact tokens: `{args.warn_total_tokens}`",
        f"- Target max active compact tokens: `{args.max_total_tokens}`",
        f"- Estimated hard trigger tokens: `{args.hard_trigger_tokens}`",
        "",
        "## Results",
        "",
    ]
    for result in results:
        status = status_for(
            result["total_tokens"],
            args.warn_total_tokens,
            args.max_total_tokens,
            args.hard_trigger_tokens,
            len(result["parse_errors"]),
        )
        lines.extend(
            [
                f"### `{result['path']}`",
                "",
                f"- Status: `{status}`",
                f"- Rows: `{result['rows']}`",
                f"- Bytes: `{result['bytes']}`",
                f"- Active compact tokens (gate): `{result['total_tokens']}`",
                f"- Storage/tool proxy tokens excluded from gate: `{result['compact_storage_proxy_tokens']}`",
                f"- All proxy tokens: `{result['compact_proxy_tokens_all']}`",
                f"- Raw JSONL tokens: `{result['raw_json_tokens']}`",
                f"- Parse errors: `{len(result['parse_errors'])}`",
                f"- SHA-256: `{result['sha256']}`",
                f"- Content text chars: `{result['content_text_chars']}`",
                "",
                "Top row-type token totals:",
                "",
            ]
        )
        for key, value in sorted(result["row_type_tokens"].items(), key=lambda item: item[1], reverse=True)[:8]:
            lines.append(f"- `{key}`: `{value}` tokens across `{result['row_type_counts'].get(key, 0)}` rows")
        lines.append("")
        lines.extend(["Top compact proxy parts:", ""])
        for key, value in sorted(result["compact_proxy_parts"].items(), key=lambda item: item[1], reverse=True)[:8]:
            lines.append(f"- `{key}`: `{value}`")
        lines.append("")

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "summary": str(summary_path), "top_rows": str(top_rows_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sessions", nargs="+", type=Path)
    parser.add_argument("--encoding", default="o200k_base")
    parser.add_argument("--warn-total-tokens", type=int, default=180_000)
    parser.add_argument("--max-total-tokens", type=int, default=200_000)
    parser.add_argument("--hard-trigger-tokens", type=int, default=258_000)
    parser.add_argument("--top-rows", type=int, default=25)
    parser.add_argument("--evidence-stem")
    parser.add_argument("--no-evidence", action="store_true")
    args = parser.parse_args()

    results = []
    exit_code = 0
    for session in args.sessions:
        result = analyze_file(session, args.encoding, args.top_rows)
        status = status_for(
            result["total_tokens"],
            args.warn_total_tokens,
            args.max_total_tokens,
            args.hard_trigger_tokens,
            len(result["parse_errors"]),
        )
        result["status"] = status
        results.append(result)
        print(
            f"{session}: status={status} rows={result['rows']} bytes={result['bytes']} "
            f"tokens={result['total_tokens']} parse_errors={len(result['parse_errors'])}"
        )
        if status.startswith("fail"):
            exit_code = 1

    if not args.no_evidence:
        paths = write_evidence(results, args)
        print(f"evidence_json={paths['json']}")
        print(f"evidence_summary={paths['summary']}")
        print(f"evidence_top_rows={paths['top_rows']}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
