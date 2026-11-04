import hashlib
import json
from pathlib import Path

import pytest

from airsource.model_registry import inspect_model_registry, load_verified_model


def _write_registry(tmp_path: Path, payload: bytes = b"model"):
    artifact = tmp_path / "model.bin"
    artifact.write_bytes(payload)
    manifest = {
        "runtime_versions": {},
        "dataset_sha256": "dataset-hash",
        "artifacts": [{
            "file": "model.bin",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "station": "A",
            "horizon": "0-24h",
            "model": "test",
        }],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


def test_registry_verifies_artifact_checksum(tmp_path):
    _write_registry(tmp_path)
    report = inspect_model_registry(tmp_path, dataset_sha256="dataset-hash")
    assert report["artifacts"][0]["status"] == "verified"
    assert report["status"] in {"verified", "warning"}


def test_registry_detects_artifact_tampering(tmp_path):
    _write_registry(tmp_path)
    (tmp_path / "model.bin").write_bytes(b"tampered")
    report = inspect_model_registry(tmp_path)
    assert report["status"] == "invalid"
    assert "checksum mismatch" in report["errors"][0]


def test_registry_detects_dataset_mismatch(tmp_path):
    _write_registry(tmp_path)
    report = inspect_model_registry(tmp_path, dataset_sha256="different")
    assert report["status"] == "invalid"


def test_loader_rejects_unsafe_path(tmp_path):
    _write_registry(tmp_path)
    with pytest.raises(ValueError):
        load_verified_model(tmp_path, filename="../model.bin", expected_sha256="x")
