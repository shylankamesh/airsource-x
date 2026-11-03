# AirSource X — Hackathon submission brief

## Team details to complete

- Team name: **[ADD TEAM NAME]**
- Members: **[ADD MEMBER NAMES]**
- Public repository: **[ADD VERIFIED PUBLIC URL]**
- Hosted demo: **[ADD URL IF DEPLOYED]**

## Short description

AirSource X is an experimental air-quality research prototype that pairs short-horizon PM2.5 forecasting with transparent, rule-based screening of possible pollution influences. It compares its forecasts with simple baselines, makes missing or conflicting evidence visible, and allows an “insufficient evidence” outcome instead of presenting unsupported source claims.

## What is implemented

- Separate retrospective 0–24h and 24–48h PM2.5 forecast experiments.
- Chronological train, validation, and test splits with a temporal gap between partitions.
- LightGBM compared with persistence and a training-only seasonal mean.
- Hourly aggregation and coverage auditing for 15-minute monitor data.
- A qualitative evidence-rule prototype with provenance, contradictions, missing evidence, and abstention.
- A responsive, interactive website presenting the ITO Delhi study and its limitations.

## Delhi study result

Source: OpenCity listing for ITO, Delhi - CPCB, 15-minute records. This retrospective run contains 130 held-out forecast issues per horizon. The test set covers the later study period; see `results/delhi_ito_2024_25/forecast_splits.json` for exact boundaries.

| Horizon | Method | MAE (µg/m³) | RMSE (µg/m³) | Bias (µg/m³) |
|---|---|---:|---:|---:|
| 0–24h | LightGBM | 28.3714 | 44.0980 | -10.4540 |
| 0–24h | Persistence | 26.6446 | 42.3394 | -0.7258 |
| 0–24h | Seasonal mean | 39.8846 | 58.7243 | -16.8635 |
| 24–48h | LightGBM | 34.5325 | 57.0693 | -10.5718 |
| 24–48h | Persistence | 38.9823 | 58.9929 | -4.2081 |
| 24–48h | Seasonal mean | 42.0340 | 62.3870 | -17.8866 |

Persistence is better for 0–24h; LightGBM is better for 24–48h. Validation-selected methods are LightGBM for 0–24h and persistence for 24–48h. Test metrics are reported without using the test set to reselect a model.

The nominal 90% intervals achieved 71.5% and 74.6% empirical coverage, so they must be described as exploratory and under-covering. The source file contains 68,985 records through 1 January 2026; hourly PM2.5 coverage after aggregation is 93.257%, with a 148-hour maximum missing streak and one blank footer row excluded from timestamped data. The downloaded CSV and source manifest are included in `data/raw/`; acknowledge CPCB and its contributing agencies.

## Demo narration

1. Open `website/index.html`.
2. Show the dataset and retrospective scope in the hero and provenance sections.
3. Switch between the two forecast horizons and compare LightGBM with persistence and the seasonal baseline.
4. Point out the interval under-coverage and the limits section: no live forecast proof, no all-Delhi generalization, and no physical source attribution.
5. Open `results/delhi_ito_2024_25/EXPERIMENT_RESULTS.md` for the full metrics, split dates, coverage, and policy fixture results.

## Limitations to disclose

- One station; retrospective evaluation only. Publication availability at forecast issue time has not been independently verified.
- Dataset includes a long missing interval; no imputation is used for target labels.
- Evidence-policy fixtures are author-authored software consistency cases, not source attribution ground truth.
- No actual satellite fire feed, atmospheric trajectory integration, causal source method, or measured source fractions.
- Overall AQI and health advice are not provided.
- The run is retrospective and timestamp availability at forecast issue time remains unverified.

## Pre-submission fields still required

Fill the team, member, repository, and hosted demo fields above. Confirm the hackathon’s submission format and deadline. Check data reuse terms before redistributing the raw CSV. Deploy the site and test it in the target demo environment if a live URL is required. Select a project license before inviting reuse.
