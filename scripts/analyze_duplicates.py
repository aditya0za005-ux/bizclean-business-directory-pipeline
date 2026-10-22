
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.standardizer import standardize_business_data
from src.validator import validate_business_data


DATA_PATH = "data/raw/chicago_business_licenses.csv"


def main():

    df = pd.read_csv(DATA_PATH, dtype=str)

    standardized_df = standardize_business_data(df)
    clean_df, rejected_df = validate_business_data(standardized_df)

    business_key = [
        "business_name",
        "address",
        "city",
        "state"
    ]

    groups = (
        clean_df.groupby(business_key, dropna=False)
        .agg(
            record_count=("license_id", "size"),
            account_count=("account_number", "nunique"),
            site_count=("site_number", "nunique"),
            license_id_count=("license_id", "nunique"),
            license_number_count=("license_number", "nunique")
        )
        .reset_index()
    )

    repeated = groups[groups["record_count"] > 1].copy()

    print("\n========== BUSINESS GROUP CLASSIFICATION ==========")

    print("Repeated business groups:", len(repeated))

    print(
        "Groups with multiple accounts:",
        (repeated["account_count"] > 1).sum()
    )

    print(
        "Groups with multiple sites:",
        (repeated["site_count"] > 1).sum()
    )

    print(
        "Groups with multiple license IDs:",
        (repeated["license_id_count"] > 1).sum()
    )

    print(
        "Groups with multiple license numbers:",
        (repeated["license_number_count"] > 1).sum()
    )

    print("\n========== TOP 15 GROUPS ==========")

    print(
        repeated.sort_values(
            "record_count",
            ascending=False
        ).head(15).to_string(index=False)
    )

    print("\n========== SOURCE IDENTIFIER CHECK ==========")

    print(
        "Duplicate source IDs:",
        clean_df["id"].duplicated().sum()
    )

    print(
        "Duplicate license IDs:",
        clean_df["license_id"].duplicated().sum()
    )

    print(
        "Duplicate license numbers:",
        clean_df["license_number"].duplicated().sum()
    )

    # Investigate duplicate source IDs
    print("\n========== DUPLICATE SOURCE ID EXAMPLES ==========")

    duplicate_ids = clean_df[
        clean_df["id"].duplicated(keep=False)
    ]

    if duplicate_ids.empty:
        print("No duplicate source IDs found.")
    else:
        print(
            duplicate_ids[
                [
                    "id",
                    "license_id",
                    "business_name",
                    "address",
                    "license_number"
                ]
            ].sort_values("id").to_string(index=False)
        )

    # Investigate duplicate license numbers
    print("\n========== DUPLICATE LICENSE NUMBER EXAMPLES ==========")

    duplicate_numbers = clean_df[
        clean_df["license_number"].duplicated(keep=False)
    ]

    if duplicate_numbers.empty:
        print("No duplicate license numbers found.")
    else:
        print(
            duplicate_numbers[
                [
                    "license_number",
                    "id",
                    "license_id",
                    "business_name",
                    "address",
                    "account_number"
                ]
            ].head(30).to_string(index=False)
        )


if __name__ == "__main__":
    main()
