"""
Experiment tracking helper for CryptoShield AI.

Wraps MLflow so every model attempt (parameters, metrics, and the trained
model itself) gets logged the same way with a couple of function calls,
instead of results living only in scrolled-past notebook output. Think of
this as the shared lab notebook: every experiment gets written down
consistently, so any run can be compared or reproduced later.

Tracking now points at team03's SageMaker MLflow App (set up via
notebooks/01A_setup_sagemaker_mlflow_app_team03.ipynb, adapted from the
ITI113 course template). The tracking URI is the MLflow App's ARN and the
experiment name follows the course convention (ITI113/<team_id>/Experiment1)
exactly, as printed by notebook 01A's "Output values to copy into future
notebooks" cell. If the App is ever recreated and gets a new ARN, only
MLFLOW_APP_ARN below needs updating -- nothing in the logging calls does.

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

To view the results, run print_ui_command() and open the printed presigned
URL in a browser -- SageMaker MLflow App UI links expire, so a fresh one
must be generated each time (there is no fixed http://localhost URL anymore).
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import mlflow
import mlflow.sklearn

ROOT_DIR = Path(__file__).resolve().parent.parent
TRACKING_DIR = ROOT_DIR / "mlruns"  # no longer used for tracking; kept only as a historical fallback

# team03's SageMaker MLflow App (see notebooks/01A_setup_sagemaker_mlflow_app_team03.ipynb).
# Tracking URI + experiment naming follow the ITI113 course template exactly.
TEAM_ID = "team03"
MLFLOW_APP_ARN = "arn:aws:sagemaker:ap-southeast-1:044528205969:mlflow-app/app-J5AYUG4AJHVW"
EXPERIMENT_NAME = f"ITI113/{TEAM_ID}/Experiment1"


def start_experiment(experiment_name: str = EXPERIMENT_NAME) -> None:
    """Point MLflow at team03's SageMaker MLflow App and select the experiment.

    Call this once at the top of a training notebook, before any runs.
    """
    mlflow.set_tracking_uri(MLFLOW_APP_ARN)
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


def print_ui_command() -> None:
    """Print a reminder of how to open the experiment tracking dashboard.

    Unlike the old local setup, the SageMaker MLflow App UI needs a fresh
    presigned URL each time (they expire) -- generate one by re-running the
    "Get a presigned MLflow UI URL" cell in notebooks/01A_setup_sagemaker_mlflow_app_team03.ipynb.
    """
    print(
        "The SageMaker MLflow App UI needs a fresh presigned URL each time "
        "(they expire). Re-run the 'Get a presigned MLflow UI URL' cell in "
        "notebooks/01A_setup_sagemaker_mlflow_app_team03.ipynb to get one, "
        f"then open it in a browser.\n"
        f"    MLflow App ARN:  {MLFLOW_APP_ARN}\n"
        f"    Experiment name: {EXPERIMENT_NAME}"
    )
