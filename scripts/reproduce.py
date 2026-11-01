"""Reproduce the final submission, at two depths.

    python scripts/reproduce.py                 # fast, about 1 minute: rebuild the finals from the archived signals
    python scripts/reproduce.py --full DIR      # full, about 1 hour: rebuild every feature and every signal of the
                                                # final blend from the raw challenge data, in a fresh copy at DIR

Fast mode. The final blend f2 (Zindi 8DPgZvCX) is a deterministic function of 60 signal files in submissions/
and of their public RMSEs in submissions/log.csv. The script checks each file's SHA-256 against the log, refits
the blend exactly as scripts/make_finals.py does, writes the CSV to a temporary folder in the submission format
and compares its SHA-256 with the logged one. It does the same for f5 (Zindi LEGqiwj2, sent after the close and
therefore not ranked). Nothing in submissions/ is written.

Full mode. DIR must be empty or absent. The script copies the code (src/, scripts/, tests/, project files) to DIR,
links DIR/data/raw to this project's raw data (a directory junction on Windows, a symlink elsewhere; read only),
creates DIR/.venv from requirements.txt, and runs with DIR as the project root:
  1. the data check (byte counts and SHA-256 against data/MANIFEST.sha256) and the unit tests;
  2. the feature builders (per-region layers, modelling table, six extra feature passes);
  3. every script that produced a signal of the final blend, in the order they were first run;
  4. a comparison of each regenerated signal file with the submitted one (SHA-256, else the largest difference);
  5. the fast mode inside DIR, with the public RMSEs recorded from Zindi (submissions/log.csv).
The report is written to DIR/reproduction_report.md.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Final submissions: (file, ridge, keep s07/s22). Recipes as in scripts/make_finals.py and scripts/make_f5.py.
FINALS = [("f2_blend_ridge0005_with_s07_s22.csv", 0.005, True), ("f5_blend_ridge002.csv", 0.02, False)]

FEATURE_STEPS = [
    ["scripts/build_features.py"],
    ["-c", "from bbx.dataset import save_table; save_table()"],
    ["-c", "from bbx import features_extra as m; m.build()"],
    ["-c", "from bbx import features_roadref as m; m.build()"],
    ["-c", "from bbx import features_bldref as m; m.build()"],
    ["-c", "from bbx import features_bizaddr as m; m.build()"],
    ["-c", "from bbx import features_osmfac as m; m.build()"],
    ["-c", "from bbx import features_bandruns as m; m.build()"],
    ["scripts/build_uncounted_majors.py"],
]

# Scripts that wrote the signals of the final blend, in the order they were first run, with the UTC date of that
# run (prepared_utc in submissions/log.csv). Before each one, the scores Zindi had returned by that date are
# recorded in the copy's log, as bbx.submit.record did between batches: make_s16_s18 builds the first blend
# s16 from the scores of s03-s10 (no other script reads scores, and no blend enters the final one).
SIGNAL_SCRIPTS = [
    ("make_s01_s03", "2026-10-16"), ("make_s04_s05", "2026-10-16"), ("make_s06_s10", "2026-10-16"),
    ("make_s11_s15", "2026-10-17"), ("make_s16_s18", "2026-10-17"), ("make_s19_s23", "2026-10-18"),
    ("make_queue_oct19_21", "2026-10-18"), ("make_queue_oct20_21", "2026-10-19"), ("make_queue_oct22", "2026-10-20"),
    ("make_queue_oct23_v2", "2026-10-22"), ("make_queue_oct24", "2026-10-23"), ("make_cbp4", "2026-10-23"),
    ("make_queue_oct25b", "2026-10-24"), ("make_queue_oct25e", "2026-10-24"), ("make_s95", "2026-10-24"),
    ("make_s106", "2026-10-25"), ("make_queue_oct26", "2026-10-25"), ("make_queue_oct27", "2026-10-25"),
    ("make_s116_s117", "2026-10-26"), ("make_s134", "2026-10-28"), ("make_s136", "2026-10-28"),
    ("make_s140", "2026-10-29"), ("make_s146", "2026-10-30"), ("make_s147", "2026-10-30"),
]

COPY = ["src", "scripts", "tests", "pyproject.toml", "requirements.txt", "README.md",
        "data/MANIFEST.sha256", "data/bucket_listing.txt"]


def _load_finals_module():
    spec = importlib.util.spec_from_file_location("make_finals", ROOT / "scripts" / "make_finals.py")
    mf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mf)
    return mf


def fast() -> bool:
    """Rebuild each final from the archived signals; True if every SHA-256 matches the log."""
    import pandas as pd

    from bbx import config, submit
    from bbx.dataset import load_table

    if config.ROOT != ROOT:
        raise SystemExit(f"bbx is imported from {config.ROOT}, not from {ROOT}: install this copy (pip install -e .)")
    mf = _load_finals_module()
    log = pd.read_csv(submit.LOG, dtype=str, keep_default_na=False).drop_duplicates("file", keep="last")
    sha = dict(zip(log["file"], log["sha256"]))
    df = load_table()
    ok = True
    for name, ridge, keep in FINALS:
        files = [f for f in mf.basis_files() if f not in mf.WEAK and (keep or f not in mf.EXCLUDED)]
        bad = [f for f in files if submit.sha256(config.SUBMISSIONS / f) != sha[f]]
        pred, expected, used, _ = mf.fit_without_wa(df, files, ridge)
        sub = submit.validate(pd.DataFrame({"GEOID": df["GEOID"], "coverage_gap_score": pred}))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / name
            sub.to_csv(out, index=False, lineterminator="\n", float_format="%.6f")
            got = submit.sha256(out)
        same = got == sha[name]
        ok &= same and not bad
        print(f"{name}: {len(used)} signals used ({len(files)} listed, {len(bad)} with a changed SHA-256), "
              f"ridge {ridge}, expected public {expected:.6f}")
        print(f"  SHA-256 {got[:16]}... logged {sha[name][:16]}...  {'IDENTICAL' if same else 'DIFFERENT'}")
        for f in bad:
            print(f"  changed input: {f}")
    return ok


def _run(py: Path, args: list[str], cwd: Path, log, env: dict) -> float:
    t0 = time.time()
    log.write(f"\n$ python {' '.join(args)}\n")
    log.flush()
    res = subprocess.run([str(py), *args], cwd=cwd, stdout=log, stderr=subprocess.STDOUT, env=env)
    if res.returncode:
        raise SystemExit(f"step failed (exit {res.returncode}): {' '.join(args)}; see {log.name}")
    return time.time() - t0


def _link(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(dst), str(src)], check=True, stdout=subprocess.DEVNULL)
    else:
        dst.symlink_to(src, target_is_directory=True)


def _record_scores(work: Path, scored, upto: str) -> None:
    """Copy into the copy's log the Zindi scores of the files written so far that were known on `upto`
    (submitted_utc <= upto), on the last log row of each file, as bbx.submit.record did."""
    import pandas as pd

    path = work / "submissions" / "log.csv"
    if not path.exists():
        return
    log = pd.read_csv(path, dtype=str, keep_default_na=False)
    known = scored[scored["submitted_utc"].str[:10] <= upto].set_index("file")
    cols = ["zindi_id", "public_rmse", "submitted_utc"]
    for i in log.index[~log["file"].duplicated(keep="last")]:
        if log.at[i, "file"] in known.index:
            log.loc[i, cols] = known.loc[log.at[i, "file"], cols].to_numpy()
    log.to_csv(path, index=False, lineterminator="\n")


def full(work: Path, resume: bool = False) -> bool:
    """Rebuild from the raw data in `work`. With `resume`, `work` holds an earlier run whose environment and
    features are complete: the code is refreshed from this project and only the signal stage is rerun."""
    import pandas as pd

    orig = pd.read_csv(ROOT / "submissions" / "log.csv", dtype=str, keep_default_na=False)
    scored = orig[orig["public_rmse"] != ""].drop_duplicates("file", keep="last")
    if resume:
        if not (work / ".venv").exists() or not (work / "data" / "features" / "features_uncounted.parquet").exists():
            raise SystemExit(f"{work} has no complete environment and features to resume from")
        for item in ["src", "scripts", "tests"]:
            shutil.rmtree(work / item)
            shutil.copytree(ROOT / item, work / item, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.rmtree(work / "submissions")
        shutil.rmtree(work / "data" / "interim", ignore_errors=True)  # outputs of the signal scripts
        (work / "data" / "interim").mkdir()
    else:
        if work.exists() and any(work.iterdir()):
            raise SystemExit(f"{work} is not empty")
        work.mkdir(parents=True, exist_ok=True)
        for item in COPY:
            src, dst = ROOT / item, work / item
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            else:
                shutil.copy2(src, dst)
        _link(ROOT / "data" / "raw", work / "data" / "raw")
    (work / "submissions").mkdir()
    timings = []
    py = work / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    with open(work / "reproduction.log", "a" if resume else "w", encoding="utf-8") as log:
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "VIRTUAL_ENV")}
        if resume:
            log.write(f"\n# resumed {time.strftime('%Y-%m-%d %H:%M')}: signal stage only\n")
        else:
            t0 = time.time()
            subprocess.run([sys.executable, "-m", "venv", str(work / ".venv")], check=True)
            _run(py, ["-m", "pip", "install", "--quiet", "-r", "requirements.txt"], work, log, env)
            _run(py, ["-m", "pip", "install", "--quiet", "--no-deps", "-e", "."], work, log, env)
            timings.append(("fresh environment (venv + pinned requirements)", time.time() - t0))
        _run(py, ["-c", f"import bbx.config as c, pathlib; assert c.ROOT == pathlib.Path(r'{work}').resolve(), c.ROOT"],
             work, log, env)
        if not resume:
            timings.append(("data check", _run(py, ["scripts/verify_download.py"], work, log, env)))
            for step in FEATURE_STEPS:
                timings.append((" ".join(step)[-70:], _run(py, step, work, log, env)))
        for name, day in SIGNAL_SCRIPTS:
            _record_scores(work, scored, day)
            timings.append((f"scripts/{name}.py", _run(py, [f"scripts/{name}.py"], work, log, env)))
        timings.append(("unit tests", _run(py, ["-m", "pytest", "-q"], work, log, env)))

        # Compare the regenerated signals with the submitted ones.
        mf = _load_finals_module()
        needed = sorted({f for f in mf.blend.scored_signals()["file"] if "blend" not in f} - mf.WEAK,
                        key=lambda f: list(scored["file"]).index(f))
        rows = []
        for f in needed:
            new = work / "submissions" / f
            ref = pd.read_csv(ROOT / "submissions" / f, dtype={"GEOID": str})
            if not new.exists():
                rows.append((f, "not regenerated", "", ""))
                continue
            got = pd.read_csv(new, dtype={"GEOID": str})
            same = mf.submit.sha256(new) == scored.set_index("file").loc[f, "sha256"]
            d = (got["coverage_gap_score"] - ref["coverage_gap_score"]).abs()
            rows.append((f, "identical" if same else "different", f"{d.max():.6f}", str(int((d > 0).sum()))))
        # Fast mode inside the copy: submitted files that were not regenerated are copied, regenerated ones kept.
        for f in scored["file"]:
            if not (work / "submissions" / f).exists():
                shutil.copy2(ROOT / "submissions" / f, work / "submissions" / f)
        shutil.copy2(ROOT / "submissions" / "log.csv", work / "submissions" / "log.csv")
        res = subprocess.run([str(py), "scripts/reproduce.py"], cwd=work, capture_output=True, text=True, env=env)
        log.write(res.stdout + res.stderr)
    n_same = sum(r[1] == "identical" for r in rows)
    how = ("resumed run: environment and features from the earlier run in the same copy, code refreshed, "
           "signal stage rerun" if resume else "one run from an empty folder")
    report = [f"# Reproduction report ({time.strftime('%Y-%m-%d %H:%M')})", "",
              f"Copy: `{work}` ({how}); raw data linked from `{ROOT / 'data' / 'raw'}`.", "",
              f"**{n_same} of {len(rows)} signal files of the final blend regenerated bit for bit.**", "",
              "| Signal file | Result | Largest difference | Tracts that differ |", "|---|---|---|---|",
              *[f"| `{a}` | {b} | {c} | {d} |" for a, b, c, d in rows], "",
              "## Final blends rebuilt inside the copy", "", "```", res.stdout.strip(), "```", "",
              "## Timings", "", "| Step | Seconds |", "|---|---|", *[f"| {a} | {b:.0f} |" for a, b in timings]]
    (work / "reproduction_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return n_same == len(rows) and res.returncode == 0 and "DIFFERENT" not in res.stdout


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--full", metavar="DIR", type=Path, help="empty folder for the full rebuild")
    ap.add_argument("--resume", action="store_true", help="with --full: rerun only the signal stage in DIR")
    a = ap.parse_args()
    sys.exit(0 if (full(a.full.resolve(), a.resume) if a.full else fast()) else 1)
