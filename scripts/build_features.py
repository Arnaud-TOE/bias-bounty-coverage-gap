"""Build per-tract feature tables.

    python scripts/build_features.py                      # all regions, all layers
    python scripts/build_features.py eastern-wa           # one region
    python scripts/build_features.py eastern-wa --layers pois roads
"""
import argparse

from bbx import config
from bbx.features import LAYERS, build

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("regions", nargs="*", default=list(config.REGIONS))
    ap.add_argument("--layers", nargs="*", default=list(LAYERS))
    ap.add_argument("--threads", type=int, default=None)
    args = ap.parse_args()
    for region in args.regions:
        build(region, args.layers, threads=args.threads)
