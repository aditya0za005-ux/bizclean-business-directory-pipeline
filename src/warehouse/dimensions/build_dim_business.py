import pandas as pd
import pyarrow.dataset as ds
from pathlib import Path


def build_dim_business():

    print("Starting dim_business build...")

    # 1. Read the Silver businesses dataset
    source = ds.dataset(
        "data/silver/businesses",
        format="parquet",
        partitioning="hive"
    )

    df = source.to_table(
        columns=[
            "business_id",
            "business_name",
            "address",
            "city",
            "state"
        ]
    ).to_pandas()

    print("Silver records loaded:", len(df))

    # 2. Validate business IDs
    if df["business_id"].isna().any():
        raise ValueError("Null business IDs found.")

    if df["business_id"].duplicated().any():
        raise ValueError("Duplicate business IDs found.")

    # 3. Sort by source business ID
    df = df.sort_values(
        "business_id"
    ).reset_index(drop=True)

    # 4. Generate warehouse surrogate keys
    df.insert(
        0,
        "business_key",
        range(1, len(df) + 1)
    )

    # 5. Validate surrogate keys
    if df["business_key"].duplicated().any():
        raise ValueError("Duplicate business keys found.")

    # 6. Save dimension as Parquet
    output_dir = Path("data/warehouse/dimensions")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "dim_business.parquet"

    df.to_parquet(
        output_path,
        index=False,
        engine="pyarrow"
    )

    print("\n========== DIM_BUSINESS SUMMARY ==========")
    print("Total business records:", len(df))
    print("Unique business IDs:", df["business_id"].nunique())
    print("Unique business keys:", df["business_key"].nunique())
    print("Output:", output_path)
    print("\nDimension build successful!")


if __name__ == "__main__":
    build_dim_business()
