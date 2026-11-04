# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary audience: Neural Storm 2026 hackathon judges reviewing the Green Planet air-quality monitoring and source-attribution track. They need to understand what was built, what the Delhi experiment measured, and what it does not establish.

## Product Purpose

AirSource X is an experimental PM2.5 forecasting and evidence-screening prototype. Its demo should help a visitor understand the retrospective ITO, Delhi evaluation, compare the tested forecast horizons and baselines, and inspect the experiment's limits and data provenance.

## Positioning

The project makes forecast errors, evidence provenance, uncertainty, and unsupported claims visible. Its distinguishing commitment is to allow insufficient evidence and to keep forecast evaluation separate from source-hypothesis screening. It does not estimate physical pollution-source fractions.

## Operating Context

The public site is a static judge-facing project presentation. It links to a local Gradio prototype and a portable experiment report in the GitHub repository. The forecast evaluation uses CPCB ITO observations listed by OpenCity, aggregated from 15-minute to hourly records, with a chronological held-out evaluation.

## Capabilities and Constraints

- The committed Delhi run evaluates one station, ITO, over records spanning January 2024 through January 2026.
- It compares LightGBM forecasts with simple baselines for 0–24-hour and 24–48-hour horizons.
- Results are retrospective, based on 130 held-out issues per horizon, and are not validated live forecasts or evidence of performance across Delhi, other states, or cities.
- Nominal 90% prediction intervals under-cover in this test (71.5% and 74.6%); they must remain labeled exploratory and uncalibrated.
- Biomass-burning and dust-like screens are evidence hypotheses, not measured source attribution. Synthetic scenarios are software logic fixtures, not ground truth.
- The product is not an official forecast, AQI service, health advisory, or emergency warning authority.
- Existing website stack is static HTML, CSS, and JavaScript, with project-relative links required for GitHub Pages deployment.

## Brand Commitments

Keep the name AirSource X and the evidence-first voice. For this demo, the user selected the supplied Ascend page as a visual reference: adapt its immersive deep-space/navy atmosphere and mint accent to AirSource X. Do not use Ascend's fictional product name, copy, customers, logos, metrics, or external planet assets.

## Evidence on Hand

- `results/delhi_ito_2024_25/EXPERIMENT_RESULTS.md` and its CSV/JSON artifacts: actual retrospective experiment outputs.
- `website/index.html`, `website/styles.css`, and `website/app.js`: existing working static demo and interactive horizon comparison.
- `assets/screenshots/airsource-x-homepage.jpg`: earlier public-site screenshot; it must be recaptured after the visual change.
- No live forecast feed, validated source-attribution dataset, multi-city evaluation, verified public Gradio deployment, or measured public-health impact is established. These must not be implied or fabricated.

## Product Principles

- Show the baseline comparison before claiming model value.
- Keep provenance and measurement scope close to every result.
- Distinguish measured observations, model outputs, and conceptual graphics.
- Make uncertainty and unsupported interpretations easy to find.
- Never present a heuristic hypothesis as a measured source contribution.

## Accessibility & Inclusion

Keep the static page readable and operable by keyboard, preserve semantic headings and chart labels, support narrow screens, and honor reduced-motion preferences. The dark reference treatment must maintain readable contrast.
