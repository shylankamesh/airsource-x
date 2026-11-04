# AirSource-X V3 integration blueprint

## Development boundary
This project is a separate working copy. The original `airsource-x` GitHub repository is read-only and must not be modified by this workflow.

## Adopted architecture
- Streamlit remains the presentation layer.
- `airsource.data` remains the canonical observation normalisation layer.
- `airsource.quality` provides non-destructive quality diagnostics.
- `airsource.forecast` remains the forecasting engine pending full benchmark replication and temporal/spatial validation.
- `airsource.evidence_v3` introduces stable evidence IDs, dependency groups and traceable assessments.
- `airsource.monitoring` classifies source freshness; missing retrieval metadata is explicitly unavailable.
- `configs/station_registry_template.csv` defines the metadata contract. Coordinates and site classifications must be populated only from verified sources.

## Reference-project integration
- JanVayu: adapt interaction patterns, maps, guided exploration and multilingual UX; do not transplant its separate frontend stack.
- Paldom Streamlit styling: adopt native theme configuration and scoped reusable styling; avoid brittle internal DOM selectors.
- AirAtlas: adapt source-ingestion separation, raw/processed storage, Parquet where appropriate, provenance and scheduled validation; do not substitute its AQI methodology for PM2.5 forecasting.

## Implementation gates
1. Reproduce existing benchmark outputs and verify model/runtime compatibility.
2. Establish station registry, source freshness and common temporal coverage.
3. Add spatial validation before displaying regional claims.
4. Migrate existing investigation rules into evidence records with dependency-aware tests.
5. Add source connectors only after access, licence, temporal coverage, QA fields and timestamp semantics are checked.
6. Build eight Streamlit pages over stable service interfaces.
7. Add reproducible model releases, drift reports and end-to-end tests.

## Scientific constraints
- Satellite AOD and NO2 are contextual indicators, not direct surface PM2.5 measurements.
- A missing fire detection is not evidence that no fire occurred.
- Road/facility proximity and co-pollutant correlation do not establish source causality.
- Forecast-as-of mode must use only information available at the forecast issue time.
- Do not display uncalibrated source probabilities or source-contribution percentages.
- Insufficient data must produce an explicit unavailable/abstention state, never a fabricated zero.

## New modules in this increment
- `airsource.quality`: non-destructive quality diagnostics.
- `airsource.evidence_v3`: structured evidence and assessment records.
- `airsource.monitoring`: source freshness classification.
- `tests/`: initial unit tests for these contracts.

## Engineering increment 2: model artifact integrity

Added `airsource/model_registry.py` to inspect artifact hashes, safe paths, dataset identity and runtime version differences without deserialising models. The Data & Methods page now displays this audit. Model loading verifies SHA-256 and refuses scikit-learn version-warning artifacts by default. See `MODEL_COMPATIBILITY_AND_REGISTRY.md`.

Automated tests: 9 passing in the workspace at this increment. These tests do not constitute end-to-end Streamlit or scientific forecast validation.


### Increment 3 safeguards
- Severe-event metrics are only computed when the analyst supplies an explicit concentration threshold; they are not presented as official AQI classes.
- Historical replay uses `observed_at` and `available_at`; observation time alone is insufficient to establish when a record became available.
- Station coordinates must have a traceable metadata source and quality designation. Missing coordinates block spatial claims.
- Legacy investigation output can be traced as qualitative rule statements; this adapter does not convert heuristic text into measured sensor evidence.


### Increment 4 — spatial intelligence
- Station geometry is joined only by exact station ID and sourced registry coordinates.
- The bundled six-station registry uses coordinates rounded to 0.001 degree from a published Delhi station inventory supplement; aliases are documented.
- The spatial page reports exact common-time comparisons and pairwise correlations only above a user-selected overlap count. Missing values are not interpolated.
- Spatial correlation and distance remain descriptive; no source attribution or plume direction is inferred.

## V7 implementation note

V7 implements the first local persistence slice: canonical OpenAQ/FIRMS adapters, SQLite observations and ingestion-run audit, explicit one-shot ingestion, and conservative event-to-FIRMS context matching. It does not yet implement scheduled ingestion, retries, full raw payload retention, OGD field mappings, TROPOMI/MAIAC ingestion, or distributed storage. These remain gated on source access, licence/schema verification, and deployment persistence requirements.
