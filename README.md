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
| Serverless inference endpoint | Deployed, `InService` |
| S3-triggered retraining (CI/CD) | Proof-of-concept, proven end-to-end |
| Streamlit client | Built; **note: still using placeholder prediction logic** pending endpoint integration |

---

## Features

- Detects cryptocurrency scam messages from raw text
- TF-IDF text vectorisation plus 18 engineered indicator features
- Risk level assessment (Low / Medium / High) with a scam probability score
- Suspicious keyword and pattern detection for user-facing explanation
- Responsible AI guidance and referral to official reporting channels
- Interactive Streamlit interface

---

## Architecture

Training and retraining run on AWS; the Streamlit client calls a serverless endpoint for inference.

```
Kaggle dataset
      │  SHA256 hash + version pointer (_latest.json)
      ▼
S3 raw/  ──►  SageMaker Pipeline
                 │
                 ├─ PreprocessData   clean text, 18 engineered features,
                 │                   TF-IDF fitted on the training split only
                 ├─ TrainModel       Random Forest; metrics captured by SageMaker
                 ├─ AUCQualityGate   registration only if test AUC-ROC >= 0.85
                 └─ RegisterModel    SageMaker Model Registry
                                     (PendingManualApproval — human approval required)
                                            │
                                            ▼
                              SageMaker Serverless Endpoint
                                            │
      Streamlit client  ──► {"text": "..."} ──► {"prediction", "label", "probability"}
```

Experiment runs are tracked in the team's SageMaker MLflow App. New CSV files landing in a
watched S3 prefix trigger a retraining run of the same pipeline.

---

## Project Structure

```
CryptoScam-AI/
│
├── app.py                    Streamlit entry point
├── requirements.txt
├── README.md
│
├── data/
│   ├── crypto_scam_dataset.csv
│   └── processed/            empty by design — processed artifacts live in S3
│
├── models/                   empty by design — model artifacts are held in the
│                             SageMaker Model Registry and S3, not committed to git
│
├── notebooks/
│   ├── 01_eda_and_data_preparation_team03.ipynb
│   ├── 01A_setup_sagemaker_mlflow_app_team03.ipynb
│   ├── 02_baseline_experiments_sagemaker_mlflow_app_with_team03.ipynb
│   ├── 03_sagemaker_pipeline_mlflow_app_with_preprocessing_bundle_team03.ipynb
│   ├── 04_test_serverless_endpoint_team03.ipynb
│   └── 05_s3_trigger_cicd_team03.ipynb
│
├── pages/
│   ├── 1_Scam_Detector.py
│   ├── 2_About_the_Model.py
│   └── 3_Responsible_AI.py
│
├── utils/
│   └── indicators.py         keyword/pattern detection used by the Streamlit app
│
├── assets/screenshots/       MLflow, Model Registry, pipeline and endpoint evidence
│
└── docs/
    └── iti113_project proposal_team03.pdf
```

`models/` and `data/processed/` are intentionally empty. Versioned datasets, the fitted
TF-IDF vectoriser and trained model artifacts are stored in S3 and the SageMaker Model
Registry rather than in version control, so that lineage is tracked by the platform.

---

## Notebooks

| Notebook | Purpose |
|---|---|
| **01** | EDA, data quality checks, and the data pipeline: SHA256 raw-data versioning with an `_latest.json` pointer, text cleaning, 18 engineered indicator features, stratified 80/20 split, and TF-IDF fitted on the training split only. Outputs are written to S3. |
| **01A** | Creates or reuses the team's SageMaker MLflow App with the tags that drive team-level IAM access control, and verifies logging end to end. |
| **02** | Baseline experiments: Logistic Regression and Random Forest, plus a five-candidate hyperparameter sweep, all logged to the team MLflow experiment. |
| **03** | SageMaker Pipeline (Preprocess → Train → AUC quality gate → Register), post-run MLflow logging, model approval, and serverless endpoint deployment. |
| **04** | Endpoint verification: confirms `InService`, traces the endpoint back to its Model Registry package, and tests single and batch invocation. |
| **05** | S3-triggered retraining: a watched S3 prefix starts the same pipeline automatically when new data arrives. |

---

## Installation

Clone the repository:

```bash
git clone https://github.com/evaonghuilin-hub/CryptoScam-AI.git
```

Install the required packages:

```bash
pip install -r requirements.txt
```

The notebooks additionally require AWS credentials with access to the team's SageMaker
resources, and are intended to be run in SageMaker Studio.

---

## Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`.

**Note:** the Scam Detector page currently returns placeholder probabilities derived from
keyword counts. Connecting it to the deployed endpoint is outstanding work; the exact call
to use is `invoke_scam_detector()` in Notebook 04.

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

- **Deployment** — approved models are deployed to a SageMaker Serverless Endpoint that
  accepts raw message text and returns a label and probability. Preprocessing is bundled
  with the model, so the endpoint applies the same TF-IDF vocabulary learned during training.

- **Retraining trigger** — CSV files placed in a watched S3 prefix start the pipeline
  automatically with that file as input. The trigger is a polling loop rather than a
  production EventBridge/Lambda chain (see Known Limitations).

---

## Models Evaluated

Logistic Regression and Random Forest were trained and compared, followed by a
five-candidate Random Forest hyperparameter sweep. The best configuration
(`n_estimators=200, max_depth=8, min_samples_leaf=2`) is the one used by the SageMaker
Pipeline. Naive Bayes, SVM and neural networks were considered in the project proposal but
have not been evaluated at this stage.

---

## Known Limitations (as of 14 Aug)

- **The dataset appears to be synthetically generated.** Models score near-perfect AUC.
  The code was audited for leakage and none was found; n-gram analysis shows repeated
  template fragments, which makes the classes close to linearly separable. Results should
  not be taken as evidence of real-world performance without validation on genuine data.
- **The Streamlit client is not yet wired to the endpoint** and returns placeholder values.
- **The retraining trigger is a proof-of-concept.** It polls from a notebook, so it only
  runs while that notebook is running, and its state is stored locally.
- **A failed quality gate is currently silent** — the pipeline completes without
  registering a model rather than reporting a failure.

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
