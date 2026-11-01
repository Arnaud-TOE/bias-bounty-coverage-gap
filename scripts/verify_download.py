"""Check local data against the bucket listing (byte counts) and write a SHA-256 manifest.

A parallel download can exit cleanly and still leave truncated files (bucket README,
"Check the byte counts"). Run after `aws s3 sync`:

    python scripts/verify_download.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
LISTING = ROOT / "data" / "bucket_listing.txt"
PREFIX = "humane-intelligence/bias-bounty-mapping-equity-challenge/"


def expected_files():
    for line in LISTING.read_text(encoding="utf-8-sig").splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        size, key = int(parts[2]), parts[3]
        rel = key.removeprefix(PREFIX)
        top = rel.split("/")[0]
        if top in {"reference", "boundaries"} or (top == "strata" and rel.endswith(".parquet")):
            yield rel, size
        elif rel == "README.md":
            yield rel, size


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    bad, manifest, total = [], [], 0
    for rel, size in sorted(expected_files()):
        local = RAW / rel
        if not local.exists():
            bad.append(f"MISSING {rel}")
            continue
        if local.stat().st_size != size:
            bad.append(f"SIZE {rel}: local {local.stat().st_size} != bucket {size}")
            continue
        total += size
        manifest.append(f"{sha256(local)}  {rel}")
    (ROOT / "data" / "MANIFEST.sha256").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(f"{len(manifest)} files OK, {total / 1e9:.2f} GB")
    for b in bad:
        print(b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
