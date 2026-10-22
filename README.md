# BizClean – Business Directory Data Pipeline

An end-to-end AWS batch ETL pipeline that cleans, standardizes, validates, and deduplicates business license records from the City of Chicago public dataset.

The project uses Python, Pandas, Amazon S3, AWS Glue, AWS Glue Data Catalog, and Amazon Athena to transform raw business license records into analytics-ready Parquet datasets.

## Architecture

```text
City of Chicago Public Dataset
              |
              v
       Amazon S3 (Bronze)
          Raw CSV
              |
              v
       AWS Glue Python Shell
        Python + Pandas
              |
       Data Cleaning
       Standardization
       Validation
       Deduplication
              |
       +------+------+
       |             |
       v             v
  Amazon S3      Amazon S3
  (Silver)       (Rejected)
       |
       +----------------------+
       |                      |
       v                      v
  Businesses              Licenses
  Parquet                 Parquet
  Partitioned by city     Partitioned by city
       |                      |
       +----------+-----------+
                  |
                  v
          AWS Glue Data Catalog
                  |
                  v
             Athena
           SQL Analytics

       CloudWatch Logs
       ETL Monitoring
```
