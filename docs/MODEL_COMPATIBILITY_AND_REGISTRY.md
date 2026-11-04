# Model artifact integrity and runtime compatibility

AirSource-X now provides a read-only model registry audit in `airsource/model_registry.py`.

## What it checks
- Manifest readability and required artifact records.
- Artifact path safety (artifacts must be direct children of the model directory).
- SHA-256 integrity for every artifact.
- Optional dataset checksum agreement.
- Recorded training runtime versus the current Python, pandas, scikit-learn and joblib versions.

## Loading policy
`load_verified_model` verifies the artifact checksum before deserialisation. It captures scikit-learn `InconsistentVersionWarning` messages and refuses to return a model by default when a version mismatch is detected. The application should show the compatibility issue rather than silently treating the artifact as production-ready.

## Important limitations
- A matching checksum proves file integrity, not that the model is scientifically valid.
- Matching package versions do not prove forecast quality.
- The current historical artifacts are research artifacts trained on 2018–2019 data. They are not current operational warning models.
- Do not set `allow_version_mismatch=True` for production use without a documented compatibility test.

## Operator workflow
1. Run the application and open Data & Methods.
2. Review model artifact integrity and runtime compatibility.
3. If a version mismatch is reported, reproduce the original training environment or retrain and re-evaluate the model in the target environment.
4. Record new model hashes, training cutoff, feature schema and evaluation report in a new release manifest.
