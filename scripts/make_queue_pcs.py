"""Residual principal-component queue (23-29 October), replacing the s46 blend slot.

Basis = all scored signals (s16 excluded) + those queued for 22-23 October. The 30 leading
principal components of the 431-feature matrix left unexplained by that basis are written as
s47_rpc01 ... s76_rpc30 (deterministic SVD; components saved to data/interim/residual_pcs.npy).

Decision D1-bis caps the measured signals at about 50: the lists mark later components as
conditional until the cap is raised.
"""
import numpy as np

from bbx import blend, config
from bbx.dataset import load_table
from bbx.residual_pcs import residual_pcs
from bbx.signals import write_signal

QUEUED = ["s39_fire0_nbr300.csv", "s40_fire0_no_nbr1km.csv", "s41_log_msft_area.csv", "s42_zip_area_k05.csv",
          "s43_zip_area_k1.csv", "s32_region_ca.csv", "s35_whp_log.csv", "s44_blend_tail_hinge.csv",
          "s45_school0_nbr300.csv"]
CAP = 50

df = load_table()
sig = blend.scored_signals()
scored = [f for f in sig["file"] if not f.startswith("s16")]
basis = scored + [q for q in QUEUED if q not in scored]
pcs, explained, tab = residual_pcs(basis, n=30)
np.save(config.INTERIM / "residual_pcs.npy", pcs)
print(tab.round(4).head(10).to_string())

names = []
for i in range(pcs.shape[1]):
    name = f"s{47 + i}_rpc{i + 1:02d}"
    write_signal(df, pcs[:, i], name,
                 f"residual principal component {i + 1} of 431 permitted features ({explained[i]:.3f} of residual variance)",
                 rho_guess=0.05)
    names.append(name)

n_before = len(basis)
days = {"2026-10-23": ["s32_region_ca", "s35_whp_log", "s44_blend_tail_hinge", "s45_school0_nbr300", names[0]]}
rest = names[1:]
for d, chunk in zip(["2026-10-24", "2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29"],
                    [rest[i:i + 5] for i in range(0, 30, 5)]):
    days[d] = chunk
count = n_before
for day, files in days.items():
    lines = []
    for i, f in enumerate(files, 1):
        new = f.startswith("s4") or f.startswith("s5") or f.startswith("s6") or f.startswith("s7")
        if f in ("s32_region_ca", "s35_whp_log", "s44_blend_tail_hinge", "s45_school0_nbr300"):
            new = False  # already counted in the basis above
        if new:
            count += 1
        tag = "" if count <= CAP or not new else "   [conditionnel : au-delà de 50 signaux, D1-bis]"
        lines.append(f"{i}. {f}.csv{tag}")
    (config.SUBMISSIONS / f"upload_{day}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(day, lines)
print("signals after the queue:", count)
