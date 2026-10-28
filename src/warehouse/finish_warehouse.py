from pathlib import Path
import pandas as pd
import pyarrow.dataset as ds

ROOT = Path(".")
SILVER = ROOT / "data/silver/licenses"
DIM = ROOT / "data/warehouse/dimensions"
FACT_DIR = ROOT / "data/warehouse/facts"
REPORT_DIR = ROOT / "data/warehouse/reports"
DOCS_DIR = ROOT / "docs/warehouse"

for folder in [FACT_DIR, REPORT_DIR, DOCS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


def load_parquet(path):
    return pd.read_parquet(path)


def merge_dimension(fact, dimension, left_on, right_on, key_name):
    required = list(dict.fromkeys(right_on + [key_name]))
    lookup = dimension[required].copy()

    if lookup.duplicated(subset=right_on).any():
        raise ValueError(f"Duplicate natural keys found in {key_name}")

    return fact.merge(
        lookup,
        how="left",
        left_on=left_on,
        right_on=right_on,
        validate="many_to_one",
        sort=False
    )


def main():
    print("\n========== BUILDING FACT TABLE ==========")

    # Load Silver source
    source = ds.dataset(SILVER, format="parquet", partitioning="hive").to_table().to_pandas()
    expected_rows = len(source)

    print("Silver records:", expected_rows)

    if source["license_id"].isna().any():
        raise ValueError("Null license_id found in Silver")

    if source["license_id"].duplicated().any():
        raise ValueError("Duplicate license_id found in Silver")

    fact = source[[
        "license_id",
        "business_id",
        "address",
        "city",
        "state",
        "license_code",
        "license_description",
        "business_activity_id",
        "business_activity",
        "license_status",
        "zip_code",
        "ward",
        "precinct",
        "police_district",
        "community_area",
        "community_area_name",
        "neighborhood",
        "ssa"
    ]].copy()

    # Load dimensions
    business = load_parquet(DIM / "dim_business.parquet")
    location = load_parquet(DIM / "dim_location.parquet")
    geography = load_parquet(DIM / "dim_geography.parquet")
    license_type = load_parquet(DIM / "dim_license_type.parquet")
    activity = load_parquet(DIM / "dim_business_activity.parquet")
    date_dim = load_parquet(DIM / "dim_date.parquet")

    # Join business dimension
    fact = merge_dimension(
        fact, business,
        ["business_id"], ["business_id"],
        "business_key"
    )

    # Join physical location dimension
    fact = merge_dimension(
        fact, location,
        ["address", "city", "state"],
        ["address", "city", "state"],
        "location_key"
    )

    # Join geography dimension
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

    fact = merge_dimension(
        fact, geography,
        geography_columns,
        geography_columns,
        "geography_key"
    )

    # Join license type dimension
    fact = merge_dimension(
        fact, license_type,
        ["license_code", "license_description"],
        ["license_code", "license_description"],
        "license_type_key"
    )

    # Join business activity dimension
    fact = merge_dimension(
        fact, activity,
        ["business_activity_id", "business_activity"],
        ["business_activity_id", "business_activity"],
        "activity_key"
    )

    # Join all six role-playing date keys
    date_columns = {
        "application_created_date": "application_date_key",
        "payment_date": "payment_date_key",
        "license_start_date": "license_start_date_key",
        "expiration_date": "expiration_date_key",
        "date_issued": "date_issued_key",
        "license_status_change_date": "status_change_date_key"
    }

    date_lookup = date_dim.dropna(subset=["full_date"]).copy()
    date_lookup["full_date"] = pd.to_datetime(date_lookup["full_date"]).dt.normalize()

    date_mapping = dict(zip(
        date_lookup["full_date"],
        date_lookup["date_key"]
    ))

    invalid_date_counts = {}

    for source_column, key_column in date_columns.items():
        parsed = pd.to_datetime(
            source[source_column],
            format="mixed",
            errors="coerce"
        ).dt.normalize()

        implausible = parsed.notna() & (parsed.dt.year < 1900)
        invalid_date_counts[source_column] = int(implausible.sum())

        keys = parsed.map(date_mapping).fillna(0).astype("int64")
        fact[key_column] = keys

    # Select final fact columns
    fact_columns = [
        "license_id",
        "business_id",
        "business_key",
        "location_key",
        "geography_key",
        "license_type_key",
        "activity_key",
        *date_columns.values(),
        "license_status",
        "license_code"
    ]

    fact = fact[fact_columns].copy()

    # Validate fact grain and dimension references
    if len(fact) != expected_rows:
        raise ValueError("Fact row count does not match Silver row count")

    if fact["license_id"].duplicated().any():
        raise ValueError("Duplicate license_id in fact table")

    dimension_keys = {
        "business_key": set(business["business_key"]),
        "location_key": set(location["location_key"]),
        "geography_key": set(geography["geography_key"]),
        "license_type_key": set(license_type["license_type_key"]),
        "activity_key": set(activity["activity_key"])
    }

    for column, valid_keys in dimension_keys.items():
        missing = fact[column].isna().sum()
        invalid = (~fact[column].isin(valid_keys)).sum()

        print(f"{column}: missing={missing}, invalid={invalid}")

        if missing or invalid:
            raise ValueError(f"Foreign key validation failed: {column}")

    for column in date_columns.values():
        invalid = (~fact[column].isin(set(date_dim["date_key"]))).sum()

        if invalid:
            raise ValueError(f"Date foreign key validation failed: {column}")

    # Save fact table
    fact_path = FACT_DIR / "fact_business_license.parquet"
    fact.to_parquet(fact_path, index=False, engine="pyarrow")

    print("\nFact table created:", fact_path)
    print("Fact rows:", len(fact))
    print("Unique licenses:", fact["license_id"].nunique())

    # Re-read fact to verify the saved file
    saved_fact = pd.read_parquet(fact_path)

    if len(saved_fact) != expected_rows:
        raise ValueError("Saved fact row count verification failed")

    print("Saved Parquet read-back: PASSED")

    # Build local analytical outputs
    print("\n========== GENERATING ANALYTICS ==========")

    city_report = (
        saved_fact[["location_key"]]
        .merge(
            location[["location_key", "city"]],
            on="location_key",
            how="left",
            validate="many_to_one"
        )
        .groupby("city", dropna=False)
        .size()
        .reset_index(name="license_count")
        .sort_values("license_count", ascending=False)
    )
    city_report.to_csv(REPORT_DIR / "licenses_by_city.csv", index=False)

    status_report = (
        saved_fact.groupby("license_status", dropna=False)
        .size()
        .reset_index(name="license_count")
        .sort_values("license_count", ascending=False)
    )
    status_report.to_csv(REPORT_DIR / "licenses_by_status.csv", index=False)

    type_report = (
        saved_fact.groupby("license_type_key")
        .size()
        .reset_index(name="license_count")
        .merge(
            license_type[["license_type_key", "license_code", "license_description"]],
            on="license_type_key",
            how="left",
            validate="one_to_one"
        )
        .sort_values("license_count", ascending=False)
    )
    type_report.to_csv(REPORT_DIR / "licenses_by_type.csv", index=False)

    issued_dates = saved_fact["date_issued_key"]
    issued_report = (
        issued_dates[issued_dates != 0]
        .astype(str)
        .str[:4]
        .value_counts()
        .sort_index()
        .rename_axis("year")
        .reset_index(name="license_count")
    )
    issued_report.to_csv(REPORT_DIR / "licenses_by_year_issued.csv", index=False)

    print("Created licenses_by_city.csv")
    print("Created licenses_by_status.csv")
    print("Created licenses_by_type.csv")
    print("Created licenses_by_year_issued.csv")

    # Generate Athena SQL
    sql = """
-- BIZCLEAN WAREHOUSE ANALYTICS
-- Run after uploading warehouse Parquet folders to S3
-- and creating/querying the corresponding Glue Catalog tables.

-- 1. Total licenses by city
SELECT l.city, COUNT(*) AS license_count
FROM fact_business_license f
JOIN dim_location l ON f.location_key = l.location_key
GROUP BY l.city
ORDER BY license_count DESC;

-- 2. Licenses by status
SELECT license_status, COUNT(*) AS license_count
FROM fact_business_license
GROUP BY license_status
ORDER BY license_count DESC;

-- 3. Most common license types
SELECT d.license_code, d.license_description,
       COUNT(*) AS license_count
FROM fact_business_license f
JOIN dim_license_type d
  ON f.license_type_key = d.license_type_key
GROUP BY d.license_code, d.license_description
ORDER BY license_count DESC;

-- 4. Licenses issued per year
SELECT d.year, COUNT(*) AS license_count
FROM fact_business_license f
JOIN dim_date d ON f.date_issued_key = d.date_key
WHERE f.date_issued_key <> 0
GROUP BY d.year
ORDER BY d.year;

-- 5. Business activity analysis
SELECT a.business_activity, COUNT(*) AS license_count
FROM fact_business_license f
JOIN dim_business_activity a
  ON f.activity_key = a.activity_key
GROUP BY a.business_activity
ORDER BY license_count DESC
LIMIT 20;

-- 6. License expiration analysis
SELECT d.year, d.month, COUNT(*) AS expiring_licenses
FROM fact_business_license f
JOIN dim_date d
  ON f.expiration_date_key = d.date_key
WHERE f.expiration_date_key <> 0
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 7. Geography analysis
SELECT g.neighborhood, g.community_area_name,
       COUNT(*) AS license_count
FROM fact_business_license f
JOIN dim_geography g
  ON f.geography_key = g.geography_key
GROUP BY g.neighborhood, g.community_area_name
ORDER BY license_count DESC;
"""

    (DOCS_DIR / "analytics_queries.sql").write_text(
        sql.strip() + "\n",
        encoding="utf-8"
    )

    # Warehouse validation report
    validation = [
        "BIZCLEAN WAREHOUSE VALIDATION",
        "============================",
        f"Silver source rows: {expected_rows}",
        f"Fact rows: {len(saved_fact)}",
        f"Unique license IDs: {saved_fact['license_id'].nunique()}",
        f"Fact row count matches Silver: {len(saved_fact) == expected_rows}",
        f"License IDs unique: {saved_fact['license_id'].is_unique}",
        "",
        "DIMENSION ROW COUNTS"
    ]

    for name, dimension in [
        ("dim_business", business),
        ("dim_location", location),
        ("dim_geography", geography),
        ("dim_license_type", license_type),
        ("dim_business_activity", activity),
        ("dim_date", date_dim)
    ]:
        validation.append(f"{name}: {len(dimension)}")

    validation.extend(["", "INVALID DATES BEFORE 1900"])

    for column, count in invalid_date_counts.items():
        validation.append(f"{column}: {count}")

    validation.extend([
        "",
        "All dimension foreign keys validated: YES",
        "Saved fact read-back validated: YES"
    ])

    report_text = "\n".join(validation)
    (REPORT_DIR / "warehouse_validation.txt").write_text(
        report_text,
        encoding="utf-8"
    )

    # Warehouse documentation
    documentation = """
# BizClean Dimensional Data Warehouse

## Architecture

The warehouse uses a star-schema design built from the Silver Parquet datasets.

### Fact table

`fact_business_license`

**Grain:** One row per source license record.

The source `license_id` is retained as the record identifier. The fact table connects to the dimensions through surrogate keys.

### Dimensions

- `dim_business`: business details.
- `dim_location`: physical address and coordinates.
- `dim_geography`: geographic classifications.
- `dim_license_type`: license category and description.
- `dim_business_activity`: business activity classification.
- `dim_date`: calendar attributes, reused for six date roles.

### Date handling

Missing and implausible dates use date key `0` (Unknown). The original Silver source is not modified.

### Data validation

The build process checks:
- Fact row count against Silver.
- Unique license IDs.
- Dimension natural-key uniqueness during joins.
- Foreign key validity.
- Parquet read-back.

### Local outputs

- `data/warehouse/dimensions/`
- `data/warehouse/facts/`
- `data/warehouse/reports/`
- `docs/warehouse/analytics_queries.sql`

## AWS deployment

Upload the warehouse dimensions and fact Parquet outputs to separate S3 prefixes. Create or update Glue crawlers for the warehouse tables, then run the SQL queries in `analytics_queries.sql` through Athena.

The SQL file is generated locally; Athena execution and screenshots are a separate AWS-console step.
"""

    (DOCS_DIR / "README.md").write_text(
        documentation.strip() + "\n",
        encoding="utf-8"
    )

    print("\n========== FINAL SUMMARY ==========")
    print("Fact records:", len(saved_fact))
    print("Dimensions connected: 6")
    print("Foreign key validation: PASSED")
    print("Fact Parquet read-back: PASSED")
    print("Analytics CSV files: 4")
    print("Athena SQL file: docs/warehouse/analytics_queries.sql")
    print("Documentation: docs/warehouse/README.md")
    print("Validation report: data/warehouse/reports/warehouse_validation.txt")
    print("\nWAREHOUSE BUILD COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
