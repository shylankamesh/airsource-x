# AirSource X — final submission checklist

## Verification status

| Requirement | Status | Evidence / remaining action |
|---|---|---|
| Latest integration on `main` | PASS | PR #1 merged on 4 November 2026 as `23bcb2546073ab0ea9a3dddac0e9c86a6a7baf85`. |
| Automated tests | PASS | 32 passed, 0 failed, 0 skipped with the supplied dependency environment and workspace temp directory. |
| App startup and forecast results | PASS | Gradio app started on localhost; dashboard showed held-out result rows for both horizons. |
| Six-station provenance, exact-time overlap, coverage, and comparative trends | PASS | Six labeled stations; 11,704 common all-station hours and 11,704 hours with at least four reporting; dataset hash checked by automated test. |
| Same-hour anomaly and coincident elevation screens | PASS | Displayed as retrospective descriptive screens with explicit caveats; station coordinates are not supplied. |
| Evidence engine and removal recomputation | PASS | Removing FIRMS changed the biomass hypothesis to insufficient evidence and added missing-data guidance. The case is synthetic. |
| Forecast results and interval caveat | PASS | Results checked against saved metrics; nominal 90% coverage is 71.5% / 74.6%, so intervals are marked exploratory and under-covering. |
| Website navigation and responsive behavior | PASS | Website includes hash-linked section navigation and responsive CSS; browser review also confirmed the Gradio app's tab navigation at a narrow viewport. |
| Team members | PASS | Shylan Kamesh S, Sai Santhosh T, Derin Godson. |
| Team name | PASS | Confirmed by the team: Fresh_coderz. |
| Public GitHub source | PASS | Repository default branch `main` contains the integrated submission. |
| Pull request to `main` | PASS | [PR #1](https://github.com/shylankamesh/airsource-x/pull/1) was merged on 4 November 2026. |
| GitHub Pages / public demo | PASS | Latest deployment run 41814656372 succeeded. The public site opens at `https://shylankamesh.github.io/airsource-x/`; report links resolve under the project path and the Gradio setup link points to `main`. |
| Committed UI screenshots | PASS | Genuine capture of the public static demo homepage is in `assets/screenshots/airsource-x-homepage.jpg` and embedded in README. |
| Clean-clone reproducibility | PASS | Fresh public clone of the branch: 32 passed, 0 failed, 0 skipped using the supplied dependency environment. |
| Hackathon format and deadline requirements | NOT VERIFIED | Confirm submission form/format and team registration details. |
| License choice | NOT VERIFIED | No project license selected; third-party dataset terms are documented. |

## Submission scope

This is a one-station retrospective forecast experiment plus a separate 2018–2019 six-station historical context view. Forecast issue-time data availability has not been audited. Synthetic evidence scenarios test policy behavior only; they do not establish source-attribution accuracy. The model's test results do not establish all-Delhi or live performance.

## Before submitting

1. Confirm the team name is spelled **Fresh_coderz** in the hackathon registration.
2. Genuine homepage screenshot is committed and embedded; live report links were verified after deployment.
3. Confirm the hackathon form, data terms, and any requested AI disclosure format.
4. Complete the team registration check, then submit the project through the hackathon portal before its deadline.

