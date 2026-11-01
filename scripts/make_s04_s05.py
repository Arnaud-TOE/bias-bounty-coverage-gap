"""S04: structural composite v1.  S05: expected fire-station gap (undefined counts as 0).

Both are submitted as standardised signals around the measured public mean (bbx.signals),
so their public RMSE gives their correlation with the truth.
"""
import pandas as pd

from bbx.dataset import load_table
from bbx.signals import write_signal
from bbx.structural import Params, fit_lambdas, simulate

df = load_table()
out = simulate(df, Params(n_draws=1000, lam=fit_lambdas(df)))
out.to_parquet("data/interim/structural_v1.parquet", index=False)

fire_contrib = (out["fire"].fillna(0) * out["p_fire_defined"]).to_numpy()

for name, sig, rho, purpose in [
    ("s04_structural_v1", out["score"].to_numpy(), 0.35,
     "structural model v1: MC expectation of organiser formula (route proxy, physical fire density, CBP proxy)"),
    ("s05_fire_expected_gap", fire_contrib, 0.30,
     "expected fire-station gap from physical station density, misfiled names, Overture fire_department count"),
]:
    path, exp = write_signal(df, sig, name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

print(pd.read_csv("submissions/log.csv").tail(2)[["file", "expected_public_rmse", "sha256"]].to_string())
