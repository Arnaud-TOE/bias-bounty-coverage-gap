"""Queue for 22 October: the least redundant second-pass signals (R2 on the 22-signal basis).

s39 fire0_nbr300 (0.08), s40 fire0_no_nbr1km (0.15), s41 log_msft_area (0.26),
s42 zip_ALAND_k0.5 (0.38), s43 zip_ALAND_k1.0 (0.46).
"""
from bbx import config
from bbx.candidates_extra import build
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
cand = df[["GEOID"]].merge(build(), on="GEOID", how="left")
jobs = [
    ("s39_fire0_nbr300", "fire0_nbr300", 0.08,
     "no Overture fire_department place in the tract but one within ~300 m across its boundary"),
    ("s40_fire0_no_nbr1km", "fire0_no_nbr1km", 0.10,
     "no Overture fire_department place in the tract nor within ~1 km of it"),
    ("s41_log_msft_area", "log_msft_area", 0.05, "mean footprint area of Microsoft-sourced Overture buildings (log)"),
    ("s42_zip_area_k05", "zip_ALAND_k0.5", 0.05,
     "CBP half if ZIP establishments are spread to tracts by land area (2 places per establishment)"),
    ("s43_zip_area_k1", "zip_ALAND_k1.0", 0.05,
     "CBP half if ZIP establishments are spread to tracts by land area (1 place per establishment)"),
]
for name, col, rho, purpose in jobs:
    path, exp = write_signal(df, cand[col].to_numpy(float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")
files = [j[0] for j in jobs]
(config.SUBMISSIONS / "upload_2026-10-22.txt").write_text(
    "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n", encoding="utf-8")
print("2026-10-22", files)
