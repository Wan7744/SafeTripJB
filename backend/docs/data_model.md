# SafeTrip JB Data Model

## Core Models

### Region
- `region_id`: stable text identifier such as `jeonju`
- `region_name`: public Korean display name
- `parent_region_id`: parent administrative region
- `saturation_status`: one of `safe`, `normal`, `caution`, `crowded`

### Festival
- `festival_id`: stable text identifier
- `region_id`: owning region
- `name`: festival name
- `start_date`, `end_date`: festival period
- `visitor_growth_rate`: comparison result against baseline period
- `expected_visitor_count`: model or rule-based prediction
- `source_id`: source dataset

### CongestionIndex
- `observed_at`: date for the calculated index
- `region_id`: target region
- `traffic_congestion_level`: transport-side status
- `tourist_spot_congestion_level`: tourism-side status
- `restaurant_wait_index`: local wait-pressure proxy
- `saturation_status`: final 4-step status
- `is_estimated`: true when fallback or prediction is used

### DataSource
- `source_id`: stable source identifier
- `provider`: public provider name
- `dataset_name`: dataset title
- `endpoint`: API or file source
- `reference_date`: provider reference date
- `updated_at`: local update timestamp
- `is_estimated`: true when this data is generated from fallback or sample input

## Storage Rules

- PostgreSQL owns master tables: `regions`, `festivals`, `users`, `roles`, `user_roles`, `data_sources`.
- TimescaleDB owns time-series tables: `visitor_counts`, `congestion_indices`.
- Redis keys are namespaced by feature:
  - `dashboard:{region_id}`
  - `visitor-stats:{region_id}:{period_days}`
  - `festival-history:{region_id}`
  - `data-source-health:{source_id}`
- Raw public data responses are stored under `data/raw/{provider}/{dataset}/{yyyy}/{mm}/{dd}/`.
- Processed app-ready outputs are stored under `data/processed/`.
- Report exports are stored under `data/exports/{yyyy}/{mm}/{dd}/`.

## Data Quality Rules

- Every external record must carry `source.provider`, `source.reference_date`, `source.updated_at`, and `source.is_estimated`.
- Fallback, synthetic, or predicted values must set `is_estimated: true`.
- Missing daily visitor records use the previous processed file when available.
- Duplicate visitor rows are grouped by `(date, region, source_endpoint)` before dashboard aggregation.
- Visitor values are parsed as decimal numbers first, then rounded, so `158.49` does not become `15849`.
- Saturation status uses the first MVP thresholds:
  - `safe`: fewer than 50,000 visitors
  - `normal`: 50,000 to 149,999 visitors
  - `caution`: 150,000 to 299,999 visitors
  - `crowded`: 300,000 or more visitors

## Reproduction

Apply schema and seed data:

```bash
psql "$DATABASE_URL" -f backend/db/migrations/001_init.sql
psql "$DATABASE_URL" -f backend/db/seeds/001_seed_core.sql
```

Generate sample dashboard features:

```bash
python -m safetrip_jb.pipeline derive --visitor-input backend/data/processed/jeonbuk_visitors_daily.json --output data/processed/dashboard_features.json
```
