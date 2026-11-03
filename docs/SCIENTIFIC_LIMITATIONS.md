# Scientific limitations and blockers

**CRITICAL: No observational Delhi metrics are provided in this package.** The runtime has no outbound CSV access. OpenCity metadata was discovered on the public web, but the CSV bytes were not accessible from the sandbox, and no original monitoring observations were supplied by the user.

1. **Forecast validity:** Synthetic tests verify that code executes and avoids obvious forward timestamp leakage. They do not verify accuracy for Delhi or any other real city. Observed measurement timestamps need an independent publication/availability audit; 48h split purge alone does not ensure operational replay if source labels are delayed.
2. **Model skill:** On synthetic stations the LightGBM model underperforms persistence. The validation-based selection falls back to the better method. Severe-event detection also underperforms. No improvement should be claimed without data and better model development.
3. **Physical source attribution:** Hypothesis rules identify compatible observations only; no percentage contributions or causal claims. Source labels remain unvalidated. FIRMS is unavailable, not evidence of no burning.
4. **Evidence policy experiment:** 36 cases are 12 synthetic patterns with 3 quantitative variations; these are code-consistency tests against author-defined policies. B0 and B1 are weak constructed baselines; results cannot establish superiority to independent research methods.
5. **Spatial:** Synthetic stations have no geographic meaning. Pairwise overlap and correlations do not establish local versus transported pollution. No real coordinates, HYSPLIT, satellite footprints, or spatial holdout provided.
6. **Uncertainty:** Split residual intervals are exploratory. Nominal 90% bounds miss nominal coverage on the generated test data; empirical values are exported. Time dependence/distribution shift can reduce coverage.
7. **Weather forecasts:** Future archived weather forecast data are not used. This minimizes leakage but may reduce forecast skill. Real as-issued archived forecast integration requires provider run provenance.
8. **Health guidance / AQI:** No personalized health guidance. Overall Indian AQI requires enough pollutants and official computations; only PM2.5 mass concentration forecasts are produced.
9. **Deployment:** Local Gradio UI can run where dependencies are installed. It is not publicly hosted and has not been verified on all operating systems or browsers.
10. **Licensing:** Real raw CSVs and scientific provider products should only be redistributed after checking licenses/attribution and API terms.
