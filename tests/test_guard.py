import pandas as pd
import pytest

from bbx.io import ForbiddenDataError, drop_forbidden_columns, permitted


@pytest.mark.parametrize(
    "path",
    [
        "data/raw/reference/eastern-ok/eastern-ok-tiger-roads.parquet",
        "data/raw/reference/eastern-ok/eastern-ok-microsoft-buildings.parquet",
        "data/raw/reference/eastern-ok/eastern-ok-hifld-fire-stations.parquet",
        "data/raw/reference/eastern-ok/eastern-ok-census-cbp.parquet",
        "data/raw/reference/eastern-ok/eastern-ok-coverage-gap.csv",
    ],
)
def test_withdrawn_layers_are_refused(path):
    with pytest.raises(ForbiddenDataError):
        permitted(path)


def test_permitted_layers_pass():
    for layer in ["overture-buildings", "overture-roads", "overture-pois", "census-acs-housing"]:
        permitted(f"data/raw/reference/eastern-ok/eastern-ok-{layer}.parquet")


def test_footprint_derived_strata_columns_are_dropped():
    df = pd.DataFrame(columns=[
        "GEOID", "usfs_BuildingCount_sum", "usfs_BuildingCover_mean", "usfs_BuildingDensity_mean",
        "usfs_HUCount_sum", "usfs_HUDen_mean", "usfs_HURisk_mean", "usfs_PopCount_sum",
        "usfs_PopDen_mean", "carbonplan_buildings", "usfs_WHP_mean", "svi_overall",
    ])
    assert list(drop_forbidden_columns(df).columns) == ["GEOID", "usfs_WHP_mean", "svi_overall"]
