
import pandas as pd
import re


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

        if pd.notna(zip_code):
            if not re.fullmatch(r"\d{5}", str(zip_code)):
                reasons.append("INVALID_ZIP_CODE")

        rejection_reasons.append(reasons)

    df["rejection_reasons"] = rejection_reasons

    rejected_df = df[
        df["rejection_reasons"].apply(len) > 0
    ].copy()

    clean_df = df[
        df["rejection_reasons"].apply(len) == 0
    ].copy()

    # Missing business activity is optional,
    # so we flag it instead of rejecting it.
    clean_df["missing_business_activity"] = (
        clean_df["business_activity"].isna()
    )

    return clean_df, rejected_df
