-- Create the raw table if it doesn't exist
CREATE TABLE IF NOT EXISTS apple_health_raw (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  data JSON NOT NULL,
  ts_ingestion TIMESTAMP NOT NULL DEFAULT now()
);


-- Create the table for transformed sleep analysis
CREATE TABLE IF NOT EXISTS apple_health_sleep_analysis (
  ts_start TIMESTAMPTZ NOT NULL,
  ts_end   TIMESTAMPTZ NOT NULL,
  value    TEXT        NOT NULL
);


-- Create a unique index to avoid duplicates
CREATE UNIQUE INDEX IF NOT EXISTS idx_sleep_analysis_unique
  ON apple_health_sleep_analysis (ts_start, ts_end, value);


-- Create the table for transformed sleep analysis
CREATE TABLE IF NOT EXISTS foodlog (
  id       BIGINT      NOT NULL,
  ts_start TIMESTAMPTZ NOT NULL,
  ts_end   TIMESTAMPTZ NOT NULL,
  description TEXT     NOT NULL
);


-- Create or replace the trigger function that extracts "sleep_analysis" data
CREATE OR REPLACE FUNCTION transform_sleep_analysis()
RETURNS TRIGGER AS $$
DECLARE
  metric    JSONB;
  datapoint JSONB;
BEGIN
  -- Loop over each metric in NEW.data (cast to jsonb)
  FOR metric IN
    SELECT * FROM jsonb_array_elements(NEW.data::jsonb->'metrics')
  LOOP
    IF metric->>'name' = 'sleep_analysis' THEN
      FOR datapoint IN
        SELECT * FROM jsonb_array_elements(metric->'data')
      LOOP
        INSERT INTO apple_health_sleep_analysis (ts_start, ts_end, value)
        VALUES (
          (datapoint->>'startDate')::timestamptz,
          (datapoint->>'endDate')::timestamptz,
          datapoint->>'value'
        )
        ON CONFLICT DO NOTHING;
      END LOOP;
    END IF;
  END LOOP;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Drop the old trigger if it exists, then recreate it
DROP TRIGGER IF EXISTS after_insert_apple_health_raw ON apple_health_raw;

CREATE TRIGGER after_insert_apple_health_raw
AFTER INSERT ON apple_health_raw
FOR EACH ROW
EXECUTE FUNCTION transform_sleep_analysis();
