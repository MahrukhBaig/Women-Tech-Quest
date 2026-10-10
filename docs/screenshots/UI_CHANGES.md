# WTQ Utility Bill Decoder — UI Polish & Presentation Report

**Date**: 2026-10-10  
**Model**: `gemini-3.5-flash-lite`  
**Compliance**: Strict single-model, zero external CDNs, plain text rendering, zero PII.

---

## 1. Summary of Changes Made in the UI Fix Pass

### A. Correctness & Deterministic Trust
1. **Accurate Tax & Energy Share Percentages**:
   - Denominator calculated from `current_bill` (fallback: `total_charges + total_taxes`).
   - For `LESCO_0005`, taxes correctly calculate to **16.20%** (`PKR 3,358.23 / PKR 20,726.00`).
   - Energy charges calculate to **83.80%**, summing cleanly to 100.0%.
   - When breakdown cannot be mathematically calculated, displays `"cannot be determined"` rather than an inaccurate fallback.

2. **Calibrated Badges & Explanations**:
   - Removed the generic static `"Grounded in bill"` badge.
   - Added dynamic `✓ Calculated` badge strictly for precomputed arithmetic (percentages, seasonal differences, monthly averages).
   - Added `Not found on bill` badge when data was absent or unreadable.
   - For bills with no history rows, explicitly states that history could not be read, avoiding misleading `"0 months"` claims.

3. **In-Memory Privacy Guarantee**:
   - Enabled `force_no_cache=True` for API and web UI uploads so user uploads are processed strictly in memory and never written to disk cache.
   - Confirmed header privacy notice: `"Bills are processed in memory and are not stored."`

4. **Empty State Clarity**:
   - Updated introductory empty state prompt to: *"Select a bill image or test sample to view extracted details, precomputed stats, and customer explanations."*

---

### B. Display & Visual Formatting
5. **12-Month Usage History Chart Scaling & Month Labels**:
   - **Month Truncation Fixed**: Replaced slice indexing with full month abbreviation formatter (`JUL 25`, `AUG 25`, `JAN 26`).
   - **Negative Values & Zero Baseline**: Calculates SVG bounds from `minVal` (down to `-1955`) to `maxVal`, drawing a dashed zero baseline. Negative adjustment bars extend downwards in red (`var(--accent-danger)`), and positive consumption bars extend upwards in blue/yellow (`var(--accent-info)` / `var(--accent-warning)`).
   - **No Collisions**: Value labels sit strictly outside bars, and month labels are anchored cleanly at the bottom margin.

6. **Neutral Credit & Null Formatting**:
   - **Negative Payable (Credits)**: Negative amounts format in neutral theme text: `Credit: PKR 54,770.00 (nothing to pay)` (avoiding confusing bright green styling).
   - **Null / Not Applicable Payable**: Displays `"Not to be paid"` or `"Not on bill"` without an orphaned `PKR` prefix.
   - **Due Date Chips**: Hidden for historical sample bills to avoid false `"days overdue"` alerts.

7. **Standardized Currency Formatting & Plain English Labels**:
   - All monetary values are formatted with thousands separators and two decimals (e.g. `PKR 20,726.00`, `PKR 3,430.24`).
   - Charges table: *Energy charges, Fixed charges, Fuel price adjustment (FPA), Quarterly tariff adjustment (QTA), Surcharges & financing cost, Meter rent, Government relief subsidy*.
   - Taxes table: *Sales tax (GST), Electricity duty, Income tax, Municipal tax, Other government duty/tax*.

---

### C. Level 2 Q&A & Interactivity
8. **Full Question Text & Free-Text Ask Box**:
   - Every answer bubble displays the complete, readable question above the customer explanation.
   - Added an interactive custom question input box allowing users to ask natural questions (e.g. *"What is the due date?"*, *"How much is tax?"*).

---

### D. Layout & Navigation Polish
9. **Click-to-Enlarge Modal**:
   - Clicking the bill image preview opens a centered, responsive image lightbox modal with close button, backdrop click dismissal, and `Escape` key handling.

10. **Renamed Navigation Tabs**:
    - **"Bill details"**: Summary hero card, proportion bar, itemized charges/taxes tables, and usage history chart.
    - **"Ask about your bill"**: Full-question explanation bubbles, custom query input, and quick suggestion chips.
    - **"Technical data (JSON)"**: Formatted Level 1 JSON with Copy/Download buttons, and collapsed **System Diagnostics & Reconciliation Notices** accordion.
    - **"Run all bills (CLI)"**: Dual PowerShell and Bash command blocks with one-click **Copy** buttons.

11. **Sample Bill Selectors**:
    - Descriptive chip names: `KE Standard (KESC_0008)`, `IESCO Subsidy (IESCO_0004)`, `KE Net-Metered (KESC_0004)`, `LESCO High-Load (LESCO_0005)`, `LESCO Commercial (LESCO_0006)`.
    - Automatically hide if a sample file is absent.

12. **WCAG AA Contrast & Responsive Polish**:
    - Enhanced text contrast in dark and light modes.
    - Fully responsive across desktop and mobile viewports.
    - Clean console output with zero JavaScript warnings or errors.
