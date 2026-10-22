import pandas as pd
from src.standardizer import normalize_text, standardize_business_data


def test_normalize_text_trims_and_uppercases():
    assert normalize_text("  acme   stores  ") == "ACME STORES"


def test_normalize_text_handles_missing_values():
    assert pd.isna(normalize_text(None))
    assert pd.isna(normalize_text("N/A"))
    assert pd.isna(normalize_text("[REDACTED FOR PRIVACY]"))


def test_business_name_prefers_dba_name():
    df = pd.DataFrame({
        "legal_name": ["ACME LLC"],
        "doing_business_as_name": ["ACME STORES"],
        "address": ["123 main st"],
        "city": ["chicago"],
        "state": ["il"],
        "zip_code": ["00601"]
    })

    result = standardize_business_data(df)

    assert result.loc[0, "business_name"] == "ACME STORES"


def test_business_name_falls_back_to_legal_name():
    df = pd.DataFrame({
        "legal_name": ["ACME LLC"],
        "doing_business_as_name": [None],
        "address": ["123 main st"],
        "city": ["chicago"],
        "state": ["il"],
        "zip_code": ["00601"]
    })

    result = standardize_business_data(df)

    assert result.loc[0, "business_name"] == "ACME LLC"


def test_zip_code_preserves_leading_zero():
    df = pd.DataFrame({
        "legal_name": ["ACME LLC"],
        "doing_business_as_name": [None],
        "address": ["123 main st"],
        "city": ["chicago"],
        "state": ["il"],
        "zip_code": ["00601"]
    })

    result = standardize_business_data(df)

    assert result.loc[0, "zip_code"] == "00601"
