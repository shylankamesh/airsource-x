# Three-minute demo script

Use the **Bundled Delhi station history** source for the reproducible retrospective benchmark. It contains six CPCB-derived historical station series from 2018–2019 under CC BY 4.0; it is not current air quality. The separate Open-Meteo provider view is a gridded model estimate and must not be presented as station truth.

## 0:00–0:30 — The problem

“A PM₂.₅ number tells us what a monitor observed, but it does not tell us whether the episode is regional, which explanations fit, or what evidence is missing. AirSource X joins forecasting to an auditable investigation.”

## 0:30–1:00 — Data and provenance

Show the selected station, period, missingness, and the dataset's Mendeley/CPCB provenance in **Data & methods**. Point out that missing hours are not interpolated and that the bundled values end in October 2019.

## 1:00–1:40 — Forecast evaluation

Open **Forecast lab** and show the instant historical forecast loaded from the verified station artifact. Then run the two-horizon evaluation and show candidates selected across three purged expanding-window validation folds, untouched chronological test window, 48-hour purge, sample count, MAE/RMSE/bias, persistence and weekly-naive comparison, plus calibrated interval coverage and width. Only present numbers produced from the verified dataset loaded for the demonstration.

## 1:40–2:15 — Spatial and unusual-pattern context

Open **Station watch**, compare the synchronized readings, then run the Isolation Forest screen. Explain that “unusual” means statistically atypical in this dataset, not a confirmed pollution event.

## 2:15–2:45 — Evidence and abstention

Open **Evidence room**. Point out a support signal, a contradiction, missing satellite/fire or boundary-layer context, and the next measurement recommendation. Remove one evidence family and show the conclusion changing or becoming insufficient.

## 2:45–3:00 — Close

“AirSource X does not label a source from a nearby marker or a model explanation. It shows the evidence we have, the evidence we lack, and a defensible next step.”

## Judge questions to prepare for

- **What is the ground truth?** Name the exact monitor dataset, dates, units, QA policy, and license used in the live demonstration. If none, report no measured model performance.
- **How is leakage controlled?** Chronological holdout plus a 48-hour purge for the longer target; no random split.
- **Does the app identify the source?** No. It screens non-specific patterns and abstains; this build has no independent source-apportionment labels.
- **Why use Open-Meteo?** It provides a keyless user walkthrough. Its grid estimates are clearly separated from station measurements and never used as model validation truth.
- **What would you build next?** Add spatial holdout and validated station harmonization, then provenance-rich satellite/fire context and user task evaluation.
