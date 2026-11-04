# AirSource X — Hackathon submission brief

## Team details

- Team name: **Fresh_coderz**
- Members: **Shylan Kamesh S**, **Sai Santhosh T**, **Derin Godson**
- Public repository: **[https://github.com/shylankamesh/airsource-x](https://github.com/shylankamesh/airsource-x)**
- Hosted demo: [Public static website](https://shylankamesh.github.io/airsource-x/). The interactive Gradio app is local-only.

## Short description

AirSource X is an experimental air-quality research prototype that pairs short-horizon PM2.5 forecasting with transparent, rule-based screening of possible pollution influences. It compares its forecasts with simple baselines, makes missing or conflicting evidence visible, and allows an “insufficient evidence” outcome instead of presenting unsupported source claims.

## What is implemented

- Separate retrospective 0–24h and 24–48h PM2.5 forecast experiments.
- Chronological train, validation, and test splits with a temporal gap between partitions.
- LightGBM compared with last-observation, preceding-24-hour mean, and training-only seasonal baselines.
- Hourly aggregation and coverage auditing for 15-minute monitor data.
- A qualitative evidence-rule prototype with provenance, contradictions, missing evidence, and abstention.
- A responsive, interactive website presenting the ITO Delhi study and its limitations.
- A separate historical six-station Delhi view with station coverage, daily observed means, and an exploratory same-hour network-relative outlier screen; it is not used to claim multi-station forecast performance.
- Exact-time overlap summary and a retrospective co-occurrence screen for stations above their own historical 90th percentile; coordinates are not available, so this is not geographic mapping or causal attribution.

## Delhi study result

Source: OpenCity listing for ITO, Delhi - CPCB, 15-minute records. This retrospective run contains 130 held-out forecast issues per horizon. The test set covers the later study period; see `results/delhi_ito_2024_25/forecast_splits.json` for exact boundaries.

| Horizon | Method | MAE (µg/m³) | RMSE (µg/m³) | Bias (µg/m³) |
|---|---|---:|---:|---:|
| 0–24h | LightGBM | 28.3714 | 44.0980 | -10.4540 |
| 0–24h | Last observed hourly value | 45.0920 | 65.0981 | -38.3379 |
| 0–24h | Persistence | 26.6446 | 42.3394 | -0.7258 |
| 0–24h | Seasonal mean | 39.8846 | 58.7243 | -16.8635 |
| 24–48h | LightGBM | 34.5325 | 57.0693 | -10.5718 |
| 24–48h | Last observed hourly value | 57.9046 | 84.8592 | -42.6489 |
| 24–48h | Persistence | 38.9823 | 58.9929 | -4.2081 |
| 24–48h | Seasonal mean | 42.0340 | 62.3870 | -17.8866 |

The preceding-24-hour mean is better for 0–24h; raw LightGBM is better for 24–48h. Validation-selected methods are LightGBM for 0–24h and the preceding-24-hour mean for 24–48h. Test metrics are reported without using the test set to reselect a model.

The nominal 90% intervals achieved 71.5% and 74.6% empirical coverage, so they must be described as exploratory and under-covering. The source file contains 68,985 records through 1 January 2026; hourly PM2.5 coverage after aggregation is 93.257%, with a 148-hour maximum missing streak and one blank footer row excluded from timestamped data. The downloaded CSV and source manifest are included in `data/raw/`; acknowledge CPCB and its contributing agencies.

The separate six-station benchmark contains 70,227 hourly rows spanning June 2018–October 2019. Its six station series have 11,704 timestamps with all six reporting and 11,704 timestamps with at least four reporting. The benchmark's compressed and uncompressed checksums are recorded in `data/benchmarks/manifest.json` and checked by tests. It remains a historical context dataset, not a forecast holdout.

## Demo narration

1. Open `website/index.html`.
2. Show the dataset and retrospective scope in the hero and provenance sections.
3. Switch between the two forecast horizons and compare LightGBM with the last observation, preceding-24-hour mean, and seasonal baseline.
4. Point out the interval under-coverage and the limits section: no live forecast proof, no all-Delhi generalization, and no physical source attribution.
5. In Gradio, show the separate historical Multi-station Context tab; clarify that it is descriptive 2018–2019 data, not the ITO forecast test or geographic source evidence.
6. In Source Investigation Studio, toggle FIRMS to demonstrate a genuine recomputation to insufficient evidence. Explain that the case is synthetic and shows rule behavior only.
7. Open `results/delhi_ito_2024_25/EXPERIMENT_RESULTS.md` for the full metrics, split dates, coverage, and policy fixture results.

## Limitations to disclose

- One station; retrospective evaluation only. Publication availability at forecast issue time has not been independently verified.
- Dataset includes a long missing interval; no imputation is used for target labels.
- Evidence-policy fixtures are author-authored software consistency cases, not source attribution ground truth.
- No actual satellite fire feed, atmospheric trajectory integration, causal source method, or measured source fractions.
- Overall AQI and health advice are not provided.
- The run is retrospective and timestamp availability at forecast issue time remains unverified.

## Pre-submission checks still required

The team name (Fresh_coderz), member names, public repository, and live static demo are filled in. The interactive Gradio app is local-only. The image in `assets/screenshots/` is from the previous website design and must be replaced with a current homepage capture before final judging. Confirm team registration, data reuse terms, any additional AI tools used by the team, and the project's license choice before submitting.


