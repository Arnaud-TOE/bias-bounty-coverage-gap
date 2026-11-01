"""Assemble the public Best Bias Discovery repository in release/bias-bounty-phantom-homes/.

Only the discovery (phantom homes + nursing-home annex) is released before the leaderboard
closes; the scored pipeline (src/bbx/) is published after 31 October (decision D3).

    python scripts/make_release_discovery.py

The release has its own git history (release/ is ignored by this repository). External files
are shipped gzip-compressed (deterministic, mtime 0) so the judges reproduce the exact inputs
even if CAL FIRE or CMS update their downloads.
"""
import gzip
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = ROOT / "release" / "bias-bounty-phantom-homes"
BUCKET = "https://data.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge"
REGIONS = ["south-central-tx", "maricopa-az", "eastern-ok", "northern-ca", "eastern-wa"]
CHALLENGE_FILES = (
    [f"strata/{r}/{r}-census-tracts.parquet" for r in REGIONS]
    + [f"strata/{r}/{r}-strata-tract-table.parquet" for r in REGIONS]
    + [f"reference/{r}/{r}-overture-pois.parquet" for r in REGIONS]
    + [f"reference/{r}/{r}-sample-submission.csv" for r in REGIONS]
    + ["reference/northern-ca/northern-ca-census-acs-housing.parquet",
       "reference/northern-ca/northern-ca-overture-buildings.parquet"]
)
EXTERNAL = ["discovery/external/raw/calfire_dins/dins.csv",
            "discovery/external/raw/cms_nh/NH_ProviderInfo_Sep2026_3.csv"]
CODE = ["discovery/phantom_homes.py", "discovery/phantom_maps.py", "discovery/cms_nursing_homes.py",
        "discovery/exposure.py", "discovery/reproduce.py", "discovery/dins_footprints.py",
        "discovery/README.md", "discovery/external/SOURCES.md",
        "writeup/bias_discovery.md", "writeup/figures/phantom_by_year.png",
        "writeup/figures/phantom_case_maps.png", "writeup/pdf/bias_discovery.pdf"]
REQUIREMENTS = ["duckdb==1.5.6", "pandas==3.0.6", "numpy==2.5.4", "pyarrow==26.0.0",
                "matplotlib==3.11.2", "shapely==2.2.0", "statsmodels==0.15.0", "scipy==1.18.1"]

README = """# Phantom homes: destroyed homes still on the map

Best Bias Discovery entry for the Zindi **Bias Bounty Mapping Equity Challenge**
(Zindi user **Arnaud_TOE**, associated leaderboard submission `iu1dZ8Hf`).

Of the 6,868 structures destroyed by Northern California wildfires from 2020 to 2025 (CAL FIRE
damage inspections), **2,063 (30.0 %) are still drawn as standing buildings** in Overture
release 2026-08-19.0, each with a source date earlier than the fire. Net of chance proximity
the excess is **24.3 % (95 % CI 17.4-35.8 %, clustered by fire)**. For fires up to 2019 the
rate is 0.2 %. The write-up is `writeup/bias_discovery.md` (PDF in `writeup/pdf/`).

## Reproduce (about 2 minutes after the download)

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -I get_data.py                # challenge files (~470 MB) + the two external files, all SHA-256 checked
python -I discovery/reproduce.py     # every number, table (discovery/out/) and figure (writeup/figures/)
```

`get_data.py` downloads the challenge extract from the public Source Cooperative bucket and
decompresses the two external files shipped in `discovery/external/` (CAL FIRE DINS, CC-BY;
CMS Nursing Home Provider Information, public domain). Their original URLs and retrieval dates
are in `discovery/external/SOURCES.md`.

## Scope and compliance

- External data is used for this discovery only, as the challenge rules allow for this prize.
- No withdrawn reference layer (TIGER, Microsoft footprints, HIFLD/USGS, CBP) is read.
- The scored leaderboard pipeline is a separate code base, published after the leaderboard
  closes (31 October 2026).

## Licences

Code: MIT (`LICENSE`). Data: see `DATA_LICENCES.md`.
"""

DATA_LICENCES = """# Data licences

| Data | Licence | Where |
|---|---|---|
| Overture Maps 2026-08-19.0 (buildings, places), challenge extract | ODbL 1.0 / CDLA Permissive 2.0 per theme (Overture) | downloaded by `get_data.py` |
| Challenge strata tables, tract geometry (TIGER 2025), ACS | public domain (US Government) and per-source terms in the bucket README | downloaded by `get_data.py` |
| CAL FIRE Damage Inspection (DINS) | Creative Commons Attribution | `discovery/external/calfire_dins.csv.gz` |
| CMS Nursing Home Provider Information | US Government work, public | `discovery/external/cms_nh.csv.gz` |

Derived tables in `discovery/out/` combine these sources and keep their attribution.
"""

MIT = """MIT License

Copyright (c) 2026 Arnaud_TOE (Zindi)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

GET_DATA = '''"""Fetch the inputs of the phantom-homes discovery and check every SHA-256.

    python -I get_data.py
"""
import gzip
import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUCKET = "{bucket}"
CHALLENGE = {challenge}
EXTERNAL = {external}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    for rel, digest in CHALLENGE.items():
        dest = ROOT / "data" / "raw" / rel
        if not (dest.exists() and sha256(dest) == digest):
            dest.parent.mkdir(parents=True, exist_ok=True)
            print("downloading", rel, flush=True)
            # The bucket's CDN refuses urllib's default User-Agent.
            req = urllib.request.Request(f"{{BUCKET}}/{{rel}}", headers={{"User-Agent": "Mozilla/5.0"}})
            with urllib.request.urlopen(req) as r, open(dest, "wb") as out:
                shutil.copyfileobj(r, out, 1 << 22)
        if sha256(dest) != digest:
            print("checksum mismatch for", rel)
            return 1
    for packed, (target, digest) in EXTERNAL.items():
        dest = ROOT / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(ROOT / packed, "rb") as src, open(dest, "wb") as out:
            shutil.copyfileobj(src, out)
        if sha256(dest) != digest:
            print("checksum mismatch for", target)
            return 1
    print("all inputs present and verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

GITIGNORE = """data/
discovery/external/raw/
discovery/out/*.parquet
writeup/pdf/*.html
__pycache__/
.venv/
"""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    REL.mkdir(parents=True, exist_ok=True)
    for rel in CODE:
        dest = REL / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dest)
    (REL / "discovery" / "out").mkdir(parents=True, exist_ok=True)
    for f in sorted((ROOT / "discovery" / "out").glob("*.csv")):
        shutil.copyfile(f, REL / "discovery" / "out" / f.name)

    manifest = {}
    for line in (ROOT / "data" / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(None, 1)
        manifest[rel.strip()] = digest
    challenge = {rel: manifest[rel] for rel in CHALLENGE_FILES}
    for rel, digest in challenge.items():
        assert sha256(ROOT / "data" / "raw" / rel) == digest, rel

    external = {}
    for rel, packed in zip(EXTERNAL, ["discovery/external/calfire_dins.csv.gz",
                                      "discovery/external/cms_nh.csv.gz"]):
        with open(ROOT / rel, "rb") as src, open(REL / packed, "wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as gz:
                shutil.copyfileobj(src, gz)
        external[packed] = (rel, sha256(ROOT / rel))

    (REL / "README.md").write_text(README, encoding="utf-8")
    (REL / "DATA_LICENCES.md").write_text(DATA_LICENCES, encoding="utf-8")
    (REL / "LICENSE").write_text(MIT, encoding="utf-8")
    (REL / "requirements.txt").write_text("\n".join(REQUIREMENTS) + "\n", encoding="utf-8")
    (REL / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (REL / "get_data.py").write_text(GET_DATA.format(
        bucket=BUCKET, challenge=repr(challenge), external=repr(external)), encoding="utf-8")
    # The discovery README points at the scored pipeline, which is not part of this release.
    readme = REL / "discovery" / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8").replace(
        "the scored\npipeline (`src/bbx/`) never reads them (I/O guard in `src/bbx/io.py`).",
        "the scored\nleaderboard pipeline, published separately after 31 October, never reads them."),
        encoding="utf-8")
    total = sum(p.stat().st_size for p in REL.rglob("*") if p.is_file() and ".git" not in p.parts)
    print(f"release written to {REL} ({total / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
