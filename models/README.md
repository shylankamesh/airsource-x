# AirSource X model artifacts

The `.joblib` files are validation-selected PM₂.₅ forecast regressors, refit separately for each station and horizon on the bundled historical Delhi dataset. `manifest.json` records data and artifact SHA-256 digests, selected algorithms, training cutoff, and per-file holdout MAE.

These are research artifacts, not live or independently validated warning models. They inherit the source dataset's CC BY 4.0 attribution and historical coverage limitations. Load only trusted files; joblib uses Python pickle serialization. Use compatible Python, scikit-learn, and LightGBM package versions (see `requirements.txt`).

Recreate them with `python scripts/train_model_artifacts.py`. They are not required to run the Streamlit app, which trains on the active station dataset.
