# AirSource X — final submission checklist

## Verification status

| Requirement | Status | Evidence / remaining action |
|---|---|---|
| Latest integration kept on the submission branch | PASS | `codex/airsourcex-submission-ready-20261104`; `main` remains unchanged. |
| Automated tests | PASS | 32 passed, 0 failed, 0 skipped with the supplied dependency environment and workspace temp directory. |
| App startup and forecast results | PASS | Gradio app started on localhost; dashboard showed held-out result rows for both horizons. |
| Six-station provenance, exact-time overlap, coverage, and comparative trends | PASS | Six labeled stations; 11,704 common all-station hours and 11,704 hours with at least four reporting; dataset hash checked by automated test. |
| Same-hour anomaly and coincident elevation screens | PASS | Displayed as retrospective descriptive screens with explicit caveats; station coordinates are not supplied. |
| Evidence engine and removal recomputation | PASS | Removing FIRMS changed the biomass hypothesis to insufficient evidence and added missing-data guidance. The case is synthetic. |
| Forecast results and interval caveat | PASS | Results checked against saved metrics; nominal 90% coverage is 71.5% / 74.6%, so intervals are marked exploratory and under-covering. |
| Website navigation and responsive behavior | PASS | Website includes hash-linked section navigation and responsive CSS; browser review also confirmed the Gradio app's tab navigation at a narrow viewport. |
| Team members | PASS | Shylan Kamesh S, Sai Santhosh T, Derin Godson. |
| Team name | NOT VERIFIED | `[ADD TEAM NAME]` remains for the team to fill in. |
| Public GitHub source branch | PASS | Submission branch is public; see PR link in the delivery report. `main` is not changed. |
| Pull request to `main` | NOT VERIFIED | Create after the final verified commit; leave open and do not merge. |
| GitHub Pages / public demo | NOT VERIFIED | No deployment claim until the public URL responds and is usable. |
| Committed UI screenshots | NOT VERIFIED | Genuine screenshot files still need to be added under `assets/screenshots/` and embedded in README. |
| Clean-clone reproducibility | NOT VERIFIED | Must rerun after the final commit is pushed. |
| Hackathon format and deadline requirements | NOT VERIFIED | Confirm submission form/format and team registration details. |
| License choice | NOT VERIFIED | No project license selected; third-party dataset terms are documented. |

## Submission scope

This is a one-station retrospective forecast experiment plus a separate 2018–2019 six-station historical context view. Forecast issue-time data availability has not been audited. Synthetic evidence scenarios test policy behavior only; they do not establish source-attribution accuracy. The model's test results do not establish all-Delhi or live performance.

## Before submitting

1. Add the actual team name.
2. Add verified screenshots and link a public demo only after deployment and live verification.
3. Confirm the hackathon form, data terms, and any requested AI disclosure format.
4. Review the open PR and submit it to the hackathon; do not merge without authorization.
