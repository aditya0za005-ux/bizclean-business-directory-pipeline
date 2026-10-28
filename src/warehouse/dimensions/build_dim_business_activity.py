from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds


def build_dim_business_activity():

    print("Starting dim_business_activity build...")

    # 1. Load required columns from Silver licenses
    source_path = Path("data/silver/licenses")

    dataset = ds.dataset(source_path, format="parquet")

    df = dataset.to_table(
        columns=[
            "business_activity_id",
            "business_activity"
        ]
    ).to_pandas()

    print(f"Silver license records loaded: {len(df)}")

    # 2. Identify distinct business activities
    dim_activity = df.drop_duplicates(
        subset=[
            "business_activity_id",
            "business_activity"
        ]
    ).copy()

    # 3. Validate activity ID-description mapping
    activity_mapping = (
        dim_activity
        .groupby("business_activity_id", dropna=True)["business_activity"]
        .nunique(dropna=True)
    )

    conflicting_ids = activity_mapping[activity_mapping > 1]

    if not conflicting_ids.empty:
        raise ValueError(
            f"Business activity IDs map to multiple descriptions: "
            f"{len(conflicting_ids)}"
        )

    # 4. Sort records consistently
    dim_activity = dim_activity.sort_values(
        by=["business_activity_id", "business_activity"],
        na_position="last"
    ).reset_index(drop=True)

    # 5. Generate surrogate keys
    dim_activity.insert(
        0,
        "activity_key",
        range(1, len(dim_activity) + 1)
    )

    # 6. Validate surrogate keys
    if dim_activity["activity_key"].duplicated().any():
        raise ValueError("Duplicate activity keys found!")

    # 7. Validate source activity IDs
    unique_ids = dim_activity["business_activity_id"].nunique(
        dropna=True
    )

    print("\n========== DIM_BUSINESS_ACTIVITY SUMMARY ==========")
    print(f"Source records: {len(df)}")
    print(f"Unique activity combinations: {len(dim_activity)}")
    print(f"Unique non-null activity IDs: {unique_ids}")
    print(
        "Missing activity IDs:",
        dim_activity["business_activity_id"].isna().sum()
    )
    print(
        "Missing activity descriptions:",
        dim_activity["business_activity"].isna().sum()
    )
    print(
        "Unique activity keys:",
        dim_activity["activity_key"].nunique()
    )

    # 8. Save dimension
    output_path = Path("data/warehouse/dimensions")
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / "dim_business_activity.parquet"

    dim_activity.to_parquet(
        file_path,
        index=False,
        engine="pyarrow"
    )

    print(f"\nOutput: {file_path}")
    print("\nDimension build successful!")


if __name__ == "__main__":
    build_dim_business_activity()
