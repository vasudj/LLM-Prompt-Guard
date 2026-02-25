from mitmproxy import http
import re
import requests
import datetime

# ================= CONFIG ================= #

SECRET_PATTERNS = {
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "CREDIT_CARD": r"\b(?:\d{4}[ -]?){3}\d{4}\b",
    "PAN_CARD": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    "PHONE": r"\b[6-9]\d{9}\b"
}

TARGET_DOMAINS = [
    "chatgpt.com",
    "openai.com",
    "gemini.google.com",
    "claude.ai"
]

vault = {}
token_counters = {key: 0 for key in SECRET_PATTERNS}


# ================= HELPERS ================= #

def is_target(flow: http.HTTPFlow) -> bool:
    return any(domain in flow.request.pretty_host for domain in TARGET_DOMAINS)


def is_valid_body(flow: http.HTTPFlow) -> bool:
    return flow.request.method == "POST" and flow.request.text


def sanitize_content(content: str):
    modified = content
    replacements = []

    for label, pattern in SECRET_PATTERNS.items():
        matches = re.findall(pattern, modified)

        for secret in matches:
            token = next((t for t, s in vault.items() if s == secret), None)

            if not token:
                token_counters[label] += 1
                token = f"{{{{{label}_{token_counters[label]}}}}}"
                vault[token] = secret

            modified = modified.replace(secret, token)
            replacements.append((secret, token))

    return modified, replacements


# ================= REQUEST ================= #

def request(flow: http.HTTPFlow) -> None:

    if not is_target(flow):
        return

    if not is_valid_body(flow):
        return

    original_content = flow.request.text
    modified_content, replacements = sanitize_content(original_content)

    if not replacements:
        return

    flow.request.text = modified_content

    print("\n[🛡️ SANITIZED REQUEST]")
    print(f"Target : {flow.request.pretty_host}")
    print("-" * 50)

    for original, token in replacements:
        print(f"{original}  →  {token}")

    print("-" * 50)

    # Send event to dashboard
    try:
        requests.post(
            "http://127.0.0.1:8000/event",
            json={
                "type": "SANITIZED REQUEST",
                "domain": flow.request.pretty_host,
                "original": original_content[:200],
                "modified": modified_content[:200],
                "replacements": replacements,
                "timestamp": str(datetime.datetime.now())
            },
            timeout=1
        )
    except:
        pass


# ================= RESPONSE ================= #

def response(flow: http.HTTPFlow) -> None:

    if not is_target(flow):
        return

    if not flow.response.text:
        return

    original_content = flow.response.text
    modified_content = original_content
    restored = False

    for token, secret in vault.items():
        if token in modified_content:
            modified_content = modified_content.replace(token, secret)
            restored = True

    if not restored:
        return

    flow.response.text = modified_content

    print("\n[🔄 RESTORED RESPONSE]")
    print(f"Source : {flow.request.pretty_host}")
    print("-" * 50)

    try:
        requests.post(
            "http://127.0.0.1:8000/event",
            json={
                "type": "RESTORED RESPONSE",
                "domain": flow.request.pretty_host,
                "original": original_content[:200],
                "modified": modified_content[:200],
                "timestamp": str(datetime.datetime.now())
            },
            timeout=1
        )
    except:
        pass
