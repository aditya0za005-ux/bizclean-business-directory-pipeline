
import pyarrow.dataset as ds

datasets = {
    "BUSINESSES": "data/silver/businesses",
    "LICENSES": "data/silver/licenses"
}

for name, path in datasets.items():

    print(f"\n{'=' * 60}")
    print(f"{name} SILVER DATASET")
    print(f"{'=' * 60}")

    dataset = ds.dataset(
        path,
        format="parquet",
        partitioning="hive"
    )

    print("\nSCHEMA:")
    print(dataset.schema)

    print("\nTOTAL ROWS:")
    print(dataset.count_rows())

    print("\nSAMPLE RECORDS:")
    table = dataset.head(5)
    print(table.to_pandas().to_string(index=False))

    print("\nPARTITION INFORMATION:")
    print(dataset.partitioning)
