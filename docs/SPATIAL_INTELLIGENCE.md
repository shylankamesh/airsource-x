# Multi-station spatial intelligence

## Scope
The spatial workspace joins observations to a station registry using exact station IDs. It provides:
- a station-position plot from sourced coordinates;
- latest common-timestamp PM2.5 comparison (no interpolation);
- straight-line Haversine distances;
- pairwise Pearson correlations only when the requested number of overlapping hourly rows exists;
- observed station time series and coverage exports.

## Registry provenance
`configs/delhi_station_registry.csv` maps the six bundled dataset IDs to published Delhi monitoring-station names. Coordinates are rounded to 0.001 degree from Table S1 of Miinalainen et al.'s supplementary material (2022). `DCStadium` is mapped to Major Dhyan Chand National Stadium; `Okhla` to Okhla Phase-2. Station labels are aliases in the curated dataset, so check these mappings against the original dataset metadata before operational use.

The cited supplement identifies operator and coordinate values. It reports station coverage by year; it does not establish that every station maintained unchanged coordinates or instrumentation over the entire bundled dataset period. The `valid_from` field is a registry scope marker, not a claim of independently verified commissioning date.

## Interpretation guardrails
- Distances are straight-line geometry, not road distance or atmospheric transport distance.
- Correlation is descriptive co-variation and does not establish a common emission source.
- A synchronized elevation at multiple stations is regional context, not source attribution.
- No interpolation, kriging, plume reconstruction, or upwind/downwind inference is performed.
- Missing station coordinates prevent spatial joining; no coordinates are guessed.
- Historical observations (2018–2019) must not be described as current conditions.

## Sources
- Miinalainen et al., supplementary Table S1, *Assessing the climate and air quality effects of future aerosol mitigation in India using a global climate model combined with statistical downscaling*, https://acp.copernicus.org/preprints/acp-2022-513/acp-2022-513-supplement.pdf
- Government of NCT of Delhi, Department of Environment, *Inventory of major point air pollution sources in Delhi: Hotspots and other priority areas* (2023), https://dpcc.delhigovt.nic.in/uploads/news/ae9ce818bf8b9e12ddb90177ce3108c7.pdf
- Station site-type cross-check for Ashok Vihar and Nehru Nagar: https://researchportal.northumbria.ac.uk/files/43668715/Unprecedented_Reduction_in_Air_Pollution_and_Corresponding_Short_term_Premature_Mortality_Associated_with_COVID_19_Lockdown_in_Delhi_India.pdf
