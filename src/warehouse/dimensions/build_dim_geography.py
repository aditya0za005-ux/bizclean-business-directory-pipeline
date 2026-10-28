import pandas as pd
import pyarrow.dataset as ds
from pathlib import Path


def build_dim_geography():

    print("Starting dim_geography build...")

    # 1. Read geographical columns from Silver licenses
    source = ds.dataset(
        "data/silver/licenses",
        format="parquet",
        partitioning="hive"
    )

    geography_columns = [
        "zip_code",
        "ward",
        "precinct",
        "police_district",
        "community_area",
        "community_area_name",
        "neighborhood",
        "ssa"
    ]

    df = source.to_table(
        columns=geography_columns
    ).to_pandas()

    print("Silver license records loaded:", len(df))

    # 2. Keep distinct geographical combinations
    dim_geography = (
        df[geography_columns]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    print(
        "Distinct geographical combinations:",
        len(dim_geography)
    )

    # 3. Generate surrogate keys
    dim_geography.insert(
        0,
        "geography_key",
        range(1, len(dim_geography) + 1)
    )

    # 4. Validate surrogate keys
    if dim_geography["geography_key"].duplicated().any():
        raise ValueError("Duplicate geography keys found.")

    # 5. Validate geographical combinations
    if dim_geography.duplicated(
        subset=geography_columns
    ).any():
        raise ValueError("Duplicate geographical combinations found.")

    # 6. Save as Parquet
    output_dir = Path("data/warehouse/dimensions")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "dim_geography.parquet"

    dim_geography.to_parquet(
        output_path,
        index=False,
        engine="pyarrow"
    )

    # 7. Summary
    print("\n========== DIM_GEOGRAPHY SUMMARY ==========")
    print("Source records:", len(df))
    print("Unique geographical combinations:", len(dim_geography))
    print("Unique geography keys:", dim_geography["geography_key"].nunique())

    print("\nMissing values:")

    for column in geography_columns:
        print(
            f"{column}: {dim_geography[column].isna().sum()}"
        )

    print("\nOutput:", output_path)
    print("\nDimension build successful!")


if __name__ == "__main__":
    build_dim_geography()
