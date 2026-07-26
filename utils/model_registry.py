"""
Model registry helpers for CryptoShield AI.

Saves a trained model with a version number and its metrics side by side,
following the convention documented in models/MODEL_REGISTRY.md. This is
the "labelled archive" step -- what lets the team roll back to a previous
model if a newer one underperforms, as promised in the AI Risk Assessment
(Model Performance Risk mitigation).

Usage in a notebook, after training and evaluating a model:

    from utils.model_registry import save_model_version, promote_to_best

    saved = save_model_version(
        model,
        metrics={
            "accuracy": 0.91, "precision": 0.83,
            "recall": 0.88, "f1": 0.855, "roc_auc": 0.93,
        },
        notes="Logistic Regression baseline with TF-IDF (1,2-gram) features",
    )

    # Once reviewed and it meets the proposal's success thresholds:
    promote_to_best(saved["version"])
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import joblib

ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"


def next_version_number() -> int:
    """Find the next free model version number based on existing files."""
    existing = sorted(MODELS_DIR.glob("model_v*.joblib"))
    versions = []
    for path in existing:
        try:
            versions.append(int(path.stem.split("_v")[-1]))
        except ValueError:
            continue
    return max(versions, default=0) + 1


def save_model_version(model, metrics: dict, notes: str = "") -> dict:
    """Save a trained model + its metrics as the next version in the registry."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    version = next_version_number()

    model_path = MODELS_DIR / f"model_v{version}.joblib"
    metrics_path = MODELS_DIR / f"model_v{version}_metrics.json"

    joblib.dump(model, model_path)
    metrics_path.write_text(json.dumps({**metrics, "notes": notes}, indent=2))

    print(f"Saved model version {version} -> {model_path.name}")
    print(
        "Reminder: add a row for this version to models/MODEL_REGISTRY.md "
        "so the registry log stays up to date."
    )
    return {"version": version, "model_path": model_path, "metrics_path": metrics_path}


def promote_to_best(version: int) -> Path:
    """Copy a specific version to best_model.joblib (the file the app loads)."""
    source = MODELS_DIR / f"model_v{version}.joblib"
    if not source.exists():
        raise FileNotFoundError(f"No saved model found for version {version}: {source}")

    destination = MODELS_DIR / "best_model.joblib"
    shutil.copy(source, destination)
    print(f"Promoted model_v{version}.joblib -> best_model.joblib")
    return destination


def rollback_to(version: int) -> Path:
    """Alias for promote_to_best -- used when reverting a bad deployment."""
    return promote_to_best(version)
