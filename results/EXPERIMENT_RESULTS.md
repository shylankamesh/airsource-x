# AirSource X — Experiment execution report

**DATA STATUS: SYNTHETIC / NOT DELHI MEASUREMENTS**

> Do not cite simulated forecast errors as measured Delhi prediction performance. No physical source-apportionment accuracy is established.

## Input coverage

| station     | source                            | first_hour_ist            | last_hour_ist             |   total_hours |   valid_pm25_hours |   pm25_hour_coverage | WARNING                  |
|:------------|:----------------------------------|:--------------------------|:--------------------------|--------------:|-------------------:|---------------------:|:-------------------------|
| SYNTHETIC_A | DETERMINISTIC SYNTHETIC GENERATOR | 2024-01-01 00:00:00+05:30 | 2025-03-05 23:00:00+05:30 |         10320 |              10051 |              0.97393 | Not empirical Delhi data |
| SYNTHETIC_B | DETERMINISTIC SYNTHETIC GENERATOR | 2024-01-01 00:00:00+05:30 | 2025-03-05 23:00:00+05:30 |         10320 |              10046 |              0.97345 | Not empirical Delhi data |

## Forecast benchmark (0–24h and 24–48h)

| data_label                         | station     | horizon      | model               |   n |     mae |    rmse |     bias |
|:-----------------------------------|:------------|:-------------|:--------------------|----:|--------:|--------:|---------:|
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_0_24  | LightGBM            |  84 | 17.6594 | 31.1279 | -15.1289 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_0_24  | Persistence         |  84 |  9.5579 | 13.5841 |  -0.4737 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_0_24  | Seasonal            |  84 | 27.7397 | 41.9265 | -25.2317 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_0_24  | Validation-selected |  84 |  9.5579 | 13.5841 |  -0.4737 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_24_48 | LightGBM            |  84 | 19.6461 | 33.6778 | -17.8049 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_24_48 | Persistence         |  84 | 16.0718 | 23.6884 |  -0.2626 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_24_48 | Seasonal            |  84 | 27.6298 | 41.3798 | -25.2686 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_24_48 | Validation-selected |  84 | 16.0718 | 23.6884 |  -0.2626 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_0_24  | LightGBM            |  84 | 15.3237 | 26.363  | -12.8629 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_0_24  | Persistence         |  84 | 10.1117 | 13.8884 |  -0.5243 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_0_24  | Seasonal            |  84 | 23.7836 | 36.4982 | -22.5097 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_0_24  | Validation-selected |  84 | 10.1117 | 13.8884 |  -0.5243 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_24_48 | LightGBM            |  84 | 16.9435 | 29.4503 | -14.7782 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_24_48 | Persistence         |  84 | 15.3627 | 23.083  |  -0.2699 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_24_48 | Seasonal            |  84 | 23.5476 | 35.8264 | -22.2802 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_24_48 | Validation-selected |  84 | 15.3627 | 23.083  |  -0.2699 |

## Locked evaluation partition metadata

```json
[
  {
    "station": "SYNTHETIC_A",
    "train_n": 256,
    "valid_n": 83,
    "test_n": 84,
    "train_last": "2024-09-13 00:00:00+05:30",
    "validation_first": "2024-09-16 00:00:00+05:30",
    "validation_last": "2024-12-07 00:00:00+05:30",
    "test_first": "2024-12-10 00:00:00+05:30"
  },
  {
    "station": "SYNTHETIC_B",
    "train_n": 256,
    "valid_n": 83,
    "test_n": 84,
    "train_last": "2024-09-13 00:00:00+05:30",
    "validation_first": "2024-09-16 00:00:00+05:30",
    "validation_last": "2024-12-07 00:00:00+05:30",
    "test_first": "2024-12-10 00:00:00+05:30"
  }
]
```

## Exploratory elevated-pollution event metrics (150 µg/m³; not official AQI)

| data_label                         | station     | horizon      | model               |   threshold_ugm3 | threshold_label                              |   actual_events |   hits |   misses |   false_alarms |   true_negatives |   precision |   recall |
|:-----------------------------------|:------------|:-------------|:--------------------|-----------------:|:---------------------------------------------|----------------:|-------:|---------:|---------------:|-----------------:|------------:|---------:|
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_0_24  | LightGBM            |              150 | EXPLORATORY high-PM event (not official AQI) |              20 |      0 |       20 |              0 |               64 |  nan        | 0        |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_0_24  | Persistence         |              150 | EXPLORATORY high-PM event (not official AQI) |              20 |     17 |        3 |              3 |               61 |    0.85     | 0.85     |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_0_24  | Seasonal            |              150 | EXPLORATORY high-PM event (not official AQI) |              20 |      0 |       20 |              0 |               64 |  nan        | 0        |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_0_24  | Validation-selected |              150 | EXPLORATORY high-PM event (not official AQI) |              20 |     17 |        3 |              3 |               61 |    0.85     | 0.85     |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_24_48 | LightGBM            |              150 | EXPLORATORY high-PM event (not official AQI) |              20 |      0 |       20 |              0 |               64 |  nan        | 0        |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_24_48 | Persistence         |              150 | EXPLORATORY high-PM event (not official AQI) |              20 |     14 |        6 |              6 |               58 |    0.7      | 0.7      |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_24_48 | Seasonal            |              150 | EXPLORATORY high-PM event (not official AQI) |              20 |      0 |       20 |              0 |               64 |  nan        | 0        |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_24_48 | Validation-selected |              150 | EXPLORATORY high-PM event (not official AQI) |              20 |     14 |        6 |              6 |               58 |    0.7      | 0.7      |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_0_24  | LightGBM            |              150 | EXPLORATORY high-PM event (not official AQI) |              15 |      0 |       15 |              0 |               69 |  nan        | 0        |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_0_24  | Persistence         |              150 | EXPLORATORY high-PM event (not official AQI) |              15 |     10 |        5 |              3 |               66 |    0.769231 | 0.666667 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_0_24  | Seasonal            |              150 | EXPLORATORY high-PM event (not official AQI) |              15 |      0 |       15 |              0 |               69 |  nan        | 0        |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_0_24  | Validation-selected |              150 | EXPLORATORY high-PM event (not official AQI) |              15 |     10 |        5 |              3 |               66 |    0.769231 | 0.666667 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_24_48 | LightGBM            |              150 | EXPLORATORY high-PM event (not official AQI) |              14 |      0 |       14 |              0 |               70 |  nan        | 0        |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_24_48 | Persistence         |              150 | EXPLORATORY high-PM event (not official AQI) |              14 |      6 |        8 |              7 |               63 |    0.461538 | 0.428571 |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_24_48 | Seasonal            |              150 | EXPLORATORY high-PM event (not official AQI) |              14 |      0 |       14 |              0 |               70 |  nan        | 0        |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_24_48 | Validation-selected |              150 | EXPLORATORY high-PM event (not official AQI) |              14 |      6 |        8 |              7 |               63 |    0.461538 | 0.428571 |

## Exploratory split-residual 90% interval coverage (temporal dependence caveat)

| data_label                         | station     | horizon      |   nominal_coverage |   empirical_coverage |   mean_interval_width_ugm3 |   calibration_rows |   test_rows | calibration_limitation                                     |
|:-----------------------------------|:------------|:-------------|-------------------:|---------------------:|---------------------------:|-------------------:|------------:|:-----------------------------------------------------------|
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_0_24  |                0.9 |             0.821429 |                    98.8251 |                 83 |          84 | Temporal dependence: coverage is empirical, not guaranteed |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_A | target_24_48 |                0.9 |             0.845238 |                   118.246  |                 83 |          84 | Temporal dependence: coverage is empirical, not guaranteed |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_0_24  |                0.9 |             0.833333 |                    83.1071 |                 83 |          84 | Temporal dependence: coverage is empirical, not guaranteed |
| SYNTHETIC / NOT DELHI MEASUREMENTS | SYNTHETIC_B | target_24_48 |                0.9 |             0.869048 |                   113.146  |                 83 |          84 | Temporal dependence: coverage is empirical, not guaranteed |

## B0 / B1 / X evidence policy test — SYNTHETIC LOGIC FIXTURES ONLY

| experiment                                                | method     |   cases |   hypothesis_assessments |   policy_insufficient_count |   unsupported_conclusion_rate |   appropriate_abstention_rate |   supported_decision_retention |   provenance_trace_rate |   contradiction_visibility_rate |   exact_policy_outcome_match |
|:----------------------------------------------------------|:-----------|--------:|-------------------------:|----------------------------:|------------------------------:|------------------------------:|-------------------------------:|------------------------:|--------------------------------:|-----------------------------:|
| SYNTHETIC POLICY-CONSISTENCY TEST; NOT SOURCE ATTRIBUTION | B0-naive   |      36 |                       72 |                          27 |                             1 |                             0 |                              1 |                       0 |                               0 |                     nan      |
| SYNTHETIC POLICY-CONSISTENCY TEST; NOT SOURCE ATTRIBUTION | B1-badge   |      36 |                       72 |                          27 |                             1 |                             0 |                              1 |                       0 |                               0 |                     nan      |
| SYNTHETIC POLICY-CONSISTENCY TEST; NOT SOURCE ATTRIBUTION | X-evidence |      36 |                       72 |                          27 |                             0 |                             1 |                              1 |                       1 |                               1 |                       0.9167 |

These cases test rule-policy consistency, NOT ground-truth source fractions or source-classification accuracy.

## Multi-station overlap

| station_a   | station_b   |   common_hours |   correlation |   mean_difference_ugm3 |
|:------------|:------------|---------------:|--------------:|-----------------------:|
| SYNTHETIC_A | SYNTHETIC_B |           9783 |      0.677761 |                15.3325 |

## Data and model limitations

- No real Delhi training metrics unless a sourced monitoring CSV was imported and its timestamps/coverage verified.
- Forecast models are lag-only and historic observed weather is used only in past-looking features; no future weather leakage.
- Real monitor publication delays have not been validated; operational as-issued replay requires ingestion availability timestamps.
- Original model uses deterministic LightGBM hyperparameters; no tuning against the untouched test set.
- Overall CPCB AQI not computed from PM2.5 alone.
- FIRMS, HYSPLIT, TROPOMI, and MAIAC are not fetched; they are explicitly unavailable, not zero.
- Source hypotheses are policy-screening, not physical source contributions.
- Spatial comparison is only coincident-station correlation, not causal origin or spatial interpolation.
- The local environment could not install Streamlit; install requirements on a connected machine to run app.py.
