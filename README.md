# 🏥 NL2SQL Clinic Chatbot

> Ask plain-English questions about clinic data — no SQL required.  
> Built with **Vanna AI 2.0**, **FastAPI**, and **Ollama (Mistral)**.

---

## 📋 Project Overview

This project is a production-ready Natural Language to SQL (NL2SQL) system for a simulated clinic database. Users ask questions in plain English and receive structured results, generated SQL, and optional visualisation charts — all without writing a single line of SQL.

**Pipeline:**
```
User Question (English)
        │
        ▼
  FastAPI Backend   (/chat endpoint)
        │
        ▼
  SQL Validation    (SELECT only, no dangerous keywords)
        │
        ▼
   Vanna 2.0 Agent
   ├── OpenAILlmService   (Ollama/mistral — local, free, no API key)
   ├── RunSqlTool         (executes against clinic.db)
   ├── VisualizeDataTool  (generates Plotly charts)
   └── DemoAgentMemory    (learns from 15 pre-seeded Q&A pairs)
        │
        ▼
  Results + SQL + Chart → JSON response
```

---

## 🗂️ File Structure

```
project/
├── setup_database.py   # Creates clinic.db with schema + dummy data
├── vanna_setup.py      # Vanna 2.0 Agent initialisation
├── seed_memory.py      # Seeds 15 Q&A pairs into agent memory
├── main.py             # FastAPI application
├── requirements.txt    # All Python dependencies
├── .env.example        # Environment variable template
├── README.md           # This file
├── RESULTS.md          # Test results for 20 questions
└── clinic.db           # Generated SQLite database (after setup)
```

---

## ⚙️ Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10+ | Required |
| pip | Latest | `pip install --upgrade pip` |
| Ollama | Latest | [Download here](https://ollama.com) — runs locally, completely free |

---

## 🚀 Setup Instructions

### Step 1 — Clone / download the project

```bash
git clone https://github.com/<your-username>/nl2sql-clinic.git
cd nl2sql-clinic
```

### Step 2 — Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set up your LLM provider

This project supports **3 free LLM providers**. Set your choice in `.env`:

#### Option C — Ollama (default, local, NO API key)
```bash
# Install Ollama from https://ollama.com
ollama pull mistral          # one-time ~4 GB download
ollama serve                 # keep running in a separate terminal
```
In `.env`:
```
LLM_PROVIDER=ollama
```
> **No API key needed!** Ollama runs entirely on your local machine.

#### Option B — Groq (free cloud, needs key)
1. Sign up at [console.groq.com](https://console.groq.com)
2. Get a free API key
3. In `.env`:
```
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your-key-here
```

#### Option A — Google Gemini (free cloud, needs key)
1. Get a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. In `.env`:
```
LLM_PROVIDER=gemini
GOOGLE_API_KEY=AIzaSy...your-key-here
```

### Step 5 — Create the database

```bash
python setup_database.py
```

Expected output:
```
✅ Database created: clinic.db
   Patients      : 200
   Doctors       : 15  (across 5 specializations)
   Appointments  : 500 (varied statuses over last 12 months)
   Treatments    : 292 (linked to completed appointments)
   Invoices      : 200
```

### Step 6 — Seed the agent memory

```bash
python seed_memory.py
```

Expected output:
```
🌱 Seeding Vanna 2.0 agent memory …

  [01/15] Seeded: How many patients do we have?
  [02/15] Seeded: List all patients and their cities
  ...
  [15/15] Seeded: Top 5 patients by total spending

✅ Agent memory seeded with 15 Q&A pairs.
```

### Step 7 — Start the API server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at **http://localhost:8000**

---

## 📡 API Documentation

### `POST /chat`

Ask a natural language question about the clinic data.

**Request:**
```http
POST http://localhost:8000/chat
Content-Type: application/json

{
  "question": "Show me the top 5 patients by total spending"
}
```

**Response:**
```json
{
  "question": "Show me the top 5 patients by total spending",
  "message": "Here are the top 5 patients by total spending...",
  "sql_query": "SELECT p.first_name || ' ' || p.last_name AS patient, ROUND(SUM(i.total_amount), 2) AS total_spending FROM invoices i JOIN patients p ON p.id = i.patient_id GROUP BY p.id ORDER BY total_spending DESC LIMIT 5;",
  "columns": ["patient", "total_spending"],
  "rows": [
    ["Rahul Sharma", 4821.50],
    ["Priya Patel", 4310.00],
    ["Arjun Singh", 3987.75],
    ["Neha Gupta", 3654.20],
    ["Vikram Mehta", 3401.00]
  ],
  "row_count": 5,
  "chart": { "data": [...], "layout": {...} },
  "chart_type": "bar",
  "cached": false,
  "error": null
}
```

**Error response:**
```json
{
  "question": "...",
  "message": "I could not generate a SQL query for that question.",
  "error": "No SQL generated"
}
```

---

### `GET /health`

Check system status and memory diagnostics.

**Request:**
```http
GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "db_path": "clinic.db",
  "tables": "appointments, doctors, invoices, patients, treatments",
  "agent_memory_items": 15
}
```

---

### Interactive API Docs

FastAPI provides built-in Swagger UI:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 💬 Example Questions

Try these with the `/chat` endpoint:

```
How many patients do we have?
List all doctors and their specializations
Which doctor has the most appointments?
What is the total revenue?
Show revenue by doctor
Top 5 patients by spending
Average treatment cost by specialization
Which city has the most patients?
List patients who visited more than 3 times
Show unpaid invoices
What percentage of appointments are no-shows?
Show the busiest day of the week for appointments
Revenue trend by month
Show monthly appointment count for the past 6 months
Compare revenue between departments
```

---

## 🧪 Running the Test Suite

To test all 20 questions from the assignment:

```bash
# Start the server first (in a separate terminal)
uvicorn main:app --port 8000

# Then run the test script
python test_questions.py
```

Or test individual questions with curl:

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How many patients do we have?"}' | python -m json.tool
```

---

## 🏗️ Architecture Overview

### LLM Provider

**Ollama** (`mistral`) — chosen for:
- Completely free — runs locally, no API key needed
- No rate limits or billing
- Strong SQL generation capability
- Privacy — your data never leaves your machine

### Vanna 2.0 Components

| Component | Role |
|-----------|------|
| `OpenAILlmService` | Converts English → SQL via Ollama (local) or Groq (cloud) |
| `SqliteRunner` | Executes validated SQL against `clinic.db` |
| `RunSqlTool` | Wires the runner into the agent tool system |
| `VisualizeDataTool` | Generates Plotly charts for result sets |
| `DemoAgentMemory` | Stores & retrieves 15+ example Q→SQL pairs |
| `SaveQuestionToolArgsTool` | Saves new successful Q→SQL pairs at runtime |
| `SearchSavedCorrectToolUsesTool` | Retrieves past Q→SQL pairs for context |
| `SimpleUserResolver` | Maps all requests to a single default user |
| `Agent` | Orchestrates everything |

### Bonus Features Implemented

| Feature | Where |
|---------|-------|
| ✅ Chart Generation | `VisualizeDataTool` + `main.py` parser |
| ✅ Input Validation | `min_length=3`, `max_length=500` on `QuestionRequest` |
| ✅ Query Caching | `_CACHE` dict with 5-minute TTL in `main.py` |
| ✅ Rate Limiting | `slowapi` – 30 requests/minute per IP on `/chat` |
| ✅ Structured Logging | Python `logging` module throughout |
| ✅ SQL Validation | SELECT-only, blocked keyword list |

---

## 🗄️ Database Schema

```
patients (200 rows)
├── id, first_name, last_name, email, phone
├── date_of_birth, gender, city, registered_date

doctors (15 rows — 5 specializations)
├── id, name, specialization, department, phone

appointments (500 rows)
├── id, patient_id → patients.id
├── doctor_id → doctors.id
├── appointment_date, status, notes
└── status ∈ {Scheduled, Completed, Cancelled, No-Show}

treatments (≈290 rows — Completed appointments only)
├── id, appointment_id → appointments.id
├── treatment_name, cost (50–5000), duration_minutes

invoices (200 rows)
├── id, patient_id → patients.id
├── invoice_date, total_amount, paid_amount
└── status ∈ {Paid, Pending, Overdue}
```

---

## 🔒 Security Notes

- API keys are **never hardcoded** — loaded from `.env` via `python-dotenv`
- SQL validation rejects all non-SELECT statements before execution
- Blocked keywords prevent injection: `DROP`, `DELETE`, `EXEC`, `xp_`, etc.
- Rate limiting prevents abuse (30 req/min per IP)

---

## 🧑‍💻 LLM Provider: Ollama (Local, Free)

This project uses **Ollama** (Option C) with the **Mistral** model as the default LLM provider.
Switching between all 3 approved providers is done via `LLM_PROVIDER` in `.env` — no code changes needed.

```python
# vanna_setup.py — Ollama uses OpenAI-compatible endpoint
from vanna.integrations.openai import OpenAILlmService

# Option C — Ollama (default)
llm_service = OpenAILlmService(
    model="mistral",
    api_key="ollama",                       # placeholder, Ollama ignores it
    base_url="http://localhost:11434/v1",    # Ollama's OpenAI-compatible API
)

# Option B — Groq (set LLM_PROVIDER=groq and GROQ_API_KEY in .env)
# llm_service = OpenAILlmService(
#     model="llama-3.3-70b-versatile",
#     api_key=os.getenv("GROQ_API_KEY"),
#     base_url="https://api.groq.com/openai/v1",
# )

# Option A — Gemini (set LLM_PROVIDER=gemini and GOOGLE_API_KEY in .env)
# from vanna.integrations.google import GeminiLlmService
# llm_service = GeminiLlmService(
#     model="gemini-2.0-flash",
#     api_key=os.getenv("GOOGLE_API_KEY"),
#     temperature=0.2,
# )
```

---

## 📞 One-liner to run everything

```bash
ollama pull mistral && pip install -r requirements.txt && python setup_database.py && python seed_memory.py && uvicorn main:app --port 8000
```
