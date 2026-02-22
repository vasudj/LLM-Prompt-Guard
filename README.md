# 🛡️ LLM Prompt-Armor: LLM AI Proxy

> **Code with AI. Keep your secrets.**

**Prompt-Armor** is a smart DLP (Data Loss Prevention) middleware that sits between you and Large Language Models (LLMs) like ChatGPT, Gemini, and Claude. It allows developers to use AI tools freely without violating corporate security policies.

## 🛑 The Problem: Breaking the Flow
Organizations are terrified of data leaks. To stay safe, they often ban AI tools entirely or force developers to manually "redact" sensitive code before pasting it into ChatGPT.

This **breaks the coder's flow**. It turns a 5-second AI query into a 5-minute manual scrubbing task.

## ⚡ The Solution: "Hot-Swapping" Secrets
Prompt-Armor automates privacy so you don't have to think about it. It acts as a **transparent sanitization layer**:

1.  **Intercept:** As you send a prompt, Prompt-Armor scans it for sensitive data (API Keys, PII, Credit Cards).
2.  **Alias:** It instantly replaces the secret with a dummy token (e.g., swapping `AKIA...` with `{{AWS_KEY_1}}`).
3.  **Process:** The AI solves your problem using the alias. **It never sees your real data.**
4.  **Restore:** When the AI responds, Prompt-Armor catches the alias and "hydrates" it back to the original secret.

**The Result?** You see your real code. The AI sees safe tokens. Your company stays compliant.

## 🚀 Key Features
- **Zero-Friction Security:** No copy-pasting into scrubbing tools. Just use ChatGPT as normal.
- **Real-time Interception:** Powered by `mitmproxy` to handle HTTPS traffic seamlessly.
- **Smart PII Detection:** Auto-detects & redacts:
  - 🇮🇳 Indian ID (Aadhaar, PAN)
  - 💳 Financials (Credit Cards, Bank Accounts)
  - 🔑 Dev Secrets (AWS Keys, JWTs, GitHub Tokens)
- **Zero-Knowledge Architecture:** Secrets are held in a local, temporary RAM vault. No external server ever touches your PII.
- **Context-Aware Restoration:** The "Swap Back" mechanism ensures the code you copy from ChatGPT is ready to run immediately.

## 🛠️ Installation & Usage

1. **Clone & Install:**
   ```bash
   git clone [https://github.com/vasudj/Prompt-Armor.git](https://github.com/vasudj/Prompt-Armor.git)
   pip install -r requirements.txt

Install dependencies:

pip install -r requirements.txt
Install the Certificate:

Run mitmweb once to generate certificates.

Install ~/.mitmproxy/mitmproxy-ca-cert.pem to your Trusted Root Authorities.
