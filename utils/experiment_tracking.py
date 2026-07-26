"""
Experiment tracking helper for CryptoShield AI.

Wraps MLflow so every model attempt (parameters, metrics, and the trained
model itself) gets logged the same way with a couple of function calls,
instead of results living only in scrolled-past notebook output. Think of
this as the shared lab notebook: every experiment gets written down
consistently, so any run can be compared or reproduced later.

MLflow is used because it runs locally out of the box (no AWS setup
required to get started) and is a widely-used, portable choice. If the
team later wants to point tracking at a remote server (including one
hosted alongside SageMaker), only the tracking URI in start_experiment()
needs to change -- nothing in the logging calls below has to change.

Usage in a notebook:

    from utils.experiment_tracking import start_experiment, log_run

    start_experiment()

    with log_run(
        run_name="logreg_baseline",
        params={"model": "LogisticRegression", "max_features": 5000},
    ) as run:
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        run.log_metrics({
            "accuracy": accuracy_score(y_test, preds),
            "recall": recall_score(y_test, preds, pos_label="scam"),
            "precision": precision_score(y_test, preds, pos_label="scam"),
            "f1": f1_score(y_test, preds, pos_label="scam"),
        })
        run.log_model(model, artifact_path="model")

To view the results, run this from the project root in a terminal:

    mlflow ui --backend-store-uri file:./mlruns --port 5000

then open http://localhost:5000
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import mlflow
import mlflow.sklearn

ROOT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = ROOT_DIR / "mlruns"


def start_experiment(experiment_name: str = "crypto-scam-detector") -> None:
    """Point MLflow at the local tracking store and select the experiment.

    Call this once at the top of a training notebook, before any runs.
    """
    mlflow.set_tracking_uri(f"file:{TRACKING_DIR}")
    mlflow.set_experiment(experiment_name)


class _RunHandle:
    """Small convenience wrapper around the currently active MLflow run."""

    def log_metrics(self, metrics: dict) -> None:
        mlflow.log_metrics(metrics)

    def log_model(self, model, artifact_path: str = "model") -> None:
        mlflow.sklearn.log_model(model, artifact_path)

    def log_artifact(self, path: str) -> None:
        mlflow.log_artifact(path)


@contextmanager
def log_run(run_name: str, params: dict | None = None):
    """Context manager that starts an MLflow run and logs params up front.

    Yields a _RunHandle so metrics/model/artifacts can be logged inside
    the `with` block once results are available.
    """
    with mlflow.start_run(run_name=run_name):
        if params:
            mlflow.log_params(params)
        yield _RunHandle()


def print_ui_command(port: int = 5000) -> None:
    """Print the terminal command to open the experiment dashboard."""
    print(
        "Run this in a terminal from the project root to open the "
        "experiment tracking dashboard:\n"
        f"    mlflow ui --backend-store-uri file:{TRACKING_DIR} --port {port}"
    )
