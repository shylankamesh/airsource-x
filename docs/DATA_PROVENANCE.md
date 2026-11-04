# Data provenance and preparation

## Source

AirSource X bundles the prepared form of **Sonawani, Shilpa; Patil, Kailas (2021), “Delhi Multi-Site Air-Quality Data Set,” Version 1, Mendeley Data, DOI: [10.17632/bzhzr9b64v.1](https://doi.org/10.17632/bzhzr9b64v.1)**. The source page describes hourly CPCB-monitor data from six Delhi stations, June 1, 2018 to October 1, 2019, with 11,704 rows per site, and licenses it under **CC BY 4.0**. The source data are author-curated; this project does not claim to independently audit the CPCB instruments or raw feeds.

The source archive is not redistributed in this repository. The prepared station/time series is provided at `data/processed/delhi_multisite_hourly.csv` under the same attribution and license. Run `scripts/prepare_public_dataset.py` to reproduce it from the original archive; download instructions are in `data/raw/README.md`.

## Preparation

- The six files are combined into one station-labelled table; `year`, `month`, `day`, and `hour` become a local, timezone-aware timestamp in Asia/Kolkata.
- PM2.5 and other pollutant values are carried through without interpolation or synthetic replacement. The source files contain one hourly row per station and report no missing PM2.5 values; the preparation script emits row counts and coverage so changes are visible.
- The `WS` weather field is reported in metres per second in a peer-reviewed study using this same dataset; AirSource converts it to the app's km/h schema by multiplying by 3.6. That paper also describes temperature as °C, relative humidity as %, wind direction in degrees, solar radiation in W/m², and pressure in mmHg: [Sankar & Arasu, PLOS ONE (2025)](https://doi.org/10.1371/journal.pone.0330465).
- Station coordinates are not bundled with this benchmark because one published location table contains an apparent coordinate anomaly. AirSource does not use those coordinates or imply spatial distances from station names.
- The benchmark is historical and short (roughly 16 months); it is not a live CPCB feed, does not capture interannual variation, and cannot establish current-season performance.

## Evaluation protocol

For each station independently, issue times are split chronologically. The last 20% is the untouched test block; a 48-hour purge prevents the longer target's future values from crossing the train/test boundary. Candidate LightGBM configurations and a HistGradientBoosting fallback are selected using three expanding-window validation folds, with a 48-hour label purge at each fold boundary. A later calibration block estimates a 90% split-conformal absolute-residual radius; that calibration is evaluated for empirical coverage on the untouched test block. Test intervals can under-cover during seasonal or distribution shift, so observed test coverage and width are reported rather than assuming the nominal 90% guarantee.

The target is mean PM2.5 concentration for hours `t+1..t+24` and `t+25..t+48`; each requires a complete hourly target window. Features use only values at or before issue time. Results are compared against current-PM2.5 persistence and a weekly same-horizon target from one week earlier on matching test issue times. Per-station and aggregate benchmark outputs are written to `reports/` by `scripts/benchmark_public_dataset.py`.

This is an in-period temporal evaluation on one dataset. It is not a spatial holdout, external replication, official forecast, health-warning evaluation, or source-attribution validation.
