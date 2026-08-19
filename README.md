# CryptoScam-AI

ITI113 ML Project

CryptoShield AI is a machine learning application that detects potentially fraudulent cryptocurrency-related messages using classical machine learning techniques.

This project was developed as part of the **Nanyang Polytechnic Specialist Diploma in Applied AI (ITI113)**.

---

## Current Status

| Component | Status |
|---|---|
| EDA and data quality checks | Complete |
| Data pipeline (versioning, cleaning, feature engineering, TF-IDF, split) | Complete |
| Experiment tracking (SageMaker MLflow App) | Complete |
| Baseline models (Logistic Regression, Random Forest) and tuning sweep | Complete |
| SageMaker Pipeline with quality gate and Model Registry | Complete |
| Serverless inference endpoint | Deployed, `InService`, returning predictions with per-prediction explanations |
| S3-triggered retraining (CI/CD) | Proof-of-concept, proven end-to-end |
| Streamlit client | Built and wired to the deployed endpoint via a FastAPI + ngrok relay (Notebook 06) |

---

## Features

- Detects cryptocurrency scam messages from raw text
- TF-IDF text vectorisation plus 15 engineered indicator features
- Risk level assessment (Low / Medium / High) with a scam probability score
- Suspicious keyword and pattern detection for user-facing explanation
- Per-prediction explainability: the endpoint returns the features that contributed
  most to each score (feature value x model coefficient), shown in plain English in the app
- User feedback links for reporting incorrect predictions
- Responsible AI guidance and referral to official reporting channels
- Interactive Streamlit interface

---

## Architecture

Training and retraining run on AWS; the Streamlit client calls a serverless endpoint for
inference through a temporary FastAPI + ngrok relay, so the app never holds AWS credentials.

```
Kaggle dataset
      │  SHA256 hash + version pointer (_latest.json)
      ▼
S3 raw/  ──►  SageMaker Pipeline
                 │
                 ├─ PreprocessData   clean text, 15 engineered features,
                 │                   TF-IDF fitted on the training split only
                 ├─ TrainModel       Logistic Regression (C=10.0, L2, lbfgs);
                 │                   metrics captured by SageMaker
                 ├─ AUCQualityGate   registration only if test AUC-ROC >= 0.85
                 └─ RegisterModel    SageMaker Model Registry
                                     (PendingManualApproval — human approval required)
                                            │
                                            ▼
                       SageMaker Serverless Endpoint
                                            │
                                            ▼
                FastAPI relay (SageMaker Studio, Notebook 06)
                                POST /predict
                                            │  ngrok HTTPS tunnel
                                            ▼
       Streamlit client ──► {"text": "..."} ──► {"prediction", "label", "probability"}
```

The relay runs inside SageMaker Studio and calls the endpoint using the SageMaker
execution role; the Streamlit app only ever holds the relay's public ngrok URL and a shared
API key, never AWS credentials. Experiment runs are tracked in the team's SageMaker MLflow App.
New CSV files landing in a watched S3 prefix trigger a retraining run of the same pipeline.

---

## Project Structure

```
CryptoScam-AI/
│
├── app.py                    Streamlit entry point
├── requirements.txt           Streamlit app dependencies
├── requirements-notebooks.txt Notebook / SageMaker / MLflow dependencies
├── README.md
│
├── data/
│   └── processed/            empty by design — raw and processed data are versioned
│                             in S3 (Notebook 01 re-downloads from Kaggle each run)
│
├── models/                   empty by design — model artifacts are held in the
│                             SageMaker Model Registry and S3, not committed to git
│
├── notebooks/
│   ├── 01_eda_and_data_preparation_team03.ipynb
│   ├── 01A_setup_sagemaker_mlflow_app_team03.ipynb
│   ├── 02_baseline_experiments_sagemaker_mlflow_app_with_team03.ipynb
│   ├── 03_sagemaker_pipeline_mlflow_app_with_preprocessing_bundle_team03.ipynb
│   ├── 05_s3_trigger_cicd_team03.ipynb
│   ├── 06_fastapi_ngrok_relay_team03.ipynb
│   └── best_model.json, mlflow_app_config_team03_s301.json,
│       sagemaker_pipeline_run_summary.json   state saved between notebook runs
│
├── pages/
│   ├── 1_Scam_Detector.py
│   ├── 2_About_the_Model.py
│   └── 3_Responsible_AI.py
│
├── utils/
│   └── indicators.py         keyword/pattern detection used by the Streamlit app
│
├── assets/
│   ├── screenshots/           MLflow, Model Registry, pipeline and endpoint evidence
│   └── system architecture diagram/   editable Word diagram of the full pipeline
│
└── docs/
    └── iti113_project proposal_team03.pdf
```

`models/` and `data/processed/` are intentionally empty. Versioned datasets, the fitted
TF-IDF vectoriser and trained model artifacts are stored in S3 and the SageMaker Model
Registry rather than in version control, so that lineage is tracked by the platform.

**Note:** `preprocess.py`, `train.py` and `inference.py` are not committed to this repo as
standalone files — they are written by the notebooks (`%%writefile`) into a local
`pipeline_src/` folder during a SageMaker Studio session, then uploaded to the S3 prefix
`pipeline_src/` that both pipelines re-download from. The notebooks are the source of truth
for this code.

---

## Notebooks

| Notebook | Purpose |
|---|---|
| **01** | EDA, data quality checks, and the data pipeline: SHA256 raw-data versioning with an `_latest.json` pointer, text cleaning, 15 engineered indicator features, stratified 80/20 split, and TF-IDF fitted on the training split only. Outputs are written to S3. |
| **01A** | Creates or reuses the team's SageMaker MLflow App with the tags that drive team-level IAM access control, and verifies logging end to end. |
| **02** | Baseline experiments: Logistic Regression and Random Forest, plus a hyperparameter sweep (6 Logistic Regression + 5 Random Forest candidates), all logged to the team MLflow experiment. |
| **03** | SageMaker Pipeline (Preprocess → Train → AUC quality gate → Register), post-run MLflow logging, model approval, and serverless endpoint deployment (Sections 1–5); endpoint verification — `InService` check, Model Registry traceability, single and batch invocation (Section 6). |
| **05** | S3-triggered retraining: a watched S3 prefix starts the same pipeline automatically when new data arrives. |
| **06** | FastAPI + ngrok relay: exposes the deployed endpoint to the Streamlit app over HTTPS without sharing AWS credentials, using the same request/response shape validated in Notebook 03 Section 6. |

Notebook 04 (endpoint verification) has been folded into Notebook 03 (Section 6) — it was a direct continuation of the deployment done there, not a distinct MLOps stage.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/evaonghuilin-hub/CryptoScam-AI.git
```

Install the packages needed to run the Streamlit app:

```bash
pip install -r requirements.txt
```

If you also want to open and read the notebooks locally (e.g. to review the data
pipeline, training or pipeline-orchestration code), install the notebook stack too:

```bash
pip install -r requirements-notebooks.txt
```

Note that installing `requirements-notebooks.txt` lets you read and lint the notebooks,
but does not make them runnable end-to-end on a plain local machine — Notebooks 01, 01A,
02, 03 and 05 call `sagemaker.get_execution_role()`, which only resolves inside a
SageMaker Studio environment with an attached execution role, and require AWS credentials
with access to the team's SageMaker resources. They are intended to be run in SageMaker
Studio, where they additionally self-install a few packages in their own setup cells.

---

## Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`.

**Before analysing a message**, run Notebook 06 in SageMaker Studio to start the FastAPI
relay and ngrok tunnel, then paste the printed `/predict` URL and the relay API key into
the Scam Detector page's sidebar. Free ngrok URLs change each time the tunnel restarts, so
this needs to be redone whenever Notebook 06 is re-run (e.g. before a demo or presentation).

---

## MLOps Components

- **Data pipeline** — the raw dataset is hashed with SHA256 and stored under a version
  number, with a `_latest.json` pointer recording the current version. Re-running the
  pipeline on unchanged data reuses the existing version rather than creating a duplicate,
  and previous versions are retained so any past result can be traced to the exact bytes
  that produced it. Processed splits and the fitted TF-IDF vectoriser are written to S3 and
  reused by every downstream model.

- **Experiment tracking** — all runs are logged to the team's SageMaker MLflow App
  (experiment `ITI113/team03/Experiment1`), tagged with team and student identifiers so
  individual contributions can be attributed. Access is governed by AWS tag-based IAM and
  short-lived presigned URLs rather than shared credentials.

- **Model registry and quality gate** — models are registered to the
  `team03-CryptoScamDetector` package group only if test AUC-ROC meets the 0.85 threshold
  set in the project proposal. Registered models are held at `PendingManualApproval`, so a
  team member must approve a model before it can be deployed.

- **Deployment** — the approved model is deployed to a SageMaker Serverless Endpoint that
  accepts raw message text and returns a label and probability. Preprocessing is bundled
  with the model, so the endpoint applies the same TF-IDF vocabulary learned during training.
  A FastAPI relay (Notebook 06), exposed over ngrok, sits between the endpoint and the
  Streamlit client so the client never needs AWS credentials — this mirrors the FastAPI +
  ngrok pattern taught for external endpoint access.

- **Retraining trigger** — CSV files placed in a watched S3 prefix start the pipeline
  automatically with that file as input. The trigger is a notebook-driven check rather
  than a production EventBridge/Lambda chain (see Known Limitations).

---

## Models Evaluated

Logistic Regression and Random Forest were trained and compared as baselines, followed by
a hyperparameter sweep of 6 Logistic Regression candidates (regularisation strength and
penalty type) and 5 Random Forest candidates (tree count, depth, leaf size). The best
Logistic Regression candidate (`C=10.0`, `penalty=l2`, `solver=lbfgs`) reached test
ROC-AUC 0.8908 versus the best Random Forest candidate's 0.86, and is the configuration
used by the SageMaker Pipeline. Naive Bayes, SVM and neural networks were considered in
the project proposal but have not been evaluated at this stage.

---

## Known Limitations (as of 19 Aug)

- **The dataset appears to be synthetically generated.** Models score consistently high
  AUC (0.8446–0.8908 across all four baseline/tuned runs). The code was audited for
  leakage and none was found; n-gram analysis shows repeated template fragments, which
  makes the classes close to linearly separable. Results should not be taken as evidence
  of real-world performance without validation on genuine data.
- **The FastAPI + ngrok relay is a temporary demo mechanism**, not a production deployment
  path. It must be running (in SageMaker Studio) for the Streamlit app to get live
  predictions, and the free ngrok URL changes every time the relay is restarted.
- **The retraining trigger is a proof-of-concept.** The watch folder is checked from a
  notebook cell rather than by an event-driven service, so a new file is picked up only
  when that check is run, and the seen-file state is stored locally.

---

## Responsible AI

CryptoShield AI is intended as a **decision-support tool**.

Users should note that:

- Predictions may contain false positives.
- Predictions may contain false negatives.
- Scam tactics evolve over time.
- The application does not replace human judgement.
- Users should verify suspicious messages through official channels before making financial decisions.

---

## Future Improvements

- Validation against real-world scam data
- Production-grade external access (API Gateway + Lambda) in place of the temporary
  FastAPI + ngrok relay
- Event-driven retraining trigger (EventBridge and Lambda)
- Production monitoring for model drift and platform-level recall
- Multi-language scam detection
- Screenshot OCR support
- LLM-assisted scam explanation

---

## Authors

Developed by:

- Royston Quek — Model Development and EDA
- Ong Hui Lin — MLOps, Deployment and AI Governance

Specialist Diploma in Applied AI

Nanyang Polytechnic

Aug 2026

---

## Disclaimer

This application is developed for educational purposes.

It is not affiliated with ScamShield, the Singapore Police Force, the Monetary Authority of Singapore (MAS), or any cryptocurrency exchange.

The predictions generated by the application should not be regarded as financial, legal, or cybersecurity advice.
