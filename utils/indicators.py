import re


URGENT_KEYWORDS = [
    "urgent",
    "immediately",
    "act now",
    "act fast",
    "hurry",
    "limited time",
    "today only",
    "expires today",
    "offer ends soon",
    "last chance",
    "don't miss out",
    "within 24 hours",
    "within 1 hour",
    "respond now",
    "claim now",
    "limited slots",
    "before it's too late",
    "time-sensitive",
]

GUARANTEED_RETURN_KEYWORDS = [
    "guaranteed return",
    "guaranteed returns",
    "guaranteed profit",
    "risk-free",
    "risk free",
    "100% profit",
    "double your money",
    "high returns",
    "稳赚不赔",
]

PAYMENT_KEYWORDS = [
    "deposit",
    "transfer funds",
    "send payment",
    "pay now",
    "top up",
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "usdt",
    "wallet address",
]

OFF_PLATFORM_KEYWORDS = [
    "telegram",
    "whatsapp",
    "discord",
    "wechat",
    "private chat",
    "dm me",
    "direct message",
]

CREDENTIAL_KEYWORDS = [
    "seed phrase",
    "private key",
    "wallet password",
    "recovery phrase",
    "otp",
    "verification code",
    "security code",
]


def find_keyword_matches(message: str, keywords: list[str]) -> list[str]:
    """Return keywords found in the message."""
    message_lower = message.lower()

    return [
        keyword
        for keyword in keywords
        if keyword.lower() in message_lower
    ]


def detect_warning_signs(message: str) -> dict[str, list[str]]:
    """Detect rule-based scam indicators for user-facing explanations."""

    warning_signs = {}

    urgency_matches = find_keyword_matches(message, URGENT_KEYWORDS)
    if urgency_matches:
        warning_signs["Urgency language"] = urgency_matches

    return_matches = find_keyword_matches(
        message,
        GUARANTEED_RETURN_KEYWORDS,
    )
    if return_matches:
        warning_signs["Guaranteed or unusually high returns"] = return_matches

    payment_matches = find_keyword_matches(message, PAYMENT_KEYWORDS)
    if payment_matches:
        warning_signs["Cryptocurrency payment request"] = payment_matches

    platform_matches = find_keyword_matches(
        message,
        OFF_PLATFORM_KEYWORDS,
    )
    if platform_matches:
        warning_signs["Off-platform communication"] = platform_matches

    credential_matches = find_keyword_matches(
        message,
        CREDENTIAL_KEYWORDS,
    )
    if credential_matches:
        warning_signs["Sensitive credential request"] = credential_matches

    urls = re.findall(r"https?://[^\s]+|www\.[^\s]+", message)
    if urls:
        warning_signs["URL detected"] = urls

    wallet_addresses = re.findall(
        r"\b(?:0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b",
        message,
    )
    if wallet_addresses:
        warning_signs["Possible wallet address"] = wallet_addresses

    return warning_signs