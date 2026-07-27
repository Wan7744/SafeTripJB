# SafeTrip JB Backend

Historical festival utilities for the public data portal dataset.

## Environment

Fill in `.env` at the repository root. The CLI can also find `backend/.env`, but the root `.env` is the clearest default for this workspace.

```bash
ODCLOUD_SERVICE_KEY=
ODCLOUD_BASE_URL=https://api.odcloud.kr/api
ODCLOUD_NAMESPACE=15055596/v1
ODCLOUD_RESOURCE_PATH=/15055596/v1/uddi:54ab775e-8d6b-4e86-acbb-d6841dee1013
ODCLOUD_RESPONSE_FORMAT=json
KTO_SERVICE_KEY=
KTO_DATALAB_BASE_URL=https://apis.data.go.kr/B551011/DataLabService
KTO_MOBILE_OS=ETC
KTO_MOBILE_APP=SafeTrip
KTO_RESPONSE_TYPE=json
KMA_SERVICE_KEY=
KAKAO_MAP_API_KEY=
CLAUDE_API_KEY=
DATABASE_URL=postgresql://safetrip:safetrip@localhost:5432/safetrip_jb
REDIS_URL=redis://localhost:6379/0
```

`ODCLOUD_RESOURCE_PATH` must be the Swagger API path, not the Swagger docs page URL. This dataset's latest path is `/15055596/v1/uddi:54ab775e-8d6b-4e86-acbb-d6841dee1013`.

## Commands

Fetch from the public data portal:

```bash
python -m safetrip_jb.festival_history fetch --env .env --output data/raw/historical_festivals.json
```

You can run that command from the repository root or from `backend/`.

Convert JSON, XML, or CSV into English-column CSV:

```bash
python -m safetrip_jb.festival_history convert --input data/raw/historical_festivals.json --output data/processed/historical_festivals_en.csv
```

Predict expected visitors for a future festival period:

```bash
python -m safetrip_jb.festival_history predict --input data/processed/historical_festivals_en.csv --opening-date 2026-08-01 --closing-date 2026-08-04 --administrative-level 시군 --festival-name "Jeonju Summer Festival"
```

Fetch Korea Tourism Organization DataLab visitor counts for Jeonbuk:

```bash
python -m safetrip_jb.kto_visitors fetch --env .env --output data/processed/jeonbuk_visitors_daily.json --start-ymd 20240725 --end-ymd 20240731
```

Create fallback weather records:

```bash
python -m safetrip_jb.weather write --output data/processed/weather_daily.json
```

Build dashboard feature data from processed visitor and festival files:

```bash
python -m safetrip_jb.pipeline derive --visitor-input data/processed/jeonbuk_visitors_daily.json --festival-csv data/processed/historical_festivals_en.csv --output data/processed/dashboard_features.json
```

Run the local MVP pipeline and JSONL logging:

```bash
python -m safetrip_jb.pipeline run --visitor-input data/processed/jeonbuk_visitors_daily.json --festival-csv data/processed/historical_festivals_en.csv --weather-output data/processed/weather_daily.json --output data/processed/dashboard_features.json --log data/logs/pipeline/local.jsonl
```

## Data Model and Batch Setup

- DB schema: `backend/db/migrations/001_init.sql`
- Seed data: `backend/db/seeds/001_seed_core.sql`
- External source policy: `backend/config/external_sources.json`
- Local cron draft: `backend/config/pipeline.cron`
- Data model notes: `backend/docs/data_model.md`

## Output CSV Columns

- `serial_number`
- `administrative_level`
- `festival_name`
- `opening_date`
- `closing_date`
- `visitor_count`
- `notes`
