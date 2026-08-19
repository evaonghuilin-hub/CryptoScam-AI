import re


URGENT_KEYWORDS = [
    "urgent",
    "immediately",
    "act now",
    "act fast",
    "act before",
    "hurry",
    "limited time",
    "limited slots",
    "limited spots",
    "today only",
    "expires today",
    "expires",
    "closes tonight",
    "ends tonight",
    "offer ends soon",
    "last chance",
    "final notice",
    "don't miss out",
    "24 hours",
    "48 hours",
    "1 hour",
    "respond now",
    "claim now",
    "before it's too late",
    "time-sensitive",
]

GUARANTEED_RETURN_KEYWORDS = [
    "guaranteed",
    "guaranteed return",
    "guaranteed returns",
    "guaranteed profit",
    "risk-free",
    "risk free",
    "double your money",
    "double your crypto",
    "high returns",
    "稳赚不赔",
]

# Intent to move money, rather than a mere mention of a currency. Bare currency
# names (eth, btc, usdt) are deliberately excluded: they appear just as often in
# ordinary market discussion as in scams, and flagging them produced false
# positives on legitimate messages.
PAYMENT_KEYWORDS = [
    "deposit",
    "transfer funds",
    "send payment",
    "send money",
    "send me",
    "pay now",
    "top up",
    "wallet address",
    "cover gas",
    "gas fee",
    "processing fee",
    "activation fee",
]

OFF_PLATFORM_KEYWORDS = [
    "telegram",
    "whatsapp",
    "discord",
    "wechat",
    "private chat",
    "private group",
    "private investment group",
    "dm me",
    "direct message",
    "message me directly",
    "message me",
    "referral link",
    "link in bio",
]

CREDENTIAL_KEYWORDS = [
    "seed phrase",
    "private key",
    "wallet password",
    "recovery phrase",
    "otp",
    "verification code",
    "security code",
    "verify your wallet",
    "verify your account",
    "unusual activity",
]

# Return-rate claims such as "200% profit" or "15% a month", which keyword lists
# cannot cover because the number varies.
PERCENTAGE_RETURN_PATTERN = re.compile(
    r"\b\d{1,4}\s*%\s*(?:profit|return|returns|gain|gains|monthly|a month|per month|apy|roi)\b",
    re.IGNORECASE,
)

# Links, including bare and shortened domains such as bit.ly/xyz, which the
# earlier http/www-only pattern missed even though shortened links are a common
# phishing vector. The trailing path requirement keeps ordinary filenames
# (for example "indicators.py") from matching.
URL_PATTERN = re.compile(
    r"https?://\S+"
    r"|www\.\S+"
    r"|\b[a-z0-9][a-z0-9-]*\.(?:ly|gg|io|me|co|link|xyz|top|site|click|info|com|net|org)/\S+",
    re.IGNORECASE,
)

WALLET_PATTERN = re.compile(r"\b(?:0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b")


def find_keyword_matches(message: str, keywords: list[str]) -> list[str]:
    """Return keywords found in the message.

    Matching is bounded so that a keyword only matches a whole word or phrase.
    Plain substring matching caused false positives on short keywords — "eth"
    matched inside "whether" and "together", and "otp" inside longer words.
    """
    message_lower = message.lower()
    matches = []

    for keyword in keywords:
        pattern = (
            r"(?<![a-z0-9])" + re.escape(keyword.lower()) + r"(?![a-z0-9])"
        )
        if re.search(pattern, message_lower):
            matches.append(keyword)

    return matches


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
    return_matches += PERCENTAGE_RETURN_PATTERN.findall(message)
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

    urls = URL_PATTERN.findall(message)
    if urls:
        warning_signs["URL detected"] = urls

    wallet_addresses = WALLET_PATTERN.findall(message)
    if wallet_addresses:
        warning_signs["Possible wallet address"] = wallet_addresses

    return warning_signs
