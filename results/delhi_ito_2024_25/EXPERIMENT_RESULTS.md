# AirSource X — Experiment execution report

**DATA STATUS: OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED**

> Forecast metrics are retrospective observations from one station. They do not establish live/as-issued performance or physical source-apportionment accuracy.

## Input coverage

| station        | file                  | sha256                                                           |   source_rows |   bad_timestamps |   duplicate_timestamps | input_cadence   | timestamp_assumption                    | first_hour_ist            | last_hour_ist             |   total_hours |   valid_pm25_hours |   pm25_hour_coverage |   max_missing_streak_hours | optional_coverage                                       |
|:---------------|:----------------------|:-----------------------------------------------------------------|--------------:|-----------------:|-----------------------:|:----------------|:----------------------------------------|:--------------------------|:--------------------------|--------------:|-------------------:|---------------------:|---------------------------:|:--------------------------------------------------------|
| ITO Delhi CPCB | ito_delhi_2024_25.csv | dfd2f715c38326a08ce096bd05d800e770ef041ed77978660c026d7dc1822df8 |         68985 |                1 |                      0 | 15-minute       | Timestamp is IST unless explicit offset | 2024-01-01 05:00:00+05:30 | 2026-01-01 05:00:00+05:30 |         17545 |              16362 |              0.93257 |                        148 | {'pm10': 0.93474, 'no2': 0.96637, 'ws': 0.0, 'rh': 0.0} |

## Forecast benchmark (0–24h and 24–48h)

| data_label                                             | station        | horizon      | model               |   n |     mae |    rmse |     bias |
|:-------------------------------------------------------|:---------------|:-------------|:--------------------|----:|--------:|--------:|---------:|
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  | LightGBM            | 130 | 28.3714 | 44.098  | -10.454  |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  | Last-observation    | 130 | 45.092  | 65.0981 | -38.3379 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  | Persistence         | 130 | 26.6446 | 42.3394 |  -0.7258 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  | Seasonal            | 130 | 39.8846 | 58.7243 | -16.8635 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  | Validation-selected | 130 | 28.3714 | 44.098  | -10.454  |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 | LightGBM            | 130 | 34.5325 | 57.0693 | -10.5718 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 | Last-observation    | 130 | 57.9046 | 84.8592 | -42.6489 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 | Persistence         | 130 | 38.9823 | 58.9929 |  -4.2081 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 | Seasonal            | 130 | 42.034  | 62.387  | -17.8866 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 | Validation-selected | 130 | 38.9823 | 58.9929 |  -4.2081 |

## Locked evaluation partition metadata

```json
[
  {
    "station": "ITO Delhi CPCB",
    "train_n": 404,
    "valid_n": 133,
    "test_n": 133,
    "train_last": "2025-03-08 00:00:00+05:30",
    "validation_first": "2025-03-11 00:00:00+05:30",
    "validation_last": "2025-08-07 00:00:00+05:30",
    "test_first": "2025-08-16 00:00:00+05:30"
  }
]
```

## Exploratory elevated-pollution event metrics (150 µg/m³; not official AQI)

| data_label                                             | station        | horizon      | model               |   threshold_ugm3 | threshold_label                              |   actual_events |   hits |   misses |   false_alarms |   true_negatives |   precision |   recall |
|:-------------------------------------------------------|:---------------|:-------------|:--------------------|-----------------:|:---------------------------------------------|----------------:|-------:|---------:|---------------:|-----------------:|------------:|---------:|
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  | LightGBM            |              150 | EXPLORATORY high-PM event (not official AQI) |              54 |     43 |       11 |              7 |               69 |    0.86     | 0.796296 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  | Last-observation    |              150 | EXPLORATORY high-PM event (not official AQI) |              54 |     27 |       27 |              1 |               75 |    0.964286 | 0.5      |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  | Persistence         |              150 | EXPLORATORY high-PM event (not official AQI) |              54 |     45 |        9 |              9 |               67 |    0.833333 | 0.833333 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  | Seasonal            |              150 | EXPLORATORY high-PM event (not official AQI) |              54 |     47 |        7 |             10 |               66 |    0.824561 | 0.87037  |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  | Validation-selected |              150 | EXPLORATORY high-PM event (not official AQI) |              54 |     43 |       11 |              7 |               69 |    0.86     | 0.796296 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 | LightGBM            |              150 | EXPLORATORY high-PM event (not official AQI) |              55 |     42 |       13 |             10 |               65 |    0.807692 | 0.763636 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 | Last-observation    |              150 | EXPLORATORY high-PM event (not official AQI) |              55 |     24 |       31 |              4 |               71 |    0.857143 | 0.436364 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 | Persistence         |              150 | EXPLORATORY high-PM event (not official AQI) |              55 |     44 |       11 |              9 |               66 |    0.830189 | 0.8      |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 | Seasonal            |              150 | EXPLORATORY high-PM event (not official AQI) |              55 |     47 |        8 |             10 |               65 |    0.824561 | 0.854545 |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 | Validation-selected |              150 | EXPLORATORY high-PM event (not official AQI) |              55 |     44 |       11 |              9 |               66 |    0.830189 | 0.8      |

## Exploratory split-residual 90% interval coverage (temporal dependence caveat)

| data_label                                             | station        | horizon      |   nominal_coverage |   empirical_coverage |   mean_interval_width_ugm3 |   calibration_rows |   test_rows | calibration_limitation                                     |
|:-------------------------------------------------------|:---------------|:-------------|-------------------:|---------------------:|---------------------------:|-------------------:|------------:|:-----------------------------------------------------------|
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_0_24  |                0.9 |             0.715385 |                    63.5685 |                126 |         130 | Temporal dependence: coverage is empirical, not guaranteed |
| OBSERVATIONAL CSV; SOURCE AVAILABILITY TIME UNVERIFIED | ITO Delhi CPCB | target_24_48 |                0.9 |             0.746154 |                    82.6497 |                123 |         130 | Temporal dependence: coverage is empirical, not guaranteed |

## B0 / B1 / X evidence policy test — SYNTHETIC LOGIC FIXTURES ONLY

| experiment                                                | method     |   cases |   hypothesis_assessments |   policy_insufficient_count |   unsupported_conclusion_rate |   appropriate_abstention_rate |   supported_decision_retention |   provenance_trace_rate |   contradiction_visibility_rate |   exact_policy_outcome_match |
|:----------------------------------------------------------|:-----------|--------:|-------------------------:|----------------------------:|------------------------------:|------------------------------:|-------------------------------:|------------------------:|--------------------------------:|-----------------------------:|
| SYNTHETIC POLICY-CONSISTENCY TEST; NOT SOURCE ATTRIBUTION | B0-naive   |      36 |                       72 |                          27 |                             1 |                             0 |                              1 |                       0 |                               0 |                     nan      |
| SYNTHETIC POLICY-CONSISTENCY TEST; NOT SOURCE ATTRIBUTION | B1-badge   |      36 |                       72 |                          27 |                             1 |                             0 |                              1 |                       0 |                               0 |                     nan      |
| SYNTHETIC POLICY-CONSISTENCY TEST; NOT SOURCE ATTRIBUTION | X-evidence |      36 |                       72 |                          27 |                             0 |                             1 |                              1 |                       1 |                               1 |                       0.9167 |

These cases test rule-policy consistency, NOT ground-truth source fractions or source-classification accuracy.

## Multi-station overlap

Not enough stations.

## Data and model limitations

- No real Delhi training metrics unless a sourced monitoring CSV was imported and its timestamps/coverage verified.
- Forecast models are lag-only and historic observed weather is used only in past-looking features; no future weather leakage.
- Real monitor publication delays have not been validated; operational as-issued replay requires ingestion availability timestamps.
- Original model uses deterministic LightGBM hyperparameters; no tuning against the untouched test set.
- Overall CPCB AQI not computed from PM2.5 alone.
- FIRMS, HYSPLIT, TROPOMI, and MAIAC are not fetched; they are explicitly unavailable, not zero.
- Source hypotheses are policy-screening, not physical source contributions.
- Spatial comparison is only coincident-station correlation, not causal origin or spatial interpolation.
- The interactive interface is Gradio; it reads the configured result directory and does not claim live operational forecasts.
