
---

## ⚙️ Tech Stack

### Core Proxy Layer
- **Python 3**
- **mitmproxy**
  - HTTP request interception
  - WebSocket stream handling
- **Regex-based detection engine**

### Analytics & Dashboard
- **FastAPI**
- **WebSockets**
- **Jinja2 Templates**
- **Uvicorn**
- **CORS Middleware**

### Communication
- Local REST calls using `requests`
- WebSocket broadcasting for live updates

### Security Model
- In-memory RAM vault
- No disk persistence
- No cloud storage
- No third-party services

---

## 🧠 Secret & PII Detection

Secrets are detected using regex patterns defined in `proxy.py`.

### Supported Types

| Category | Examples |
|-------|--------|
| Developer Secrets | AWS keys, OpenAI keys, JWT |
| Financial Data | Credit cards |
| Indian PII | PAN |
| Personal Data | Email, Phone |

---

## 🔐 Risk Scoring

Each detected entity contributes to a cumulative risk score.

| Data Type | Risk Score |
|---------|-----------|
| Email / Phone | 2 |
| PAN Card | 5 |
| JWT Token | 8 |
| Credit Card | 10 |
| API Keys | 15 |

**Total Risk = Σ (count × weight)**

Displayed in the dashboard for visibility.

---

## 🔄 Workflow (Detailed)

### 1. Request Interception
- Outbound POST requests intercepted
- Only LLM provider domains processed
- `REQUEST_SEEN` event emitted

### 2. Sanitization
- Regex scans request body
- Secrets replaced with tokens (e.g. `{{AWS_ACCESS_KEY_1}}`)
- Originals stored in RAM vault

### 3. Analytics Emission
- `SANITIZED_REQUEST` event sent to dashboard
- Includes types detected and risk score

### 4. LLM Processing
- LLM receives anonymized prompt only
- No real secrets transmitted

### 5. Response Restoration
- Tokens replaced back locally
- Works for normal & streaming responses

### 6. Live Dashboard Update
- WebSocket broadcasts updated metrics

---

## 📊 Analytics Dashboard

### Metrics Tracked
- Total requests
- Sanitized requests
- Restored responses
- Protection rate
- Average risk score

### Distributions
- Secret types detected
- LLM provider usage
- Daily request activity

---

## 📡 API Reference

### `POST /event`
Used internally by the proxy to report events.

#### Event Types
- `REQUEST_SEEN`
- `SANITIZED_REQUEST`
- `RESTORED_RESPONSE`

#### Sample Payload
```json
{
  "event_type": "SANITIZED_REQUEST",
  "timestamp": "2026-02-28T10:15:30Z",
  "provider": "openai",
  "types_detected": {
    "AWS_ACCESS_KEY": 1,
    "EMAIL": 2
  },
  "risk_score": 19
}
