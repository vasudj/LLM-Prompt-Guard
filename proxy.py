"""
Prompt-Armor: Robust Version
"""
from mitmproxy import http
import re

# --- CONFIGURATION ---
SECRET_PATTERNS = {
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "CREDIT_CARD": r"\b(?:\d[ -]*?){13,19}\b",
    "PAN_CARD": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    "PHONE": r"\b\d{10}\b"
}

vault = {}
token_counters = {key: 0 for key in SECRET_PATTERNS}

def request(flow: http.HTTPFlow) -> None:
    # 1. VISUAL HEARTBEAT: Proves the proxy is hooked
    # If you don't see this, the browser isn't using the proxy.
    if flow.request.method == "POST":
        print(f"[DEBUG] 👁️  Seeing POST to: {flow.request.pretty_host}")

    # 2. FILTERING: Only look at text data
    if flow.request.method != "POST" or not flow.request.text:
        return

    # 3. DOMAIN CHECK (Optional: Remove if you want to scan EVERYTHING)
    # Uncomment lines below to restrict to AI only:
    # allowed = ["openai", "chatgpt", "claude", "gemini"]
    # if not any(d in flow.request.pretty_host for d in allowed):
    #     return

    content = flow.request.text
    modified = content
    found = False

    # 4. SCANNING LOGIC
    for label, pattern in SECRET_PATTERNS.items():
        matches = re.findall(pattern, modified)
        for secret in matches:
            # Reuse token or mint new one
            token = next((t for t, s in vault.items() if s == secret), None)
            if not token:
                token_counters[label] += 1
                token = f"{{{{{label}_{token_counters[label]}}}}}"
                vault[token] = secret
            
            modified = modified.replace(secret, token)
            found = True

    # 5. ACTION
    if found:
        print(f"\n[>>>] 🛡️  SANITIZING REQUEST TO: {flow.request.pretty_host}")
        print(f"      ❌ Original: {content[:100]}...")
        print(f"      ✅ Sent:     {modified[:100]}...")
        print("-" * 50)
        flow.request.text = modified

def response(flow: http.HTTPFlow) -> None:
    if not flow.response.text:
        return

    modified = flow.response.text
    restored = False

    for token, secret in vault.items():
        if token in modified:
            modified = modified.replace(token, secret)
            restored = True

    if restored:
        print(f"[<<<] 🔄 RESTORED DATA from {flow.request.pretty_host}")
        flow.response.text = modified