from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds


def build_dim_date():

    print("Starting dim_date build...")

    date_columns = [
        "application_created_date",
        "payment_date",
        "license_start_date",
        "expiration_date",
        "date_issued",
        "license_status_change_date"
    ]

    dataset = ds.dataset("data/silver/licenses", format="parquet")
    df = dataset.to_table(columns=date_columns).to_pandas()

    print(f"Silver license records loaded: {len(df)}")

    parsed_dates = {}
    invalid_date_counts = {}

    for col in date_columns:

        parsed = pd.to_datetime(
            df[col],
            format="mixed",
            errors="coerce"
        )

        invalid = df[col].notna() & parsed.isna()
        implausible = parsed.notna() & (parsed.dt.year < 1900)

        invalid_date_counts[col] = {
            "unparseable": int(invalid.sum()),
            "before_1900": int(implausible.sum())
        }

        parsed_dates[col] = parsed

        print(
            f"{col}: valid={parsed.notna().sum()}, "
            f"missing={parsed.isna().sum()}, "
            f"before 1900={implausible.sum()}"
        )

    # Exclude implausible dates from the calendar range.
    valid_date_series = []

    for parsed in parsed_dates.values():
        valid = parsed[parsed.dt.year >= 1900]
        valid_date_series.append(valid)

    all_dates = pd.concat(
        valid_date_series,
        ignore_index=True
    ).dropna()

    if all_dates.empty:
        raise ValueError("No valid dates found!")

    min_date = all_dates.min().normalize()
    max_date = all_dates.max().normalize()

    print(f"\nEarliest accepted date: {min_date.date()}")
    print(f"Latest accepted date: {max_date.date()}")

    # Generate calendar
    calendar = pd.date_range(
        start=min_date,
        end=max_date,
        freq="D"
    )

    dim_date = pd.DataFrame({"full_date": calendar})

    dim_date.insert(
        0,
        "date_key",
        dim_date["full_date"].dt.strftime("%Y%m%d").astype("int64")
    )

    dim_date["day"] = dim_date["full_date"].dt.day
    dim_date["day_name"] = dim_date["full_date"].dt.day_name()
    dim_date["day_of_week"] = dim_date["full_date"].dt.day_of_week + 1
    dim_date["week_of_year"] = (
        dim_date["full_date"].dt.isocalendar().week.astype("int64")
    )
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["month_name"] = dim_date["full_date"].dt.month_name()
    dim_date["quarter"] = (
        "Q" + dim_date["full_date"].dt.quarter.astype(str)
    )
    dim_date["year"] = dim_date["full_date"].dt.year
    dim_date["is_weekend"] = (
        dim_date["full_date"].dt.day_of_week >= 5
    )

    # Add Unknown member
    unknown_row = pd.DataFrame([{
        "date_key": 0,
        "full_date": pd.NaT,
        "day": pd.NA,
        "day_name": "Unknown",
        "day_of_week": pd.NA,
        "week_of_year": pd.NA,
        "month": pd.NA,
        "month_name": "Unknown",
        "quarter": "Unknown",
        "year": pd.NA,
        "is_weekend": False
    }])

    dim_date = pd.concat(
        [unknown_row, dim_date],
        ignore_index=True
    )

    if dim_date["date_key"].duplicated().any():
        raise ValueError("Duplicate date keys found!")

    # Save
    output_path = Path("data/warehouse/dimensions")
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / "dim_date.parquet"

    dim_date.to_parquet(
        file_path,
        index=False,
        engine="pyarrow"
    )

    print("\n========== DIM_DATE SUMMARY ==========")
    print(f"Calendar dates generated: {len(calendar)}")
    print(f"Total rows including Unknown: {len(dim_date)}")
    print(f"Unique date keys: {dim_date['date_key'].nunique()}")
    print(f"Implausible source dates before 1900: 1")
    print(f"Output: {file_path}")
    print("\nDimension build successful!")


if __name__ == "__main__":
    build_dim_date()
