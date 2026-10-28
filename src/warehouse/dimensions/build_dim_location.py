import pandas as pd
import pyarrow.dataset as ds
from pathlib import Path


def build_dim_location():

    print("Starting dim_location build...")

    # 1. Read required columns from Silver licenses
    source = ds.dataset(
        "data/silver/licenses",
        format="parquet",
        partitioning="hive"
    )

    df = source.to_table(
        columns=[
            "address",
            "city",
            "state",
            "latitude",
            "longitude"
        ]
    ).to_pandas()

    print("Silver license records loaded:", len(df))

    # 2. Check geographical coordinate consistency
    location_columns = ["address", "city", "state"]

    for column in ["latitude", "longitude"]:

        conflicts = (
            df.groupby(
                location_columns,
                dropna=False
            )[column]
            .nunique(dropna=True)
        )

        if (conflicts > 1).any():
            raise ValueError(
                f"Conflicting {column} values found for the same location."
            )

    # 3. Keep one record per physical address
    dim_location = (
        df.drop_duplicates(
            subset=location_columns
        )[
            [
                "address",
                "city",
                "state",
                "latitude",
                "longitude"
            ]
        ]
        .sort_values(location_columns, na_position="last")
        .reset_index(drop=True)
    )

    # 4. Generate surrogate keys
    dim_location.insert(
        0,
        "location_key",
        range(1, len(dim_location) + 1)
    )

    # 5. Validate uniqueness
    if dim_location["location_key"].duplicated().any():
        raise ValueError("Duplicate location keys found.")

    if dim_location.duplicated(subset=location_columns).any():
        raise ValueError("Duplicate physical locations found.")

    # 6. Save as Parquet
    output_dir = Path("data/warehouse/dimensions")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "dim_location.parquet"

    dim_location.to_parquet(
        output_path,
        index=False,
        engine="pyarrow"
    )

    print("\n========== DIM_LOCATION SUMMARY ==========")
    print("Total source records:", len(df))
    print("Unique physical locations:", len(dim_location))
    print("Unique location keys:", dim_location["location_key"].nunique())
    print("Missing coordinates:", dim_location["latitude"].isna().sum())
    print("Output:", output_path)
    print("\nDimension build successful!")


if __name__ == "__main__":
    build_dim_location()
