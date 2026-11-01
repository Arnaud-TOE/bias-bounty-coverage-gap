"""Data contract checks that run against the downloaded challenge data."""
import math

import pytest

from bbx import config
from bbx.io import connect, read_sample_submission, ref_path

pytestmark = pytest.mark.skipif(
    not (config.REFERENCE / "eastern-wa").exists(), reason="challenge data not downloaded"
)


def test_scored_tract_counts_and_geoid_text():
    sub = read_sample_submission()
    assert len(sub) == config.N_SCORED
    assert sub["GEOID"].is_unique
    assert sub.groupby("region").size().to_dict() == config.REGIONS
    # Maricopa keeps the leading zero of state FIPS 04; one NM tract is a member.
    az = sub.loc[sub.region == "maricopa-az", "GEOID"]
    assert az.str.len().eq(11).all()
    assert az.str.startswith("04").sum() == 1592
    assert (az == "35023970000").sum() == 1


def test_lengths_use_lon_lat_axis_order():
    """A road segment's spheroid length must match its projected (EPSG:5070) length.

    Both silent DuckDB failure modes (inf from ST_Transform without always_xy, NaN from
    ST_Length_Spheroid on lon/lat input) would break this equality.
    """
    con = connect()
    path = ref_path("northern-ca", "overture-roads").as_posix()
    row = con.sql(f"""
        SELECT ST_Length_Spheroid(ST_FlipCoordinates(geometry)) AS m_sph,
               ST_Length(ST_Transform(geometry, 'EPSG:4326', 'EPSG:5070', always_xy := true)) AS m_alb
        FROM '{path}'
        WHERE class = 'motorway'
        LIMIT 1
    """).fetchone()
    m_sph, m_alb = row
    assert math.isfinite(m_sph) and math.isfinite(m_alb) and m_sph > 0
    assert abs(m_sph - m_alb) / m_sph < 0.01
