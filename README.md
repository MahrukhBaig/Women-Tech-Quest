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

## 🏗️ System Architecture & Workflow

The solution operates through an end-to-end, 5-stage pipeline that strictly decouples visual data extraction from numerical reasoning to guarantee zero-hallucination accuracy:

### 1. Ingestion & Security Guardrails
- **Payload & Format Verification**: Enforces a strict $\le 15$ MB cap and inspects magic bytes directly (only `.png` and `.jpeg` accepted).
- **Computer Vision Pre-processing**: Auto-rotates orientation using EXIF orientation tags, normalizes color profiles to RGB, and caps dimensions at 2048 px on the longest edge without cropping.
- **Untrusted Content Isolation**: All bill text is isolated as untrusted data within strict system prompts to prevent prompt injection attempts.

### 2. Level 1: Schema-Validated Extraction
- **Multimodal Intelligence**: Uses `gemini-3.5-flash-lite` to extract non-identifying billing attributes conforming strictly to the competition Pydantic schema.
- **Post-Processing Normalization**: Cleans dates (`YYYY-MM-DD`, `YYYY-MM`), enforces negative signs on subsidy credits, and resolves multi-register net-metered arrays (Rule A).
- **PII Scrubbing**: Regex patterns sanitize and redact any inadvertent CNIC numbers or customer contact details.

### 3. Historical Consumption Extraction
- **12–13 Month Usage Tracking**: Extracts historical consumption from bar charts (KE) and historical tables (LESCO/IESCO) covering units consumed, bill amounts, and payments.

### 4. Deterministic Python Calculator
- **Zero-Hallucination Arithmetic**: The LLM is strictly prohibited from computing numbers. A pure Python calculation engine precomputes:
  - Exact tax share percentage and breakdown.
  - 12-month average monthly consumption and variance against current bill.
  - Exact count and names of months exceeding the 200-unit threshold.
  - Largest itemized charge and Fuel Price Adjustment (FPA) totals.
  - Late payment surcharge difference.

### 5. Level 2: Grounded Reasoning & Delivery
- **Grounded Q&A**: Answers customer queries using plain English, injecting precalculated facts and citing exact printed PKR values.
- **Delivery Outputs**: Writes standardized `output/level1.csv` and `output/level2.csv`, and streams live results to the interactive web application.

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

## 🎯 Design Decisions & Edge Case Protocols (Rules A–E)

| Rule | Name | Problem Solved | Resolution Protocol |
|:---:|---|---|---|
| **A** | **Multi-Register Bills** | Solar / Net-metered bills with Peak, Off-Peak, and Import registers | Sets `units_consumed` to the printed billed-units figure. Selects the register row matching `units_consumed` or sums consumption registers (excluding "Import"). |
| **B** | **Subsidy Bills** | Subsidies printed as offsets (e.g. IESCO/LESCO) | Enforces negative numbers on subsidies (`-3332.0`). Treats `total_charges` as gross electricity before subsidies. |
| **C** | **Post-Total Balance Lines** | Lines printed after grand total (e.g., "Net Metering Benefit") | Excluded from Level 1 charges to protect schema purity; cited in Level 2 Q&A when asked. |
| **D** | **Strict Printed Values** | Missing or obscured data points | Extracted strictly as printed; occluded/missing fields return `null` instead of speculative guesses. |
| **E** | **Totals-Only Charge Guard** | LESCO bills printing subtotals as pseudo-lines | Resets single non-subsidy line items equal to `total_charges` to `charges = []` to prevent double-counting. |

---

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
