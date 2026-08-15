import streamlit as st


st.set_page_config(
    page_title="About the Model",
    page_icon="📊",
    layout="wide",
)

st.title("📊 About the Model")

st.write(
    """
    CryptoShield AI uses supervised machine learning to classify
    cryptocurrency-related messages as scam or legitimate.
    """
)

st.subheader("Planned Machine Learning Pipeline")

st.markdown(
    """
    1. User submits a message.
    2. The message is cleaned and preprocessed.
    3. TF-IDF converts the message into numerical features.
    4. A trained machine learning classifier generates a scam prediction.
    5. The application converts the prediction into a risk category.
    6. Rule-based indicators provide a user-friendly explanation.
    """
)

st.subheader("Models Evaluated")

st.markdown(
    """
    - **Logistic Regression** — selected model (test ROC-AUC 0.891)
    - **Random Forest** — evaluated for comparison (test ROC-AUC 0.860)

    Naive Bayes, Support Vector Machines and Decision Trees were considered in
    the project proposal but have not been evaluated at this stage.
    """
)

st.subheader("Evaluation Metrics")

st.markdown(
    """
    - Accuracy
    - Precision
    - Recall
    - F1-score
    - ROC-AUC (used as the model registry quality gate, threshold 0.85)
    """
)

st.info(
    """
    The final model has not yet been integrated. This page will be updated with
    the selected model, its hyperparameters, and evaluation results.
    """
)