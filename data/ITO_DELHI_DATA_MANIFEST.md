# ITO Delhi source data manifest

- Dataset: ITO CPCB 15-minute observations, resource labelled 2024–25
- Source listing: https://data.opencity.in/dataset/delhi-hourly-air-quality-reports/resource/890f786d-fb9f-475e-8516-191bfa1b01ea
- Provider source: CPCB Central Control Room: https://airquality.cpcb.gov.in/ccr/
- Accessed: 4 November 2026
- OpenCity metadata: CSV, updated 15 January 2026, license listed as Public Domain
- Attribution: CPCB requests acknowledgement of contributing agencies in research and other publications
- Local file: `data/raw/ito_delhi_2024_25.csv`
- SHA-256: `dfd2f715c38326a08ce096bd05d800e770ef041ed77978660c026d7dc1822df8`
- Source rows: 68,985, including one blank footer row
- Timestamp format: explicit UTC offsets; converted to Asia/Kolkata for analysis
- Observation span: 1 January 2024 through 1 January 2026
- Duplicate timestamps: 0
- Hourly PM2.5 coverage after 3-of-4 gate: 16,362 / 17,545 = 93.257%
- Longest missing PM2.5 run: 148 hours
- Parsed coverage: PM10 93.474%, NO2 96.637%; WS/RH unavailable in this file

The raw CSV is included in the full submission bundle and excluded from GitHub. Download it from the source link into `data/raw/` to reproduce the analysis. Retain the CPCB contributor acknowledgement.
