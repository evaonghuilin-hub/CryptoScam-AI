import streamlit as st

from utils.indicators import detect_warning_signs


st.set_page_config(
    page_title="Scam Detector",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Cryptocurrency Scam Detector")

st.write(
    """
    Paste a cryptocurrency-related message below. The current prototype uses
    placeholder prediction logic while the final machine learning model is being developed.
    """
)

sample_message = (
    "Act now! Deposit 500 USDT today and receive guaranteed returns. "
    "Contact our Telegram adviser immediately at https://example.com."
)

if "message_text" not in st.session_state:
    st.session_state.message_text = ""

col1, col2 = st.columns([1, 4])

with col1:
    if st.button("Use Sample Message"):
        st.session_state.message_text = sample_message

with col2:
    if st.button("Clear Message"):
        st.session_state.message_text = ""

message = st.text_area(
    "Message to analyse",
    key="message_text",
    height=220,
    placeholder=(
        "Example: Act now and transfer 500 USDT to receive guaranteed returns..."
    ),
)

analyse_clicked = st.button(
    "Analyse Message",
    type="primary",
    use_container_width=True,
)

if analyse_clicked:

    if not message.strip():
        st.warning("Please enter a message before running the analysis.")

    else:
        warning_signs = detect_warning_signs(message)

        # Placeholder logic pending endpoint integration.
        # To be replaced with a call to the deployed SageMaker Serverless
        # Endpoint (iti113-team03-crypto-scam-detector) using the
        # invoke_scam_detector() pattern from Notebook 04.
        indicator_count = len(warning_signs)

        if indicator_count >= 3:
            risk_level = "High"
            scam_probability = 0.92
        elif indicator_count >= 1:
            risk_level = "Medium"
            scam_probability = 0.68
        else:
            risk_level = "Low"
            scam_probability = 0.21

        st.markdown("---")
        st.subheader("Analysis Result")

        result_col1, result_col2 = st.columns(2)

        with result_col1:
            st.metric(
                label="Estimated Scam Probability",
                value=f"{scam_probability:.0%}",
            )

        with result_col2:
            st.metric(
                label="Predicted Risk Level",
                value=risk_level,
            )

        if risk_level == "High":
            st.error(
                "High-risk indicators were detected. Do not transfer money or "
                "share personal, financial, or wallet information."
            )

        elif risk_level == "Medium":
            st.warning(
                "Some suspicious indicators were detected. Verify the message "
                "through official channels before taking any action."
            )

        else:
            st.success(
                "Few common warning indicators were detected. However, a low-risk "
                "result does not guarantee that the message is legitimate."
            )

        st.subheader("Detected Warning Signs")

        if warning_signs:
            for category, matches in warning_signs.items():
                with st.expander(f"⚠️ {category}", expanded=True):
                    for match in matches:
                        st.write(f"- `{match}`")
        else:
            st.write("No hard-coded warning indicators were detected.")

        st.subheader("Recommended Actions")

        st.markdown(
            """
            - Do not transfer money based solely on the message.
            - Do not disclose passwords, OTPs, seed phrases, or private keys.
            - Verify the sender through an official communication channel.
            - Contact ScamShield at **1799** when further assistance is needed.
            """
        )

        st.caption(
            "This is a proof-of-concept decision-support tool. The current "
            "probability is a placeholder and is not produced by the final ML model."
        )