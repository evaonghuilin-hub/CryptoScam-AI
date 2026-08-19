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

st.subheader("Machine Learning Pipeline")

st.markdown(
    """
    1. A user submits a message on the Scam Detector page.
    2. The message is sent, via a FastAPI + ngrok relay, to a SageMaker Serverless
       Endpoint, which cleans and preprocesses the text.
    3. TF-IDF converts the message into numerical features, combined with 15
       engineered indicator features (urgency, contact patterns, structural cues).
    4. The trained logistic regression classifier generates a scam probability.
    5. The application converts the prediction into a risk category (Low / Medium / High).
    6. Rule-based indicators provide a user-friendly explanation alongside the prediction.
    """
)

st.subheader("Champion and Baseline Models")

st.markdown(
    """
    Two versions of the model are deployed, so the effect of tuning is visible live
    rather than only in a report table:

    - **Champion** — tuned logistic regression, `C=10.0`, test ROC-AUC 0.8908,
      accuracy 77.51%, recall 76.7%, F1 0.7786. This is the model used for the main
      Analysis Result.
    - **Baseline** — untuned logistic regression, `C=1.0`, test ROC-AUC 0.8898. Shown
      alongside the champion in the Champion vs Baseline panel for comparison.

    **Random Forest** was also evaluated (test ROC-AUC 0.86) but was not selected —
    its recall (52–56%) was well below logistic regression's, which matters more than
    the AUC gap given that a missed scam is costlier than a false alarm for this project.
    Naive Bayes, Support Vector Machines and neural networks were considered in the
    project proposal but have not been evaluated at this stage.
    """
)

st.subheader("Evaluation Metrics")

st.markdown(
    """
    - Accuracy
    - Precision
    - Recall — treated as the priority metric, given the cost asymmetry of a missed scam
    - F1-score
    - ROC-AUC (used as the SageMaker Model Registry quality gate, threshold 0.85)
    """
)

st.info(
    """
    Recall (76.7%) currently falls short of the project's 85% target. This is an honest,
    known limitation rather than an unresolved bug — see Responsible AI for details.
    """
)