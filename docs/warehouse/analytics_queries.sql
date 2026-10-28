-- BIZCLEAN WAREHOUSE ANALYTICS
-- Run after uploading warehouse Parquet folders to S3
-- and creating/querying the corresponding Glue Catalog tables.

-- 1. Total licenses by city
SELECT l.city, COUNT(*) AS license_count
FROM fact_business_license f
JOIN dim_location l ON f.location_key = l.location_key
GROUP BY l.city
ORDER BY license_count DESC;

-- 2. Licenses by status
SELECT license_status, COUNT(*) AS license_count
FROM fact_business_license
GROUP BY license_status
ORDER BY license_count DESC;

-- 3. Most common license types
SELECT d.license_code, d.license_description,
       COUNT(*) AS license_count
FROM fact_business_license f
JOIN dim_license_type d
  ON f.license_type_key = d.license_type_key
GROUP BY d.license_code, d.license_description
ORDER BY license_count DESC;

-- 4. Licenses issued per year
SELECT d.year, COUNT(*) AS license_count
FROM fact_business_license f
JOIN dim_date d ON f.date_issued_key = d.date_key
WHERE f.date_issued_key <> 0
GROUP BY d.year
ORDER BY d.year;

-- 5. Business activity analysis
SELECT a.business_activity, COUNT(*) AS license_count
FROM fact_business_license f
JOIN dim_business_activity a
  ON f.activity_key = a.activity_key
GROUP BY a.business_activity
ORDER BY license_count DESC
LIMIT 20;

-- 6. License expiration analysis
SELECT d.year, d.month, COUNT(*) AS expiring_licenses
FROM fact_business_license f
JOIN dim_date d
  ON f.expiration_date_key = d.date_key
WHERE f.expiration_date_key <> 0
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 7. Geography analysis
SELECT g.neighborhood, g.community_area_name,
       COUNT(*) AS license_count
FROM fact_business_license f
JOIN dim_geography g
  ON f.geography_key = g.geography_key
GROUP BY g.neighborhood, g.community_area_name
ORDER BY license_count DESC;
