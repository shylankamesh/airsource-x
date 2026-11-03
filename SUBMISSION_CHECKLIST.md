# AirSource X — final submission checklist

## Completed in this package
- Delhi ITO retrospective experiment, trained forecast models, saved predictions, evaluation tables, and data audit.
- Gradio app defaults to the Delhi experiment; synthetic policy fixtures are identified as synthetic.
- Static presentation site and judge walkthrough are included.
- README and submission brief contain the verified public repository URL.
- Automated test suite passed: 22 passed. Existing pandas deprecation warnings were reported.

## Team must fill in before submitting
- Replace team name and member-name placeholders with the actual names.
- Confirm hackathon deadline and required submission format.
- Add a hosted demo URL only if one is successfully published.
- Confirm which AI tools the team used and retain the required disclosure.
- Select a project license if the team intends to invite reuse.

## Demo publication
The Pages workflow is included, but GitHub Pages is not enabled for the repository. Enable it in **Repository Settings → Pages → Build and deployment → Source: GitHub Actions**, then run the **Publish AirSource X demo** workflow. The workflow alone cannot enable Pages without a separate repository-scoped credential. Until the deployment succeeds, use the included static site locally and do not claim a live URL.

## Scientific scope to disclose
This is a retrospective benchmark for one CPCB ITO station. Publication-time availability is unverified; interval coverage is below its nominal 90%; results do not establish multi-station performance, live forecasting, physical source attribution, or measured source contributions. The evidence-policy cases are synthetic software checks.
