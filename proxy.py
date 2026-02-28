from mitmproxy import http, websocket
import re
import requests
import datetime
import uuid

# ================= CONFIG ================= #

SECRET_PATTERNS = {
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "PHONE": r"\b[6-9]\d{9}\b",
    "PAN_CARD": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    "CREDIT_CARD": r"\b(?:\d{4}[ -]?){3}\d{4}\b",
    "OPENAI_KEY": r"\bsk-[A-Za-z0-9]{20,}\b",
    "AWS_ACCESS_KEY": r"\bAKIA[0-9A-Z]{16}\b",
    "JWT_TOKEN": r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
}

RISK_SCORES = {
    "EMAIL": 2,
    "PHONE": 2,
    "PAN_CARD": 5,
    "CREDIT_CARD": 10,
    "OPENAI_KEY": 15,
    "AWS_ACCESS_KEY": 15,
    "JWT_TOKEN": 8
}

TARGET_DOMAINS = [
    "chatgpt.com",
    "ab.chatgpt.com",
    "ws.chatgpt.com",
    "openai.com",
    "gemini.google.com",
    "claude.ai"
]

vault = {}
token_counters = {key: 0 for key in SECRET_PATTERNS}


# ================= HELPERS ================= #

def detect_provider(host: str):
    if "gemini" in host:
        return "gemini"
    elif "chatgpt" in host or "openai" in host:
        return "openai"
    elif "claude" in host:
        return "claude"
    return "unknown"


def is_target(flow: http.HTTPFlow) -> bool:
    return any(domain in flow.request.pretty_host for domain in TARGET_DOMAINS)


def is_valid_body(flow: http.HTTPFlow) -> bool:
    return flow.request.method == "POST" and flow.request.text


def sanitize_content(content: str):
    modified = content
    replacements = []
    type_counts = {}

    for label, pattern in SECRET_PATTERNS.items():
        matches = re.findall(pattern, modified)

        for secret in matches:
            token = next((t for t, s in vault.items() if s == secret), None)

            if not token:
                token_counters[label] += 1
                token = f"{{{{{label}_{token_counters[label]}}}}}"
                vault[token] = secret

            modified = modified.replace(secret, token)

            replacements.append({
                "type": label,
                "original": secret,
                "token": token
            })

            type_counts[label] = type_counts.get(label, 0) + 1

    return modified, replacements, type_counts


def restore_tokens(content: str):
    modified = content
    restored = False

    for token, secret in vault.items():
        if token in modified:
            modified = modified.replace(token, secret)
            restored = True

    return modified, restored


def calculate_risk(type_counts):
    score = 0
    for t, count in type_counts.items():
        score += RISK_SCORES.get(t, 0) * count
    return score


# ================= REQUEST ================= #

def request(flow: http.HTTPFlow) -> None:

    if not is_target(flow):
        return

    provider = detect_provider(flow.request.pretty_host)

    # Emit TOTAL request event (for protection rate calculation)
    try:
        requests.post(
            "http://127.0.0.1:8000/event",
            json={
                "event_type": "REQUEST_SEEN",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "domain": flow.request.pretty_host,
                "provider": provider
            },
            timeout=0.5
        )
    except:
        pass

    if not is_valid_body(flow):
        return

    original_content = flow.request.text
    modified_content, replacements, type_counts = sanitize_content(original_content)

    if not replacements:
        return

    flow.request.text = modified_content

    risk_score = calculate_risk(type_counts)

    event_payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "SANITIZED_REQUEST",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "provider": provider,
        "domain": flow.request.pretty_host,
        "method": flow.request.method,
        "path": flow.request.path,
        "request_size": len(original_content),
        "total_replacements": len(replacements),
        "types_detected": type_counts,
        "risk_score": risk_score,
        "replacements": replacements
    }

    print("\n[🛡️ SANITIZED REQUEST]")
    print(f"Target     : {flow.request.pretty_host}")
    print(f"Risk Score : {risk_score}")
    print("-" * 50)

    for r in replacements:
        print(f"{r['original']}  →  {r['token']}")

    print("-" * 50)

    try:
        requests.post(
            "http://127.0.0.1:8000/event",
            json=event_payload,
            timeout=0.5
        )
    except:
        pass


# ================= RESPONSE ================= #

def response(flow: http.HTTPFlow) -> None:

    if not is_target(flow):
        return

    if not flow.response or not flow.response.text:
        return

    original_content = flow.response.text
    modified_content, restored = restore_tokens(original_content)

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
                "event_id": str(uuid.uuid4()),
                "event_type": "RESTORED_RESPONSE",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "provider": detect_provider(flow.request.pretty_host),
                "domain": flow.request.pretty_host
            },
            timeout=0.5
        )
    except:
        pass


# ================= WEBSOCKET STREAM RESTORE ================= #

def websocket_message(flow: http.HTTPFlow):

    if not is_target(flow):
        return

    message = flow.websocket.messages[-1]

    if not message.from_server:
        return

    try:
        content = message.content.decode("utf-8", errors="ignore")
    except:
        return

    modified_content, restored = restore_tokens(content)

    if restored:
        message.content = modified_content.encode("utf-8")

        print("\n[🔄 RESTORED STREAM RESPONSE]")
        print(f"Source : {flow.request.pretty_host}")
        print("-" * 60)
