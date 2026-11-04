"""Reproducible model artifact inspection and guarded loading."""
from __future__ import annotations

import hashlib
import json
import platform
import warnings
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import sklearn
from sklearn.exceptions import InconsistentVersionWarning


def runtime_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
    }


def inspect_model_registry(model_dir: str | Path, *, dataset_sha256: str | None = None) -> dict[str, Any]:
    """Inspect manifests and artifact hashes without deserialising model files."""
    directory = Path(model_dir).resolve()
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file():
        return {"status": "invalid", "errors": ["manifest.json is missing"], "artifacts": []}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "invalid", "errors": [f"Manifest cannot be read: {exc}"], "artifacts": []}

    errors: list[str] = []
    warnings_list: list[str] = []
    expected_dataset = manifest.get("dataset_sha256")
    if dataset_sha256 and expected_dataset != dataset_sha256:
        errors.append("Dataset checksum does not match the model manifest.")

    trained_versions = manifest.get("runtime_versions", {})
    current_versions = runtime_versions()
    for key, current in current_versions.items():
        trained = trained_versions.get(key)
        if trained and trained != current:
            warnings_list.append(f"{key}: trained with {trained}, running with {current}")

    records = []
    seen_files: set[str] = set()
    for item in manifest.get("artifacts", []):
        name = str(item.get("file", ""))
        candidate = (directory / name).resolve()
        record_errors = []
        if not name or candidate.parent != directory or candidate.name != name:
            record_errors.append("Unsafe or invalid artifact path.")
        elif name in seen_files:
            record_errors.append("Duplicate artifact filename in manifest.")
        else:
            seen_files.add(name)
            if not candidate.is_file():
                record_errors.append("Artifact file is missing.")
            else:
                digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
                if digest != item.get("sha256"):
                    record_errors.append("Artifact checksum mismatch.")
        records.append({
            "file": name, "station": item.get("station"), "horizon": item.get("horizon"),
            "model": item.get("model"), "status": "invalid" if record_errors else "verified",
            "errors": record_errors,
        })
        errors.extend(f"{name}: {message}" for message in record_errors)

    if not records:
        errors.append("Manifest contains no model artifacts.")
    return {
        "status": "invalid" if errors else ("warning" if warnings_list else "verified"),
        "errors": errors, "warnings": warnings_list,
        "trained_runtime": trained_versions, "current_runtime": current_versions,
        "dataset_sha256": expected_dataset, "artifacts": records,
    }


def load_verified_model(model_dir: str | Path, *, filename: str, expected_sha256: str,
                        allow_version_mismatch: bool = False):
    """Load only a manifest-verified artifact; version warnings are not suppressed by default."""
    directory = Path(model_dir).resolve()
    candidate = (directory / filename).resolve()
    if candidate.parent != directory or candidate.name != filename or not candidate.is_file():
        raise ValueError("Model artifact path is missing or unsafe.")
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise ValueError("Model artifact checksum mismatch; refusing to load.")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", InconsistentVersionWarning)
        model = joblib.load(candidate)
    compatibility = [str(item.message) for item in caught
                     if issubclass(item.category, InconsistentVersionWarning)]
    if compatibility and not allow_version_mismatch:
        raise RuntimeError("Model was trained with a different scikit-learn version: " + "; ".join(compatibility))
    return model
