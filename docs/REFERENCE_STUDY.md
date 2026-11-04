# Public project study

This short study informs product and engineering choices. It is not a claim that AirSource X copied any project code. Referenced projects retain their own code and licenses.

## Project CoolCity — AI for Change Hackathon

- **Repository:** [thabir303/AI-for-Change-Hackathon](https://github.com/thabir303/AI-for-Change-Hackathon)
- **Award:** Its [Devpost submission](https://devpost.com/software/project-coolcity) lists two winner awards in the AI for Change Hackathon.
- **Repository structure reviewed:** root README, `client/`, `server/`, and `docker-compose.yml`.
- **Product pattern:** interactive map and selected-location context connect environmental APIs to a user-facing recommendation workflow.
- **What AirSource X adopts:** a map/station-first experience, visible context for the selected place, a clear flow from data to investigation, and a documented runnable path.
- **What AirSource X changes:** no general-purpose chatbot is allowed to invent environmental conclusions. Each evidence card carries its inputs, contradictions, and limitations. The feature is disabled when the required observations are absent.

## CleanCast — AIR PPM Hackathon 2025

- **Official result:** [AIR PPM winner announcement](https://www.airppm.org/for-participants/results) identifies CleanCast as the top-performing team.
- **Reported approach:** the organizers highlight meteorological and environmental inputs, multi-climate-zone forecasting, scalability, and interpretability.
- **Design implication:** AirSource X treats temporal holdout evaluation, baseline comparison, multiple environmental variables, and clear model disclosure as first-class product features.
- **Public code limitation:** the winner announcement did not link an official CleanCast source repository, so its implementation was not inspected or copied.

## AIR PPM submission contract

- **Reference template:** [AIRPPM/submission_example](https://github.com/AIRPPM/submission_example)
- **Official challenge specification:** [AIR PPM challenge description](https://www.airppm.org/for-participants/challenge-description)
- **Useful engineering pattern:** a small, deterministic input/output contract and reproducible container build make automated evaluation easier. AirSource X uses this as a documentation lesson; its dashboard is not the AIR PPM competition submission.

## Findings applied here

1. Make the first useful interaction obvious: fetch a public context or load a local file.
2. Present maps and local context as navigational aids, not proof of causality.
3. Place model metrics and simple baselines beside the forecast rather than hiding them in documentation.
4. Keep provenance, missing evidence, and limitation notes adjacent to the conclusion.
5. Keep implementation auditable and avoid bundling unlicensed datasets or copying another team's code.
