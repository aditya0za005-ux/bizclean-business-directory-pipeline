import pandas as pd

DATA_PATH = "data/raw/chicago_business_licenses.csv"


def inspect_dataset():
    df = pd.read_csv(DATA_PATH, dtype=str)

    print("\n========== DATASET OVERVIEW ==========")

    print("Shape:", df.shape)

    print("\n========== COLUMN NAMES ==========")
    print(df.columns.tolist())

    print("\n========== DATA TYPES ==========")
    print(df.dtypes)

    print("\n========== FIRST 5 RECORDS ==========")
    print(df.head())

    print("\n========== MISSING VALUES ==========")
    print(df.isnull().sum())

    print("\n========== EXACT DUPLICATES ==========")
    print(df.duplicated().sum())

    print("\n========== DATASET MEMORY ==========")
    print(df.memory_usage(deep=True).sum() / 1024**2, "MB")


if __name__ == "__main__":
    inspect_dataset()