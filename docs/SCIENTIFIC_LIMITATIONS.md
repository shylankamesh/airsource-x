# Scientific limitations

## Forecast evaluation

- The Delhi run is a retrospective evaluation at one ITO monitor. It is not a live/as-issued forecast replay because monitor publication/availability timestamps were not audited.
- The source file spans January 2024 through 1 January 2026, has 93.257% hourly PM2.5 coverage, and a 148-hour maximum PM2.5 gap. One empty footer row has no timestamp.
- There are 130 held-out valid target issues per horizon. The last-observation baseline has substantially higher test error on this split. The preceding-24-hour mean has lower 0–24h test MAE; LightGBM has lower raw 24–48h test MAE. Validation selects LightGBM for 0–24h and the 24-hour mean for 24–48h. Do not imply LightGBM wins consistently.
- Nominal 90% split-residual intervals cover 71.5% and 74.6% of the two test horizons. They are exploratory and under-cover; they are not calibrated confidence bounds.
- These results do not establish accuracy at other Delhi stations, for other seasons or cities, or under distribution shift. Independent rolling-origin and station holdouts remain future validation work.
- LightGBM uses fixed hyperparameters; the final test partition was not used to select a model. The experiment does not show that a tuned or operational system would have the same performance.

## Data and operational timing

- The ITO file contains explicit UTC offsets, which are converted to IST. The resource is named 2024–25 but its last timestamp is 1 January 2026.
- CPCB is the listed source; the dataset is hosted by OpenCity. The OpenCity metadata marks the file Public Domain, and CPCB requests acknowledgement of contributing agencies. See `data/ITO_DELHI_DATA_MANIFEST.md`.
- Timestamp meaning and time at which each measurement became available to an operator are unverified. Past-only feature timestamps and a 48-hour split embargo reduce leakage risks but do not prove operational availability.
- Missing PM2.5 labels are not filled. The weather inputs WS and RH are unavailable in the file; no future observed weather is used.

## Source screening

- Biomass-burning and dust-like outputs are qualitative software heuristics. There are no independent source ground-truth labels, validated atmospheric transport analysis, source percentages, or chemical source-apportionment model.
- All 36 evidence-policy cases are variations on 12 author-written synthetic scenarios. They test code-policy consistency, not atmospheric source classification or superiority to research methods.
- Satellite fire detections, HYSPLIT trajectories, TROPOMI and MAIAC data are not integrated. Missing inputs are unavailable, not evidence that the source is absent.
- Evidence removal simulates information loss, not a real-world intervention.

## Use and deployment

- This is not an official CPCB forecast, overall AQI calculation, health guidance, medical tool, or emergency warning service.
- The static website and local Gradio app are included. No public demo deployment or browser-verified screenshot is included in this source package.
