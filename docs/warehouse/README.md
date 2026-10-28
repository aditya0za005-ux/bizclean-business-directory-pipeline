# BizClean Dimensional Data Warehouse

## Architecture

The warehouse uses a star-schema design built from the Silver Parquet datasets.

### Fact table

`fact_business_license`

**Grain:** One row per source license record.

The source `license_id` is retained as the record identifier. The fact table connects to the dimensions through surrogate keys.

### Dimensions

- `dim_business`: business details.
- `dim_location`: physical address and coordinates.
- `dim_geography`: geographic classifications.
- `dim_license_type`: license category and description.
- `dim_business_activity`: business activity classification.
- `dim_date`: calendar attributes, reused for six date roles.

### Date handling

Missing and implausible dates use date key `0` (Unknown). The original Silver source is not modified.

### Data validation

The build process checks:
- Fact row count against Silver.
- Unique license IDs.
- Dimension natural-key uniqueness during joins.
- Foreign key validity.
- Parquet read-back.

### Local outputs

- `data/warehouse/dimensions/`
- `data/warehouse/facts/`
- `data/warehouse/reports/`
- `docs/warehouse/analytics_queries.sql`

## AWS deployment

Upload the warehouse dimensions and fact Parquet outputs to separate S3 prefixes. Create or update Glue crawlers for the warehouse tables, then run the SQL queries in `analytics_queries.sql` through Athena.

The SQL file is generated locally; Athena execution and screenshots are a separate AWS-console step.
