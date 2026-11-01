#!/usr/bin/env python3
"""Build a local VM load-test chamber for a prepared Codex session sandbox.

Lane: session asset management.
Authority: `Sessions/Plans/session-jsonl-sandbox-load-test.md`.

This script creates a QEMU-oriented test directory under ignored
`Sessions/Lab/`. It copies only an already prepared sandbox `codex-home`,
creates a sparse qcow2 disk when requested, writes manual launch and guest
verification scripts, and records a manifest. It does not edit production
session files, copy auth material, promote JSONL candidates, or launch Codex.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_ROOT = ROOT / "Sessions" / "Lab" / "VM-Load-Test"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sandbox-run",
        required=True,
        help="Prepared Sessions/Lab/Codex-Session-Sandbox/<run> directory.",
    )
    parser.add_argument(
        "--stamp",
        help="Stable output directory name. Default: current local timestamp.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Parent output directory. Default: Sessions/Lab/VM-Load-Test.",
    )
    parser.add_argument(
        "--disk-size",
        default="40G",
        help="Sparse qcow2 disk size to create. Default: 40G.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned paths and checks without writing files.",
    )
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Create VM load-test chamber files. Does not launch the VM.",
    )
    args = parser.parse_args()
    if not args.dry_run and not args.prepare:
        raise SystemExit("Choose --dry-run or --prepare.")
    return args


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command_probe(name: str, args: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError:
        return {"name": name, "command": args, "found": False, "returncode": None, "stdout": "", "stderr": "missing"}
    return {
        "name": name,
        "command": args,
        "found": True,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def inspect_jsonl(path: Path) -> dict[str, Any]:
    rows = 0
    parse_errors = 0
    largest_line_bytes = 0
    with path.open("rb") as handle:
        for raw in handle:
            rows += 1
            largest_line_bytes = max(largest_line_bytes, len(raw))
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                parse_errors += 1
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "rows": rows,
        "parse_errors": parse_errors,
        "largest_line_bytes": largest_line_bytes,
    }


def find_candidate_jsonl(codex_home: Path) -> Path:
    session_dir = codex_home / "sessions"
    candidates = sorted(session_dir.glob("**/*.jsonl"))
    if len(candidates) != 1:
        raise SystemExit(f"Expected exactly 1 candidate JSONL under {session_dir}, found {len(candidates)}.")
    return candidates[0]


def chmod_exec(path: Path) -> None:
    current = path.stat().st_mode
    path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_launch_script(path: Path, disk_path: Path, share_path: Path) -> None:
    script = f"""#!/usr/bin/env bash
set -euo pipefail

ISO_PATH="${{1:-}}"
if [[ -z "$ISO_PATH" ]]; then
  cat <<'EOF'
Usage:
  ./launch-qemu.sh /path/to/ubuntu-desktop.iso

This chamber is intended for a manual Ubuntu Desktop live or install VM test.
The existing SystemRescue ISO can prove the QEMU path, but it does not prove
VS Code or Codex extension session loading.

No Codex launch is performed by this script. It starts only QEMU.
EOF
  exit 2
fi

if [[ ! -f "$ISO_PATH" ]]; then
  echo "ISO not found: $ISO_PATH" >&2
  exit 3
fi

ACCEL="tcg,thread=multi"
CPU_MODEL="max"
if [[ -r /dev/kvm && -w /dev/kvm ]]; then
  ACCEL="kvm"
  CPU_MODEL="host"
fi

exec qemu-system-x86_64 \\
  -name codex-round7-loadtest \\
  -machine q35,accel="$ACCEL" \\
  -cpu "$CPU_MODEL" \\
  -smp 2 \\
  -m 4096 \\
  -drive file="{disk_path}",format=qcow2,if=virtio \\
  -cdrom "$ISO_PATH" \\
  -boot d \\
  -device virtio-vga \\
  -display gtk,gl=off \\
  -nic user,model=virtio-net-pci \\
  -virtfs local,path="{share_path}",mount_tag=codexshare,security_model=mapped-xattr,id=codexshare \\
  -device virtio-rng-pci
"""
    path.write_text(script, encoding="utf-8")
    chmod_exec(path)


def write_guest_scripts(share_path: Path, candidate_stats: dict[str, Any]) -> None:
    readme = f"""# Round 7 VM Load-Test Share

This share contains a copied Codex session candidate only. It contains no
`auth.json`, no credentials, and no production session file.

Candidate rows: `{candidate_stats["rows"]}`.
Candidate bytes: `{candidate_stats["bytes"]}`.
Candidate parse errors: `{candidate_stats["parse_errors"]}`.
Candidate SHA-256:

```text
{candidate_stats["sha256"]}
```

Inside an Ubuntu guest, mount the share:

```bash
sudo mkdir -p /mnt/codexshare
sudo mount -t 9p -o trans=virtio,version=9p2000.L codexshare /mnt/codexshare
bash /mnt/codexshare/guest-verify-round7.sh
```

For an isolated Codex UI test, copy only the `sessions` folder into the guest
home:

```bash
mkdir -p "$HOME/.codex"
rsync -a /mnt/codexshare/codex-home/sessions/ "$HOME/.codex/sessions/"
```

Then install or launch VS Code and Codex manually in the guest. If login is
needed, allow it to write only inside the guest disk unless the operator
explicitly approves another credential path.
"""
    (share_path / "README-FIRST.md").write_text(readme, encoding="utf-8")

    verifier = f"""#!/usr/bin/env bash
set -euo pipefail

ROOT="${{1:-/mnt/codexshare}}"
CANDIDATE="$ROOT/codex-home/sessions/2026/04/26/{Path(candidate_stats["path"]).name}"

echo "guest_share=$ROOT"
echo "candidate=$CANDIDATE"
test -f "$CANDIDATE"

BYTES="$(wc -c < "$CANDIDATE")"
ROWS="$(wc -l < "$CANDIDATE")"
SHA="$(sha256sum "$CANDIDATE" | awk '{{print $1}}')"

echo "candidate_bytes=$BYTES"
echo "candidate_rows=$ROWS"
echo "candidate_sha256=$SHA"

test "$BYTES" = "{candidate_stats["bytes"]}"
test "$ROWS" = "{candidate_stats["rows"]}"
test "$SHA" = "{candidate_stats["sha256"]}"

if find "$ROOT/codex-home" -maxdepth 2 -name 'auth.json' -print -quit | grep -q .; then
  echo "auth_file_present=1" >&2
  exit 4
fi

echo "auth_file_present=0"
echo "round7_candidate_share_verification=pass"
"""
    verifier_path = share_path / "guest-verify-round7.sh"
    verifier_path.write_text(verifier, encoding="utf-8")
    chmod_exec(verifier_path)


def build_manifest(
    *,
    output_dir: Path,
    sandbox_run: Path,
    codex_home_source: Path,
    codex_home_copy: Path,
    candidate_stats: dict[str, Any],
    disk_path: Path,
    share_path: Path,
    disk_size: str,
    prepared: bool,
) -> dict[str, Any]:
    return {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "prepared": prepared,
        "authority": "Sessions/Plans/session-jsonl-sandbox-load-test.md",
        "output_dir": str(output_dir),
        "sandbox_run": str(sandbox_run),
        "codex_home_source": str(codex_home_source),
        "codex_home_copy": str(codex_home_copy),
        "share_path": str(share_path),
        "disk_path": str(disk_path),
        "disk_size_requested": disk_size,
        "candidate": candidate_stats,
        "host": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "uid": os.getuid(),
            "groups": os.getgroups(),
        },
        "tooling": {
            "qemu": command_probe("qemu-system-x86_64", ["qemu-system-x86_64", "--version"]),
            "qemu_img": command_probe("qemu-img", ["qemu-img", "--version"]),
            "virsh": command_probe("virsh", ["virsh", "--version"]),
        },
        "safety_counts": {
            "production_session_edits": 0,
            "source_session_rewrites": 0,
            "jsonl_promotions": 0,
            "auth_file_copies": 0,
            "automatic_codex_launches": 0,
            "vm_launches": 0,
            "dropbox_payload_moves": 0,
            "permanent_deletes": 0,
        },
    }


def main() -> None:
    args = parse_args()
    sandbox_run = Path(args.sandbox_run).expanduser().resolve()
    if not sandbox_run.exists() or not sandbox_run.is_dir():
        raise SystemExit(f"Sandbox run not found: {sandbox_run}")
    codex_home_source = sandbox_run / "codex-home"
    if not codex_home_source.is_dir():
        raise SystemExit(f"Sandbox codex-home not found: {codex_home_source}")
    candidate = find_candidate_jsonl(codex_home_source)
    candidate_stats = inspect_jsonl(candidate)

    stamp = args.stamp or now_stamp()
    output_root = Path(args.output_root).expanduser().resolve()
    output_dir = output_root / stamp
    share_path = output_dir / "vm-share"
    codex_home_copy = share_path / "codex-home"
    disk_path = output_dir / "round7-loadtest.qcow2"
    manifest_path = output_dir / "manifest.json"
    receipt_path = output_dir / "vm-load-test-receipt.md"
    launch_path = output_dir / "launch-qemu.sh"

    manifest = build_manifest(
        output_dir=output_dir,
        sandbox_run=sandbox_run,
        codex_home_source=codex_home_source,
        codex_home_copy=codex_home_copy,
        candidate_stats=candidate_stats,
        disk_path=disk_path,
        share_path=share_path,
        disk_size=args.disk_size,
        prepared=False,
    )

    if args.dry_run:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        print("vm_environment_prepared: 0")
        print("vm_launches: 0")
        print("auth_file_copies: 0")
        print("production_session_edits: 0")
        return

    if output_dir.exists():
        raise SystemExit(f"VM load-test output already exists: {output_dir}")
    share_path.mkdir(parents=True)
    shutil.copytree(codex_home_source, codex_home_copy)
    write_guest_scripts(share_path, candidate_stats)
    write_launch_script(launch_path, disk_path, share_path)

    qemu_img = shutil.which("qemu-img")
    if qemu_img is None:
        raise SystemExit("qemu-img not found; cannot create sparse qcow2 disk.")
    subprocess.run([qemu_img, "create", "-f", "qcow2", str(disk_path), args.disk_size], check=True)

    manifest = build_manifest(
        output_dir=output_dir,
        sandbox_run=sandbox_run,
        codex_home_source=codex_home_source,
        codex_home_copy=codex_home_copy,
        candidate_stats=inspect_jsonl(find_candidate_jsonl(codex_home_copy)),
        disk_path=disk_path,
        share_path=share_path,
        disk_size=args.disk_size,
        prepared=True,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt = f"""# Round 7 VM Load-Test Environment Receipt

Status: environment prepared; VM not launched.

Prepared: {manifest["generated"]}

VM chamber:

```text
{output_dir}
```

Manual launch script:

```text
{launch_path}
```

Candidate copied into VM share:

```text
{codex_home_copy}
```

Candidate bytes: `{manifest["candidate"]["bytes"]}`.
Candidate rows: `{manifest["candidate"]["rows"]}`.
Candidate parse errors: `{manifest["candidate"]["parse_errors"]}`.
Candidate SHA-256:

```text
{manifest["candidate"]["sha256"]}
```

## Manual Load-Test Record

- ISO used:
- VM booted: unknown
- candidate share mounted: unknown
- guest verification passed: unknown
- VS Code launched: unknown
- Codex extension loaded: unknown
- session appeared in picker: unknown
- session opened: unknown
- new message accepted: unknown
- observed errors:
- outcome: untested

## Safety Counts

- production_session_edits: `0`
- source_session_rewrites: `0`
- jsonl_promotions: `0`
- auth_file_copies: `0`
- automatic_codex_launches: `0`
- vm_launches_by_script_builder: `0`
- dropbox_payload_moves: `0`
- permanent_deletes: `0`
"""
    receipt_path.write_text(receipt, encoding="utf-8")

    print("vm_environment_prepared: 1")
    print(f"output_dir: {output_dir}")
    print(f"vm_share: {share_path}")
    print(f"disk: {disk_path}")
    print(f"manifest: {manifest_path}")
    print(f"receipt: {receipt_path}")
    print(f"launch_script: {launch_path}")
    print("vm_launches: 0")
    print("auth_file_copies: 0")
    print("production_session_edits: 0")
    print("jsonl_promotions: 0")


if __name__ == "__main__":
    main()
