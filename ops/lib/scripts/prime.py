#!/usr/bin/env python3
"""Build a prime session candidate packet without copying raw sessions."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import socket
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
INVENTORY = ROOT / "Sessions" / "logs"
PACKET_ROOT = ROOT / "Sessions" / "Candidates"

BOOT_CANON = [
    "README.md",
    "START.md",
    "STATUS.md",
    "REVIEW.md",
    "llms.txt",
    "Sessions/README.md",
    "Sessions/INDEX.md",
    "Sessions/Plans/session-asset-management.md",
    "Sessions/Plans/session-succession-management.md",
    "Sessions/Plans/prime-session-candidate-standard.md",
    "Sessions/archives/legacy/Scripts/README.md",
    "Sessions/logs/README.md",
]

EVIDENCE_INPUTS = {
    "succession-capsule.md": INVENTORY / "codex-succession-capsule-current.md",
    "session-handoff.txt": INVENTORY / "codex-session-handoff-current.txt",
    "session-bloat-summary.txt": INVENTORY / "codex-session-bloat-analysis-summary.txt",
    "session-assets-summary.txt": INVENTORY / "codex-session-assets-summary.txt",
}

LIVE_USB_MARKER = (
    "You are running from a rescue or live-USB environment. Assume temporary "
    "local state. Do not trust persistence until verified. Mount and verify "
    "`/media/nos4r2/user_vol` before acting. Do not perform destructive repair "
    "unless the operator explicitly authorizes the specific target and action."
)


def run_text(cmd: list[str], cwd: Path = ROOT) -> tuple[str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        return "", "missing executable: " + cmd[0]
    out = proc.stdout.strip()
    err = proc.stderr.strip()
    if proc.returncode != 0 and not err:
        err = f"exit_code={proc.returncode}"
    return out, err


def git_state() -> dict[str, object]:
    branch, branch_err = run_text(["git", "branch", "--show-current"])
    head, head_err = run_text(["git", "rev-parse", "--short", "HEAD"])
    status, status_err = run_text(["git", "status", "--short", "--branch"])
    remote, remote_err = run_text(["git", "remote", "-v"])
    return {
        "branch": branch,
        "head": head,
        "status": status,
        "remote": remote,
        "errors": {
            "branch": branch_err,
            "head": head_err,
            "status": status_err,
            "remote": remote_err,
        },
    }


def command_version(label: str, cmd: list[str]) -> dict[str, str]:
    out, err = run_text(cmd)
    return {"label": label, "command": " ".join(cmd), "stdout": out, "stderr": err}


def environment_versions() -> list[dict[str, str]]:
    return [
        {
            "label": "python",
            "command": "platform/python",
            "stdout": platform.python_version(),
            "stderr": "",
        },
        command_version("git", ["git", "--version"]),
        command_version("code", ["code", "--version"]),
        command_version("codex", ["codex", "--version"]),
        command_version("uname", ["uname", "-a"]),
        command_version("lsb_release", ["lsb_release", "-a"]),
    ]


def read_optional(path: Path, limit: int | None = None) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if limit is not None and len(text) > limit:
        return text[:limit] + "\n\n[truncated]\n"
    return text


def compute_fit(profile: str, missing_inputs: list[str], git_dirty: bool, codex_version_missing: bool) -> dict[str, object]:
    components = {
        "operator_fit": 20,
        "repo_fit": 20,
        "moment_fit": 20,
        "tool_fit": 15,
        "safety_fit": 15,
        "promotion_readiness": 0,
    }
    if missing_inputs:
        components["moment_fit"] = max(0, components["moment_fit"] - (5 * len(missing_inputs)))
    if git_dirty:
        components["repo_fit"] = max(0, components["repo_fit"] - 5)
    if codex_version_missing:
        components["tool_fit"] = max(0, components["tool_fit"] - 5)
    if profile == "live-usb":
        components["promotion_readiness"] = 5
    else:
        components["promotion_readiness"] = 5
    score = sum(components.values())
    return {
        "score": score,
        "components": components,
        "prime_candidate": score >= 80,
        "note": "Packet only. JSONL derivative promotion still requires sandbox load test and operator approval.",
    }


def write_packet(profile: str, out_dir: Path, git: dict[str, object]) -> dict[str, object]:
    git_dirty = any(
        line and not line.startswith("## ")
        for line in str(git.get("status", "")).splitlines()
    )
    out_dir.mkdir(parents=True, exist_ok=False)
    missing_inputs: list[str] = []
    copied_inputs: list[str] = []

    for out_name, source in EVIDENCE_INPUTS.items():
        if source.exists():
            shutil.copy2(source, out_dir / out_name)
            copied_inputs.append(str(source.relative_to(ROOT)))
        else:
            missing_inputs.append(str(source.relative_to(ROOT)))
            (out_dir / out_name).write_text(
                f"# Missing Evidence\n\nExpected source was absent: `{source}`\n",
                encoding="utf-8",
            )

    versions = environment_versions()
    codex_version_missing = any(
        row["label"] == "codex" and row["stderr"].startswith("missing executable")
        for row in versions
    )
    fit = compute_fit(profile, missing_inputs, git_dirty, codex_version_missing)

    generated = datetime.now().replace(microsecond=0).isoformat()
    manifest = {
        "generated": generated,
        "profile": profile,
        "repo_root": str(ROOT),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "boot_canon": BOOT_CANON,
        "copied_inputs": copied_inputs,
        "missing_inputs": missing_inputs,
        "git": git,
        "environment_versions": versions,
        "fit": fit,
        "live_usb_marker": LIVE_USB_MARKER if profile == "live-usb" else "",
        "source_session_edits": 0,
        "raw_session_copies": 0,
        "auth_file_copies": 0,
        "payload_moves": 0,
        "permanent_deletes": 0,
    }

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    version_lines = []
    for row in versions:
        version_lines.append(f"## {row['label']}")
        version_lines.append(f"command: `{row['command']}`")
        version_lines.append("")
        version_lines.append("stdout:")
        version_lines.append("```text")
        version_lines.append(row["stdout"] or "")
        version_lines.append("```")
        version_lines.append("")
        version_lines.append("stderr:")
        version_lines.append("```text")
        version_lines.append(row["stderr"] or "")
        version_lines.append("```")
        version_lines.append("")
    (out_dir / "environment-versions.txt").write_text("\n".join(version_lines), encoding="utf-8")

    readme = [
        "# Prime Session Candidate Packet",
        "",
        f"Generated: {generated}",
        f"Profile: `{profile}`",
        f"Repo root: `{ROOT}`",
        f"Fit score: `{fit['score']}`",
        f"Prime candidate: `{fit['prime_candidate']}`",
        "",
        "## Authority",
        "Repo canon is memory. The capsule is awakening. The session candidate is acceleration. The operator is authority.",
        "",
        "## Contents",
        "- `manifest.json`",
        "- `CHECKLIST.md`",
        "- `succession-capsule.md`",
        "- `session-handoff.txt`",
        "- `session-bloat-summary.txt`",
        "- `session-assets-summary.txt`",
        "- `environment-versions.txt`",
        "",
        "## Safety",
        "- Raw session copies in this packet: `0`",
        "- Auth file copies in this packet: `0`",
        "- Source-session edits performed: `0`",
        "- Payload moves performed: `0`",
        "- Permanent deletes performed: `0`",
        "",
    ]
    if profile == "live-usb":
        readme.extend(["## Live-USB Marker", "", LIVE_USB_MARKER, ""])
    (out_dir / "README.md").write_text("\n".join(readme), encoding="utf-8")

    checklist = [
        "# Prime Candidate Checklist",
        "",
        "- [ ] Read `README.md`.",
        "- [ ] Read `manifest.json`.",
        "- [ ] Read `succession-capsule.md`.",
        "- [ ] Read `session-handoff.txt`.",
        "- [ ] Verify repo path exists.",
        "- [ ] Verify Git state against manifest.",
        "- [ ] Verify no auth files are present in this packet.",
        "- [ ] Verify no raw session file is present in this packet.",
        "- [ ] Decide whether this packet is sufficient without JSONL derivative work.",
        "- [ ] If JSONL derivative work is needed, preserve raw source first.",
        "- [ ] Sandbox load-test any derivative before promotion.",
        "- [ ] Record operator approval before any derivative becomes a prime seed.",
        "",
        "Current packet evidence:",
        "",
        f"- Fit score: `{fit['score']}`",
        f"- Prime candidate: `{fit['prime_candidate']}`",
        f"- Missing evidence inputs: `{len(missing_inputs)}`",
        f"- Git dirty at packet build: `{git_dirty}`",
        f"- Codex version evidence missing: `{codex_version_missing}`",
        "",
    ]
    (out_dir / "CHECKLIST.md").write_text("\n".join(checklist), encoding="utf-8")

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=["normal", "live-usb", "both"],
        default="normal",
        help="Candidate packet profile to build.",
    )
    parser.add_argument("--stamp", default=datetime.now().strftime("%Y%m%d-%H%M%S"))
    parser.add_argument(
        "--current-only",
        action="store_true",
        help="Refresh only current-<profile> packet directories without retaining stamped packet directories.",
    )
    args = parser.parse_args()

    profiles = ["normal", "live-usb"] if args.profile == "both" else [args.profile]
    PACKET_ROOT.mkdir(parents=True, exist_ok=True)
    base_git = git_state()
    manifests = []
    for profile in profiles:
        current_dir = PACKET_ROOT / f"current-{profile}"
        if args.current_only:
            out_dir = current_dir
            if out_dir.exists() or out_dir.is_symlink():
                if out_dir.is_dir() and not out_dir.is_symlink():
                    shutil.rmtree(out_dir)
                else:
                    out_dir.unlink()
            manifest = write_packet(profile, out_dir, base_git)
        else:
            out_dir = PACKET_ROOT / f"{args.stamp}-{profile}"
            manifest = write_packet(profile, out_dir, base_git)
            if current_dir.exists() or current_dir.is_symlink():
                if current_dir.is_dir() and not current_dir.is_symlink():
                    shutil.rmtree(current_dir)
                else:
                    current_dir.unlink()
            shutil.copytree(out_dir, current_dir)
        manifests.append((profile, out_dir, manifest))

    print(f"packets_built: {len(manifests)}")
    for profile, out_dir, manifest in manifests:
        print(f"{profile}: {out_dir}")
        print(f"{profile}_fit_score: {manifest['fit']['score']}")
        print(f"{profile}_prime_candidate: {manifest['fit']['prime_candidate']}")
    print("raw_session_copies: 0")
    print("auth_file_copies: 0")
    print("source_session_edits: 0")
    print("payload_moves: 0")
    print("permanent_deletes: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
