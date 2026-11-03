# AirSource X

**Forecast the pollution. Investigate the evidence. Make uncertainty visible.**

AirSource X is a proposed, research-oriented air-quality intelligence platform for Delhi, India. Its goal is to combine short-horizon PM2.5 forecasting with transparent investigation of possible pollution influences. The system is intended to show the observations behind each result, the evidence that is missing or contradictory, and what additional measurement could help.

> **Project status:** This repository currently contains the project README and development direction. Features described below are planned; they are not claims that an application, dataset, model, or evaluation has already been implemented or validated.

## Why AirSource X

A forecast gives a concentration estimate, but that estimate alone does not show whether an episode is local or widespread, which observations support a possible explanation, or what evidence is unavailable. AirSource X aims to make those limits inspectable.

The project is an evidence-screening and decision-support prototype. It is not a chemical source-apportionment model, an official CPCB forecast, or a replacement for expert systems such as the IITM/MoES Delhi Decision Support System.

## Planned capabilities

- **PM2.5 forecasting:** 0–24 hour and 24–48 hour targets, with persistence and seasonal baselines. Forecast inputs must be available at the stated issue time.
- **Forecast evaluation:** chronological holdouts, target-window leakage controls, MAE, RMSE, bias, and severe-episode metrics reported alongside sample counts and split dates.
- **Multi-station context:** compare stations over common, quality-screened time windows to explore whether patterns are localised or network-wide. Spatial association is not source attribution.
- **Anomaly screening:** flag unusual observations for review while keeping anomalies distinct from confirmed pollution incidents.
- **Model explanations:** use SHAP or another validated method to explain predictive features. Predictive contributions must not be presented as physical source attribution.
- **Evidence investigation:** initially screen biomass-burning and dust-related hypotheses using available, timestamped observations. Show supporting, contradicting, and missing evidence, alternatives, provenance, and rule traces. Keep traffic and industrial hypotheses limited until discriminating evidence is available.
- **Evidence-removal counterfactuals:** recompute the investigation after evidence streams are disabled and show which rules and assessments change. Evidence removal represents information loss, not a real-world intervention.
- **Next-measurement guidance:** rank useful follow-up observations with a transparent rationale; a recommendation does not prove a source.
- **Reproducible replay and audit:** preserve source, retrieval and issue times, station metadata, quality decisions, model/rule versions, and data manifests where available.

## Scientific safeguards

1. Never fabricate observations, model scores, source fractions, or evaluation results.
2. Distinguish unavailable evidence from evidence against a hypothesis.
3. Abstain when evidence is sparse, conflicting, or not discriminating.
4. Preserve data provenance, timestamps, units, quality flags, and station metadata.
5. Keep forecast-as-issued analysis separate from retrospective analysis; use only information available at forecast issue time for operational forecasts.
6. Evaluate forecasts against simple baselines on the same test periods, with chronological splits and leakage checks.
7. Treat satellite NO2 and aerosol optical depth as contextual products, not direct surface measurements of PM2.5 or unique source indicators.
8. Treat satellite fire detections as imperfect thermal-anomaly observations; no detection does not establish that no fire occurred.
9. Do not publish source percentages or causal claims without an appropriate validated method and ground truth.
10. Mark unavailable integrations and unvalidated features clearly rather than filling dashboard space with simulated results.

## Data strategy

Candidate ground-monitor sources include the [OpenCity Delhi hourly air-quality collection](https://data.opencity.in/dataset/delhi-hourly-air-quality-reports), the [CPCB repository](https://airquality.cpcb.gov.in/ccr/), and [OpenAQ](https://docs.openaq.org/). Candidate contextual sources include [Open-Meteo](https://open-meteo.com/), [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/), and quality-screened satellite products where their coverage and licensing permit.

Actual access, coverage, licensing, and suitability must be audited before use. Each accepted dataset should have a manifest recording its source, station or sensor, timestamp range, units, missingness, duplicates, quality checks, retrieval time, and checksum when practical. CSV import should provide a documented fallback when a source cannot be obtained. Synthetic fixtures, if later added for software tests, must never be shown as real Delhi observations.

## Proposed technical direction

The initial implementation is expected to use Python, pandas/NumPy, scikit-learn, LightGBM where supported by the available data, Streamlit, and Plotly. Geospatial and satellite packages should be added only when a working, quality-controlled data path needs them. Package versions, model artifacts, and reproducible commands should be documented as implementation develops.

## Development sequence

1. Inspect the repository and establish a runnable foundation.
2. Audit and validate real station data; add CSV import and a station coverage report.
3. Build forecast targets, leakage checks, baseline models, and chronological evaluation.
4. Add multi-station comparisons and event-aware metrics when coverage supports them.
5. Add anomaly screening and predictive explanations with clear interpretation limits.
6. Implement evidence records, hypothesis screening, abstention, and evidence-removal recomputation.
7. Add a guided dashboard, retrospective replay, audit outputs, and next-measurement suggestions.
8. Validate each enabled feature and document blocked or unvalidated work honestly.

## Intended dashboard

The proposed dashboard may include an environmental overview, forecast lab, investigation studio, evidence map, model explanation, historical replay, reliability and research view, and public-impact guidance. Pages should expose data coverage and unavailable states. Build a working end-to-end slice before adding optional satellite layers, an LLM assistant, or decorative features.

## Research and limitations

The project direction is based on the supplied Version 3.0 research proposal and master development prompt. The proposal is a blueprint, not implementation evidence. It highlights multi-station context, spatially honest evaluation, forecast-run provenance, extreme-event performance, evidence dependence, drift monitoring, and next-best-measurement guidance as valuable extensions to the original forecasting and investigation scope.

Forecast skill can be measured against observed monitor values. Source-screening reliability can be tested for provenance, contradictions, abstention, counterfactual responsiveness, and stability. Neither evaluation alone establishes causal source contributions. Strong source attribution would require suitable independent ground truth or a validated physical source-apportionment methodology.

## Contributing

Contributions should preserve the scientific safeguards above. Before adding a data integration or model, document its input timing, quality controls, provenance, validation design, known limitations, and how unavailable data are represented.

## License

No license has been selected yet. Until one is added, all rights are reserved by default; please contact the project owner before reusing or redistributing this work. 
