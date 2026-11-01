# Coverage-gap scores without labels

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
