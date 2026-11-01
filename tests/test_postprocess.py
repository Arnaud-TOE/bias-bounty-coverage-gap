import numpy as np
import pandas as pd
import pytest

from bbx import config
from bbx.postprocess import apply_formula_rules, empty_overture_mask


def test_empty_tract_gets_score_one():
    df = pd.DataFrame({"km_scored": [0.0, 0.0, 3.2], "bld_n": [0, 5, 10], "poi_n": [0, 0, 4]})
    out = apply_formula_rules(df, np.array([0.4, 0.4, 0.4]))
    assert out.tolist() == [1.0, 0.4, 0.4]


@pytest.mark.skipif(not config.FEATURES.joinpath("features.parquet").exists(), reason="features not built")
def test_only_the_two_gulf_water_tracts_are_empty():
    from bbx.dataset import load_table

    df = load_table()
    assert sorted(df.loc[empty_overture_mask(df), "GEOID"]) == ["48039990000", "48057990000"]
