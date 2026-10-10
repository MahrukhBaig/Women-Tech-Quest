# WTQ Build Track: Utility Bill Decoder

An AI-powered assistant designed for the **Women Tech Quest (WTQ) Build Track Competition** that reads Pakistani electricity bills (K-Electric, LESCO, IESCO; scans, photos, screenshots; tilted, partially in Urdu; personal details occluded by grey boxes) and:
- **Level 1**: Extracts non-identifying billing details, readings, charges, taxes, and payable amounts into a validated JSON object conforming strictly to the competition schema.
- **Level 2**: Explains customer queries in plain English, citing exact printed PKR values, with deterministic statistical calculations (averages, counts, differences, percentages) precomputed in Python.

---

## 1. System Requirements & Runtime

- **Python Version**: Python 3.11+ (Tested and verified on Python 3.14)
- **Dependencies**: Pinned exactly in `requirements.txt` (`package==x.y.z`)
- **Allowed LLM**: Google `gemini-3.5-flash-lite` (via official `google-genai` SDK)

---

## 2. Setup & Installation

1. **Clone or Extract the Project**:
   ```bash
   cd wtq-project
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Add your Google Gemini API key:
   ```env
   MODEL_PROVIDER=google
   MODEL_NAME=gemini-3.5-flash-lite
   API_KEY=your-api-key-here
   ```
   *(Note: `GEMINI_API_KEY` is also supported. Never commit `.env` to version control).*

---

## 3. Running the Solution

### A. CLI Pipeline (Primary Workflow)

To process a folder of bills and generate both required output CSV files:

```bash
python -m billdecoder.cli --bills-dir <path_to_bills> --level1-template <path_to_level1.csv> --level2-template <path_to_level2.csv> --output-dir output
```

**Example (processing the 10 test bills at 12:30 PM)**:
```bash
python -m billdecoder.cli --bills-dir test/bills --level1-template test/csv/level1.csv --level2-template test/csv/level2.csv --output-dir output
```

**Options**:
- `--bills-dir`: Directory containing bill images (`.png`, `.jpg`).
- `--level1-template`: Path to `level1.csv` template.
- `--level2-template`: Path to `level2.csv` template.
- `--output-dir`: Destination folder for output CSVs (default: `./output`).
- `--no-cache`: Force bypass of disk cache (by default, responses are cached on disk to protect API quotas).

### B. FastAPI Backend & Interactive UI

Start the local server:
```bash
uvicorn api:app --host 127.0.0.1 --port 8000
```
Open **`http://127.0.0.1:8000`** in your browser to access the web application:
- Drag-and-drop upload for PNG/JPEG bills.
- Instant overview cards (Provider, Month, Units, Payable amount, Due date).
- Itemized charges & taxes breakdown tables.
- Customer Q&A view with precomputed stats.
- Raw Level 1 JSON preview with copy button.
- Quick test chips for sample training bills (`KESC_0008`, `IESCO_0004`, `KESC_0004`, `LESCO_0005`, `LESCO_0006`).

### C. Running Tests

Run the complete test suite:
```bash
pytest tests/
```

---

## 4. Architecture

The system is organized around a unified core package (`billdecoder/`) shared by both CLI and API:

- **`billdecoder/image_prep.py`**:
  - Validates image magic bytes (`PNG`, `JPEG`) and enforces size caps (15 MB).
  - Automatically corrects phone photo EXIF rotation.
  - Converts to RGB and caps the long edge at 2048 px (never upscales or crops).
  - Applies mild contrast enhancement to make small table fonts legible.

- **`billdecoder/llm_client.py`**:
  - Gemini SDK client wrapping `gemini-3.5-flash-lite`.
  - Rate limiter: Global sliding window enforcing $\le 10$ requests/minute to safely respect free-tier quotas.
  - Retries: Exponential backoff with jitter on 429/5xx/ResourceExhausted errors.
  - Disk Caching: Responses cached by `(image_sha256, prompt_version, model)` to prevent duplicate API usage.
  - Usage Tracking: Thread-safe tracking of prompt, candidate, and total token counts.

- **`billdecoder/prompts.py`**:
  - Treats all bill text as untrusted data (prompt-injection boundaries).
  - Enforces schema, date formatting, and negative sign conventions.
  - Level 2 prompts incorporate precomputed statistics so the LLM never does arithmetic.

- **`billdecoder/calculator.py`**:
  - Deterministic Python calculator. Computes exact tax share percentage, monthly averages, max/min consumption, count and names of months exceeding 200 units, and difference vs average.

- **`billdecoder/postprocessing.py`**:
  - Normalizes numbers, dates (`YYYY-MM-DD`, `YYYY-MM`), and subsidies (enforces negative sign).
  - Executes multi-register rules (Rule A).
  - Runs reconciliation audits (sum of charges vs total_charges; total_charges + total_taxes vs current_bill) and emits structured warnings without modifying printed values.
  - PII sanitization ensuring zero CNIC patterns or consumer identifiers leak.

- **`billdecoder/csv_writer.py`**:
  - Preserves exact template row order, column names, and IDs using standard `csv` library.
  - Generates single-line Level 1 JSON with standard quotation-mark doubling (`""`).

- **`package_submission.py`**:
  - Validates outputs, runs live API key secret scanning, checks size $\le 15$ MB, and generates `wtq-submission.zip`.

---

## 5. Design Decisions (Rules A–D)

*(Note: These decided rules resolve ambiguous edge cases and are documented per competition specification; they were validated against the official golden bill `KESC_0008`)*:

- **Rule A (Multi-Register Bills)**:
  1. `units_consumed` is set to the printed billed-units figure (e.g. KE "Current Month ... units"). If none, the units of the first printed register row are used.
  2. For meter readings: If exactly one register row's `current - previous` equals `units_consumed` within 1, that row is used.
  3. Otherwise, if the energy/consumption registers (excluding "Import") sum to `units_consumed` within 1, the sum of their previous readings and sum of their current readings are used.
  4. Otherwise, the first printed register row is used.
  *(Example: In net-metering bill `KESC_0004`, Off-Peak 1163.29 $\to$ 1923.73 and Peak 402.35 $\to$ 542.85 sum to the billed 901 units; Import rows are excluded).*

- **Rule B (Subsidy Bills with No Itemised Charges, e.g. IESCO)**:
  - `charges`: Contains the printed subsidy as a negative `"subsidy"` entry, plus any printed FPA line as `"fpa"`.
  - `total_charges`: The printed "Total Electricity Charges" figure (gross, before subsidy).
  - Combined tax: Placed in `total_taxes` with `taxes = []`.

- **Rule C (Net-Metering Benefit / Outstanding Balance Lines)**:
  - Lines printed after the current-bill / grand-total area (e.g. KE "Net Metering Benefit", "Outstanding Balance") are excluded from Level 1 charges/taxes. They are incorporated into Level 2 answers when the question pertains to them.

- **Rule D (Level 1 Numbers Use Printed Values)**:
  - Numbers are extracted strictly as printed; missing values are set to `null` rather than inferred or estimated.

---

## 6. Known Limitations

- **Severely Blurry or Occluded Images**: If a section of the bill is heavily crumpled or obscured by grey boxes, the pipeline sets unavailable fields to `null` instead of guessing, as mandated by the scoring guide.
- **Truncated Historical Tables**: If a consumption history table is cut off at the edge of the bill image, only the visible months are extracted; unprinted months are never fabricated.

---

## 7. AI Usage Disclosure

In compliance with Section 3 and Section 7.4 of the Participant Guide:

- **Model Used**: `gemini-3.5-flash-lite`
- **SDK**: `google-genai` (version 2.29.0)
- **External Invoice / Receipt Extraction APIs**: None (no Azure Prebuilt Invoice, no AWS Textract, no Mindee).
- **AI Coding Tools Used**: Antigravity IDE (Google DeepMind) was used as the pair-programming assistant to author code and tests.
- **Other AI Chatbots / Services**: None.

---

## 8. Packaging & Submission

To build the verified submission ZIP:
```bash
python package_submission.py
```
This script:
1. Validates that `output/level1.csv` and `output/level2.csv` are present.
2. Scans every file for real API keys or credential patterns.
3. Packages source code, requirements, README, and CSVs into `wtq-submission.zip`.
4. Confirms the archive size is $\le 15$ MB.
