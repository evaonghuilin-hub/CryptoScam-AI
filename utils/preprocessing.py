"""
Data pipeline for CryptoShield AI.

This module is the shared "prep station" for the project: it takes the raw
crypto-related messages and turns them into (1) TF-IDF features for the ML
model and (2) the hand-engineered indicator features described in the
project proposal (urgency, contact/link, structural characteristics).

Both the training notebook and the Streamlit app should import from this
module rather than re-implementing cleaning/feature logic, so training and
inference always stay in sync.

Usage as a script (run from the project root):

    python -m utils.preprocessing

This will:
    1. Load data/crypto_scam_dataset.csv
    2. Clean the text and engineer features
    3. Split into train/test sets (stratified on label)
    4. Fit a TF-IDF vectorizer on the training text
    5. Save outputs to data/processed/ and models/
"""

from __future__ import annotations

import re
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

from utils.indicators import (
    CREDENTIAL_KEYWORDS,
    GUARANTEED_RETURN_KEYWORDS,
    OFF_PLATFORM_KEYWORDS,
    PAYMENT_KEYWORDS,
    URGENT_KEYWORDS,
    find_keyword_matches,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = ROOT_DIR / "data" / "crypto_scam_dataset.csv"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MODELS_DIR = ROOT_DIR / "models"

URL_PATTERN = re.compile(r"https?://[^\s]+|www\.[^\s]+")
WALLET_PATTERN = re.compile(
    r"\b(?:0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b"
)
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(?:\+?\d[\d\s-]{7,}\d)")
COUNTDOWN_PATTERN = re.compile(
    r"\b\d+\s*(?:hour|hours|hr|hrs|minute|minutes|min|mins|day|days)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Text cleaning (for TF-IDF)
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Normalise raw message text before TF-IDF vectorisation.

    Lower-cases the text and collapses URLs to a placeholder token so the
    model can learn "messages with links are riskier" without memorising
    specific domains, then collapses extra whitespace.
    """
    if not isinstance(text, str):
        return ""

    text = text.strip()
    text = URL_PATTERN.sub(" <url> ", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Engineered / indicator features (for interpretability + explanations)
# ---------------------------------------------------------------------------

def extract_engineered_features(text: str) -> dict:
    """Extract the numeric indicator features described in the proposal.

    Groups:
      - Urgency indicators
      - Contact and link characteristics
      - Structural characteristics

    These reuse the same keyword lists as utils.indicators, so the numbers
    fed to the model line up with the human-readable warning signs shown
    in the Streamlit app.
    """
    if not isinstance(text, str):
        text = ""

    urgency_keyword_hits = len(find_keyword_matches(text, URGENT_KEYWORDS))
    guaranteed_return_hits = len(find_keyword_matches(text, GUARANTEED_RETURN_KEYWORDS))
    countdown_hits = len(COUNTDOWN_PATTERN.findall(text))
    exclamation_count = text.count("!")

    urgency_score = urgency_keyword_hits + countdown_hits + min(exclamation_count, 3)

    wallet_matches = WALLET_PATTERN.findall(text)
    url_matches = URL_PATTERN.findall(text)
    email_matches = EMAIL_PATTERN.findall(text)
    phone_matches = PHONE_PATTERN.findall(text)
    payment_hits = len(find_keyword_matches(text, PAYMENT_KEYWORDS))
    off_platform_hits = len(find_keyword_matches(text, OFF_PLATFORM_KEYWORDS))
    credential_hits = len(find_keyword_matches(text, CREDENTIAL_KEYWORDS))

    letters = [c for c in text if c.isalpha()]
    capital_ratio = (
        sum(1 for c in letters if c.isupper()) / len(letters) if letters else 0.0
    )
    digit_count = sum(1 for c in text if c.isdigit())

    return {
        # Urgency indicators
        "urgency_keyword_count": urgency_keyword_hits,
        "guaranteed_return_keyword_count": guaranteed_return_hits,
        "countdown_phrase_count": countdown_hits,
        "exclamation_count": exclamation_count,
        "urgency_score": urgency_score,
        # Contact and link characteristics
        "has_wallet_address": int(bool(wallet_matches)),
        "wallet_address_count": len(wallet_matches),
        "has_url": int(bool(url_matches)),
        "url_count": len(url_matches),
        "has_email": int(bool(email_matches)),
        "has_phone_number": int(bool(phone_matches)),
        "payment_keyword_count": payment_hits,
        "off_platform_keyword_count": off_platform_hits,
        "credential_keyword_count": credential_hits,
        # Structural characteristics
        "message_length": len(text),
        "capital_letter_ratio": round(capital_ratio, 4),
        "has_numeric_content": int(digit_count > 0),
        "digit_count": digit_count,
    }


def build_feature_table(df: pd.DataFrame, text_column: str = "text") -> pd.DataFrame:
    """Build a DataFrame of engineered features, one row per message."""
    records = [extract_engineered_features(t) for t in df[text_column]]
    return pd.DataFrame(records, index=df.index)


# ---------------------------------------------------------------------------
# TF-IDF
# ---------------------------------------------------------------------------

def fit_tfidf_vectorizer(texts, max_features: int = 5000) -> TfidfVectorizer:
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        min_df=2,
    )
    vectorizer.fit(texts)
    return vectorizer


# ---------------------------------------------------------------------------
# End-to-end pipeline
# ---------------------------------------------------------------------------

def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected_columns = {"id", "platform", "text", "label"}
    missing = expected_columns - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing expected columns: {missing}")
    return df


def run_pipeline(
    raw_path: Path = RAW_DATA_PATH,
    test_size: float = 0.2,
    random_state: int = 42,
    save: bool = True,
) -> dict:
    """Run the full data pipeline and optionally persist outputs.

    Returns a dict with the train/test splits (each including engineered
    features) and the fitted TF-IDF vectorizer, so both notebooks and the
    Streamlit app can reuse it without duplicating logic.
    """
    df = load_raw_data(raw_path)
    df["clean_text"] = df["text"].apply(clean_text)

    features = build_feature_table(df, text_column="text")
    df = pd.concat([df, features], axis=1)

    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df["label"],
    )

    vectorizer = fit_tfidf_vectorizer(train_df["clean_text"])

    if save:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        train_df.to_csv(PROCESSED_DIR / "train.csv", index=False)
        test_df.to_csv(PROCESSED_DIR / "test.csv", index=False)
        joblib.dump(vectorizer, MODELS_DIR / "tfidf_vectorizer.joblib")

    return {
        "train_df": train_df,
        "test_df": test_df,
        "vectorizer": vectorizer,
    }


if __name__ == "__main__":
    result = run_pipeline()
    print(f"Train rows: {len(result['train_df'])}")
    print(f"Test rows: {len(result['test_df'])}")
    print(
        "Saved: data/processed/train.csv, data/processed/test.csv, "
        "models/tfidf_vectorizer.joblib"
    )
