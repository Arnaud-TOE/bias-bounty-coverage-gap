"""Assemble the public repository of the scored pipeline in release/bias-bounty-coverage-gap/ (decision D3).

    python scripts/make_release_pipeline.py

Copies the code, the tests, the data checksums, every submitted file with its log, the decision log, the audit
plan, the working journal (French; e-mail addresses removed) and the Best Documentation write-up. Raw challenge
data are not copied: README.md explains how to download them. The release has its own git history (release/ is
ignored by this repository); publishing it is a separate, manual step.
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = ROOT / "release" / "bias-bounty-coverage-gap"
SCRIPTS = ["build_features.py", "build_uncounted_majors.py", "build_bld_src_dates.py", "verify_download.py",
           "reproduce.py", "make_finals.py", "make_f5.py", "finalize_31.py", "make_doc_figures.py", "build_pdf.py",
           "make_structural_v9L.py", "make_blend_check.py", "make_cbp4.py", "make_release_pipeline.py"]
DOCS = ["decisions.md", "05_plan_audit.md", "journal.md", "reproduction_report_2026-11-01.md", "01_analyse_challenge.md", "02_plan_de_travail.md",
        "03_revue_litterature.md", "04_recherche_2026-10-22.md"]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")

README = """# Coverage-gap scores without labels

Scored pipeline of Zindi user **Arnaud_TOE** for the **Bias Bounty Mapping Equity Challenge** (Humane Intelligence,
Radiant Earth, Zindi; closed 31 October 2026). Best Documentation entry: `writeup/documentation.md`
(PDF in `writeup/pdf/Arnaud_TOE_Best_Documentation.pdf`).

| Final file | Zindi ID | Public RMSE | Private RMSE |
|---|---|---|---|
| `submissions/f2_blend_ridge0005_with_s07_s22.csv` (selected) | 8DPgZvCX | 0.057508 | 0.058710 (rank 36) |
| `submissions/s111_blend45_ridge0005.csv` (selected) | EboKdJHP | 0.059990 | 0.061256 |

No tract-level label exists and the reference layers were withdrawn, so nothing is trained. The pipeline:
1. models the organiser formula, drawing each unknown reference count from permitted data (`src/bbx/structural.py`);
2. measures each mechanism's covariance with the hidden truth through the public leaderboard
   (`src/bbx/lb_algebra.py`); every file's expected RMSE and SHA-256 were logged before upload (`submissions/log.csv`);
3. combines 60 measured signals in a closed-form ridge blend (`scripts/make_finals.py`).

## Reproduce

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # .venv/bin/pip on Linux/macOS
.venv/Scripts/pip install -e .
python scripts/reproduce.py                        # about 10 s: rebuilds f2 bit for bit from the archived signals
```

From the raw data (about 5 GB, public bucket, no credentials):

```bash
B=s3://us-west-2.opendata.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge
python -m awscli s3 sync $B/reference/  data/raw/reference/  --no-sign-request
python -m awscli s3 sync $B/strata/     data/raw/strata/     --exclude "*.csv" --no-sign-request
python -m awscli s3 sync $B/boundaries/ data/raw/boundaries/ --no-sign-request
python scripts/verify_download.py                  # 202 files against data/MANIFEST.sha256
python -m pytest -q                                # 13 tests
python scripts/reproduce.py --full ../repro        # features, the 60 signals and f2, in a fresh copy and venv
```

On 1 November 2026 the full mode regenerated all 61 signal files of f2, and f2 itself, bit for bit
(`docs/reproduction_report_2026-11-01.md`), in one uninterrupted run of 49 minutes on a 4-core laptop.

## Layout

| Path | Content |
|---|---|
| `src/bbx/` | guarded I/O (refuses withdrawn layers), features, structural model, signals, leaderboard algebra, blend, formula rule, submission writer |
| `scripts/` | `make_*.py`: one script per submission batch; `make_finals.py`, `make_f5.py`: final blends; `reproduce.py`; `make_doc_figures.py` |
| `submissions/` | every submitted CSV; `log.csv` (SHA-256, purpose, expected and public RMSE, Zindi ID); `zindi_scores_final.csv` (public and private scores read after the close) |
| `writeup/` | the Best Documentation write-up, its figures and PDF |
| `docs/` | decision log, audit plan, analysis and daily working journal (French) |
| `tests/` | guard, algebra, data contract and formula-rule tests |

The Best Bias Discovery entry ("phantom homes", external data) lives in its own repository:
https://github.com/Arnaud-TOE/bias-bounty-phantom-homes

## Licences

Code: MIT (`LICENSE`). Challenge data and our derived files: CC-BY-SA 4.0 (`DATA_LICENCES.md`).
"""

DATA_LICENCES = """# Data licences

| Data | Licence | Where |
|---|---|---|
| Challenge package (Overture 2026-08-19.0 extracts, ACS, strata, tract geometry) | CC-BY-SA 4.0 (challenge rules), with the per-source terms in the bucket README | downloaded from the public bucket, not stored here |
| Our submitted predictions (`submissions/*.csv`) and derived tables | CC-BY-SA 4.0 | this repository |
"""

GITIGNORE = """.venv/
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
data/raw/
data/interim/
data/features/
"""

# scripts/reproduce.py checks the submitted files byte for byte against the SHA-256 in submissions/log.csv, so git
# must never rewrite their line endings (core.autocrlf would turn them into CRLF on a Windows checkout).
GITATTRIBUTES = """* text=auto
submissions/** -text
data/MANIFEST.sha256 -text
"""


def copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> None:
    keep_git = REL / ".git"
    if REL.exists():
        for item in REL.iterdir():
            if item != keep_git:
                shutil.rmtree(item) if item.is_dir() else item.unlink()
    REL.mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "src" / "bbx").glob("*.py"):
        copy(f, REL / "src" / "bbx" / f.name)
    for f in (ROOT / "tests").glob("*.py"):
        copy(f, REL / "tests" / f.name)
    for f in sorted((ROOT / "scripts").glob("make_*.py")) + [ROOT / "scripts" / s for s in SCRIPTS]:
        copy(f, REL / "scripts" / f.name)
    for name in ["pyproject.toml", "requirements.txt", "data/MANIFEST.sha256", "data/bucket_listing.txt"]:
        copy(ROOT / name, REL / name)
    for f in (ROOT / "submissions").iterdir():
        if f.suffix in (".csv", ".json", ".txt"):
            copy(f, REL / "submissions" / f.name)
    copy(ROOT / "writeup" / "documentation.md", REL / "writeup" / "documentation.md")
    copy(ROOT / "writeup" / "pdf" / "Arnaud_TOE_Best_Documentation.pdf",
         REL / "writeup" / "pdf" / "Arnaud_TOE_Best_Documentation.pdf")
    for f in (ROOT / "writeup" / "figures").iterdir():
        if f.name.startswith("fig") or f.suffix in (".json", ".csv"):
            copy(f, REL / "writeup" / "figures" / f.name)
    for name in DOCS:
        text = (ROOT / "docs" / name).read_text(encoding="utf-8")
        (REL / "docs").mkdir(exist_ok=True)
        (REL / "docs" / name).write_text(EMAIL.sub("[e-mail removed]", text), encoding="utf-8")
    (REL / "README.md").write_text(README, encoding="utf-8")
    (REL / "DATA_LICENCES.md").write_text(DATA_LICENCES, encoding="utf-8")
    (REL / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (REL / ".gitattributes").write_text(GITATTRIBUTES, encoding="utf-8", newline="\n")
    mit = (ROOT / "release" / "bias-bounty-phantom-homes" / "LICENSE").read_text(encoding="utf-8")
    (REL / "LICENSE").write_text(mit, encoding="utf-8")
    leaks = [p for p in REL.rglob("*") if p.is_file() and p.suffix in (".md", ".py", ".txt")
             and EMAIL.search(p.read_text(encoding="utf-8", errors="ignore"))]
    n = sum(1 for p in REL.rglob("*") if p.is_file() and ".git" not in p.parts)
    size = sum(p.stat().st_size for p in REL.rglob("*") if p.is_file() and ".git" not in p.parts)
    print(f"{REL}: {n} files, {size / 1e6:.1f} MB; files with an e-mail address: {[str(p) for p in leaks]}")


if __name__ == "__main__":
    main()
