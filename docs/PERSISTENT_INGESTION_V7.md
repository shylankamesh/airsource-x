# AirSource-X V7 — Persistent ingestion and context matching

## What changed

V7 adds a local SQLite store, canonical observation adapters for the existing OpenAQ latest and NASA FIRMS connectors, ingestion audit history, source-level collection summaries, an explicit one-shot CLI, and conservative fire-detection-to-event space/time matching.

### Canonical record

`airsource/ingestion.py` defines a common record with source and provider record identifiers, location/station identifiers, parameter/value/unit, observed and available times, coordinates, data class, quality flag, raw-record SHA-256, and retrieval time. Original units are preserved. The adapter does not infer `available_at` where the provider does not supply it. `raw_payload_hash` is a hash of the row returned by the connector; it is not a claim that the complete provider payload has been archived.

Current adapters:

- OpenAQ latest sensor rows → `ground_sensor_measurement`.
- NASA FIRMS detections → `satellite_fire_detection`; FRP is retained in MW when supplied and is not mapped to PM2.5.

India OGD remains deliberately unmapped because resource schemas and units depend on the exact configured resource. Open-Meteo remains provider-modelled context. TROPOMI and MAIAC are still catalogue entries only, not ingested.

## Persistence and deduplication

`airsource/store.py` uses SQLite schema version 1, WAL mode, a primary key on deterministic `observation_id`, `INSERT OR IGNORE` for idempotent ingestion, and an `ingestion_runs` audit table. A repeated identical record is counted as ignored rather than inserted again. The audit captures provider metadata, completion time, status, row counts, and errors. The database path used by the UI/CLI is `data/airsource_observations.sqlite` and is excluded from Git.

This is a local single-instance research store, not a distributed ingestion service. The database should be placed on a persistent volume for deployment; ephemeral hosting can lose it on restart or redeploy. SQLite is appropriate for a single-user prototype; concurrent multi-worker production deployments should move to a managed database with backups and access controls.

## Context matching

`airsource/context_matching.py` matches an event to FIRMS detections only when both spatial distance and absolute time difference are within explicit thresholds. The output says “candidate spatiotemporal context only”; it does not infer transport direction, plume trajectory, source attribution, or causality. A proper transport analysis would require wind fields at relevant heights/times, source timing, boundary-layer context, uncertainty, and preferably independent corroboration.

## Running ingestion explicitly

No scheduled network activity is enabled by default. Set credentials in environment variables, then invoke one-shot commands:

```bash
export OPENAQ_API_KEY="..."
python scripts/ingest_external.py openaq --location-id 2178

export NASA_FIRMS_MAP_KEY="..."
python scripts/ingest_external.py firms --west 76.7 --south 28.2 --east 77.8 --north 29.1 --days 1
```

Do not put keys in source files, commit them, or expose them in logs. Check provider terms, rate limits, licensing, and coverage before operational use. The CLI is intentionally opt-in; no cron/GitHub Actions schedule is activated.

## Validation and limitations

Unit tests cover canonicalization, data-class separation, unit preservation, absent availability timestamps, SQLite idempotency/audit, and bounded time/distance matching. They use synthetic/mock data. No live external API call was made as part of this build. The Streamlit page persists successful OpenAQ and FIRMS fetches and exposes local ingestion history and a CSV export. Streamlit is not installed in the build environment, so the UI was syntax-compiled but not browser-smoke-tested.

The store does not yet implement scheduled collection, retries/backoff, cursor pagination, a raw-payload archive, OGD schema mappings, TROPOMI/MAIAC ingestion, or a production database migration framework. Source health is based on local ingestion runs, not an independent provider uptime probe.
