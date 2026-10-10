# WTQ Utility Bill Decoder: 3-Minute Demo Recording Script

This script walks through recording the optional 5-point bonus demo video (`demo/demo.mp4`, `.mov`, or `.webm`).

> **Recording Tip**: Use Windows Snipping Tool (`Win + Shift + R`), select a 720p region (1280x720) around the browser and terminal window, and save as `demo/demo.mp4`. Ensure the recording stays **under 10 MB** so the final ZIP remains comfortably within the **15 MB total competition limit**.

---

### Step 1: Start the Solution (0:00 – 0:30)
1. Open PowerShell in `wtq-project`:
   ```powershell
   & .venv\Scripts\uvicorn api:app --host 127.0.0.1 --port 8000
   ```
2. Open your web browser to `http://127.0.0.1:8000`.
3. Highlight on screen:
   - Header with **"Utility Bill Decoder"** and privacy notice (*"Bills are processed in memory and are not stored"*).
   - Live model badge: **`gemini-3.5-flash-lite`**.
   - Dark/light theme toggle.

---

### Step 2: Select / Upload a Bill Image (0:30 – 1:00)
1. In the left panel, click the quick sample chip: **`KESC_0008 (Golden)`** (or drag & drop `train/bills/KESC_0008.png`).
2. Show the bill image clearly in the preview box (anonymized grey boxes visible).
3. Click the primary action button: **`Decode Bill`**.
4. Show the 3-step progress indicator (*Reading &rarr; Extracting &rarr; Answers*).

---

### Step 3: Demonstrate Extracted Level 1 Fields (1:00 – 1:45)
Show the populated Overview tab:
1. **Hero Summary Card**:
   - Provider: **KE**
   - Tariff: **A1-R**
   - Month: **2026-04**
   - Units Billed: **151 kWh**
   - Payable by Due Date: **PKR 3,430**
   - Due Date: **2026-04-21** (with days-left indicator)
   - Payable After Due Date: **PKR 3,716**
2. **Proportion Bar Chart**:
   - Precomputed tax share: **16.61%** vs energy charges: **83.39%**.
3. **Itemized Charges Table**:
   - Fixed charges (PKR 900.00), Energy lines (PKR 1,054.00, PKR 663.51), QTA (PKR 52.91), FPA (PKR 125.27), Surcharge (PKR 64.93). Total: **PKR 2,860.62**.
4. **Itemized Taxes Table**:
   - ED (PKR 29.41), GST (PKR 520.21), MUCT/KMC (PKR 20.00). Total: **PKR 569.62**.

---

### Step 4: Level 2 Customer Answers (1:45 – 2:20)
1. Click the **"Ask Questions (Level 2)"** tab.
2. Show the grounded, plain-English answers citing exact PKR figures:
   - **Q1 (Taxes)**: Shows exact PKR 569.62 (16.61%) with the **`✓ Calculated`** tag.
   - **Q2 (History > 200 units)**: Shows historical count grounded in the billing history.
   - **Q4 (Largest charge)**: Points out the primary energy charge (PKR 1,054.00).
   - **Q5 (Due date & payable)**: Clearly answers due date 2026-04-21 and payable PKR 3,430.
3. Click the **"Level 1 JSON & Diagnostics"** tab and briefly show the clean, structured single-line JSON with the Copy button.

---

### Step 5: Command-Line Generation of Scored CSVs (2:20 – 3:00)
1. Switch to PowerShell terminal window.
2. Execute the CLI command for the test dataset:
   ```powershell
   & .venv\Scripts\python -m billdecoder.cli --bills-dir test\bills --level1-template test\csv\level1.csv --level2-template test\csv\level2.csv --output-dir output
   ```
3. Show the run summary on terminal screen:
   - Total Bills Processed: **10**
   - Level 1 Rows Written: **10**
   - Level 2 Rows Written: **120**
   - Fallbacks: **0**
   - Validation: **[SUCCESS] Output CSVs passed all validation self-checks.**
4. Conclude the video by running the packaging verification script:
   ```powershell
   & .venv\Scripts\python package_submission.py
   ```
   Show `wtq-submission.zip` generated, 0 secrets detected, and archive size $\le 15$ MB.
