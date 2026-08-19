import random

import requests
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
    Paste a cryptocurrency-related message below. The message is sent to the
    deployed SageMaker champion model (via a FastAPI + ngrok relay) for a scam
    probability, alongside a rule-based check for common warning signs. The
    same message is also sent to the baseline (untuned) model, so the
    improvement from tuning is visible live rather than only in a table.
    """
)

with st.sidebar:
    st.subheader("Model Endpoint Settings")
    st.caption(
        "Values from Notebook 06 (FastAPI + ngrok relay), Section 9. "
        "The ngrok URL changes each time the relay is restarted."
    )
    relay_url = st.text_input(
        "Relay Predict URL (champion model)",
        value="https://your-ngrok-url.ngrok-free.app/predict",
    )
    relay_api_key = st.text_input(
        "Relay API Key",
        value="team03-demo-key",
        type="password",
    )
    st.caption(
        "The baseline model's URL is derived automatically from the champion "
        "URL above (…/predict → …/predict/baseline) — no separate field needed. "
        "Requires Notebook 03 Section 7's baseline endpoint to be deployed and Notebook 06's "
        "relay restarted after it, or the baseline comparison will show an error."
    )

SAMPLE_MESSAGES = [
    "Act now! Deposit 500 USDT today and receive guaranteed returns. "
    "Contact our Telegram adviser immediately at https://example.com.",
    "URGENT: Your wallet has been selected for a guaranteed 100% profit airdrop! "
    "Deposit 500 USDT to your wallet address within 1 hour to claim now. "
    "Contact us on Telegram immediately, don't miss out!",
    "Congratulations! You have been selected to receive a free NFT, claim your "
    "prize now before it expires! Limited slots, act fast.",
    "Been dollar-cost averaging into ETH for about a year now, curious what "
    "everyone's thoughts are on the current market conditions.",
    "Hey, our community wallet is doing a small giveaway this week, check the "
    "pinned post in the group for details.",
    "Anyone else having trouble syncing their hardware wallet after the latest "
    "firmware update?",
    # Subtler / borderline phrasing — softer signal than the messages above, useful
    # for showing where the tuned champion and untuned baseline diverge most.
    "hey just a heads up, this promo for the new token airdrop closes tonight, "
    "thought you might want to grab it before it's gone.",
    "Our support team noticed unusual activity on your account. Please verify "
    "your wallet details here to keep it secure: bit.ly/verify-wallet",
    "been using this new staking platform for a few weeks, returns have been "
    "steady around 15% a month, referral link in bio if you want in.",
    "reminder that the exchange's scheduled maintenance starts at midnight, "
    "make sure any pending withdrawals are done before then.",
    "quick favor, can you send 0.05 ETH to cover gas for the contract "
    "deployment, I'll refund you plus a bit extra once it's live.",
    "someone in the Discord posted a link to double your crypto in 24 hours, "
    "has anyone actually tried this or is it obviously fake.",
    "getting a connection timeout when I try to bridge from Polygon to "
    "Arbitrum, anyone else seeing this or found a workaround?",
    "limited spots left in our private investment group, message me directly "
    "if you're interested in learning more.",
]

if "message_text" not in st.session_state:
    st.session_state.message_text = ""

col1, col2 = st.columns([1, 4])

with col1:
    if st.button("Use Sample Message"):
        st.session_state.message_text = random.choice(SAMPLE_MESSAGES)

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


def call_relay(url, api_key, text):
    """Call a relay /predict route. Returns (label, probability, error_message)."""
    try:
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
            },
            json={"text": text},
            timeout=30,
        )
    except Exception as e:
        return None, None, f"Could not reach the model relay: {e}"

    if response.status_code != 200:
        return None, None, f"Relay returned status {response.status_code}: {response.text}"

    try:
        result = response.json()[0]
        return result["label"], result["probability"], None
    except Exception as e:
        return None, None, f"Unexpected response shape from relay: {e}"


def risk_level_for(probability):
    if probability >= 0.7:
        return "High"
    elif probability >= 0.4:
        return "Medium"
    else:
        return "Low"


if analyse_clicked:

    if not message.strip():
        st.warning("Please enter a message before running the analysis.")

    else:
        warning_signs = detect_warning_signs(message)

        # Champion model: the deployed SageMaker Serverless Endpoint
        # (iti113-team03-crypto-scam-detector) through the FastAPI + ngrok
        # relay set up in Notebook 06, using the same {"text": ...} request
        # and [{"prediction", "label", "probability"}] response shape as
        # invoke_scam_detector() in Notebook 03 Section 6.
        champ_label, champ_probability, champ_error = call_relay(
            relay_url, relay_api_key, message
        )

        # Baseline model: same relay, /predict/baseline route, forwarding to the
        # untuned endpoint deployed by Notebook 03 Section 7 — for the live champion-vs-baseline
        # comparison shown below, not the main Analysis Result.
        if relay_url.rstrip("/").endswith("/predict"):
            baseline_url = relay_url.rstrip("/")[: -len("/predict")] + "/predict/baseline"
        else:
            baseline_url = None

        if baseline_url:
            base_label, base_probability, base_error = call_relay(
                baseline_url, relay_api_key, message
            )
        else:
            base_label, base_probability = None, None
            base_error = "Relay Predict URL does not end in /predict — could not derive the baseline route."

        st.markdown("---")
        st.subheader("Analysis Result")

        if champ_error:
            st.error(
                "Could not get a prediction from the deployed model. "
                "Check that Notebook 06's relay and ngrok tunnel are running, "
                "and that the sidebar URL and API key are correct."
            )
            st.caption(champ_error)

        else:
            risk_level = risk_level_for(champ_probability)

            result_col1, result_col2 = st.columns(2)

            with result_col1:
                st.metric(
                    label="Estimated Scam Probability",
                    value=f"{champ_probability:.0%}",
                )

            with result_col2:
                st.metric(
                    label="Predicted Risk Level",
                    value=risk_level,
                )

            st.caption(f"Model label: `{champ_label}`")

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

        st.subheader("Champion vs Baseline")

        st.caption(
            "Same message scored by both deployed models — the tuned champion "
            "(logistic regression, C=10.0) and the untuned baseline (C=1.0) — to "
            "show the effect of tuning live rather than only in the report's tables."
        )

        champ_col, base_col = st.columns(2)

        with champ_col:
            st.markdown("**Champion** (tuned, C=10.0)")
            if champ_error:
                st.caption(f"Unavailable: {champ_error}")
            else:
                st.metric("Scam Probability", f"{champ_probability:.0%}", label_visibility="visible")
                st.caption(f"Label: `{champ_label}`")

        with base_col:
            st.markdown("**Baseline** (untuned, C=1.0)")
            if base_error:
                st.caption(f"Unavailable: {base_error}")
                st.caption("Run Notebook 03 Section 7 to deploy the baseline endpoint, then restart Notebook 06's relay.")
            else:
                st.metric("Scam Probability", f"{base_probability:.0%}", label_visibility="visible")
                st.caption(f"Label: `{base_label}`")

        st.subheader("Detected Warning Signs")

        st.caption(
            "Rule-based keyword and pattern check, shown alongside the model "
            "prediction for user-facing explanation."
        )

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
            "This is a proof-of-concept decision-support tool. Predictions come from "
            "a Logistic Regression model served via a temporary demo endpoint and "
            "should not be treated as a definitive judgement."
        )
