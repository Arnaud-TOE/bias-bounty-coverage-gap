"""CBP v4 candidates (prepared 23 October for the 25 October queue, after the research of that day).

The organiser CBP half allocates ZIP establishments to tracts by the tract's share of the ZIP's
USPS business addresses (HUD BUS_RATIO, confirmed by an exact public reproduction: cbp_estab =
cbp_estab_bus; a residential-share allocation moves 1,974 tracts by 0.022). With a roughly
constant number of establishments per business address, the CBP gap is 1 - min(1, P / (k * BA))
for places P and business addresses BA. BA is proxied by large footprints (bbx.features_bizaddr);
k is the median places per proxy unit, so about half of the tracts with a proxy get a gap.
Our earlier allocations by population or housing units (residential shares) scored negative.

s86_cbp4_bld1000: BA proxied by the number of footprints of at least 1,000 m2,
s87_cbp4_area300: BA proxied by the footprint area of buildings of at least 300 m2.
Both are weighted 1 / (2 n_defined) (CBP half inside the POI component), n_defined from v3.
"""
import numpy as np
import pandas as pd

from bbx import config
from bbx.dataset import load_table
from bbx.signals import write_signal

df = load_table().merge(pd.read_parquet(config.FEATURES / "features_bizaddr.parquet"), on="GEOID", how="left")
v3 = df[["GEOID"]].merge(pd.read_parquet(config.INTERIM / "structural_v3.parquet"), on="GEOID", how="left")
places = df["poi_n"].to_numpy(float)
w_half = 1 / (2 * v3["n_defined"].clip(lower=1).to_numpy())

for name, proxy, rho in [("s86_cbp4_bld1000", "bld_ge1000", 0.10), ("s87_cbp4_area300", "area_ge300", 0.10)]:
    px = df[proxy].to_numpy(float)
    ok = px > 0
    ratio = np.where(ok, places / np.where(ok, px, 1), np.nan)
    k = np.nanmedian(ratio)
    gap = np.where(ok, 1 - np.minimum(1, ratio / k), 0.0)
    path, exp = write_signal(df, gap * w_half, name,
                             f"CBP v4: business addresses proxied by {proxy}, gap 1-min(1,places/(k*proxy)), k=median",
                             rho_guess=rho)
    print(f"{path.name}: expected public RMSE {exp:.6f} (k={k:.4g})")
