# ITO Delhi source data manifest

- Dataset: ITO CPCB 15-minute air-quality observations, resource labelled 2024–25
- Source listing: https://data.opencity.in/dataset/delhi-hourly-air-quality-reports/resource/890f786d-fb9f-475e-8516-191bfa1b01ea
- Provider source: CPCB Central Control Room: https://airquality.cpcb.gov.in/ccr/
- Accessed: 4 November 2026
- Provider listing metadata: updated 15 January 2026; CSV; license field says Public Domain
- CPCB publication notice: acknowledge the respective contributing agencies when using the data in research or other publication
- Local file: `ito_delhi_2024_25.csv`
- SHA-256: `dfd2f715c38326a08ce096bd05d800e770ef041ed77978660c026d7dc1822df8`
- Source rows: 68,985, including one blank annual footer row
- Timestamp format: explicit UTC offsets in the observations; converted to Asia/Kolkata for analysis
- Observation span: 1 January 2024 through 1 January 2026 (resource name says 2024–25; final timestamp is 2026-01-01)
- Duplicate timestamps: 0
- Hourly PM2.5 coverage after the pipeline's 3-of-4 gate: 16,362 / 17,545 = 93.257%
- Longest missing PM2.5 stretch: 148 hours
- Other parsed coverage: PM10 93.474%; NO2 96.637%; WS and RH have no usable coverage in the current file

The file is included to make this particular experiment reproducible. The public-domain designation is taken from the OpenCity resource metadata; attribution is retained above and should accompany any redistribution or presentation.
