# Data in this package

`raw/ito_delhi_2024_25.csv` is the OpenCity-listed ITO, Delhi - CPCB 15-minute resource used in the retrospective forecast experiment. `ITO_DELHI_DATA_MANIFEST.md` records the source listing, provenance, checksum, license metadata, timestamp caveat, and coverage audit. The raw data file is included in the full hackathon bundle but omitted from GitHub; download it from the source listing below to reproduce.

The OpenCity resource metadata identifies its license as Public Domain. CPCB asks users to acknowledge contributing agencies in research and other publications; preserve that attribution.

Download: https://data.opencity.in/dataset/delhi-hourly-air-quality-reports/resource/890f786d-fb9f-475e-8516-191bfa1b01ea

The file's name and listing identify 2024–25, but records extend through 1 January 2026. Timestamps contain explicit UTC offsets and the pipeline converts them to IST. A blank footer row has no timestamp. The experiment is retrospective; timestamp publication/availability latency is unknown.

Reproduce with:

```bash
python -m scripts.run --csv data/raw/ito_delhi_2024_25.csv --name "ITO Delhi CPCB" --outdir results/delhi_ito_2024_25
```

Check the generated `data_audit.json`, `forecast_splits.json`, and `EXPERIMENT_RESULTS.md` before citing metrics. Do not interpret the synthetic policy fixtures as atmospheric ground truth.
