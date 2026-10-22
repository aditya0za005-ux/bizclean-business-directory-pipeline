
import re
import hashlib
import pandas as pd
import awswrangler as wr
import boto3


BUCKET = "bizclean-chicago-licenses-2026-364569"

SOURCE_PATH = (
    f"s3://{BUCKET}/bronze/chicago_business_licenses.csv"
)

BUSINESSES_PATH = f"s3://{BUCKET}/silver/businesses/"
LICENSES_PATH = f"s3://{BUCKET}/silver/licenses/"
REJECTED_PATH = f"s3://{BUCKET}/rejected/rejected_records.csv"


def normalize_text(value):
    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if not value or value.upper() in {
        "NULL", "N/A", "NONE", "[REDACTED FOR PRIVACY]"
    }:
        return pd.NA

    value = re.sub(r"\s+", " ", value)
    return value.upper()


def standardize_business_data(df):
    df = df.copy()

    for column in [
        "legal_name",
        "doing_business_as_name",
        "address",
        "city",
        "state"
    ]:
        df[column] = df[column].apply(normalize_text)

    df["business_name"] = (
        df["doing_business_as_name"].fillna(df["legal_name"])
    )

    df["zip_code"] = df["zip_code"].apply(
        lambda x: str(x).strip() if pd.notna(x) else pd.NA
    )

    return df


def validate_business_data(df):
    df = df.copy()
    rejection_reasons = []

    for _, row in df.iterrows():
        reasons = []

        if pd.isna(row["business_name"]):
            reasons.append("MISSING_BUSINESS_NAME")

        if pd.isna(row["address"]):
            reasons.append("MISSING_ADDRESS")

        if pd.isna(row["city"]):
            reasons.append("MISSING_CITY")

        if pd.isna(row["state"]):
            reasons.append("MISSING_STATE")

        zip_code = row["zip_code"]

        if pd.notna(zip_code) and not re.fullmatch(
            r"\d{5}", str(zip_code)
        ):
            reasons.append("INVALID_ZIP_CODE")

        rejection_reasons.append(reasons)

    df["rejection_reasons"] = rejection_reasons

    rejected_df = df[
        df["rejection_reasons"].apply(len) > 0
    ].copy()

    clean_df = df[
        df["rejection_reasons"].apply(len) == 0
    ].copy()

    clean_df["missing_business_activity"] = (
        clean_df["business_activity"].isna()
    )

    return clean_df, rejected_df


BUSINESS_KEY = [
    "business_name", "address", "city", "state"
]


def generate_business_id(row):
    key = "|".join(str(row[column]) for column in BUSINESS_KEY)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def create_business_and_license_tables(clean_df):
    df = clean_df.copy()

    df["business_id"] = df.apply(
        generate_business_id, axis=1
    )

    businesses_df = (
        df[["business_id"] + BUSINESS_KEY]
        .drop_duplicates(subset=["business_id"])
        .reset_index(drop=True)
    )

    return businesses_df, df


def run_pipeline():
    print("Starting BizClean Glue ETL job")

    df = wr.s3.read_csv(
        path=SOURCE_PATH,
        dtype=str
    )

    print("Extracted records:", len(df))

    standardized_df = standardize_business_data(df)

    clean_df, rejected_df = validate_business_data(
        standardized_df
    )

    businesses_df, licenses_df = (
        create_business_and_license_tables(clean_df)
    )

    wr.s3.to_parquet(
        df=businesses_df,
        path=BUSINESSES_PATH,
        dataset=True,
        partition_cols=["city"],
        mode="overwrite"
    )

    wr.s3.to_parquet(
        df=licenses_df,
        path=LICENSES_PATH,
        dataset=True,
        partition_cols=["city"],
        mode="overwrite"
    )

    wr.s3.to_csv(
        df=rejected_df,
        path=REJECTED_PATH,
        index=False
    )

    assert len(clean_df) + len(rejected_df) == len(df)
    assert businesses_df["business_id"].is_unique
    assert licenses_df["license_id"].is_unique

    print("Raw records:", len(df))
    print("Clean license records:", len(licenses_df))
    print("Unique businesses:", len(businesses_df))
    print("Rejected records:", len(rejected_df))
    print("All reconciliation checks passed.")
    print("BizClean Glue ETL job completed.")


if __name__ == "__main__":
    run_pipeline()
