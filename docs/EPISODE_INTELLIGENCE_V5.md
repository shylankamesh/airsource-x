# V5 — Pollution episode intelligence and reliability increment

## What changed

V5 adds a transparent PM2.5 episode-screening module and a dedicated Streamlit workspace.

### Detection method

For each station, the detector:
1. Sorts observations by timestamp and removes duplicate station/timestamp rows.
2. Computes a rolling median over the preceding 24 hours by default, using only earlier observations (`closed="left"`).
3. Computes a robust dispersion estimate from the preceding median absolute deviation (MAD), scaled by 1.4826.
4. Flags readings only when all conditions hold:
   - PM2.5 is at least the configurable concentration floor (default 75 µg/m³);
   - the reading exceeds the prior rolling median by at least the larger of 25 µg/m³ or 2.5 × robust sigma;
   - the flagged run persists for at least two hours by default.
5. Reports onset, end, peak time, peak concentration, prior baseline and onset excess.

A small permitted timestamp gap can be bridged when assembling a run, but missing concentration values are never filled or interpolated. This is a screening heuristic, not a regulatory threshold or a calibrated event classifier.

### Network episode grouping

Station episodes whose onset times fall within a configurable window (default three hours from the first onset in a group) are grouped into a multi-station episode. The output includes first/last onset, affected stations, lead/last station by timestamp, onset span and highest station-level peak.

The ordering is descriptive only. It does not establish a shared emitter, plume movement, source attribution, or causal relationship.

### Wind quality gate

The wind summary screens speed and direction for basic plausibility. It does not repair or clip values. Passing the screen only means wind context may be reviewed after checking units, sensor metadata and provenance; it is not a transport model. The bundled archive has a high maximum wind-speed value that should be traced to the upstream units and quality controls before stronger use.

## UI

A new **Episode intelligence** workspace exposes:
- baseline-window and minimum-history settings;
- minimum absolute rise and concentration floor;
- minimum duration and cross-station grouping window;
- network episode timeline and station-level event table;
- CSV downloads and wind-quality audit;
- explicit source-type and interpretation caveats.

Bundled history is historical (2018–2019); provider-grid estimates and uploaded files are labelled separately.

## Tests

`tests/test_episodes.py` covers:
- persistent rise detection;
- rejection of an isolated spike;
- station onset ordering and non-causal wording;
- absent wind fields;
- implausible wind screening;
- empty input.

The GitHub Actions workflow `.github/workflows/ci.yml` runs compile checks and pytest on Python 3.11 and 3.12. This workflow is added to the package; it has not been run on GitHub because no repository has been created or modified.

## Remaining limitations

- The Streamlit UI has not been runtime-smoke-tested in this build environment because Streamlit is not installed here.
- This detector has synthetic unit tests but has not been validated against a labelled historical episode catalogue.
- It is not yet a warning system, source-apportionment model or health advisory.
- The historical wind series requires upstream metadata and quality-flag investigation.
- Existing trained model artifacts remain version-sensitive and historical. Their SHA-256 integrity does not guarantee runtime compatibility.
