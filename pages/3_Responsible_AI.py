import streamlit as st


st.set_page_config(
    page_title="Responsible AI",
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ Responsible AI")

st.subheader("Decision-Support Only")

st.write(
    """
    CryptoShield AI provides a risk assessment rather than a definitive verdict.
    Users should independently verify suspicious messages through official channels.
    """
)

st.subheader("Privacy")

st.write(
    """
    User-submitted messages are intended to be processed only for inference.
    The application does not intentionally store messages permanently.
    """
)

st.subheader("Known Limitations")

st.markdown(
    """
    - The training dataset is synthetic.
    - The proof-of-concept may not recognise new scam tactics.
    - TF-IDF has limited understanding of meaning and context.
    - Multilingual messages and deliberate misspellings may reduce performance.
    - False positives and false negatives remain possible.
    """
)

st.subheader("Human Oversight")

st.write(
    """
    Users are encouraged to review the warning indicators, exercise their own
    judgement, and verify suspicious claims through ScamShield or the relevant
    authorities.
    """
)

st.subheader("Model Monitoring")

st.write(
    """
    Future versions should monitor model performance, concept drift and platform-level
    recall. A previous stable model should be retained so that the system can be
    rolled back if a newer model performs worse.
    """
)

st.subheader("Feedback and Continuous Improvement")

st.write(
    """
    Human oversight does not end at deployment. If a prediction looks wrong, or a
    scam tactic slips through undetected, that feedback is valuable input for future
    retraining rather than something the system can act on itself.
    """
)

st.link_button(
    "📧 Report a wrong prediction or leave feedback",
    "mailto:cryptoscam-ai-team03@gmail.com?subject=CryptoShield%20AI%20Feedback",
)

st.caption(
    "This is a placeholder address for demo purposes. On the Scam Detector page, "
    "the feedback link pre-fills the message and prediction for easier review."
)