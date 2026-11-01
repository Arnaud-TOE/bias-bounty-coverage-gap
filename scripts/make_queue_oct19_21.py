"""Submission queue for 19-21 October (decision D1-bis): 15 basis signals ranked by expected
new information, plus the three already-prepared fire / EMS signals.

Writes the files into submissions/ and one upload list per day:
submissions/upload_2026-10-19.txt, ..._10-20.txt, ..._10-21.txt.
"""
import numpy as np

from bbx import config
from bbx.candidates import build
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table()
cand = build()

new = [
    # name, candidate column, rho guess, purpose
    ("s24_cbp_area_k1", "cbp_area_k1.0", 0.08, "CBP half if establishments are allocated to tracts by land area (county-relative places density)"),
    ("s25_cbp_pop_k05", "cbp_pop_k0.5", 0.08, "CBP half if establishments are allocated by population, 2 places per establishment"),
    ("s26_bld_per_hu_low", "bld_per_hu_low", 0.05, "fewer Overture buildings than ACS housing units (1 - min(1, bld/hu))"),
    ("s27_bld_small_share", "bld_small_share", 0.05, "share of Overture footprints under 50 m2"),
    ("s28_bld_esri_share", "bld_esri_share", 0.05, "share of Overture footprints sourced from Esri Community Maps"),
    ("s29_poi_closed_share", "poi_closed_share", 0.03, "share of Overture places flagged permanently closed"),
    ("s30_import_share", "import_share", 0.08, "share of road km unedited since 2012 (TIGER-import era)"),
    ("s31_region_wa", "region_wa", 0.05, "regional offset: eastern-wa indicator"),
    ("s32_region_ca", "region_ca", 0.02, "regional offset: northern-ca indicator"),
    ("s33_p_transport_defined", "p_transport_defined", 0.15, "structural v1 probability that the transport component is defined"),
    ("s34_unnamed_share", "unnamed_share", 0.15, "share of drivable road km without a primary name"),
    ("s35_whp_log", "whp_log", 0.10, "USFS wildfire hazard potential (log)"),
]
for name, column, rho, purpose in new:
    path, exp = write_signal(df, cand[column].to_numpy(float), name, purpose, rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f}")

days = {
    "2026-10-19": ["s19_fire0_with_community", "s20_partial_fire_gap", "s22_no_ems_place", "s24_cbp_area_k1", "s25_cbp_pop_k05"],
    "2026-10-20": ["s26_bld_per_hu_low", "s27_bld_small_share", "s28_bld_esri_share", "s29_poi_closed_share", "s30_import_share"],
    "2026-10-21": ["s31_region_wa", "s32_region_ca", "s33_p_transport_defined", "s34_unnamed_share", "s35_whp_log"],
}
for day, files in days.items():
    (config.SUBMISSIONS / f"upload_{day}.txt").write_text(
        "\n".join(f"{i}. {f}.csv" for i, f in enumerate(files, 1)) + "\n", encoding="utf-8")
    print(day, files)
