
import pandas as pd

DATA_PATH = "data/raw/chicago_business_licenses.csv"


def profile_businesses():

    df = pd.read_csv(DATA_PATH, dtype=str)

    print("\n========== UNIQUE CITIES ==========")
    print(df["city"].value_counts(dropna=False).head(15))

    print("\n========== UNIQUE STATES ==========")
    print(df["state"].value_counts(dropna=False))

    print("\n========== LICENSE STATUS ==========")
    print(df["license_status"].value_counts(dropna=False))

    print("\n========== BUSINESS ACTIVITY ==========")
    print(df["business_activity"].value_counts(dropna=False).head(15))

    print("\n========== BUSINESS NAME EXAMPLES ==========")
    print(df[
        ["legal_name", "doing_business_as_name"]
    ].head(15).to_string(index=False))

    print("\n========== ADDRESS EXAMPLES ==========")
    print(df["address"].head(15).to_string(index=False))

    print("\n========== ZIP CODE EXAMPLES ==========")
    print(df["zip_code"].value_counts(dropna=False).head(15))

    print("\n========== WHITESPACE CHECK ==========")

    for column in [
        "legal_name",
        "doing_business_as_name",
        "address",
        "city",
        "state",
        "zip_code"
    ]:
        values = df[column].dropna()

        whitespace_count = (
            values != values.str.strip()
        ).sum()

        print(f"{column}: {whitespace_count}")


if __name__ == "__main__":
    profile_businesses()
