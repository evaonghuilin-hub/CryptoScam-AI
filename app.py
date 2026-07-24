import streamlit as st


st.set_page_config(
    page_title="CryptoShield AI",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ CryptoShield AI")

st.subheader("Cryptocurrency Scam Message Detection")

st.write(
    """
    CryptoShield AI is a proof-of-concept decision-support tool that helps users
    assess whether a cryptocurrency-related message may contain signs of a scam.
    """
)

st.info(
    """
    This application is intended for educational and decision-support purposes only.
    A low-risk result does not guarantee that a message is legitimate.
    """
)

st.markdown("### How it works")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 1. Paste a message")
    st.write("Enter a suspicious cryptocurrency-related message.")

with col2:
    st.markdown("#### 2. Analyse")
    st.write("The system checks the message for scam-related patterns.")

with col3:
    st.markdown("#### 3. Review the result")
    st.write("View the estimated risk level and recommended safety actions.")

st.markdown("---")

st.write(
    "Use the navigation panel on the left and open **Scam Detector** to begin."
)