# Integration audit: Codex submission package and Main ZIP

## Decision

The existing Codex package remains the single application foundation: its Gradio entry point, chronological ITO experiment, evidence-policy engine, outputs, static presentation, and deployment workflow are retained. The Main ZIP's six-station dataset is added as a **separate historical context view** in the existing Gradio app. The two station datasets are not concatenated and their forecast metrics are not compared as if they were one experiment.

| Area | Codex package | Main ZIP | Integration decision |
|---|---|---|---|
| Data ingestion and provenance | ITO CPCB-derived 15-minute observations, Jan 2024–Jan 2026; availability semantics remain unverified | Prepared six-station Mendeley benchmark, Jun 2018–Oct 2019, CC BY 4.0 | Keep distinct datasets, periods, labels, and provenance. Bundle the prepared six-station file compressed with attribution. |
| Forecast targets and split | Two complete future 24-hour mean targets; chronological holdout and 48-hour purge | Similar two-horizon targets; separate per-station training and temporal evaluation | Preserve the existing Codex ITO pipeline. Do not transfer scores or fitted models between datasets. |
| Baselines | Persistence is the mean of the preceding 24 valid hourly readings; seasonal mean is learned on training rows | `current` is the latest hourly PM2.5 reading; weekly same-horizon comparison is also used | Preserve the Codex 24-hour mean and seasonal baselines. Add latest observation as a separately named comparator; all methods use the same valid rows, and validation selects among them. |
| Main dataset integrity | Not applicable to the Codex ITO artifacts | Bundled CSV SHA-256: `92cab112b34fe3daf41328c8750bbea38085e322d0347274c0ef15d7af1fbde0`; Main `models/manifest.json` expects `5b1ac3d69b1f70b30089db2563c70a1b8aaa60ddf2ef15164638df46f1250af8` | The complete dataset digests differ. Main's model artifacts are not imported or loaded, and no manifest hash is changed to bypass the mismatch. Re-training and reproducing Main's benchmark remain separate work. |
| Model artifacts | Existing per-run ITO artifacts and report | Twelve station/horizon joblib files with a dataset digest mismatch | Keep Codex artifacts and results as-is. Exclude Main joblib files pending verified training-data provenance and reproducibility. |
| Spatial/multi-station analysis | ITO run reports coincident-station metadata only; no station coordinates | Six station-labelled historical series; provenance notes coordinates are not bundled | Add per-station coverage, observed daily means, and a same-hour network-relative MAD screen. Do not claim geographic distance, citywide interpolation, or source attribution. |
| Evidence investigation | Evidence support, contradiction, missingness, abstention, and synthetic counterfactual fixtures | Separate preliminary evidence heuristics and source-screening UI | Preserve Codex evidence engine and synthetic labels. Main's Streamlit investigation module is not merged as a second competing app. |
| Interface and deployment | Gradio app plus static website and GitHub Pages workflow | Streamlit app plus Render/Docker files | Keep Gradio as the sole Python application entry point. The static site remains a presentation; it does not run Python models. |
| Tests and docs | Forecast, evidence, integration, and website tests | No comparable test suite included in the ZIP | Preserve Codex tests and add station-context tests. Record the integration decisions here. |
| Repository references | Current repository owner and links are `shylankamesh/airsource-x` | Main README's clone URL points to `tsaisanth29-ece/airsource-x` | Keep the verified `shylankamesh/airsource-x` links; do not copy the Main README wholesale. |

## Integrity audit details

The bundled Main CSV was hashed directly from the supplied ZIP. Its full SHA-256 is `92cab112b34fe3daf41328c8750bbea38085e322d0347274c0ef15d7af1fbde0`, which does not match the full digest declared in its model manifest. The files therefore cannot be treated as a verified dataset/model pair. The app code in Main guards its instant artifact preview on an exact data digest; the integration does not weaken that guard or copy those models.

The Main forecasting code uses the current hourly PM2.5 column for its `persistence` score. The retained Codex forecasting pipeline uses `pm_lag24_mean`, a mean of preceding hourly observations, and a training-only calendar baseline. The rerun adds a separately labelled `Last-observation` comparator to the Codex validation candidate set and held-out metrics. This is the primary ITO evaluation currently shown in the dashboard and report.

## What the added six-station view measures

- Per-station record counts, valid PM2.5 counts, observed first/last timestamps, and valid-share percentage.
- Daily observed PM2.5 means only when at least 18 hourly values are present that day; gaps are left as gaps.
- Same-hour deviations from the median across the stations that report in that hour, scored using median absolute deviation. A row is surfaced only when at least four stations report and the robust score is at least 3.5 in magnitude.

This is a descriptive network-relative screen. The dataset does not provide verified coordinates in the supplied provenance, and the screen is not a spatially validated anomaly detector or evidence of a pollution source.

## Still unverified

- Independent verification of either provider's instrument-level quality and availability timestamps.
- Reproduction of Main's saved models from the exact dataset digest recorded in the manifest.
- Geographic coordinates, spatially blocked generalization, and any quantitative source-attribution accuracy.
- Public hosting of the interactive Python application.
