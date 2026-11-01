#!/usr/bin/env python3
"""Build an analysis-only Codex JSONL copy with oldest image payloads externalized.

Lane: session reduction and pruning.

This script operates on copied artifacts. It does not edit live sessions, rewrite
source sessions, copy auth files, launch Codex, or promote derivatives.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
LAB = ROOT / "Sessions" / "Lab" / "Image-Externalization"
EVIDENCE = ROOT / "Sessions" / "logs"


IMAGE_KEYS = ("image_url", "data", "b64_json", "base64", "bytes")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Source JSONL to read. This must be a copied or lab source.")
    parser.add_argument("--destination", help="Destination derivative JSONL. Default: lab path under Sessions/Lab.")
    parser.add_argument("--stamp", help="Stable stamp for repeatable output. Default: local timestamp.")
    parser.add_argument(
        "--max-image-bytes",
        type=int,
        default=250 * 1024 * 1024,
        help="Oldest image bytes to externalize. Default: 250 MiB.",
    )
    parser.add_argument(
        "--write-external-images",
        action="store_true",
        help="Write decoded/opaque image payloads under the lab artifact directory.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Measure only; do not write destination JSONL.")
    return parser.parse_args()


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def encoded_bytes(value: Any) -> bytes:
    if isinstance(value, str):
        return value.encode("utf-8")
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def decode_data_url(value: str) -> tuple[str, bytes] | None:
    if not value.startswith("data:") or "," not in value:
        return None
    header, payload = value.split(",", 1)
    if ";base64" not in header:
        return None
    media_type = header[5:].split(";", 1)[0] or "application/octet-stream"
    try:
        return media_type, base64.b64decode(payload, validate=False)
    except Exception:
        return None


def extension_for_media(media_type: str) -> str:
    lower = media_type.lower()
    if "png" in lower:
        return ".png"
    if "jpeg" in lower or "jpg" in lower:
        return ".jpg"
    if "webp" in lower:
        return ".webp"
    if "gif" in lower:
        return ".gif"
    return ".bin"


def find_image_payload(block: dict[str, Any]) -> tuple[str, Any] | None:
    if block.get("type") != "input_image":
        return None
    for key in IMAGE_KEYS:
        if key in block:
            return key, block[key]
    return None


def replacement_history(payload: Any) -> list[Any] | None:
    if not isinstance(payload, dict):
        return None
    history = payload.get("replacement_history")
    return history if isinstance(history, list) else None


def iter_content_blocks(history_item: Any) -> list[dict[str, Any]]:
    if not isinstance(history_item, dict):
        return []
    content = history_item.get("content")
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


def iter_input_image_blocks(value: Any, path: str = "$") -> list[tuple[str, dict[str, Any]]]:
    """Return direct input_image dictionaries anywhere in a JSON row.

    The original externalizer only handled images embedded in compacted
    replacement history. Later session rows also carry direct input_image blocks
    under response_item payloads. Those blocks are loader-visible and must be
    treated with the same placeholder and receipt policy.
    """
    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, dict):
        if value.get("type") == "input_image" and value.get("externalized") is not True:
            found.append((path, value))
        for key, child in value.items():
            found.extend(iter_input_image_blocks(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(iter_input_image_blocks(child, f"{path}[{index}]"))
    return found


def inspect_jsonl(path: Path) -> dict[str, Any]:
    line_count = 0
    parse_errors = 0
    largest_line_bytes = 0
    largest_line_number = 0
    with path.open("rb") as handle:
        for raw in handle:
            line_count += 1
            raw_len = len(raw)
            if raw_len > largest_line_bytes:
                largest_line_bytes = raw_len
                largest_line_number = line_count
            try:
                json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError):
                parse_errors += 1
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "line_count": line_count,
        "parse_errors": parse_errors,
        "largest_line_bytes": largest_line_bytes,
        "largest_line_number": largest_line_number,
        "sha256": sha256_file(path),
    }


def placeholder(
    *,
    source_line: int,
    history_index: int,
    block_index: int,
    source_path: str,
    source_row_type: str,
    key: str,
    original_json_bytes: int,
    original_payload_bytes: int,
    digest: str,
    artifact_path: str,
    artifact_sha256: str,
) -> dict[str, Any]:
    return {
        "type": "input_image",
        "externalized_by": "Sessions/ops/lib/scripts/images.py",
        "externalized": True,
        "source_line": source_line,
        "history_index": history_index,
        "block_index": block_index,
        "source_path": source_path,
        "source_row_type": source_row_type,
        "original_key": key,
        "original_json_bytes": original_json_bytes,
        "original_payload_bytes": original_payload_bytes,
        "sha256": digest,
        "artifact_path": artifact_path,
        "artifact_sha256": artifact_sha256,
        "load_candidate_status": "sandbox_experiment_only",
    }


def write_external_artifact(
    artifacts_dir: Path,
    digest: str,
    payload_value: Any,
    payload_bytes: bytes,
    source_line: int,
    history_index: int,
    block_index: int,
    source_path: str,
    source_row_type: str,
) -> tuple[str, int, str]:
    decoded = decode_data_url(payload_value) if isinstance(payload_value, str) else None
    if decoded:
        media_type, data = decoded
        suffix = extension_for_media(media_type)
        artifact_path = artifacts_dir / f"{digest}{suffix}"
        artifact_path.write_bytes(data)
        return str(artifact_path.relative_to(ROOT)), len(data), sha256_bytes(data)
    artifact_path = artifacts_dir / f"{digest}.payload"
    artifact_path.write_bytes(payload_bytes)
    meta = {
        "source_line": source_line,
        "history_index": history_index,
        "block_index": block_index,
        "source_path": source_path,
        "source_row_type": source_row_type,
        "stored_as": "opaque_payload",
    }
    artifact_path.with_suffix(artifact_path.suffix + ".json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return str(artifact_path.relative_to(ROOT)), len(payload_bytes), sha256_bytes(payload_bytes)


def externalize(args: argparse.Namespace) -> dict[str, Any]:
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise SystemExit(f"Source not found: {source}")

    stamp = args.stamp or now_stamp()
    run_root = LAB / stamp
    destination = Path(args.destination).expanduser().resolve() if args.destination else run_root / source.name
    artifacts_dir = run_root / "externalized-images"
    evidence_prefix = EVIDENCE / f"codex-session-image-externalization-{stamp}"

    if not args.dry_run:
        if destination.exists():
            raise SystemExit(f"Destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=False)
        if args.write_external_images:
            artifacts_dir.mkdir(parents=True, exist_ok=False)
        else:
            run_root.mkdir(parents=True, exist_ok=False)

    source_start = source.stat()
    counts: dict[str, Any] = {
        "lines_read": 0,
        "lines_written": 0,
        "parse_errors": 0,
        "compacted_rows_seen": 0,
        "direct_input_image_blocks_seen": 0,
        "direct_input_image_blocks_externalized": 0,
        "input_image_blocks_seen": 0,
        "input_image_json_bytes_seen": 0,
        "input_image_payload_bytes_seen": 0,
        "input_image_blocks_externalized": 0,
        "input_image_json_bytes_externalized": 0,
        "input_image_payload_bytes_externalized": 0,
        "placeholder_json_bytes_written": 0,
        "external_artifacts_written": 0,
        "external_artifact_bytes_written": 0,
        "external_artifact_unique_paths": 0,
        "external_artifact_unique_bytes_on_disk": 0,
        "production_session_edits": 0,
        "source_session_rewrites": 0,
        "auth_files_copied": 0,
        "jsonl_derivatives_promoted": 0,
        "automatic_codex_launches": 0,
    }
    rows: list[dict[str, Any]] = []
    artifact_paths_seen: set[str] = set()

    writer = None
    if not args.dry_run:
        writer = destination.open("w", encoding="utf-8", newline="\n")
    try:
        with source.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, 1):
                counts["lines_read"] += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    counts["parse_errors"] += 1
                    if writer is not None:
                        writer.write(line)
                        counts["lines_written"] += 1
                    continue

                if isinstance(row, dict) and row.get("type") == "compacted":
                    counts["compacted_rows_seen"] += 1
                    history = replacement_history(row.get("payload"))
                    if history is not None:
                        for history_index, history_item in enumerate(history):
                            for block_index, block in enumerate(iter_content_blocks(history_item)):
                                found = find_image_payload(block)
                                if not found:
                                    continue
                                key, payload_value = found
                                block_json_bytes = json_bytes(block)
                                payload_blob = encoded_bytes(payload_value)
                                payload_byte_count = len(payload_blob)
                                counts["input_image_blocks_seen"] += 1
                                counts["input_image_json_bytes_seen"] += block_json_bytes
                                counts["input_image_payload_bytes_seen"] += payload_byte_count

                                should_externalize = (
                                    counts["input_image_json_bytes_externalized"] < args.max_image_bytes
                                )
                                if not should_externalize:
                                    continue

                                digest = sha256_bytes(payload_blob)
                                artifact_path = ""
                                artifact_bytes = 0
                                artifact_sha256 = ""
                                if args.write_external_images and not args.dry_run:
                                    artifact_path, artifact_bytes, artifact_sha256 = write_external_artifact(
                                        artifacts_dir,
                                        digest,
                                        payload_value,
                                        payload_blob,
                                        line_number,
                                        history_index,
                                        block_index,
                                        f"$.payload.replacement_history[{history_index}].content[{block_index}]",
                                        str(row.get("type", "")),
                                    )
                                    counts["external_artifacts_written"] += 1
                                    counts["external_artifact_bytes_written"] += artifact_bytes
                                    if artifact_path not in artifact_paths_seen:
                                        artifact_paths_seen.add(artifact_path)
                                        counts["external_artifact_unique_paths"] += 1
                                        counts["external_artifact_unique_bytes_on_disk"] += artifact_bytes

                                new_block = placeholder(
                                    source_line=line_number,
                                    history_index=history_index,
                                    block_index=block_index,
                                    source_path=f"$.payload.replacement_history[{history_index}].content[{block_index}]",
                                    source_row_type=str(row.get("type", "")),
                                    key=key,
                                    original_json_bytes=block_json_bytes,
                                    original_payload_bytes=payload_byte_count,
                                    digest=digest,
                                    artifact_path=artifact_path,
                                    artifact_sha256=artifact_sha256,
                                )
                                placeholder_bytes = json_bytes(new_block)
                                block.clear()
                                block.update(new_block)
                                counts["input_image_blocks_externalized"] += 1
                                counts["input_image_json_bytes_externalized"] += block_json_bytes
                                counts["input_image_payload_bytes_externalized"] += payload_byte_count
                                counts["placeholder_json_bytes_written"] += placeholder_bytes
                                rows.append(
                                    {
                                        "source_line": line_number,
                                        "history_index": history_index,
                                        "block_index": block_index,
                                        "source_path": f"$.payload.replacement_history[{history_index}].content[{block_index}]",
                                        "source_row_type": str(row.get("type", "")),
                                        "original_key": key,
                                        "original_json_bytes": block_json_bytes,
                                        "original_payload_bytes": payload_byte_count,
                                        "placeholder_json_bytes": placeholder_bytes,
                                        "sha256": digest,
                                        "artifact_path": artifact_path,
                                        "artifact_sha256": artifact_sha256,
                                    }
                                )

                if isinstance(row, dict):
                    for direct_index, (source_path, block) in enumerate(iter_input_image_blocks(row)):
                        if source_path.startswith("$.payload.replacement_history"):
                            continue
                        found = find_image_payload(block)
                        if not found:
                            continue
                        key, payload_value = found
                        block_json_bytes = json_bytes(block)
                        payload_blob = encoded_bytes(payload_value)
                        payload_byte_count = len(payload_blob)
                        counts["direct_input_image_blocks_seen"] += 1
                        counts["input_image_blocks_seen"] += 1
                        counts["input_image_json_bytes_seen"] += block_json_bytes
                        counts["input_image_payload_bytes_seen"] += payload_byte_count

                        should_externalize = counts["input_image_json_bytes_externalized"] < args.max_image_bytes
                        if not should_externalize:
                            continue

                        digest = sha256_bytes(payload_blob)
                        artifact_path = ""
                        artifact_bytes = 0
                        artifact_sha256 = ""
                        if args.write_external_images and not args.dry_run:
                            artifact_path, artifact_bytes, artifact_sha256 = write_external_artifact(
                                artifacts_dir,
                                digest,
                                payload_value,
                                payload_blob,
                                line_number,
                                -1,
                                direct_index,
                                source_path,
                                str(row.get("type", "")),
                            )
                            counts["external_artifacts_written"] += 1
                            counts["external_artifact_bytes_written"] += artifact_bytes
                            if artifact_path not in artifact_paths_seen:
                                artifact_paths_seen.add(artifact_path)
                                counts["external_artifact_unique_paths"] += 1
                                counts["external_artifact_unique_bytes_on_disk"] += artifact_bytes

                        new_block = placeholder(
                            source_line=line_number,
                            history_index=-1,
                            block_index=direct_index,
                            source_path=source_path,
                            source_row_type=str(row.get("type", "")),
                            key=key,
                            original_json_bytes=block_json_bytes,
                            original_payload_bytes=payload_byte_count,
                            digest=digest,
                            artifact_path=artifact_path,
                            artifact_sha256=artifact_sha256,
                        )
                        placeholder_bytes = json_bytes(new_block)
                        block.clear()
                        block.update(new_block)
                        counts["direct_input_image_blocks_externalized"] += 1
                        counts["input_image_blocks_externalized"] += 1
                        counts["input_image_json_bytes_externalized"] += block_json_bytes
                        counts["input_image_payload_bytes_externalized"] += payload_byte_count
                        counts["placeholder_json_bytes_written"] += placeholder_bytes
                        rows.append(
                            {
                                "source_line": line_number,
                                "history_index": -1,
                                "block_index": direct_index,
                                "source_path": source_path,
                                "source_row_type": str(row.get("type", "")),
                                "original_key": key,
                                "original_json_bytes": block_json_bytes,
                                "original_payload_bytes": payload_byte_count,
                                "placeholder_json_bytes": placeholder_bytes,
                                "sha256": digest,
                                "artifact_path": artifact_path,
                                "artifact_sha256": artifact_sha256,
                            }
                        )

                output_line = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                if writer is not None:
                    writer.write(output_line)
                    counts["lines_written"] += 1
    finally:
        if writer is not None:
            writer.close()

    source_end = source.stat()
    destination_stats = inspect_jsonl(destination) if destination.exists() else {}
    estimated_json_savings = (
        counts["input_image_json_bytes_externalized"] - counts["placeholder_json_bytes_written"]
    )
    summary = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "dry_run": args.dry_run,
        "source": str(source),
        "destination": str(destination),
        "stamp": stamp,
        "max_image_bytes": args.max_image_bytes,
        "write_external_images": args.write_external_images,
        "source_bytes_at_start": source_start.st_size,
        "source_bytes_at_end": source_end.st_size,
        "source_changed_during_scan": (
            source_start.st_size != source_end.st_size or source_start.st_mtime_ns != source_end.st_mtime_ns
        ),
        "source_sha256": sha256_file(source),
        "destination_stats": destination_stats,
        "counts": counts,
        "estimated_json_byte_savings": estimated_json_savings,
        "actual_destination_byte_delta": (
            source_end.st_size - destination_stats.get("bytes", source_end.st_size)
            if destination_stats
            else 0
        ),
        "artifact_root": str(run_root.relative_to(ROOT)) if run_root.exists() else "",
        "doctrine": {
            "active_session_reducer_authorized": False,
            "production_session_edits": 0,
            "source_session_rewrites": 0,
            "jsonl_derivatives_promoted": 0,
            "load_candidate_status": "sandbox_experiment_only",
        },
    }

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    json_path = evidence_prefix.with_suffix(".json")
    csv_path = EVIDENCE / f"codex-session-image-externalization-{stamp}.csv"
    summary_path = EVIDENCE / f"codex-session-image-externalization-{stamp}-summary.txt"
    current_json = EVIDENCE / "codex-session-image-externalization-current.json"
    current_csv = EVIDENCE / "codex-session-image-externalization-current.csv"
    current_summary = EVIDENCE / "codex-session-image-externalization-summary.txt"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    current_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "source_line",
            "history_index",
            "block_index",
            "source_path",
            "source_row_type",
            "original_key",
            "original_json_bytes",
            "original_payload_bytes",
            "placeholder_json_bytes",
            "sha256",
            "artifact_path",
            "artifact_sha256",
        ]
        writer_csv = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer_csv.writeheader()
        writer_csv.writerows(rows)
    current_csv.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")

    summary_text = [
        "Codex Session Image Externalization",
        f"generated: {summary['generated']}",
        f"source: {source}",
        f"destination: {destination}",
        f"dry_run: {args.dry_run}",
        f"source_changed_during_scan: {summary['source_changed_during_scan']}",
        "",
        "Counts:",
        f"- compacted_rows_seen: {counts['compacted_rows_seen']}",
        f"- direct_input_image_blocks_seen: {counts['direct_input_image_blocks_seen']}",
        f"- direct_input_image_blocks_externalized: {counts['direct_input_image_blocks_externalized']}",
        f"- input_image_blocks_seen: {counts['input_image_blocks_seen']}",
        f"- input_image_json_bytes_seen: {counts['input_image_json_bytes_seen']}",
        f"- input_image_blocks_externalized: {counts['input_image_blocks_externalized']}",
        f"- input_image_json_bytes_externalized: {counts['input_image_json_bytes_externalized']}",
        f"- placeholder_json_bytes_written: {counts['placeholder_json_bytes_written']}",
        f"- estimated_json_byte_savings: {estimated_json_savings}",
        f"- actual_destination_byte_delta: {summary['actual_destination_byte_delta']}",
        "",
        "Doctrine:",
        "- production_session_edits: 0",
        "- source_session_rewrites: 0",
        "- jsonl_derivatives_promoted: 0",
        "- active_session_reducer_authorized: False",
    ]
    summary_path.write_text("\n".join(summary_text) + "\n", encoding="utf-8")
    current_summary.write_text("\n".join(summary_text) + "\n", encoding="utf-8")

    return summary


def main() -> None:
    args = parse_args()
    summary = externalize(args)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
