import pyarrow.dataset as ds

datasets = {
    "BUSINESSES": "data/silver/businesses",
    "LICENSES": "data/silver/licenses"
}

for name, path in datasets.items():

    print(f"\nChecking {name}...")

    try:
        dataset = ds.dataset(
            path,
            format="parquet",
            partitioning="hive"
        )

        print("Dataset discovered successfully.")
        print("Fragments:", len(list(dataset.get_fragments())))

        for fragment in dataset.get_fragments():

            print("Reading:", fragment.path)

            try:
                table = fragment.to_table()
                print("SUCCESS:", table.num_rows, "rows")

            except Exception as e:
                print("FAILED:", fragment.path)
                print("ERROR:", repr(e))

    except Exception as e:
        print("DATASET ERROR:", repr(e))