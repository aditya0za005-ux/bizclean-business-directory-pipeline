import pandas as pd

from src.validator import validate_business_data


def sample_data():
    return pd.DataFrame({
        "business_name": ["ACME STORES"],
        "address": ["123 MAIN ST"],
        "city": ["CHICAGO"],
        "state": ["IL"],
        "zip_code": ["60601"],
        "business_activity": ["RETAIL"]
    })


def test_valid_record_is_accepted():
    df = sample_data()

    clean, rejected = validate_business_data(df)

    assert len(clean) == 1
    assert len(rejected) == 0


def test_missing_business_name_is_rejected():
    df = sample_data()
    df.loc[0, "business_name"] = pd.NA

    clean, rejected = validate_business_data(df)

    assert len(clean) == 0
    assert "MISSING_BUSINESS_NAME" in rejected.iloc[0]["rejection_reasons"]


def test_missing_address_is_rejected():
    df = sample_data()
    df.loc[0, "address"] = pd.NA

    clean, rejected = validate_business_data(df)

    assert len(clean) == 0
    assert "MISSING_ADDRESS" in rejected.iloc[0]["rejection_reasons"]


def test_invalid_zip_code_is_rejected():
    df = sample_data()
    df.loc[0, "zip_code"] = "12AB"

    clean, rejected = validate_business_data(df)

    assert len(clean) == 0
    assert "INVALID_ZIP_CODE" in rejected.iloc[0]["rejection_reasons"]


def test_missing_zip_code_is_allowed():
    df = sample_data()
    df.loc[0, "zip_code"] = pd.NA

    clean, rejected = validate_business_data(df)

    assert len(clean) == 1
    assert len(rejected) == 0


def test_missing_business_activity_is_flagged_not_rejected():
    df = sample_data()
    df.loc[0, "business_activity"] = pd.NA

    clean, rejected = validate_business_data(df)

    assert len(clean) == 1
    assert len(rejected) == 0
    assert clean.iloc[0]["missing_business_activity"] == True


def test_multiple_validation_errors_are_recorded():
    df = sample_data()
    df.loc[0, "business_name"] = pd.NA
    df.loc[0, "address"] = pd.NA
    df.loc[0, "zip_code"] = "ABC"

    clean, rejected = validate_business_data(df)

    reasons = rejected.iloc[0]["rejection_reasons"]

    assert len(clean) == 0
    assert "MISSING_BUSINESS_NAME" in reasons
    assert "MISSING_ADDRESS" in reasons
    assert "INVALID_ZIP_CODE" in reasons
