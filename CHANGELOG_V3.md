# V8 — Product completion increment

- Added Historical replay workspace with explicit as-of availability filtering and clear exclusion accounting.
- Added Public impact & decisions workspace with user-defined review thresholds and human-in-the-loop guardrails.
- Added Reliability & research workspace for saved holdout benchmark metrics and ingestion freshness.
- Added stored FIRMS detection map to External data workspace.
- Consolidated workspace navigation and added decision-support/reliability modules with tests.
- Documented remaining integration, scientific, and deployment limitations.

# V6 — External environmental data connectors

- Added OpenAQ API v3 latest sensor connector with sensor IDs, units, UTC timestamps and coordinates.
- Added configurable India OGD resource connector requiring an exact resource ID and API key.
- Added NASA FIRMS bounding-box connector for supported MODIS/VIIRS sources with MAP_KEY requirement.
- Added source catalogue distinguishing implemented, existing and not-yet-ingested satellite products.
- Added External data Streamlit workspace with source-specific forms, provenance and downloads.
- Added mocked connector tests and integration documentation.
- No credentials stored; no external data silently merged into model training data.

# V5 — Pollution episode intelligence and reliability

- Added persistent PM2.5 station-episode detection using a strictly prior rolling median and robust MAD threshold.
- Added multi-station episode grouping with onset order, onset span and peak timing; no causal/source attribution claims.
- Added wind plausibility audit and blocks unsupported wind interpretation.
- Added Streamlit Episode intelligence workspace with controls, timeline, tables and CSV/JSON downloads.
- Added synthetic tests and GitHub Actions CI for Python 3.11/3.12.
- Added V5 methodology and limitations documentation.

# AirSource-X V3 development changelog

## Increment 2 — model integrity and compatibility
- Added manifest/artifact integrity audit.
- Added safe artifact path checks and dataset checksum validation.
- Added guarded model deserialisation with scikit-learn compatibility warning handling.
- Integrated registry diagnostics into Data & Methods.
- Added four model registry tests.
- Added operator documentation.

## Verification
- `pytest -q`: 9 passed.
- Python syntax compilation is checked separately.
- Streamlit end-to-end execution and full scientific reproduction remain pending.


## Increment 3 — evaluation, station metadata, evidence trace and replay
- Added held-out prediction evaluation with MAE, RMSE, bias, peak absolute error and explicitly thresholded severe-event precision/recall.
- Added station-registry validation for unique IDs, coordinate ranges and metadata validity. Missing coordinates remain warnings; no coordinate values were invented.
- Added an adapter that wraps legacy qualitative investigation statements in traceable evidence records without presenting them as raw measurements.
- Added as-of replay filtering that requires explicit observation and availability timestamps and excludes late or impossible records.
- Added optional CSV interfaces in Data & Methods for registry validation and prediction evaluation.


## Increment 4 — multi-station spatial intelligence
- Added a sourced six-station Delhi registry with coordinate provenance and explicit station-alias notes.
- Added Haversine distance calculations, exact-timestamp station comparisons, pairwise temporal correlations with a minimum-overlap gate, and coordinate-backed station coverage summaries.
- Added a dedicated Streamlit Spatial Intelligence page with station-position plot, synchronized PM2.5 comparison, correlation/distance table, time series, and CSV/JSON exports.
- No interpolation, kriging, plume reconstruction, or source/transport inference is performed.

## V7 — Persistent ingestion and contextual matching
- Added canonical provenance-preserving observation adapters for OpenAQ latest sensor records and NASA FIRMS fire detections.
- Added SQLite schema/version metadata, idempotent observation persistence, ingestion audit history, and source collection summaries.
- Added one-shot opt-in CLI ingestion; no scheduled network collection is enabled.
- Added bounded spatiotemporal matching of FIRMS detections to events, explicitly labelled as context rather than causal evidence.
- Extended External data workspace with local store inspection, ingestion history, health summary, and CSV export.
- Added unit tests for canonical schema, data-class separation, unit preservation, idempotency, audit, and spatial-temporal matching.
