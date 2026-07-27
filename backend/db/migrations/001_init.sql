-- SafeTrip JB core schema for PostgreSQL and TimescaleDB.
-- Run after enabling PostgreSQL. TimescaleDB statements are guarded where possible.

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS regions (
  region_id TEXT PRIMARY KEY,
  region_name TEXT NOT NULL UNIQUE,
  parent_region_id TEXT REFERENCES regions(region_id),
  saturation_status TEXT NOT NULL DEFAULT 'safe',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT regions_saturation_status_check CHECK (
    saturation_status IN ('safe', 'normal', 'caution', 'crowded')
  )
);

CREATE TABLE IF NOT EXISTS festivals (
  festival_id TEXT PRIMARY KEY,
  region_id TEXT NOT NULL REFERENCES regions(region_id),
  name TEXT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  visitor_growth_rate NUMERIC(8, 2),
  expected_visitor_count INTEGER,
  source_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT festivals_date_check CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS data_sources (
  source_id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  dataset_name TEXT NOT NULL,
  endpoint TEXT,
  reference_date DATE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  is_estimated BOOLEAN NOT NULL DEFAULT false,
  raw_storage_path TEXT,
  processed_storage_path TEXT
);

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  organization TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roles (
  role_id TEXT PRIMARY KEY,
  role_name TEXT NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
  user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  role_id TEXT NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS visitor_counts (
  observed_at DATE NOT NULL,
  region_id TEXT NOT NULL REFERENCES regions(region_id),
  visitor_count INTEGER NOT NULL,
  source_id TEXT REFERENCES data_sources(source_id),
  is_estimated BOOLEAN NOT NULL DEFAULT false,
  raw_payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (observed_at, region_id)
);

SELECT create_hypertable('visitor_counts', 'observed_at', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS congestion_indices (
  observed_at DATE NOT NULL,
  region_id TEXT NOT NULL REFERENCES regions(region_id),
  traffic_congestion_level TEXT NOT NULL,
  tourist_spot_congestion_level TEXT NOT NULL,
  restaurant_wait_index NUMERIC(5, 2) NOT NULL DEFAULT 0,
  saturation_status TEXT NOT NULL,
  is_estimated BOOLEAN NOT NULL DEFAULT false,
  source_id TEXT REFERENCES data_sources(source_id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (observed_at, region_id),
  CONSTRAINT congestion_saturation_status_check CHECK (
    saturation_status IN ('safe', 'normal', 'caution', 'crowded')
  )
);

SELECT create_hypertable('congestion_indices', 'observed_at', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS festivals_region_date_idx ON festivals(region_id, start_date, end_date);
CREATE INDEX IF NOT EXISTS visitor_counts_region_date_idx ON visitor_counts(region_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS congestion_region_date_idx ON congestion_indices(region_id, observed_at DESC);
