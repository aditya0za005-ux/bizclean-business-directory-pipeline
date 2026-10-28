import shutil
import uuid
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import pyarrow.parquet as pq

from src.standardizer import standardize_business_data
from src.validator import validate_business_data
from src.deduplicator import create_business_and_license_tables


ROOT_DIR = Path(__file__).resolve().parents[1]

RAW_PATH = ROOT_DIR / "data" / "raw" / "chicago_business_licenses.csv"

BUSINESSES_PATH = ROOT_DIR / "data" / "silver" / "businesses"
LICENSES_PATH = ROOT_DIR / "data" / "silver" / "licenses"
REJECTED_PATH = ROOT_DIR / "data" / "rejected" / "rejected_records.csv"


def write_partitioned_dataset(df, output_path, dataset_name):
    """
    Write one Parquet file per city partition.
    Read every file back to verify that it is valid.
    """

    output_path.mkdir(parents=True, exist_ok=False)

    total_rows = 0
    partition_count = 0

    expected_columns = [
        column for column in df.columns if column != "city"
    ]

    for city, group in df.groupby(
        "city",
        dropna=False,
        sort=False
    ):

        if pd.isna(city):
            city_folder = "__HIVE_DEFAULT_PARTITION__"
        else:
            city_folder = quote(str(city), safe="").replace(".", "%2E")

        partition_path = output_path / f"city={city_folder}"
        partition_path.mkdir(parents=True, exist_ok=True)

        parquet_path = partition_path / "part-00000.parquet"

        group_without_city = group.drop(columns=["city"])

        group_without_city.to_parquet(
            parquet_path,
            engine="pyarrow",
            index=False,
            compression="snappy"
        )

        parquet_file = pq.ParquetFile(parquet_path)

        try:
            table = parquet_file.read()

            if table.num_rows != len(group):
                raise ValueError(
                    f"Row count mismatch in {parquet_path}"
                )

            if table.column_names != expected_columns:
                raise ValueError(
                    f"Schema mismatch in {parquet_path}"
                )

            total_rows += table.num_rows
            partition_count += 1

        finally:
            parquet_file.close()

    if total_rows != len(df):
        raise ValueError(
            f"{dataset_name}: expected {len(df)} rows, "
            f"but verified {total_rows}"
        )

    print(f"\n{dataset_name} validation:")
    print("Expected rows:", len(df))
    print("Verified rows:", total_rows)
    print("Partitions written:", partition_count)
    print("Failed partitions: 0")

    return total_rows


def replace_silver_datasets(staged_datasets, run_id):
    """
    Replace both Silver datasets only after staging validation.
    Preserve backups and restore them if replacement fails.
    """

    backups = {}
    installed = []

    targets = [
        BUSINESSES_PATH,
        LICENSES_PATH
    ]

    try:
        # Move existing datasets to backup locations.
        for target in targets:

            if target.exists():

                backup = target.parent / (
                    f".{target.name}_backup_{run_id}"
                )

                target.rename(backup)
                backups[target] = backup

        # Install both verified staging datasets.
        for staged_path, target_path in staged_datasets:

            staged_path.rename(target_path)
            installed.append(target_path)

    except Exception:

        print("\nReplacement failed. Attempting rollback...")

        # Remove newly installed datasets.
        for target in reversed(installed):

            if target.exists():
                shutil.rmtree(target)

        # Restore previous datasets.
        for target, backup in backups.items():

            if backup.exists():
                backup.rename(target)

        raise

    print("\nSilver datasets replaced successfully.")

    if backups:
        print("\nPrevious datasets preserved at:")

        for backup in backups.values():
            print(backup)


def run_pipeline():

    print("Starting BizClean ETL pipeline...")

    # 1. Extract
    df = pd.read_csv(
        RAW_PATH,
        dtype=str
    )

    print("Extracted records:", len(df))

    # 2. Standardize
    standardized_df = standardize_business_data(df)

    # 3. Validate
    clean_df, rejected_df = validate_business_data(
        standardized_df
    )

    # 4. Create business and license tables
    businesses_df, licenses_df = (
        create_business_and_license_tables(clean_df)
    )

    # 5. Reconciliation checks before writing
    assert len(clean_df) + len(rejected_df) == len(df)

    assert len(licenses_df) == len(clean_df)

    assert businesses_df["business_id"].is_unique

    assert licenses_df["license_id"].is_unique

    # 6. Prepare unique staging directories
    run_id = uuid.uuid4().hex[:12]

    silver_parent = BUSINESSES_PATH.parent
    silver_parent.mkdir(parents=True, exist_ok=True)

    staged_businesses = (
        silver_parent / f".businesses_staging_{run_id}"
    )

    staged_licenses = (
        silver_parent / f".licenses_staging_{run_id}"
    )

    try:

        # 7. Write and validate both datasets
        print("\nWriting Businesses dataset...")

        write_partitioned_dataset(
            businesses_df,
            staged_businesses,
            "Businesses"
        )

        print("\nWriting Licenses dataset...")

        write_partitioned_dataset(
            licenses_df,
            staged_licenses,
            "Licenses"
        )

        # 8. Replace production datasets only after validation
        replace_silver_datasets(
            [
                (staged_businesses, BUSINESSES_PATH),
                (staged_licenses, LICENSES_PATH)
            ],
            run_id
        )

    finally:

        # Remove incomplete staging directories, if any.
        for path in [staged_businesses, staged_licenses]:

            if path.exists():
                shutil.rmtree(path)

    # 9. Write rejected records
    REJECTED_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    rejected_df.to_csv(
        REJECTED_PATH,
        index=False
    )

    # 10. Pipeline summary
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

