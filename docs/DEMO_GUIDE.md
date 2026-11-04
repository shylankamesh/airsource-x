# Judge Demo — AirSource X

## Opening statement

“AirSource X is a research prototype. Its PM2.5 forecasts were evaluated retrospectively on one ITO, Delhi CPCB station. The evidence-removal screen is a separate synthetic software-policy demo; it does not identify real pollution sources.”

## 4-minute flow

1. **0:00–0:35 — Purpose:** Explain the goal: pair a forecast with visible evidence limits. State that this is not official CPCB forecasting or source apportionment.
2. **0:35–1:35 — Delhi forecast:** Open `website/index.html` or start `python app.py`. Show ITO Delhi, the 0–24h and 24–48h held-out comparisons, source coverage, gaps, and split dates. The preceding-24-hour mean wins at 0–24h; the validation-selected method at 24–48h is also that mean, even though raw LightGBM has lower test MAE there. Mention that the last-observation baseline was also evaluated and performed worse on this split.
3. **1:35–2:25 — Uncertainty:** Explain that the 90% interval achieved only 71.5% and 74.6% empirical coverage. Do not call it calibrated.
4. **2:25–3:20 — Evidence Investigation Studio:** Select a predeclared synthetic fixture and disable an evidence family. Say explicitly that this demonstrates rule-policy behavior on authored fixtures, not a real event or physical intervention.
5. **3:20–4:00 — Boundaries:** Briefly show Multi-station Context as a separate 2018–2019 historical dataset. Show the data audit and limitations: only one station is used for forecast evaluation, retrospective timestamps with publication lag unverified, one 148-hour data gap, no source truth labels, no live feeds or source percentages.

## Anticipated questions

- **Are these real Delhi measurements?** The forecast experiment uses the bundled OpenCity-listed CPCB ITO observations. The evidence-rule examples remain synthetic.
- **Is this an operational forecast?** No. Measurement publication/availability time at each issue time has not been verified.
- **Does LightGBM beat the baseline?** No for 0–24h held-out MAE. Raw LightGBM beats the baselines at 24–48h test MAE, but validation selects the preceding-24-hour mean. The last-observation comparator is reported separately. Report both facts.
- **Are the intervals calibrated?** No. Nominal 90% intervals covered 71.5% and 74.6% of the held-out cases.
- **Can AirSource X quantify sources?** No. There are no independent source labels or validated physical source-apportionment method.
- **What is the source-screening demo?** Synthetic policy fixtures that show support, contradictions, missing evidence, abstention, and evidence removal. Evidence removal means information loss, not an emission intervention.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

The app defaults to the real-data retrospective results in `results/delhi_ito_2024_25/`. To view the synthetic pipeline instead, set `AIRSOURCE_RESULTS_DIR=results` before launch. The static website is `website/index.html`.
