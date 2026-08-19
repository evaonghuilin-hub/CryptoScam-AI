import requests
import streamlit as st

from utils.indicators import detect_warning_signs

st.set_page_config(
    page_title="Try It (Bonus Preview)",
    page_icon="✨",
    layout="wide",
)

st.title("✨ Try It — What a Real User Would See")

st.caption(
    "Bonus preview: a simplified, non-technical version of the Scam Detector, showing "
    "how this tool could look if deployed for real end users rather than for a project "
    "demo. See About the Model for the full technical version used for evaluation."
)

st.write(
    """
    Not sure if a message about crypto is genuine? Paste it below and we'll take a look.
    """
)

# In a real deployment, the connection details below would live in server-side
# configuration (e.g. Streamlit secrets or environment variables) and a user would
# never see or set them. This bonus page has no config screen of its own — it quietly
# reuses whatever endpoint was already entered on the Scam Detector page, so you don't
# have to type it twice while testing.
relay_url = st.session_state.get("relay_url", "")
relay_api_key = st.session_state.get("relay_api_key", "")
service_configured = bool(relay_url) and "your-ngrok-url" not in relay_url

if "message_text_simple" not in st.session_state:
    st.session_state.message_text_simple = ""

message = st.text_area(
    "Message to check",
    key="message_text_simple",
    height=180,
    placeholder="Paste the message here...",
)

check_clicked = st.button("Check Message", type="primary", use_container_width=True)


def check_message(url, api_key, text):
    """Call the detection service. Returns (result_dict, friendly_error) —
    never surfaces raw status codes or response bodies to the user."""
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json", "x-api-key": api_key},
            json={"text": text},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()[0], None
    except Exception:
        return None, "We couldn't check this message right now. Please try again in a moment."


if check_clicked:
    if not message.strip():
        st.warning("Please paste a message first.")
    elif not service_configured:
        st.info(
            "This preview isn't connected yet — open the Scam Detector page, enter the "
            "endpoint details there once, then come back here."
        )
    else:
        with st.spinner("Checking..."):
            result, error = check_message(relay_url, relay_api_key, message)

        st.markdown("---")

        if error:
            st.error(error)
        else:
            probability = result["probability"]
            is_scam = result["label"].lower() == "scam"

            if probability >= 0.7:
                st.error(f"⚠️ This looks risky — we're {probability:.0%} confident this could be a scam.")
            elif probability >= 0.4:
                st.warning(f"🤔 This looks a bit suspicious — {probability:.0%} confidence.")
            else:
                st.success(f"✅ This looks okay — only {probability:.0%} confidence of scam signs.")

            warning_signs = detect_warning_signs(message)
            if warning_signs:
                with st.expander("What looks suspicious"):
                    for category, matches in warning_signs.items():
                        st.write(f"**{category}:** " + ", ".join(f"`{m}`" for m in matches))

            top_features = result.get("top_features", [])
            if top_features:
                with st.expander("Why we think this"):
                    for feat in top_features[:5]:
                        st.write(f"- `{feat['feature']}`")

            st.markdown("#### What to do")
            st.markdown(
                """
                - Don't send money or share passwords, OTPs, or private keys based on this message alone.
                - Verify the sender through an official channel before acting.
                - If in doubt, contact ScamShield at **1799**.
                """
            )

            st.caption(
                "This tool gives a helpful second opinion, not a guarantee — always use your own judgement."
            )

            st.link_button(
                "Think we got this wrong? Let us know",
                "mailto:cryptoscam-ai-team03@gmail.com?subject=Feedback",
            )
