<div align="center">

# ⚡ WTQ Build Track: Utility Bill Decoder

### *AI-Powered Document Intelligence & Grounded Reasoning for Pakistani Electricity Bills*

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-women--tech--quest.vercel.app-10b981?style=for-the-badge&logo=vercel)](https://women-tech-quest.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/Model-Gemini_3.5_Flash--Lite-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<br/>

**[🚀 Live Web Application](https://women-tech-quest.vercel.app/)** • **[📖 API Documentation](https://women-tech-quest.vercel.app/docs)** • **[📊 Health Check](https://women-tech-quest.vercel.app/health)**

---

</div>

## 📌 Executive Summary

The **WTQ Utility Bill Decoder** is a production-grade AI system developed for the **Women Tech Quest (WTQ) Build Track Competition**. It automatically parses, sanitizes, validates, and reasons over real-world Pakistani utility bills from **K-Electric (KE)**, **LESCO**, and **IESCO**.

The system is resilient against harsh real-world conditions: phone snapshots, angled & crumpled scans, mixed Urdu/English typography, multi-register solar net-metering arrays, and anonymized regions (grey boxes masking personal identifiable information).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             CORE CAPABILITIES                               │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 🏷️ Level 1: Structured Extraction    │ 💬 Level 2: Grounded Q&A             │
│ • Provider, Tariff & Sanctioned Load │ • Natural-English customer answers   │
│ • Meter readings & billed units      │ • Exact PKR line-item citations      │
│ • Itemized charges & taxes subtotal  │ • 100% deterministic Python math     │
│ • Arrears, Credits (CR) & Due Dates  │ • Zero hallucinated arithmetic       │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 🌐 Live Web Demo

The application is deployed on **Vercel** with continuous deployment from GitHub:

👉 **[https://women-tech-quest.vercel.app/](https://women-tech-quest.vercel.app/)**

### Interactive Dashboard Features:
- 📤 **Drag-and-Drop Uploader**: Accepts `.png` and `.jpeg` bill scans up to 15 MB.
- ⚡ **Preloaded Quick-Test Chips**: Instantly load and test real bills:
  - `KE Standard (KESC_0008)`
  - `IESCO Subsidy (IESCO_0004)`
  - `KE Net-Metered (KESC_0004)`
  - `LESCO High-Load (LESCO_0005)`
  - `LESCO Commercial (LESCO_0006)`
- 📊 **Level 1 Overview Cards**: High-level visual cards for bill month, units, payable amount, and due date.
- 🧾 **Itemized Charges & Tax Inspector**: Complete line-item tables with subsidy deductions and government levies.
- 💡 **Interactive Customer Q&A**: Real-time answers to the 5 competition questions + custom query input (`/api/ask`).
- 🔍 **Technical Data Inspector**: Schema-validated Level 1 JSON with one-click Copy and Download.
- 🌓 **Dark / Light Mode**: Seamless theme toggle with persistent preferences.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph INGESTION["1. Ingestion & Security Guardrails"]
        A[Bill Image File / Upload] --> B[Magic Bytes & Size Validation\nPNG/JPG <= 15MB]
        B --> C[EXIF Rotation & Contrast Normalization\nMax 2048px Long Edge]
    end

    subgraph LEVEL1["2. Level 1: Schema Extraction"]
        C --> D[Gemini 3.5 Flash-Lite\nStructured JSON Schema]
        D --> E[Post-Processing & Validation Engine]
        E -->|Rule A: Multi-Register| E1[Resolve Peak/Off-Peak Units]
        E -->|Rule E: Totals Guard| E2[Identify Non-KE Unitemized Subtotals]
        E -->|PII Sanitizer| E3[Strict CNIC & Phone Redaction]
    end

    subgraph STATS["3. Deterministic Python Calculator"]
        C --> F[History Table Extractor\n12-13 Months Usage]
        E --> G[compute_bill_stats()]
        F --> G
        G -->|Precomputed| H[• Tax Share %\n• Average Monthly Units\n• Months Above 200 Count\n• Largest Charge Item\n• Late Payment Penalty]
    end

    subgraph LEVEL2["4. Level 2: Grounded Reasoning"]
        H --> I[Grounded Prompt Builder\nUntrusted Data Isolation]
        I --> J[Gemini 3.5 Flash-Lite Q&A\nZero In-Model Math]
        J --> K[Level 2 Natural Language Answers]
    end

    subgraph OUTPUTS["5. Deliverables & Delivery"]
        E --> L[output/level1.csv]
        K --> M[output/level2.csv]
        E --> N[FastAPI Web App & UI]
        K --> N
    end

    style INGESTION fill:#f8fafc,stroke:#94a3b8
    style LEVEL1 fill:#eff6ff,stroke:#3b82f6
    style STATS fill:#f0fdf4,stroke:#22c55e
    style LEVEL2 fill:#faf5ff,stroke:#a855f7
    style OUTPUTS fill:#fffbeb,stroke:#f59e0b
```

---

## ⚙️ Core Modules Breakdown

| Module | File | Purpose |
|---|---|---|
| **API Backend** | [`api.py`](file:///c:/Projects/Women-Tech-Quest/api.py) | FastAPI service exposing `/api/decode`, `/api/ask`, `/health`, `/docs`, and static UI |
| **Image Prep** | [`billdecoder/image_prep.py`](file:///c:/Projects/Women-Tech-Quest/billdecoder/image_prep.py) | Validates magic bytes, auto-rotates EXIF, caps dimension at 2048px, gentle contrast tuning |
| **LLM Client** | [`billdecoder/llm_client.py`](file:///c:/Projects/Women-Tech-Quest/billdecoder/llm_client.py) | Rate limiting ($\le 10$ RPM), exponential backoff with jitter, token tracker, disk cache |
| **Prompts Engine** | [`billdecoder/prompts.py`](file:///c:/Projects/Women-Tech-Quest/billdecoder/prompts.py) | Security boundary against prompt injection, strict schema directives, versioned prompts |
| **Calculator** | [`billdecoder/calculator.py`](file:///c:/Projects/Women-Tech-Quest/billdecoder/calculator.py) | Deterministic math: tax percentages, history thresholds ($>200$), largest charge, late fees |
| **Post-Processing** | [`billdecoder/postprocessing.py`](file:///c:/Projects/Women-Tech-Quest/billdecoder/postprocessing.py) | Date formatting, subsidy negative signs, reconciliation cross-checks, CNIC sanitization |
| **History Extractor** | [`billdecoder/history_extractor.py`](file:///c:/Projects/Women-Tech-Quest/billdecoder/history_extractor.py) | Parses 12-13 month bar charts and tabular history for units, amounts, and payments |
| **CSV Writer** | [`billdecoder/csv_writer.py`](file:///c:/Projects/Women-Tech-Quest/billdecoder/csv_writer.py) | Conforms strictly to competition CSV output formats with double-quoted JSON strings |

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- **Python**: 3.11 or newer (compatible with 3.11, 3.12, 3.13, 3.14)
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey))

### 2. Setup Instructions

```bash
# 1. Clone the repository
git clone https://github.com/MahrukhBaig/Women-Tech-Quest.git
cd Women-Tech-Quest

# 2. Create and activate a virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your environment file
cp .env.example .env
```

Add your Google Gemini API key to `.env`:
```env
MODEL_PROVIDER=google
MODEL_NAME=gemini-3.5-flash-lite
API_KEY=your_gemini_api_key_here
```

---

## 💻 Running the Application

### Option A: Interactive Web UI (FastAPI)
```bash
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** to launch the visual decoder.

### Option B: Batch CLI Pipeline (Competition Evaluation)
To run the automated batch pipeline over a directory of bill images:
```bash
python -m billdecoder.cli \
  --bills-dir path/to/bills \
  --level1-template path/to/level1_template.csv \
  --level2-template path/to/level2_template.csv \
  --output-dir output
```

**Parameters:**
- `--bills-dir`: Folder containing `.png` / `.jpg` bills.
- `--level1-template`: Path to competition `level1.csv` template.
- `--level2-template`: Path to competition `level2.csv` template.
- `--output-dir`: Output directory for generated CSVs (default: `./output`).
- `--no-cache`: Optional flag to bypass disk caching.

---

## 🧪 Test Suite

Run the full automated test suite containing 19 test cases covering API contracts, deterministic calculations, normalization rules, security filters, and golden ground-truth bills:

```bash
python -m pytest tests/ -v
```

```text
tests/test_api.py ................. Passed [21%]
tests/test_calculator.py .......... Passed [26%]
tests/test_csv.py ................. Passed [31%]
tests/test_current_bill_regression.py  Passed [42%]
tests/test_golden_kesc0008.py ..... Passed [47%]
tests/test_mock_pipeline.py ....... Passed [52%]
tests/test_normalisation.py ....... Passed [84%]
tests/test_schema.py .............. Passed [94%]
tests/test_security.py ............ Passed [100%]

======================== 19 passed in 2.01s ========================
```

---

## 🎯 Design Decisions & Edge Case Protocols (Rules A–E)

| Rule | Name | Problem Solved | Resolution Protocol |
|:---:|---|---|---|
| **A** | **Multi-Register Bills** | Solar / Net-metered bills with Peak, Off-Peak, and Import registers | Sets `units_consumed` to the printed billed-units figure. Selects the register row matching `units_consumed` or sums consumption registers (excluding "Import"). |
| **B** | **Subsidy Bills** | Subsidies printed as offsets (e.g. IESCO/LESCO) | Enforces negative numbers on subsidies (`-3332.0`). Treats `total_charges` as gross electricity before subsidies. |
| **C** | **Post-Total Balance Lines** | Lines printed after grand total (e.g., "Net Metering Benefit") | Excluded from Level 1 charges to protect schema purity; cited in Level 2 Q&A when asked. |
| **D** | **Strict Printed Values** | Missing or obscured data points | Extracted strictly as printed; occluded/missing fields return `null` instead of speculative guesses. |
| **E** | **Totals-Only Charge Guard** | LESCO bills printing subtotals as pseudo-lines | Resets single non-subsidy line items equal to `total_charges` to `charges = []` to prevent double-counting. |

---

## 📦 Packaging & Submission Verification

Generate the verified, scanned submission package within the 15 MB limit:

```bash
python package_submission.py
```

This verification script:
1. Validates the existence and formatting of `output/level1.csv` and `output/level2.csv`.
2. Performs automated secret scanning against live API keys and credential regex patterns.
3. Packages source code, configuration, tests, and outputs into `wtq-submission.zip`.
4. Enforces the strict $\le 15$ MB package constraint.

---

## 📜 AI Usage & Participant Guide Compliance

In accordance with **Section 3** and **Section 7.4** of the WTQ Participant Guide:

| Item | Details |
|---|---|
| **Model Employed** | `gemini-3.5-flash-lite` (Official Google GenAI SDK `google-genai`) |
| **Zero Prohibited APIs** | No closed black-box invoice extraction APIs (Azure Prebuilt Invoice, AWS Textract AnalyzeExpense, Mindee) were used. |
| **Prompt Injection Defense** | All image text is tagged as untrusted context; prompt boundaries isolate instructions. |
| **Privacy & PII Protection** | Zero retention of uploaded images in persistent storage; regex scrubbing of CNIC and phone numbers. |
| **Assisting Tooling** | Antigravity IDE (Google DeepMind) used for interactive pair-programming and test validation. |

---

<div align="center">

Made with 💜 for **Women Tech Quest (WTQ) Build Track**

**[🌐 Visit Live App](https://women-tech-quest.vercel.app/)**

</div>
