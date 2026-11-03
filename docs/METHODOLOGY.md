# AirSource X: Methodology and Reproducibility

## Data mode and scope
The package contains two separate evaluation tracks: (1) a retrospective observational forecast run for ITO, Delhi - CPCB using the CSV and source manifest in `data/raw/`; and (2) deterministic synthetic fixtures used only to test evidence-rule software behavior. Synthetic evidence-policy metrics are not atmospheric accuracy. The Delhi observations are CPCB-derived but have not been independently audited for station publication/availability time semantics, so forecast skill is retrospective rather than validated as-issued operational accuracy.

## Quality and time
CSV timestamps without timezone offsets are assumed Asia/Kolkata, NOT verified. Duplicates averaged after timestamp grouping; source-marked invalid values require provider-specific expansion. Negative pollution values become NA. Hourly PM2.5 from a 15-minute feed requires 3 of 4 valid rows. Missing labels are never filled: each 24h target requires 18 actual valid hours. Past features also require a minimum of 18 valid readings in the preceding 24 hours.

## Forecast issue and targets
For a daily issue T = midnight Asia/Kolkata, the model's features are sourced only from timestamps `< T`. Target A = arithmetic mean of observed hourly PM2.5 over `(T,T+24h]`; target B = `(T+24h,T+48h]`. **Operational timestamps**: CPCB original measurement timestamp may not be when published. The code assumes a prior reading could be used after its timestamp, but this has not been independently validated for real source records. This must be audited before honest operational replay.

## Models and splits
Per station, the earlier 60% of eligible issues train the model, the next 20% validate, and the latest 20% test. Observations are excluded between partitions with a two-day embargo to avoid overlapping 48-hour labels. Simple past-24h persistence and training-only monthly calendar baselines provide controls. LightGBM uses fixed hyperparameters. The **validation** block alone selects which of these three methods to deploy; test is never used for selection. Test MAE, RMSE, mean bias, and forecast sample counts are reported per horizon.

## Forecast feature time safety
Features include lagged PM2.5 means and dispersion; past co-pollutant and observed past meteorological averages; and calendar features. Future observed weather is NEVER included. This first executable cut intentionally excludes future archived weather forecasts rather than incorrectly treating reanalysis as available at the issue time. Optional missing features remain NaN (LightGBM handles missing). No scaler or imputer is fitted on future data.

## Forecast interval caveat
The optional 90% interval uses absolute validation residual quantile and a symmetric band around LightGBM held-out predictions. This is an exploratory split-residual interval; temporal autocorrelation/distribution shift invalidate automatic exchangeability assumptions. Empirical coverage is always reported, and 90% nominal cannot be claimed as calibrated if coverage is worse.

## Source-hypothesis engine
Outputs are qualitative rule states: `supporting evidence present`, `mixed/contradictory`, `limited evidence`, `insufficient evidence`. Biomass-burning support requires independently observable fire coverage and transport compatibility. Dust-like evidence needs paired PM2.5/PM10 and compatible wind context. Humidity and wind speed share a meteorological evidence family; multiple measurements are not automatically independent. Rule thresholds are **project heuristics not physically validated emission indicators**. Missing FIRMS evidence is not 'zero fires'. Evidence-removal counterfactuals simulate missing information, not pollution interventions.

## Spatial analysis
Only common, QC-passed timestamps are compared and correlation and mean difference reported. The simulation does not represent geographically measured Delhi stations. The code performs no spatial interpolation, trajectory or emissions inference. Releasing a Delhi map requires authentic station coordinate provenance and station-siting checks.

## Scientific validation still required
Independent source-apportionment labels, atmospheric transport analyses, real satellite observations, and real station holdout validation are not available in this execution. All 36 synthetic policy tests are variations of 12 human-authored scenarios. Their policy expectations are predeclared in source code and cannot establish real-world source accuracy. The B0/B1 controls are intentionally weak, not published advanced systems. Report failures rather than hiding them.
