# FinEasy AI — AI-Assisted Indian Tax Compliance Platform (Educational Prototype)

> **IMPORTANT DISCLAIMER**:
> FinEasy AI is an **educational engineering prototype** created for demonstration and learning purposes. It uses **synthetic/demo taxpayer data** and a simulated **Mock Government API**. It is **NOT** connected to real government tax servers, does **NOT** use real PAN or Aadhaar credentials, and does **NOT** provide certified legal or tax advice. All calculation rules are simplified demo rules and must not be used for actual tax filing.

---

## 1. Overview

FinEasy AI is an educational platform designed to streamline and demystify the Indian Income Tax Return (ITR) filing workflow. Second-year engineering students often find financial and taxation logic daunting; FinEasy AI bridges the gap by pairing deterministic computation engines with multimodal AI assistance (Google Gemini), robust PostgreSQL schema design with Row-Level Security (Supabase), and clean FastAPI backend services.

While the long-term vision encompasses ITR, TDS, TCS, and GST compliance, **V1 focuses strictly on an Individual ITR filing workflow** using Form 16 PDF parsing.

---

## 2. Features

- **Automated Form 16 PDF Ingestion**: Extracts text using `pypdf`, validates file safety, size (max 10MB), and magic bytes.
- **AI Document Extraction**: Employs Google Gemini via the official `google-genai` SDK to extract employer details, gross salary, TDS, and financial year into validated Pydantic schemas, with built-in heuristic fallbacks for offline testing.
- **Deterministic Tax Engine**: Independent mathematical calculator implementing progressive slab computation, 4% Health and Education Cess, and Section 87A rebate without relying on LLMs for math.
- **Tax Data Validation**: Detects negative figures, financial year format anomalies (`YYYY-YY`), and deduction/TDS inconsistencies.
- **Natural Language Tax Explanation**: Generates plain-English summaries explaining how gross income and deductions translate into net tax payable or refund.
- **Chartered Accountant (CA) Review Workflow**: Role-Based Access Control (RBAC) allowing CA accounts to review, approve, reject, or request revisions on taxpayer filings.
- **Mock Government API**: A dedicated secondary FastAPI service (`:8001`) simulating the Income Tax Department e-Filing portal, prefill data (Form 26AS/AIS), rule validation, and synthetic `ITR-V` acknowledgement generation.
- **Audit Logging**: Secure ledger tracking every critical lifecycle state change while stripping sensitive credentials.
- **Row-Level Security (RLS)**: Database policies isolating individual taxpayer data, while granting appropriate review privileges to CAs and Admins.

---

## 3. Architecture

```
Frontend (Streamlit / Web UI)
            │
            ▼
FastAPI Backend (:8000)
 ├── Authentication & RBAC (Supabase Auth / Bearer Token)
 ├── REST Routes (/api/filings, /api/documents, /api/tax, /api/ai, /api/reviews)
 ├── Services Layer (Business Logic, Validation, & State Transitions)
 ├── AI Document Extractor (google-genai SDK + PyPDF)
 ├── Deterministic Tax Engine (Rules, Calculator, Validator)
 └── Supabase Database Layer (PostgreSQL with RLS & Audit Logs)
            │
            ▼
Mock Government API (:8001)
 ├── Simulated Auth (/mock/auth/login)
 ├── Simulated AIS/26AS Prefill (/mock/prefill/{user_id})
 ├── Schema & Rule Validation (/mock/validate)
 └── Simulated CPC Submission (/mock/submit)
```

### State Machine Workflow

```
draft ──► document_uploaded ──► analysing ──► analysed ──► calculation_complete ──► validation_pending ──► ca_review ──► approved ──► submitted
                                                                                                │              ▲
                                                                                                └──► changes_requested ──┘
                                                                                                │
                                                                                                └──► rejected
```

---

## 4. Tech Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI, Starlette
- **Server**: Uvicorn
- **Data Validation & Schemas**: Pydantic v2, Pydantic-Settings
- **Database & Auth**: Supabase PostgreSQL, Supabase Python Client
- **AI SDK**: Google GenAI (`google-genai`)
- **Document Processing**: PyPDF
- **Data & Utilities**: Pandas, python-dotenv, HTTPX
- **Testing**: pytest, pytest-asyncio

---

## 5. Project Structure

```
FinEasyAI/
├── backend/
│   ├── main.py                     # Main FastAPI application & exception handlers
│   ├── config.py                   # Environment settings & configuration
│   ├── dependencies.py             # Auth & RBAC dependencies (individual, ca, admin)
│   │
│   ├── routes/                     # REST API route controllers
│   │   ├── auth.py                 # Registration & login
│   │   ├── users.py                # Profile management
│   │   ├── filings.py              # ITR filing CRUD & status
│   │   ├── documents.py            # Form 16 PDF upload & retrieval
│   │   ├── ai.py                   # Gemini extraction & explanations
│   │   ├── tax.py                  # Calculation & validation endpoints
│   │   ├── review.py               # CA review & approval endpoints
│   │   └── government.py           # Mock government client routes
│   │
│   ├── schemas/                    # Pydantic request/response models
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── filing.py
│   │   ├── document.py
│   │   ├── ai.py
│   │   ├── tax.py
│   │   └── review.py
│   │
│   ├── services/                   # Business logic layer
│   │   ├── auth_service.py
│   │   ├── filing_service.py
│   │   ├── document_service.py
│   │   ├── ai_service.py
│   │   ├── tax_service.py
│   │   ├── validation_service.py
│   │   ├── review_service.py
│   │   └── government_service.py
│   │
│   ├── database/                   # Database client & queries
│   │   ├── supabase.py             # Supabase client with offline mock store
│   │   └── queries.py              # Centralized SQL/PostgREST queries
│   │
│   ├── ai/                         # Gemini AI modules
│   │   ├── gemini_client.py        # google-genai singleton client
│   │   ├── prompts.py              # Strict extraction & explanation prompts
│   │   └── document_extractor.py   # Extraction logic with heuristic fallback
│   │
│   ├── tax_engine/                 # Pure deterministic tax engine
│   │   ├── rules.py                # Educational demo tax slabs & cess
│   │   ├── calculator.py           # Slabs, cess, rebate, & refund calculations
│   │   └── validator.py            # Bounds & financial year validation
│   │
│   ├── utils/                      # Shared helper utilities
│   │   ├── file_utils.py           # PDF magic bytes & security validation
│   │   ├── security.py             # JWT token parsing
│   │   └── response.py             # Standardized JSON response envelope
│   │
│   └── tests/                      # Automated pytest test suite
│       ├── conftest.py             # TestClient fixtures & mock DB reset
│       ├── test_health.py          # Root & health endpoints
│       ├── test_tax.py             # Deterministic tax engine calculations
│       ├── test_validation.py      # Input validation & sanity rules
│       └── test_filing.py          # End-to-end filing, upload, review, & mock flow
│
├── mock_government/                # Standalone Simulated Government API (:8001)
│   ├── main.py                     # Mock government FastAPI entrypoint
│   ├── routes/
│   │   ├── auth.py                 # Simulated portal login
│   │   ├── prefill.py              # Simulated Form 26AS/AIS prefill
│   │   ├── validation.py           # Simulated CPC validation
│   │   └── submission.py           # Simulated submission & acknowledgement
│   └── data/
│       └── demo_taxpayer.json      # Synthetic taxpayer database
│
├── sql/
│   └── schema.sql                  # Supabase PostgreSQL schema with RLS & audit tables
│
├── sample_data/
│   ├── generate_sample_pdf.py      # Standalone Form 16 PDF generator
│   └── demo_form16.pdf             # Generated test PDF
│
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── .gitignore                      # Git exclusion rules
└── README.md                       # Complete documentation
```

---

## 6. Setup & Installation

### Step 1: Clone or Navigate to Project Directory
```bash
cd FinEasyAI
```

### Step 2: Create and Activate Virtual Environment
```bash
# On Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# On Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```ini
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
GEMINI_API_KEY=your-gemini-api-key
MOCK_GOVERNMENT_URL=http://127.0.0.1:8001
ENVIRONMENT=development
PORT=8000
HOST=127.0.0.1
```

> **Note**: FinEasy AI features a **Zero-Crash Resiliency Engine**. If you do not yet have Supabase or Gemini API keys, the system automatically runs with an in-memory database mock and regex heuristic document extraction, enabling immediate local execution and automated testing!

---

## 7. Supabase & Database Setup

1. Log into your [Supabase Dashboard](https://supabase.com).
2. Create a new project.
3. In the left navigation, open the **SQL Editor**.
4. Copy the entire contents of `sql/schema.sql` and run it.
5. This creates the 7 core tables (`profiles`, `filings`, `documents`, `ai_analysis`, `tax_calculations`, `reviews`, `audit_logs`) and applies Row Level Security (RLS) policies.
6. Retrieve your **Project URL**, **anon key**, and **service_role key** from **Project Settings -> API** and paste them into `.env`.

---

## 8. Google Gemini Setup

1. Obtain a Gemini API Key from [Google AI Studio](https://aistudio.google.com/).
2. Add your key to `.env`:
   ```ini
   GEMINI_API_KEY=AIzaSy...
   ```
3. FinEasy AI uses the official `google-genai` SDK (`from google import genai`) with the `gemini-2.5-flash` model.

---

## 9. Running the Applications

FinEasy AI consists of two separate FastAPI servers:

### 1. Run the Main Backend (Port 8000)
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs will be available at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 2. Run the Mock Government API (Port 8001)
In a separate terminal:
```bash
uvicorn mock_government.main:app --host 127.0.0.1 --port 8001 --reload
```
Mock government API docs will be available at:
- **Swagger UI**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

---

## 10. Running Automated Tests

Run the full pytest suite:
```bash
pytest backend/tests -v
```

All 21 unit and integration tests run entirely offline with zero external network dependencies, testing:
1. Root `/` and `/health` endpoints
2. Deterministic tax engine (slabs, cess, Section 87A rebate, refund/payable)
3. Tax data validation (negative numbers, bounds, financial year formatting)
4. Filing lifecycle state machine transitions
5. Form 16 PDF upload, PyPDF text extraction, and AI analysis pipeline
6. CA review approval and revision workflow
7. Mock Government API validation and submission

---

## 11. Complete Demo Filing Workflow Walkthrough

Here is how a complete taxpayer journey executes end-to-end via the API:

```
1. Register Taxpayer:
   POST /api/auth/register
   Body: {"email": "taxpayer@demo.com", "password": "password123", "name": "Arjun Sharma", "user_type": "individual"}

2. Login:
   POST /api/auth/login
   Body: {"email": "taxpayer@demo.com", "password": "password123"}
   Returns: access_token (include as "Authorization: Bearer <token>" in subsequent requests)

3. Create Filing:
   POST /api/filings
   Body: {"financial_year": "2024-25", "filing_type": "ITR"}
   Status becomes: "draft"

4. Upload Form 16 PDF:
   POST /api/documents/upload
   Form data: filing_id=<UUID>, file=sample_data/demo_form16.pdf
   Extracts text using PyPDF; status becomes: "document_uploaded"

5. Trigger AI Analysis:
   POST /api/ai/analyse/{filing_id}
   Gemini extracts Employer Name, Gross Salary, TDS, and FY into structured JSON; status becomes: "analysed"

6. Compute Tax Deterministically:
   POST /api/tax/calculate/{filing_id}
   Calculates taxable income, progressive slab tax, 4% cess, and net refund/payable; status becomes: "calculation_complete"

7. Request Plain-English AI Explanation:
   POST /api/ai/explain/{filing_id}
   Returns natural language summary explaining the numbers.

8. Validate Filing:
   POST /api/tax/validate/{filing_id}
   Performs completeness and bounds check; status advances to: "ca_review"

9. CA Reviews and Approves:
   POST /api/reviews/{filing_id}/approve (using CA authorization token)
   Status becomes: "approved"

10. Submit to Mock Government API:
    POST /api/government/submit/{filing_id}
    Simulates CPC upload; returns official demo acknowledgement number: "FINDEMO-2026-XXXX"; status becomes: "submitted"
```

---

## 12. Security & Compliance Notes

1. **Synthetic Data Only**: Real Indian PANs, Aadhaar numbers, and bank account credentials must never be inputted into this educational prototype.
2. **AI Safety Rule**: The AI is strictly an **extraction and explanation assistant**. All tax calculations are performed by the deterministic Python tax engine (`tax_engine/calculator.py`). The AI is never permitted to calculate or alter tax liabilities.
3. **Defense Against Prompt Injection**: User documents are strictly sanitized and parsed with structured JSON output constraints.
4. **Row-Level Security (RLS)**: Direct Supabase access is protected using RLS policies ensuring individuals cannot access filings or documents belonging to other taxpayers.
5. **No Hardcoded Secrets**: Credentials are read strictly from environment variables.
6. **Audit Logs**: Every status transition and calculation is logged with timestamps and user IDs; credentials and passwords are strictly stripped before audit logging.

---

## 13. Roadmap & Future Extensibility

- **V1 (Current)**: Individual ITR filing workflow, Form 16 PDF ingestion, Gemini extraction, deterministic tax engine, CA review, and Mock Government API.
- **V2**: TDS & TCS reconciliation, salary slips & bank statement OCR, multi-reviewer CA firm dashboard.
- **V3**: GST compliance, GSTR-1 & GSTR-3B reconciliation, business accounts support, anomaly detection.
- **V4**: ERI (e-Return Intermediary) government API integration, DSC (Digital Signature Certificate) support, and production-grade security compliance.

---

## 14. License

Developed for academic demonstration and educational purposes. Distributed under the MIT License.
