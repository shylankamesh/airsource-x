# V6 — External environmental data connectors

## Overview

V6 introduces an external-data workspace and connector layer. Each provider remains a separate source with explicit data class and retrieval provenance. The connectors do not silently merge provider records into the bundled training dataset.

## Implemented connectors

### OpenAQ API v3
- Fetches latest sensor values for a specified location ID.
- Requires `OPENAQ_API_KEY` or a key supplied in the UI.
- Preserves sensor/location IDs, parameter, value, units, UTC timestamp and coordinates.
- Important: OpenAQ documents that `latest` is the last value in a sensor series, not necessarily the most recently ingested measurement, and it is not a complete chronological feed.

### India Open Government Data resource
- Fetches a configured `data.gov.in` resource using its exact resource ID.
- Requires `DATA_GOV_IN_API_KEY`.
- Does not guess the resource ID or assume that arbitrary columns mean PM2.5.
- The selected catalogue resource must be checked for schema, units, station IDs, cadence, licence and data-quality notes before field mapping.

### NASA FIRMS
- Fetches a bounding-box CSV for selected MODIS/VIIRS sources.
- Requires `NASA_FIRMS_MAP_KEY`.
- Validates bounding box, product name and day range.
- Detections are satellite thermal anomalies / active-fire candidates, not PM2.5 observations and not proof of a pollution source.

## Existing and planned providers

- Open-Meteo remains the existing provider-modelled weather and CAMS air-quality context connector.
- Sentinel-5P/TROPOMI NO2 is catalogued but not ingested.
- NASA MAIAC MCD19A2 aerosol optical depth is catalogued but not ingested.

TROPOMI NO2 column products are not surface NO2 concentrations or PM2.5. MAIAC AOD is a column optical property and cannot be treated as surface PM2.5 without additional retrieval, meteorological, vertical-profile and validation work.

## Security and operations

- API keys are accepted from environment variables or entered in the UI for the current request.
- Never commit keys, place them in source files, or include them in logs/screenshots.
- For deployed use, configure secrets in the hosting platform secret manager.
- Requests use timeouts and propagate HTTP errors to the UI.
- No scheduled ingestion, persistent external-data store, retry queue, deduplication ledger or automated refresh job is included yet.
- The connectors are intentionally provider-specific and return provider-native frames plus metadata. Canonical mapping is a separate reviewed step.

## Validation

Connector unit tests mock provider responses and validate schema normalisation, required credentials, parameter validation and product-status declarations. They do not prove that external APIs are reachable or that a credential has access. No live external API call is part of automated tests.

## Official documentation

- OpenAQ Latest: https://docs.openaq.org/resources/latest
- OpenAQ API v3: https://docs.openaq.org/api
- India OGD real-time AQI catalogue: https://www.data.gov.in/catalog/real-time-air-quality
- NASA FIRMS Area API: https://firms.modaps.eosdis.nasa.gov/api/area/
- NASA FIRMS MAP_KEY: https://firms.modaps.eosdis.nasa.gov/api/map_key
- Open-Meteo Previous Runs: https://open-meteo.com/en/docs/previous-runs-api
- Open-Meteo Historical Forecast: https://open-meteo.com/en/docs/historical-forecast-api
- Open-Meteo Air Quality: https://open-meteo.com/en/docs/air-quality-api
