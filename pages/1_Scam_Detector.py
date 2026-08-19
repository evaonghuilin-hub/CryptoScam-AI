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

# Read any previously-saved values from the page URL (?relay_url=...&relay_api_key=...)
# first, then fall back to the placeholder defaults. Storing these in the URL, not just
# session_state, means the values survive a full app restart (e.g. Streamlit Community
# Cloud redeploying after a git push) as long as the browser tab keeps the same link —
# session_state alone is wiped whenever the server process restarts.
if "relay_url" not in st.session_state:
    st.session_state.relay_url = st.query_params.get(
        "relay_url", "https://your-ngrok-url.ngrok-free.app/predict"
    )
if "relay_api_key" not in st.session_state:
    st.session_state.relay_api_key = st.query_params.get("relay_api_key", "team03-demo-key")

with st.sidebar:
    st.subheader("Model Endpoint Settings")
    st.caption(
        "Values from Notebook 06 (FastAPI + ngrok relay), Section 9. "
        "The ngrok URL changes each time the relay is restarted. Saved in the page "
        "URL so it survives switching pages, refreshing, or the app restarting."
    )
    relay_url = st.text_input(
        "Relay Predict URL (champion model)",
        key="relay_url",
    )
    relay_api_key = st.text_input(
        "Relay API Key",
        key="relay_api_key",
        type="password",
    )
    # Keep the URL in sync so a copied/bookmarked link (or a page reload) restores these.
    st.query_params["relay_url"] = relay_url
    st.query_params["relay_api_key"] = relay_api_key
    st.caption(
        "The baseline model's URL is derived automatically from the champion "
        "URL above (…/predict → …/predict/baseline) — no separate field needed. "
        "Requires Notebook 03 Section 7's baseline endpoint to be deployed and Notebook 06's "
        "relay restarted after it, or the baseline comparison will show an error."
    )

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
    """Call a relay /predict route. Returns (label, probability, top_features, error_message).

    top_features is a list of {feature, contribution, direction} dicts from the
    model's coefficient-based explanation (added to inference.py). Older deployed
    endpoints won't include this field yet, so it defaults to an empty list rather
    than raising, and callers should treat an empty list as "not available" rather
    than "no signal"."""
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
        return None, None, [], f"Could not reach the model relay: {e}"

    if response.status_code != 200:
        return None, None, [], f"Relay returned status {response.status_code}: {response.text}"

    try:
        result = response.json()[0]
        return result["label"], result["probability"], result.get("top_features", []), None
    except Exception as e:
        return None, None, [], f"Unexpected response shape from relay: {e}"


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
        champ_label, champ_probability, champ_top_features, champ_error = call_relay(
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
            base_label, base_probability, base_top_features, base_error = call_relay(
                baseline_url, relay_api_key, message
            )
        else:
            base_label, base_probability, base_top_features = None, None, []
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

            st.link_button(
                "📧 This prediction looks wrong — report it",
                feedback_mailto(message, champ_label, champ_probability),
            )

            if champ_top_features:
                with st.expander("🔎 Why this prediction? (model explainability)"):
                    st.caption(
                        "The words and patterns that pushed the model's score most, based "
                        "on each feature's value multiplied by its learned coefficient. "
                        "This is a lightweight approximation for a linear model, not a "
                        "full SHAP-style explanation."
                    )
                    for feat in champ_top_features:
                        arrow = "🔺" if feat["direction"] == "scam" else "🔻"
                        st.write(
                            f"{arrow} `{feat['feature']}` — pushed toward "
                            f"**{feat['direction']}** (contribution: {feat['contribution']:+.3f})"
                        )

            st.session_state.analysis_history.insert(
                0,
                {
                    "Message": (message[:70] + "…") if len(message) > 70 else message,
                    "Champion": f"{champ_label} ({champ_probability:.0%})",
                    "Baseline": (
                        f"{base_label} ({base_probability:.0%})"
                        if base_label is not None
                        else "—"
                    ),
                    "Risk Level": risk_level,
                },
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

        if not champ_error:
            model_flagged_scam = champ_label.lower() == "scam"
            if model_flagged_scam and warning_signs:
                st.info(
                    f"The model's **{champ_label}** prediction is consistent with "
                    f"{len(warning_signs)} rule-based indicator "
                    f"{'category' if len(warning_signs) == 1 else 'categories'} found below."
                )
            elif model_flagged_scam and not warning_signs:
                st.warning(
                    f"The model predicted **{champ_label}**, but no rule-based indicators "
                    "were detected — this may reflect a subtler pattern in the message "
                    "text (e.g. TF-IDF wording) rather than an obvious keyword match."
                )
            elif not model_flagged_scam and warning_signs:
                st.warning(
                    f"The model predicted **{champ_label}**, but some rule-based "
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
