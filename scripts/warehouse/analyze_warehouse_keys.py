import pandas as pd

df = pd.read_csv(
    "data/raw/chicago_business_licenses.csv",
    dtype=str
)

columns_to_check = [
    "id",
    "license_id",
    "account_number",
    "site_number",
    "license_number",
    "license_code",
    "business_activity_id"
]

print("========== KEY ANALYSIS ==========")

for col in columns_to_check:
    print(f"\nColumn: {col}")
    print("Total records:", len(df))
    print("Unique values:", df[col].nunique())
    print("Missing values:", df[col].isna().sum())
    print("Duplicate values:", df[col].duplicated().sum())

print("\n========== ACCOUNT AND SITE ANALYSIS ==========")

print(
    "Unique account numbers:",
    df["account_number"].nunique()
)

print(
    "Unique account + site combinations:",
    df[["account_number", "site_number"]]
    .drop_duplicates()
    .shape[0]
)

print("\n========== LICENSE STATUS ==========")

print(df["license_status"].value_counts(dropna=False).head(20))

print("\n========== LICENSE TYPES ==========")

print(df["license_description"].value_counts().head(15))

print("\n========== DATE SAMPLES ==========")

date_columns = [
    "application_created_date",
    "payment_date",
    "license_start_date",
    "expiration_date",
    "date_issued",
    "license_status_change_date"
]

for col in date_columns:
    print(f"\n{col}:")
    print(df[col].dropna().head(5).tolist())