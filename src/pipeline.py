
import shutil
from pathlib import Path

import pandas as pd

from src.standardizer import standardize_business_data
from src.validator import validate_business_data
from src.deduplicator import create_business_and_license_tables


ROOT_DIR = Path(__file__).resolve().parents[1]

RAW_PATH = ROOT_DIR / "data" / "raw" / "chicago_business_licenses.csv"

BUSINESSES_PATH = ROOT_DIR / "data" / "silver" / "businesses"
LICENSES_PATH = ROOT_DIR / "data" / "silver" / "licenses"
REJECTED_PATH = ROOT_DIR / "data" / "rejected" / "rejected_records.csv"


def run_pipeline():

    print("Starting BizClean ETL pipeline...")

    # 1. Extract
    df = pd.read_csv(RAW_PATH, dtype=str)

    print("Extracted records:", len(df))

    # 2. Transform
    standardized_df = standardize_business_data(df)

    # 3. Validate
    clean_df, rejected_df = validate_business_data(
        standardized_df
    )

    # 4. Create business and license tables
    businesses_df, licenses_df = (
        create_business_and_license_tables(clean_df)
    )

    # 5. Prepare output directories
    for path in [BUSINESSES_PATH, LICENSES_PATH]:
        if path.exists():
            shutil.rmtree(path)

        path.mkdir(parents=True, exist_ok=True)

    REJECTED_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # 6. Write Silver data as partitioned Parquet
    businesses_df.to_parquet(
        BUSINESSES_PATH,
        engine="pyarrow",
        index=False,
        partition_cols=["city"]
    )

    licenses_df.to_parquet(
        LICENSES_PATH,
        engine="pyarrow",
        index=False,
        partition_cols=["city"]
    )

    # 7. Write rejected records with rejection reasons
    rejected_df.to_csv(
        REJECTED_PATH,
        index=False
    )

    # 8. Reconciliation checks
    assert len(clean_df) + len(rejected_df) == len(df)

    assert len(licenses_df) == len(clean_df)

    assert businesses_df["business_id"].is_unique

    assert licenses_df["license_id"].is_unique

    print("\n========== PIPELINE SUMMARY ==========")

    print("Raw records:", len(df))
    print("Clean license records:", len(licenses_df))
    print("Unique businesses:", len(businesses_df))
    print("Rejected records:", len(rejected_df))

    print("\n========== OUTPUT LOCATIONS ==========")

    print("Businesses:", BUSINESSES_PATH)
    print("Licenses:", LICENSES_PATH)
    print("Rejected:", REJECTED_PATH)

    print("\nAll reconciliation checks passed.")
    print("BizClean ETL pipeline completed.")


if __name__ == "__main__":
    run_pipeline()
