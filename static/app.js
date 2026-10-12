// WTQ Utility Bill Decoder - Frontend Client
// Strict Security: textContent only (no innerHTML for untrusted data), no external CDNs

document.addEventListener("DOMContentLoaded", () => {
  // Theme Management
  const themeToggle = document.getElementById("theme-toggle");
  const iconSun = document.getElementById("theme-icon-sun");
  const iconMoon = document.getElementById("theme-icon-moon");
  const htmlRoot = document.documentElement;

  function applyTheme(theme) {
    htmlRoot.setAttribute("data-theme", theme);
    localStorage.setItem("wtq_theme", theme);
    if (theme === "light") {
      iconSun.style.display = "none";
      iconMoon.style.display = "block";
    } else {
      iconSun.style.display = "block";
      iconMoon.style.display = "none";
    }
  }

  const savedTheme = localStorage.getItem("wtq_theme") ||
    (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  applyTheme(savedTheme);

  themeToggle.addEventListener("click", () => {
    const current = htmlRoot.getAttribute("data-theme") || "dark";
    applyTheme(current === "dark" ? "light" : "dark");
  });

  // DOM Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const dropzoneEmpty = document.getElementById("dropzone-empty");
  const previewBox = document.getElementById("preview-box");
  const previewImg = document.getElementById("bill-preview-img");
  const previewClickableContainer = document.getElementById("preview-clickable-container");
  const previewLabel = document.getElementById("preview-file-label");
  const btnChangeFile = document.getElementById("btn-change-file");
  const btnDecode = document.getElementById("btn-decode");
  const btnDecodeText = document.getElementById("btn-decode-text");
  const progressContainer = document.getElementById("progress-container");
  const progressDetail = document.getElementById("progress-detail-text");
  const btnCancel = document.getElementById("btn-cancel");
  const alertBanner = document.getElementById("alert-banner");
  const alertMsg = document.getElementById("alert-message");
  const btnRetry = document.getElementById("btn-retry");

  const emptyState = document.getElementById("empty-state");
  const resultsWrapper = document.getElementById("results-wrapper");
  const tabButtons = document.querySelectorAll(".tab-item");
  const tabViews = document.querySelectorAll(".tab-view");
  const sampleChips = document.querySelectorAll(".chip");
  const questionChips = document.querySelectorAll(".chip-q");

  // Modal Elements
  const imageModal = document.getElementById("image-modal");
  const modalImg = document.getElementById("modal-img");
  const modalBackdrop = document.getElementById("modal-backdrop");
  const btnCloseModal = document.getElementById("btn-close-modal");

  // Custom Ask Box
  const inputCustomQ = document.getElementById("input-custom-q");
  const btnAskCustom = document.getElementById("btn-ask-custom");

  // State
  let selectedFile = null;
  let activeAbortController = null;
  let lastDecodedPayload = null;
  let isSampleBill = false;

  // Type Mappings for Plain English display
  const CHARGE_LABELS = {
    energy: "Energy charges",
    fixed: "Fixed charges",
    fpa: "Fuel price adjustment (FPA)",
    quarterly_adjustment: "Quarterly tariff adjustment (QTA)",
    surcharge: "Surcharges & financing cost",
    meter_rent: "Meter rent",
    subsidy: "Government relief subsidy",
    other: "Other electricity charge",
  };

  const TAX_LABELS = {
    gst: "Sales tax (GST)",
    electricity_duty: "Electricity duty",
    income_tax: "Income tax",
    municipal_tax: "Municipal tax",
    other_tax: "Other government duty/tax",
  };

  const STANDARD_QUESTIONS = {
    Q1: "Is this a net-metered (solar) connection or a standard connection? How did you tell?",
    Q2: "Which month in the last 12 months had the highest units consumed?",
    Q3: "How much fuel adjustment am I being charged (shown as FPA or FCA on the bill), and for which month?",
    Q4: "If I don't pay on time, what late payment surcharges will be added?",
    Q5: "Am I consuming more units than in the same month last year?",
    Q6: "What are my average monthly units consumed, and how does this month compare?",
    Q7: "How many more units do I consume in summer (June-August) than in winter (December-February)?",
    Q8: "Looking at the payments for the 12 months shown on the bill, have I been paying every bill?",
    Q9: "Have my units consumed gone up or down over the last 3 months?",
    Q10: "Based on the 12 months trend, how many units should I expect to consume next month?",
    Q11: "If I wanted to spread my electricity cost evenly across the year, how much should I set aside each month?",
    Q12: "If I consume the same units as last month, what would my bill be roughly?",
    Q_above200: "In how many months in the billing history did my consumption go above 200 units?",
    Q_tax_pct: "What percentage of my current bill goes toward taxes and government charges?",
    Q_largest: "What is the single largest charge on my bill?",
    Q_due: "When is the due date for this bill and how much should I pay?",
  };

  // Image Modal Handler
  if (previewClickableContainer) {
    previewClickableContainer.addEventListener("click", () => {
      if (previewImg.src) {
        modalImg.src = previewImg.src;
        imageModal.style.display = "flex";
      }
    });
  }

  function closeModal() {
    imageModal.style.display = "none";
    modalImg.src = "";
  }

  if (btnCloseModal) btnCloseModal.addEventListener("click", closeModal);
  if (modalBackdrop) modalBackdrop.addEventListener("click", closeModal);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && imageModal.style.display === "flex") {
      closeModal();
    }
  });

  // Drag and Drop
  ["dragenter", "dragover"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      isSampleBill = false;
      processSelectedFile(e.dataTransfer.files[0]);
    }
  });

  dropzone.addEventListener("click", (e) => {
    if (e.target !== btnChangeFile && !previewBox.contains(e.target)) {
      fileInput.click();
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      isSampleBill = false;
      processSelectedFile(e.target.files[0]);
    }
  });

  btnChangeFile.addEventListener("click", (e) => {
    e.stopPropagation();
    resetUploadState();
    fileInput.click();
  });

  function resetUploadState() {
    selectedFile = null;
    isSampleBill = false;
    fileInput.value = "";
    previewImg.src = "";
    previewBox.style.display = "none";
    dropzoneEmpty.style.display = "flex";
    btnDecode.disabled = true;
    hideAlert();
  }

  function processSelectedFile(file) {
    hideAlert();
    if (!file.type.match("image/png") && !file.type.match("image/jpeg")) {
      showAlert("Invalid format. Only PNG and JPEG bill images are supported.");
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      showAlert("File exceeds the 15 MB size limit.");
      return;
    }

    selectedFile = file;
    previewLabel.textContent = "Bill Image (" + (file.size / 1024).toFixed(0) + " KB)";

    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      dropzoneEmpty.style.display = "none";
      previewBox.style.display = "flex";
      btnDecode.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  // Sample Chips
  sampleChips.forEach(chip => {
    chip.addEventListener("click", async () => {
      const sampleFile = chip.getAttribute("data-sample");
      showAlert("Loading sample bill...", false);
      try {
        const resp = await fetch("/sample-bills/" + sampleFile);
        if (!resp.ok) {
          chip.style.display = "none";
          throw new Error("Sample file not available.");
        }
        const blob = await resp.blob();
        const file = new File([blob], sampleFile, { type: blob.type || "image/png" });
        isSampleBill = true;
        processSelectedFile(file);
      } catch (err) {
        showAlert("Sample note: " + err.message, false);
      }
    });
  });

  // Navigation Tabs
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      tabButtons.forEach(b => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      tabViews.forEach(v => v.classList.remove("active"));
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      const targetView = document.getElementById(targetId);
      if (targetView) targetView.classList.add("active");
    });
  });

  function showAlert(msg, isError = true) {
    alertMsg.textContent = msg;
    alertBanner.style.display = "flex";
    alertBanner.style.borderColor = isError ? "var(--accent-danger)" : "var(--accent-info)";
  }

  function hideAlert() {
    alertBanner.style.display = "none";
  }

  btnRetry.addEventListener("click", () => {
    hideAlert();
    if (selectedFile) {
      btnDecode.click();
    }
  });

  // Step Progress Management
  function setProgressStep(stepNum, labelText) {
    progressDetail.textContent = labelText;
    const step1 = document.getElementById("step-1");
    const step2 = document.getElementById("step-2");
    const step3 = document.getElementById("step-3");
    const line1 = document.getElementById("line-1");
    const line2 = document.getElementById("line-2");

    [step1, step2, step3].forEach(s => {
      s.classList.remove("active", "completed");
    });
    [line1, line2].forEach(l => l.classList.remove("active"));

    if (stepNum >= 1) step1.classList.add(stepNum === 1 ? "active" : "completed");
    if (stepNum >= 2) {
      line1.classList.add("active");
      step2.classList.add(stepNum === 2 ? "active" : "completed");
    }
    if (stepNum >= 3) {
      line2.classList.add("active");
      step3.classList.add("active");
    }
  }

  btnCancel.addEventListener("click", () => {
    if (activeAbortController) {
      activeAbortController.abort();
      activeAbortController = null;
      progressContainer.style.display = "none";
      btnDecode.disabled = false;
      btnDecodeText.textContent = "Decode Bill";
      showAlert("Decoding cancelled by user.", false);
    }
  });

  // Decode Action
  btnDecode.addEventListener("click", async () => {
    if (!selectedFile) return;

    hideAlert();
    btnDecode.disabled = true;
    btnDecodeText.textContent = "Decoding in progress...";
    progressContainer.style.display = "flex";
    setProgressStep(1, "Step 1: Reading bill image & validating magic bytes...");

    activeAbortController = new AbortController();
    const formData = new FormData();
    formData.append("file", selectedFile);

    const stepTimer = setTimeout(() => {
      setProgressStep(2, "Step 2: Extracting Level 1 fields with Gemini 3.5 Flash-Lite...");
    }, 1200);

    const stepTimer2 = setTimeout(() => {
      setProgressStep(3, "Step 3: Precomputing statistics & generating Level 2 answers...");
    }, 4500);

    try {
      const response = await fetch("/api/decode", {
        method: "POST",
        body: formData,
        signal: activeAbortController.signal,
      });

      clearTimeout(stepTimer);
      clearTimeout(stepTimer2);

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || "Server returned status " + response.status);
      }

      const data = await response.json();
      lastDecodedPayload = data;
      renderBillResults(data);
      progressContainer.style.display = "none";
    } catch (err) {
      clearTimeout(stepTimer);
      clearTimeout(stepTimer2);
      progressContainer.style.display = "none";
      if (err.name !== "AbortError") {
        showAlert("Error: " + err.message);
      }
    } finally {
      activeAbortController = null;
      btnDecode.disabled = false;
      btnDecodeText.textContent = "Decode Bill";
    }
  });

  // Render Result Logic
  function renderBillResults(payload) {
    const l1 = payload.level1 || {};
    const stats = payload.stats || {};
    const answers = payload.answers || {};
    const history = payload.history || [];
    const warnings = payload.warnings || [];

    emptyState.style.display = "none";
    resultsWrapper.style.display = "flex";

    // 1. Hero Summary Card
    const provBadge = document.getElementById("hero-provider-badge");
    provBadge.textContent = l1.provider || "N/A";

    const tariffLabel = document.getElementById("hero-tariff-label");
    tariffLabel.textContent = l1.tariff ? "Tariff: " + l1.tariff : "Tariff: Not on bill";

    const monthLabel = document.getElementById("hero-month-label");
    monthLabel.textContent = l1.bill_month ? "Month: " + l1.bill_month : "Month: Not on bill";

    const dueBadge = document.getElementById("hero-due-badge");
    dueBadge.textContent = l1.due_date ? "Due: " + l1.due_date : "Due: Not on bill";

    // Days left calculation - hide for historical sample bills
    const daysChip = document.getElementById("hero-days-left");
    if (!isSampleBill && l1.due_date) {
      const parts = l1.due_date.split("-");
      if (parts.length === 3) {
        const dueDateObj = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
        const today = new Date();
        const diffDays = Math.ceil((dueDateObj - today) / (1000 * 60 * 60 * 24));
        if (diffDays < 0) {
          daysChip.textContent = Math.abs(diffDays) + " days overdue";
          daysChip.className = "days-chip overdue";
          daysChip.style.display = "inline-block";
        } else if (diffDays === 0) {
          daysChip.textContent = "Due today";
          daysChip.className = "days-chip";
          daysChip.style.display = "inline-block";
        } else {
          daysChip.textContent = diffDays + " days left";
          daysChip.className = "days-chip";
          daysChip.style.display = "inline-block";
        }
      }
    } else {
      daysChip.style.display = "none";
    }

    // Hero amounts (handle negative credits and nulls)
    const payVal = document.getElementById("hero-payable-val");
    const payCurrency = document.getElementById("hero-payable-currency");
    const payNote = document.getElementById("hero-payable-note");
    if (l1.payable_within_due_date != null) {
      const pVal = Number(l1.payable_within_due_date);
      if (pVal < 0) {
        payCurrency.style.display = "none";
        payVal.className = "amount-huge amount-credit-neutral";
        payVal.textContent = "Credit: PKR " + Math.abs(pVal).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " (nothing to pay)";
        if (payNote) payNote.style.display = "none";
      } else {
        payCurrency.style.display = "inline";
        payVal.className = "amount-huge";
        payVal.textContent = pVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (payNote) {
          if (pVal === 0 && l1.current_bill && Number(l1.current_bill) > 0) {
            payNote.style.display = "block";
            payNote.textContent = "Current bill: PKR " + Number(l1.current_bill).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " (covered by solar/credit balance)";
          } else {
            payNote.style.display = "none";
          }
        }
      }
    } else {
      payCurrency.style.display = "none";
      payVal.className = "amount-huge";
      payVal.textContent = "Not on bill";
      if (payNote) payNote.style.display = "none";
    }

    const lateVal = document.getElementById("hero-late-val");
    const lateCurrency = document.getElementById("hero-late-currency");
    if (l1.payable_after_due_date != null) {
      const lVal = Number(l1.payable_after_due_date);
      lateCurrency.style.display = "inline";
      lateVal.textContent = lVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else {
      lateCurrency.style.display = "none";
      if (l1.payable_within_due_date != null && Number(l1.payable_within_due_date) <= 0) {
        lateVal.textContent = "Not to be paid";
      } else {
        lateVal.textContent = "Not on bill";
      }
    }

    const unitsVal = document.getElementById("hero-units-val");
    unitsVal.textContent = l1.units_consumed != null ?
      l1.units_consumed + " kWh" :
      "Not on bill";

    const readVal = document.getElementById("hero-readings-val");
    const prev = l1.previous_reading != null ? l1.previous_reading : "-";
    const curr = l1.current_reading != null ? l1.current_reading : "-";
    readVal.textContent = "Readings: " + prev + " → " + curr;

    // 2. Precomputed Tax / Energy Proportion Chart (SVG)
    const taxPill = document.getElementById("tax-share-pill");
    const chartWrap = document.getElementById("proportion-svg-wrapper");
    chartWrap.textContent = "";

    // Correct denominator: current_bill (fallback: total_charges + total_taxes)
    let denom = (l1.current_bill && l1.current_bill > 0) ? l1.current_bill : null;
    if (denom == null && l1.total_charges != null && l1.total_taxes != null) {
      const comb = l1.total_charges + l1.total_taxes;
      if (comb > 0) denom = comb;
    }

    if (denom != null && l1.total_taxes != null && l1.total_charges != null) {
      const taxPct = Number(((l1.total_taxes / denom) * 100).toFixed(1));
      const chargesPct = Number(((l1.total_charges / denom) * 100).toFixed(1));
      taxPill.textContent = "Taxes: " + taxPct + "%";

      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("width", "100%");
      svg.setAttribute("height", "28");
      svg.setAttribute("viewBox", "0 0 100 8");
      svg.setAttribute("preserveAspectRatio", "none");

      const rectEnergy = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rectEnergy.setAttribute("x", "0");
      rectEnergy.setAttribute("y", "0");
      rectEnergy.setAttribute("width", String(chargesPct));
      rectEnergy.setAttribute("height", "8");
      rectEnergy.setAttribute("fill", "#0ea5e9");
      rectEnergy.setAttribute("rx", "2");

      const rectTax = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rectTax.setAttribute("x", String(chargesPct));
      rectTax.setAttribute("y", "0");
      rectTax.setAttribute("width", String(taxPct));
      rectTax.setAttribute("height", "8");
      rectTax.setAttribute("fill", "#10b981");
      rectTax.setAttribute("rx", "2");

      svg.appendChild(rectEnergy);
      svg.appendChild(rectTax);
      chartWrap.appendChild(svg);

      const expText = document.getElementById("stat-explanation-text");
      expText.textContent = "Electricity charges: PKR " + Number(l1.total_charges).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " (" + chargesPct.toFixed(1) + "%) | Taxes & duties: PKR " + Number(l1.total_taxes).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " (" + taxPct.toFixed(1) + "%).";
    } else {
      taxPill.textContent = "cannot be determined";
      const expText = document.getElementById("stat-explanation-text");
      expText.textContent = "Charges and taxes percentage breakdown cannot be determined from the bill.";
    }

    // 3. Itemized Charges Table
    const charges = l1.charges || [];
    const tbodyCharges = document.getElementById("tbody-charges");
    tbodyCharges.textContent = "";
    if (charges.length === 0) {
      const emptyTr = document.createElement("tr");
      const emptyTd = document.createElement("td");
      emptyTd.setAttribute("colspan", "2");
      emptyTd.className = "text-muted";
      emptyTd.textContent = "No itemized charges printed on bill (subtotal: PKR " + (l1.total_charges != null ? Number(l1.total_charges).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "N/A") + ")";
      emptyTr.appendChild(emptyTd);
      tbodyCharges.appendChild(emptyTr);
    } else {
      charges.forEach(c => {
        const tr = document.createElement("tr");
        const tdName = document.createElement("td");
        tdName.textContent = CHARGE_LABELS[c.type] || c.type;
        if (c.amount < 0 || c.type === "subsidy") {
          const credTag = document.createElement("span");
          credTag.className = "tag-credit";
          credTag.textContent = "relief";
          tdName.appendChild(credTag);
        }

        const tdAmt = document.createElement("td");
        tdAmt.className = "col-num";
        if (c.amount < 0) {
          tdAmt.style.color = "var(--accent-primary)";
          tdAmt.textContent = "-PKR " + Math.abs(c.amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        } else {
          tdAmt.textContent = "PKR " + Number(c.amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        tr.appendChild(tdName);
        tr.appendChild(tdAmt);
        tbodyCharges.appendChild(tr);
      });
    }
    const chargesBadge = document.getElementById("charges-subtotal-badge");
    chargesBadge.textContent = "Total: " + (l1.total_charges != null ? "PKR " + Number(l1.total_charges).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "Not on bill");

    // 4. Itemized Taxes Table
    const taxes = l1.taxes || [];
    const tbodyTaxes = document.getElementById("tbody-taxes");
    tbodyTaxes.textContent = "";
    if (taxes.length === 0) {
      const emptyTr = document.createElement("tr");
      const emptyTd = document.createElement("td");
      emptyTd.setAttribute("colspan", "2");
      emptyTd.className = "text-muted";
      emptyTd.textContent = "No itemized taxes printed (total taxes: " + (l1.total_taxes != null ? "PKR " + Number(l1.total_taxes).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "N/A") + ")";
      emptyTr.appendChild(emptyTd);
      tbodyTaxes.appendChild(emptyTr);
    } else {
      taxes.forEach(t => {
        const tr = document.createElement("tr");
        const tdName = document.createElement("td");
        tdName.textContent = TAX_LABELS[t.type] || t.type;

        const tdAmt = document.createElement("td");
        tdAmt.className = "col-num";
        tdAmt.textContent = "PKR " + Number(t.amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

        tr.appendChild(tdName);
        tr.appendChild(tdAmt);
        tbodyTaxes.appendChild(tr);
      });
    }
    const taxesBadge = document.getElementById("taxes-subtotal-badge");
    taxesBadge.textContent = "Total: " + (l1.total_taxes != null ? "PKR " + Number(l1.total_taxes).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "Not on bill");

    // 5. Usage History Chart (SVG)
    const historySec = document.getElementById("history-section");
    const historySvgWrap = document.getElementById("history-svg-wrapper");
    historySvgWrap.textContent = "";

    if (history && history.length > 0) {
      historySec.style.display = "flex";
      document.getElementById("history-months-badge").textContent = history.length + " recorded months";

      const validRows = history.filter(r => r.units != null && typeof r.units === "number");
      if (validRows.length > 0) {
        function formatMonthLabel(m) {
          if (!m) return "";
          m = String(m).trim();
          const ymMatch = m.match(/^(\d{4})-(\d{2})$/);
          if (ymMatch) {
            const months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
            const mIdx = parseInt(ymMatch[2], 10) - 1;
            const yr = ymMatch[1].slice(-2);
            if (mIdx >= 0 && mIdx < 12) return months[mIdx] + " " + yr;
          }
          return m;
        }

        const unitsVals = validRows.map(r => Number(r.units));
        const rawMax = Math.max(...unitsVals);
        const rawMin = Math.min(...unitsVals);
        const maxVal = Math.max(rawMax, 100);
        const minVal = Math.min(rawMin, 0);
        const range = (maxVal - minVal) || 1;

        const svgW = 650;
        const svgH = 170;
        const paddingTop = 25;
        const paddingBottom = 35;
        const chartH = svgH - paddingTop - paddingBottom;

        const zeroY = paddingTop + (maxVal / range) * chartH;

        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", String(svgH));
        svg.setAttribute("viewBox", "0 0 " + svgW + " " + svgH);

        if (minVal < 0) {
          const zeroLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
          zeroLine.setAttribute("x1", "0");
          zeroLine.setAttribute("y1", String(zeroY));
          zeroLine.setAttribute("x2", String(svgW));
          zeroLine.setAttribute("y2", String(zeroY));
          zeroLine.setAttribute("stroke", "var(--border-strong, #888)");
          zeroLine.setAttribute("stroke-dasharray", "3,3");
          zeroLine.setAttribute("stroke-width", "1");
          svg.appendChild(zeroLine);
        }

        const colWidth = svgW / validRows.length;
        const barW = Math.max(16, colWidth - 12);

        validRows.forEach((r, idx) => {
          const x = idx * colWidth + (colWidth - barW) / 2;
          const u = Number(r.units);
          const barH = (Math.abs(u) / range) * chartH;
          const barY = u >= 0 ? (zeroY - barH) : zeroY;

          const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
          rect.setAttribute("x", String(x));
          rect.setAttribute("y", String(barY));
          rect.setAttribute("width", String(barW));
          rect.setAttribute("height", String(Math.max(barH, 2)));
          if (u < 0) {
            rect.setAttribute("fill", "var(--accent-danger, #ef4444)");
          } else if (u > 200) {
            rect.setAttribute("fill", "var(--accent-warning, #f59e0b)");
          } else {
            rect.setAttribute("fill", "var(--accent-info, #38bdf8)");
          }
          rect.setAttribute("rx", "3");

          const txtUnits = document.createElementNS("http://www.w3.org/2000/svg", "text");
          txtUnits.setAttribute("x", String(x + barW / 2));
          if (u >= 0) {
            txtUnits.setAttribute("y", String(Math.max(barY - 5, 12)));
          } else {
            txtUnits.setAttribute("y", String(Math.min(barY + barH + 12, svgH - paddingBottom + 10)));
          }
          txtUnits.setAttribute("text-anchor", "middle");
          txtUnits.setAttribute("font-size", "10");
          txtUnits.setAttribute("font-weight", "500");
          txtUnits.setAttribute("fill", "var(--text-muted)");
          txtUnits.textContent = String(u);

          const txtMonth = document.createElementNS("http://www.w3.org/2000/svg", "text");
          txtMonth.setAttribute("x", String(x + barW / 2));
          txtMonth.setAttribute("y", String(svgH - 10));
          txtMonth.setAttribute("text-anchor", "middle");
          txtMonth.setAttribute("font-size", "9.5");
          txtMonth.setAttribute("fill", "var(--text-sub)");
          txtMonth.textContent = formatMonthLabel(r.month);

          svg.appendChild(rect);
          svg.appendChild(txtUnits);
          svg.appendChild(txtMonth);
        });

        historySvgWrap.appendChild(svg);
      }
    } else {
      historySec.style.display = "none";
    }

    // 6. Reconciliation Notices in Technical Tab
    const warnDetails = document.getElementById("warnings-details");
    const warnList = document.getElementById("warnings-list");
    warnList.textContent = "";
    if (warnings && warnings.length > 0) {
      warnDetails.style.display = "block";
      document.getElementById("warnings-count").textContent = String(warnings.length);
      warnings.forEach(w => {
        const li = document.createElement("li");
        li.textContent = w;
        warnList.appendChild(li);
      });
    } else {
      warnDetails.style.display = "none";
    }

    // 7. Q&A View (Chat bubbles with full question text)
    const qaStream = document.getElementById("qa-chat-stream");
    qaStream.textContent = "";
    const qaItems = (payload.qa_list && payload.qa_list.length > 0) ?
      payload.qa_list :
      Object.entries(answers).map(([qid, ansText]) => ({
        question_id: qid,
        question: STANDARD_QUESTIONS[qid] || qid,
        answer: ansText,
      }));

    if (qaItems.length === 0) {
      const p = document.createElement("p");
      p.className = "text-muted";
      p.textContent = "No Level 2 answers generated.";
      qaStream.appendChild(p);
    } else {
      qaItems.forEach(item => {
        const qText = item.question;
        const ansText = item.answer;

        const group = document.createElement("div");
        group.className = "qa-bubble-group";

        const qBubble = document.createElement("div");
        qBubble.className = "qa-question-bubble";
        qBubble.textContent = qText;

        const aBubble = document.createElement("div");
        aBubble.className = "qa-answer-bubble";

        const pAns = document.createElement("p");
        pAns.textContent = ansText;
        aBubble.appendChild(pAns);

        const footRow = document.createElement("div");
        footRow.className = "qa-footer-row";

        const lower = ansText.toLowerCase();
        if (lower.includes("could not be determined") || lower.includes("not on bill")) {
          const missingBadge = document.createElement("span");
          missingBadge.className = "text-muted";
          missingBadge.style.fontSize = "10px";
          missingBadge.textContent = "Not found on bill";
          footRow.appendChild(missingBadge);
        } else if (lower.includes("computed") || lower.includes("calculated") || lower.includes("%") || lower.includes("average") || lower.includes("sum")) {
          const calcBadge = document.createElement("span");
          calcBadge.className = "badge-calculated";
          calcBadge.textContent = "✓ Calculated";
          footRow.appendChild(calcBadge);
        }

        const copyBtn = document.createElement("button");
        copyBtn.className = "btn-copy-bubble";
        copyBtn.textContent = "Copy";
        copyBtn.type = "button";
        copyBtn.addEventListener("click", () => {
          navigator.clipboard.writeText(ansText).then(() => {
            copyBtn.textContent = "Copied!";
            setTimeout(() => { copyBtn.textContent = "Copy"; }, 1500);
          });
        });
        footRow.appendChild(copyBtn);

        aBubble.appendChild(footRow);
        group.appendChild(qBubble);
        group.appendChild(aBubble);
        qaStream.appendChild(group);
      });
    }

    // 8. Raw JSON View
    const codeRaw = document.getElementById("code-raw-json");
    codeRaw.textContent = JSON.stringify(l1, null, 2);
  }

  // Suggestion Q chips
  questionChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const qText = chip.getAttribute("data-q");
      if (inputCustomQ) {
        inputCustomQ.value = qText;
      }
      document.getElementById("tab-qa").click();
    });
  });

  // Custom Q&A Handler
  if (btnAskCustom && inputCustomQ) {
    function handleCustomAsk() {
      const q = inputCustomQ.value.trim();
      if (!q) return;
      if (!lastDecodedPayload) {
        showAlert("Please decode a bill first before asking questions.", false);
        return;
      }

      const qaStream = document.getElementById("qa-chat-stream");
      const group = document.createElement("div");
      group.className = "qa-bubble-group";

      const qBubble = document.createElement("div");
      qBubble.className = "qa-question-bubble";
      qBubble.textContent = q;

      const aBubble = document.createElement("div");
      aBubble.className = "qa-answer-bubble";

      const pAns = document.createElement("p");
      pAns.textContent = "Thinking...";
      aBubble.appendChild(pAns);

      const footRow = document.createElement("div");
      footRow.className = "qa-footer-row";
      const calcBadge = document.createElement("span");
      calcBadge.className = "badge-calculated";
      calcBadge.textContent = "AI Grounded";
      footRow.appendChild(calcBadge);

      aBubble.appendChild(footRow);
      group.appendChild(qBubble);
      group.appendChild(aBubble);
      qaStream.prepend(group);

      inputCustomQ.value = "";
      btnAskCustom.disabled = true;

      const l1 = lastDecodedPayload.level1 || {};
      const stats = lastDecodedPayload.stats || {};

      fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bill_id: lastDecodedPayload.bill_id || "bill",
          question: q,
          level1: l1,
          stats: stats,
          history: lastDecodedPayload.history || [],
        }),
      })
      .then(r => r.json())
      .then(resData => {
        pAns.textContent = resData.answer || "This could not be determined from the bill.";
      })
      .catch(err => {
        pAns.textContent = "Could not answer question: " + err.message;
      })
      .finally(() => {
        btnAskCustom.disabled = false;
      });
    }

    btnAskCustom.addEventListener("click", handleCustomAsk);
    inputCustomQ.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleCustomAsk();
    });
  }

  // Copy CLI commands
  document.querySelectorAll(".btn-copy-cli").forEach(btn => {
    btn.addEventListener("click", () => {
      const code = btn.getAttribute("data-code");
      if (code) {
        navigator.clipboard.writeText(code).then(() => {
          const original = btn.textContent;
          btn.textContent = "Copied!";
          setTimeout(() => { btn.textContent = original; }, 1500);
        });
      }
    });
  });

  // Copy Raw JSON
  document.getElementById("btn-copy-raw-json").addEventListener("click", () => {
    if (lastDecodedPayload && lastDecodedPayload.level1) {
      const jsonStr = JSON.stringify(lastDecodedPayload.level1, null, 2);
      navigator.clipboard.writeText(jsonStr).then(() => {
        const btn = document.getElementById("btn-copy-raw-json");
        btn.textContent = "Copied!";
        setTimeout(() => { btn.textContent = "Copy JSON"; }, 1500);
      });
    }
  });

  // Download JSON
  document.getElementById("btn-download-json").addEventListener("click", () => {
    if (lastDecodedPayload && lastDecodedPayload.level1) {
      const jsonStr = JSON.stringify(lastDecodedPayload.level1, null, 2);
      const blob = new Blob([jsonStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = (lastDecodedPayload.bill_id || "bill") + "_level1.json";
      a.click();
      URL.revokeObjectURL(url);
    }
  });
});
