# SafeCode Navigator AI

**An AI agent that helps new developers understand legacy codebases safely — without leaking company secrets, without interrupting senior engineers.**

Built for the Google Cloud GenAI Academy APAC Edition using Google ADK, Gemini 2.5 Flash, and Cloud Run.

---

## Live Demo
Note: This is a demo deployment. Please avoid excessive usage.

| Resource             | Link                                                             |
|----------------------|------------------------------------------------------------------|
| Cloud Run (Live App) | `https://safecode-navigator-ai-278503764579.asia-south1.run.app` |
|-----------------------------------------------------------------------------------------|

---

## Problem Statement

New developers joining legacy codebases face two compounding risks:

1. They paste real API keys, database URLs, and JWT tokens into AI tools — leaking company credentials.
2. They modify code they do not understand — breaking systems they cannot debug.

SafeCode Navigator AI addresses both risks through a multi-layer safety and explanation pipeline.

---

## Architecture

```
Developer Question
       │
       ▼
Layer 1 — Question Classifier
       │  Classifies intent: function logic / API / DB / config / workflow
       │  Assigns risk level: LOW / MEDIUM / HIGH / CRITICAL
       ▼
Layer 2 — Pre-Input Guidance Engine
       │  Renders contextual checklist of what to sanitize before pasting
       ▼
Layer 3 — Sensitive Data Scanner
       │  Pattern-matches against 10 sensitive data types
       │  Blocks request if match found — input never reaches Gemini
       ▼
Layer 4 — ADK Structural Decomposition
       │  Tool 1: Language and pattern detector
       │  Tool 2: Complexity signal extractor
       │  Tool 3: Risk surface analyzer
       ▼
Layer 5 — Gemini 2.5 Flash Reasoning Engine
       │  Receives sanitized code + structural decomposition
       │  Produces structured explanation in JSON mode
       ▼
Layer 6 — Output Validation + Response
          Pydantic schema enforced on every response
          Returns: purpose, behavior, risk surface, documentation, manager questions
```

---

## Key Features

**Safety Pipeline**
- Blocks AWS keys, Stripe keys, GCP service account keys, database connection strings, JWT tokens, bearer tokens, hardcoded passwords, and internal IP addresses before they reach the AI
- Contextual pre-input checklist shown based on question type before the developer pastes any code
- Input is never forwarded to Gemini if a sensitive pattern is detected

**Structured Code Explanation**
- Purpose: what business problem the code solves
- Behavior: step-by-step execution walkthrough
- Intent reconstruction: why it was written this way
- Inputs and outputs: typed, described
- Dependencies: what it calls, what calls it
- Edge cases: what it handles silently
- Risk surface: exactly what is dangerous to change and why
- Suggested documentation block: ready to paste into the codebase
- Questions for manager: what to ask the tech lead before modifying

**Question Classification**

| Question Type        | Risk Level     |
|----------------------|----------------|
| Function logic.      | Low            |
| Workflow / flow      | Low            |
| File dependencies.   | Medium         |
| Error debugging      | Medium         |
| API integration      | High           |
| Database query       | High           |
| Config / environment | Critical       |

---

## API Endpoints

| Method | Path         | Description                            |
|--------|--------------|----------------------------------------|
| GET    | `/`          | Chat interface                         |
| POST   | `/analyze`   | Full analysis pipeline                 |
| POST   | `/preflight` | Safety checklist before code is pasted |
| GET    | `/demo`      | Pre-run example output                 |
| GET    | `/health`.   | Service health check                   |
| GET    | `/docs`      | Swagger UI                             |

### Example Request

```bash
curl -X POST https://your-service-url.run.app/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why does this function sometimes return None instead of raising?",
    "code": "def sync_payments(client_id):\n    try:\n        ...\n    except Exception:\n        return None",
    "context": "Nightly billing reconciliation module"
  }'
```

---

## Tech Stack

| Layer              | Technology                         |
|--------------------|------------------------------------|
| AI Agent Framework | Google Agent Development Kit (ADK) |
| Language Model     | Gemini 2.5 Flash                   |
| API Framework      | FastAPI                            |
| Schema Validation  | Pydantic v2                        |
| Secret Management  | Google Cloud Secret Manager        |
| Deployment         | Google Cloud Run                   |
| Containerization   | Docker (python:3.11-slim)          |
| Language           | Python 3.11                        |

---

## Run Locally

**Prerequisites:** Python 3.11, a Gemini API key from [Google AI Studio](https://aistudio.google.com)

```bash
# Clone the repository
git clone https://github.com/your-username/safecode-navigator-ai.git
cd safecode-navigator-ai

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
echo "GEMINI_API_KEY=your_key_here" > .env

# Start the server
uvicorn main:app --reload --port 8080
```

Open `http://localhost:8080` in your browser.

---

## Deploy to Cloud Run

```bash
# Authenticate and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Store API key in Secret Manager
echo -n "your_key_here" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy
gcloud run deploy safecode-navigator-ai \
  --source . \
  --region asia-south1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest"
```

---

## Project Structure

```
safecode-navigator-ai/
├── main.py          # FastAPI app, routes, embedded chat UI
├── agent.py         # ADK agent definition, pipeline orchestration
├── scanner.py       # Sensitive data scanner, question classifier
├── schemas.py       # Pydantic request/response schemas
├── requirements.txt
├── Dockerfile
└── .env             # GEMINI_API_KEY (not committed)
```

---

## Sensitive Data Patterns Detected

| Pattern                    | Example Match                  |
|----------------------------|--------------------------------|
| AWS Access Key             | `AKIA...`                      |
| Stripe Live Key            | `sk_live_...`                  |
| Stripe Test Key            | `sk_test_...`                  |
| GCP Service Account Key    | `"private_key": "-----BEGIN`   |
| Database Connection String | `postgres://user:pass@host/db` |
| JWT Token                  | `eyJ...`                       |
| Bearer Token               | `Bearer abc123...`             |
| Hardcoded Password         | `password = "..."`             |
| Generic API Key Assignment | `api_key = "..."`              |
| Internal IP Address        | `192.168.x.x`, `10.x.x.x`      |

---

## Program

Built as a track -1 project for the **Google Cloud GenAI Academy APAC Edition**
Track 1: Build and Deploy AI Agents using Gemini, ADK, and Cloud Run.

---

## Author

Anuja Sakulkar
