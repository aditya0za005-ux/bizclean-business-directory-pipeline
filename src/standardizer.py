
import re
import pandas as pd


def normalize_text(value):
    """
    Standardize text by handling missing values,
    trimming whitespace and normalizing casing.
    """

    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if not value:
        return pd.NA

    # Handle known placeholder values
    if value.upper() in {
        "NULL",
        "N/A",
        "NONE",
        "[REDACTED FOR PRIVACY]"
    }:
        return pd.NA

    # Collapse multiple spaces into one
    value = re.sub(r"\s+", " ", value)

    return value.upper()


def standardize_business_data(df):
    """
    Standardize important business directory columns.
    """

    df = df.copy()

    # Standardize business names
    df["legal_name"] = df["legal_name"].apply(normalize_text)

    df["doing_business_as_name"] = (
        df["doing_business_as_name"].apply(normalize_text)
    )

    # Create canonical business name
    df["business_name"] = (
        df["doing_business_as_name"]
        .fillna(df["legal_name"])
    )

    # Standardize addresses
    df["address"] = df["address"].apply(normalize_text)

    # Standardize location information
    for column in ["city", "state"]:
        df[column] = df[column].apply(normalize_text)

    # Preserve postal codes as strings
    df["zip_code"] = df["zip_code"].apply(
        lambda x: str(x).strip() if pd.notna(x) else pd.NA
    )

    return df
