import pandas as pd
import pyarrow.dataset as ds
from pathlib import Path


def build_dim_license_type():

    print("Starting dim_license_type build...")

    # 1. Read required columns from Silver licenses
    source = ds.dataset(
        "data/silver/licenses",
        format="parquet",
        partitioning="hive"
    )

    df = source.to_table(
        columns=[
            "license_code",
            "license_description"
        ]
    ).to_pandas()

    print("Silver license records loaded:", len(df))

    # 2. Remove duplicate license types
    dim_license_type = (
        df[
            ["license_code", "license_description"]
        ]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # 3. Validate license code consistency
    conflicts = (
        df.groupby("license_code", dropna=False)
        ["license_description"]
        .nunique(dropna=True)
    )

    if (conflicts > 1).any():
        raise ValueError(
            "A license code maps to multiple descriptions."
        )

    # 4. Generate surrogate keys
    dim_license_type = (
        dim_license_type
        .sort_values("license_code", na_position="last")
        .reset_index(drop=True)
    )

    dim_license_type.insert(
        0,
        "license_type_key",
        range(1, len(dim_license_type) + 1)
    )

    # 5. Validate uniqueness
    if dim_license_type["license_type_key"].duplicated().any():
        raise ValueError("Duplicate surrogate keys found.")

    if dim_license_type["license_code"].duplicated().any():
        raise ValueError("Duplicate license codes found.")

    # 6. Save dimension
    output_dir = Path("data/warehouse/dimensions")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "dim_license_type.parquet"

    dim_license_type.to_parquet(
        output_path,
        index=False,
        engine="pyarrow"
    )

    # 7. Summary
    print("\n========== DIM_LICENSE_TYPE SUMMARY ==========")
    print("Source records:", len(df))
    print("Unique license types:", len(dim_license_type))
    print(
        "Unique license type keys:",
        dim_license_type["license_type_key"].nunique()
    )
    print("Missing license codes:", dim_license_type["license_code"].isna().sum())
    print("Output:", output_path)

    print("\nDimension build successful!")


if __name__ == "__main__":
    build_dim_license_type()
