import random
from urllib.parse import quote

import requests
import streamlit as st

from utils.indicators import detect_warning_signs

FEEDBACK_EMAIL = "cryptoscam-ai-team03@gmail.com"  # placeholder address for demo purposes


def feedback_mailto(message, label, probability):
    """Build a mailto: link pre-filled with the message and prediction, so feedback
    on a specific wrong prediction is actionable rather than just 'it was wrong'."""
    subject = quote("CryptoShield AI - Prediction Feedback")
    body = quote(
        f"Message analysed:\n{message}\n\n"
        f"Model prediction: {label} ({probability:.0%})\n\n"
        f"What did the model get wrong, or what should we know?\n"
    )
    return f"mailto:{FEEDBACK_EMAIL}?subject={subject}&body={body}"


st.set_page_config(
    page_title="Scam Detector",
    page_icon="🔍",
    layout="wide",
)

st.title(
    "🔍 Cryptocurrency Scam Detector",
    help=(
        "Paste a cryptocurrency-related message below. The message is sent to the "
        "deployed SageMaker model (via a FastAPI + ngrok relay) for a scam "
        "probability, alongside a rule-based check for common warning signs."
    ),
)

DEFAULT_RELAY_URL = "https://your-ngrok-url.ngrok-free.app/predict"
DEFAULT_RELAY_API_KEY = "team03-demo-key"

# These are stored under plain session_state keys that are deliberately NEVER passed to a
# widget as key=. Streamlit garbage-collects widget-bound session_state entries once the
# widget stops being rendered — and this sidebar only exists on this page, so switching to
# another page would wipe a widget-bound value and reset the field to the placeholder on
# return. Plain keys are not garbage-collected, so the values survive page navigation.
# The URL query params are read once on first load so a refresh or app restart can also
# recover them (Streamlit's own page navigation drops the query string, so query params
# alone are not enough).
if "saved_relay_url" not in st.session_state:
    st.session_state.saved_relay_url = st.query_params.get("relay_url", DEFAULT_RELAY_URL)
if "saved_relay_api_key" not in st.session_state:
    st.session_state.saved_relay_api_key = st.query_params.get(
        "relay_api_key", DEFAULT_RELAY_API_KEY
    )

with st.sidebar:
    st.subheader("Model Endpoint Settings")
    st.caption(
        "Values from Notebook 06 (FastAPI + ngrok relay), Section 9. "
        "The ngrok URL changes each time the relay is restarted. Kept for the whole "
        "browser session, so it survives switching between pages."
    )
    relay_url = st.text_input(
        "Relay Predict URL",
        value=st.session_state.saved_relay_url,
        help="The full URL is saved even if the sidebar is too narrow to show it all — "
        "click into the field and use Home/End to see the rest, or widen the sidebar "
        "by dragging its right edge.",
    )
    relay_api_key = st.text_input(
        "Relay API Key",
        value=st.session_state.saved_relay_api_key,
        type="password",
    )

    # Write whatever is currently in the fields back to the plain keys (survives page
    # switches) and to the URL (survives a refresh or an app restart).
    st.session_state.saved_relay_url = relay_url
    st.session_state.saved_relay_api_key = relay_api_key
    st.query_params["relay_url"] = relay_url
    st.query_params["relay_api_key"] = relay_api_key

    if st.button("Check Connection"):
        health_url = relay_url.rstrip("/")
        if health_url.endswith("/predict"):
            health_url = health_url[: -len("/predict")]
        health_url = health_url + "/health"
        try:
            health_response = requests.get(health_url, timeout=10)
            if health_response.status_code == 200:
                st.success("Relay reachable")
            else:
                st.error(f"Relay returned status {health_response.status_code}")
        except Exception as e:
            st.error(f"Could not reach relay: {e}")

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

if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []

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
    """Call the relay's /predict route. Returns (label, probability, error_message)."""
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

        # Deployed SageMaker Serverless Endpoint (iti113-team03-crypto-scam-detector)
        # through the FastAPI + ngrok relay set up in Notebook 06, using the same
        # {"text": ...} request and [{"prediction", "label", "probability"}] response
        # shape as invoke_scam_detector() in Notebook 03 Section 6.
        label, probability, error = call_relay(
            relay_url, relay_api_key, message
        )

        st.markdown("---")
        st.subheader("Analysis Result")

        if error:
            # The model is served through a temporary demo relay (Notebook 06's FastAPI +
            # ngrok tunnel), which is only online while that notebook is running. Rather
            # than presenting this as a crash, explain the limitation and fall back to the
            # rule-based check below, which runs locally and needs no network access.
            st.info(
                "**The scam-detection model is not reachable right now, so this "
                "message could not be scored.**\n\n"
                "The model runs on a temporary demo endpoint that is only online while "
                "the project's relay notebook is running, so this is expected outside a "
                "live demo rather than a fault in the application.\n\n"
                "The rule-based warning-sign check below does not depend on the model "
                "and is still shown for this message."
            )
            with st.expander("Technical details"):
                st.caption(error)
                st.caption(
                    "To reconnect: start Notebook 06's FastAPI relay and ngrok tunnel, "
                    "then paste the new relay URL and API key into the sidebar."
                )

        else:
            risk_level = risk_level_for(probability)

            result_col1, result_col2 = st.columns(2)

            with result_col1:
                st.metric(
                    label="Estimated Scam Probability",
                    value=f"{probability:.0%}",
                )

            with result_col2:
                st.metric(
                    label="Predicted Risk Level",
                    value=risk_level,
                )

            st.caption(f"Model label: `{label}`")

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

            st.link_button(
                "📧 This prediction looks wrong — report it",
                feedback_mailto(message, label, probability),
            )

            st.session_state.analysis_history.insert(
                0,
                {
                    "Message": (message[:70] + "…") if len(message) > 70 else message,
                    "Prediction": f"{label} ({probability:.0%})",
                    "Risk Level": risk_level,
                },
            )

        st.subheader("Detected Warning Signs")

        st.caption(
            "Rule-based keyword and pattern check. This runs locally and does not "
            "depend on the model, so it is available even when the model endpoint is not."
        )

        if not error:
            model_flagged_scam = label.lower() == "scam"
            if model_flagged_scam and warning_signs:
                st.info(
                    f"The model's **{label}** prediction is consistent with "
                    f"{len(warning_signs)} rule-based indicator "
                    f"{'category' if len(warning_signs) == 1 else 'categories'} found below."
                )
            elif model_flagged_scam and not warning_signs:
                st.warning(
                    f"The model predicted **{label}**, but no rule-based indicators "
                    "were detected — this may reflect a subtler pattern in the message "
                    "text (e.g. TF-IDF wording) rather than an obvious keyword match."
                )
            elif not model_flagged_scam and warning_signs:
                st.warning(
                    f"The model predicted **{label}**, but some rule-based "
                    "indicators were still found below — worth a second look."
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

if st.session_state.analysis_history:
    st.markdown("---")
    st.subheader("Session History")
    st.caption(
        "Messages analysed so far this session, most recent first — useful for "
        "comparing several results side by side without re-running each one."
    )
    st.dataframe(st.session_state.analysis_history, use_container_width=True, hide_index=True)

    if st.button("Clear History"):
        st.session_state.analysis_history = []
        st.rerun()
