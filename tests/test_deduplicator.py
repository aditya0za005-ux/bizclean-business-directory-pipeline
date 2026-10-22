import pandas as pd

from src.deduplicator import (
    generate_business_id,
    create_business_and_license_tables
)


def sample_data():
    return pd.DataFrame({
        "business_name": [
            "ACME STORES",
            "ACME STORES",
            "BETA FOODS"
        ],
        "address": [
            "123 MAIN ST",
            "123 MAIN ST",
            "456 OAK ST"
        ],
        "city": [
            "CHICAGO",
            "CHICAGO",
            "CHICAGO"
        ],
        "state": [
            "IL",
            "IL",
            "IL"
        ],
        "license_id": [
            "L001",
            "L002",
            "L003"
        ]
    })


def test_same_business_identity_generates_same_id():
    df = sample_data()

    id_1 = generate_business_id(df.iloc[0])
    id_2 = generate_business_id(df.iloc[1])

    assert id_1 == id_2


def test_different_businesses_generate_different_ids():
    df = sample_data()

    id_1 = generate_business_id(df.iloc[0])
    id_2 = generate_business_id(df.iloc[2])

    assert id_1 != id_2


def test_business_table_contains_unique_businesses():
    df = sample_data()

    businesses, licenses = create_business_and_license_tables(df)

    assert len(businesses) == 2
    assert businesses["business_id"].is_unique


def test_license_table_preserves_all_records():
    df = sample_data()

    businesses, licenses = create_business_and_license_tables(df)

    assert len(licenses) == 3
    assert licenses["license_id"].is_unique


def test_business_and_license_tables_share_business_ids():
    df = sample_data()

    businesses, licenses = create_business_and_license_tables(df)

    assert set(licenses["business_id"]).issubset(
        set(businesses["business_id"])
    )
