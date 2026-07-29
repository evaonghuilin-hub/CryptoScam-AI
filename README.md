# CryptoScam-AI
ITI113 ML Project

CryptoShield AI is a machine learning-powered web application that detects potentially fraudulent cryptocurrency-related messages using classical Machine Learning techniques.

This project was developed as part of the **Nanyang Polytechnic Specialist Diploma in Applied AI (ITI113)**.

---

## Features

- Detect cryptocurrency scam messages
- TF-IDF text vectorisation
- Machine Learning classification
- Risk level assessment (Low / Medium / High)
- Scam probability score
- Suspicious keyword detection
- Explainable AI indicators
- Responsible AI recommendations
- Interactive Streamlit dashboard

---

## Machine Learning Pipeline

```
User Input
      │
      ▼
Text Pre-processing
      │
      ▼
TF-IDF Vectorizer
      │
      ▼
Machine Learning Model
(Logistic Regression / Random Forest)
      │
      ▼
Prediction
      │
      ▼
Risk Assessment
      │
      ▼
Recommendation
```

---

## Project Structure

```
CryptoScam-AI/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── crypto_scam_dataset.csv
│   └── processed/
│       ├── train.csv
│       └── test.csv
│
├── models/
│   ├── tfidf_vectorizer.joblib
│   ├── model_v1.joblib
│   ├── model_v1_metrics.json
│   ├── best_model.joblib
│   └── MODEL_REGISTRY.md
│
├── notebooks/
│   ├── 01_eda_and_data_preparation.ipynb             (data prep + S3 upload done; EDA section is a placeholder for Royston)
│   ├── 01A_setup_sagemaker_mlflow_app_team03.ipynb   (adapted from the ITI113 course template)
│   └── 02_baseline_experiments.ipynb                 (renamed from 01_baseline_model.ipynb, numbering now matches the course template: 01/01A = EDA + MLflow setup, 02 = baseline experiments, 03 = pipeline + registry + deploy, still to come)
│
├── pages/
│   ├── 1_Scam_Detector.py
│   ├── 2_About_the_Model.py
│   └── 3_Responsible_AI.py
│
├── utils/
│   ├── indicators.py
│   ├── preprocessing.py
│   ├── experiment_tracking.py
│   └── model_registry.py
│
└── docs/
    └── iti113_project proposal_team03.pdf
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/CryptoScam-AI.git
```

Install the required packages:

```bash
pip install -r requirements.txt
```

---

## Running the Application

Launch the Streamlit application:

```bash
streamlit run app.py
```

The application will be available at:

```
http://localhost:8501
```

---

## MLOps: Data Pipeline, Experiment Tracking & Model Registry

- **Data pipeline** (`utils/preprocessing.py`) — cleans raw messages, builds the engineered indicator features (urgency, contact/link, structural characteristics), fits TF-IDF, and produces the train/test split. Run it directly with:

  ```bash
  python -m utils.preprocessing
  ```

- **Experiment tracking** (`utils/experiment_tracking.py`) — wraps MLflow so every training run's parameters, metrics, and model get logged consistently. Points at team03's SageMaker MLflow App (set up via `notebooks/01A_setup_sagemaker_mlflow_app_team03.ipynb`), not a local store. To view logged runs, re-run the "Get a presigned MLflow UI URL" cell in that notebook (the URL expires, so a fresh one is needed each time) and open it in a browser.

- **Model registry** (`utils/model_registry.py`, `models/MODEL_REGISTRY.md`) — saves each trained model as a versioned file (`model_v{N}.joblib`) alongside its metrics, and tracks which version is currently deployed (`best_model.joblib`), so a prior version can be restored if a newer one underperforms. This will be superseded by SageMaker's Model Registry once the pipeline notebook (03, adapted from the course template) is built.

- See `notebooks/02_baseline_experiments.ipynb` for a worked example tying data pipeline + experiment tracking + model registry together.

---

## Models Evaluated

During experimentation, multiple machine learning algorithms were evaluated.

- Logistic Regression
- Naive Bayes
- Random Forest
- Neural Network *(if applicable)*

The best-performing model is deployed within the application.

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

- Multi-language scam detection
- Screenshot OCR support
- Voice scam transcription
- Cloud deployment on AWS SageMaker
- Continuous model retraining
- Real-time monitoring
- LLM-assisted scam explanation

---

## Authors

Developed by:

- Royston Quek — Machine Learning Development
- Ong Hui Lin — Deployment, MLOps & Responsible AI

Specialist Diploma in Applied AI

Nanyang Polytechnic

Aug 2026

---

## Disclaimer

This application is developed for educational purposes.

It is not affiliated with ScamShield, the Singapore Police Force, the Monetary Authority of Singapore (MAS), or any cryptocurrency exchange.

The predictions generated by the application should not be regarded as financial, legal, or cybersecurity advice.
