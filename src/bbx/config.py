"""Project-wide constants: paths, regions, data release and organiser category lists."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
REFERENCE = RAW / "reference"
STRATA = RAW / "strata"
BOUNDARIES = RAW / "boundaries"
FEATURES = DATA / "features"
INTERIM = DATA / "interim"
SUBMISSIONS = ROOT / "submissions"

BUCKET = "s3://us-west-2.opendata.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge"
OVERTURE_RELEASE = "2026-08-19.0"

# Order matters only for reporting; scored tract counts from the bucket README.
REGIONS = {
    "south-central-tx": 6003,
    "maricopa-az": 1593,
    "eastern-ok": 1192,
    "northern-ca": 591,
    "eastern-wa": 415,
}
N_SCORED = sum(REGIONS.values())  # 9,794

# Organiser category definitions (bucket README, "poi_gap is per facility type").
FIRE_CATEGORIES = ("fire_department",)
EMS_CATEGORIES = ("ambulance_and_ems_services",)
SCHOOL_CATEGORIES = (
    "elementary_school",
    "middle_school",
    "high_school",
    "school",
    "private_school",
    "public_school",
)
# Overture road classes compared against TIGER S1100/S1200 by the organisers.
SCORED_ROAD_CLASSES = ("motorway", "trunk", "primary", "secondary")

SEED = 20261016
