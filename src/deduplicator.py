
import hashlib
import pandas as pd


BUSINESS_KEY = [
    "business_name",
    "address",
    "city",
    "state"
]


def generate_business_id(row):
    """
    Generate a deterministic ID from the business identity.
    The same normalized identity produces the same ID.
    """

    key = "|".join(
        str(row[column])
        for column in BUSINESS_KEY
    )

    return hashlib.sha256(
        key.encode("utf-8")
    ).hexdigest()[:16]


def create_business_and_license_tables(clean_df):

    df = clean_df.copy()

    # Generate a stable business identifier
    df["business_id"] = df.apply(
        generate_business_id,
        axis=1
    )

    # Business-level table: one row per business identity
    businesses_df = (
        df[["business_id"] + BUSINESS_KEY]
        .drop_duplicates(subset=["business_id"])
        .reset_index(drop=True)
    )

    # License-level table: preserve every valid license record
    licenses_df = df.copy()

    return businesses_df, licenses_df
