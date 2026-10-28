
import pandas as pd

df = pd.read_csv(
    "data/raw/chicago_business_licenses.csv",
    dtype=str
)

print("\n========== 1. DUPLICATE ID INVESTIGATION ==========")

duplicate_ids = df[df.duplicated("id", keep=False)]

print("Rows with duplicate IDs:", len(duplicate_ids))
print(duplicate_ids[
    ["id", "license_id", "account_number", "site_number"]
].sort_values("id").to_string(index=False))


print("\n========== 2. ACCOUNT TO BUSINESS MAPPING ==========")

account_name_counts = (
    df.groupby("account_number")["legal_name"]
    .nunique()
)

print("Accounts:", len(account_name_counts))
print("Accounts with multiple legal names:",
      (account_name_counts > 1).sum())

print("\nExamples:")
print(account_name_counts[account_name_counts > 1].head(10))


print("\n========== 3. ACCOUNT + SITE TO ADDRESS MAPPING ==========")

df["account_site"] = (
    df["account_number"] + "_" + df["site_number"]
)

site_address_counts = (
    df.groupby("account_site")["address"]
    .nunique()
)

print("Unique account-site combinations:",
      len(site_address_counts))

print("Combinations with multiple addresses:",
      (site_address_counts > 1).sum())


print("\n========== 4. LICENSE CODE MAPPING ==========")

license_mapping = (
    df.groupby("license_code")["license_description"]
    .nunique()
)

print("Unique license codes:", len(license_mapping))

print("Codes with multiple descriptions:",
      (license_mapping > 1).sum())


print("\n========== 5. ACTIVITY ID MAPPING ==========")

activity_mapping = (
    df.dropna(subset=["business_activity_id"])
    .groupby("business_activity_id")["business_activity"]
    .nunique()
)

print("Unique activity IDs:", len(activity_mapping))

print("IDs with multiple descriptions:",
      (activity_mapping > 1).sum())


print("\n========== 6. LICENSE RECORD GRAIN ==========")

print("Total records:", len(df))
print("Unique license IDs:", df["license_id"].nunique())
print("Duplicate license IDs:",
      df["license_id"].duplicated().sum())

print("\nRecords per account-site combination:")

records_per_site = (
    df.groupby("account_site")
    .size()
    .sort_values(ascending=False)
)

print(records_per_site.head(10))


print("\n========== INVESTIGATION COMPLETE ==========")
