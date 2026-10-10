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

  // State
  let selectedFile = null;
  let activeAbortController = null;
  let lastDecodedPayload = null;

  // Type Mappings for Plain English display
  const CHARGE_LABELS = {
    energy: "Energy charges (units consumed)",
    fixed: "Fixed charges",
    fpa: "Fuel price adjustment (FPA / FCA)",
    quarterly_adjustment: "Quarterly tariff adjustment (QTA)",
    surcharge: "Additional surcharge (PHL / FC)",
    meter_rent: "Meter / service rent",
    subsidy: "Government relief / subsidy",
    other: "Other charges",
  };

  const TAX_LABELS = {
    gst: "General Sales Tax (GST)",
    electricity_duty: "Electricity Duty (ED)",
    income_tax: "Income Tax / Advance IT",
    municipal_tax: "Municipal / Local Tax (MUCT/KMC)",
    other_tax: "Other taxes & TV fee",
  };

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
    // Anonymize filename display: avoid showing raw digits as IDs
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
        if (!resp.ok) throw new Error("Sample file not available.");
        const blob = await resp.blob();
        const file = new File([blob], sampleFile, { type: blob.type || "image/png" });
        processSelectedFile(file);
      } catch (err) {
        showAlert("Failed to load sample: " + err.message);
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

    // Days left calculation
    const daysChip = document.getElementById("hero-days-left");
    if (l1.due_date) {
      const parts = l1.due_date.split("-");
      if (parts.length === 3) {
        const dueDateObj = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
        const today = new Date();
        const diffDays = Math.ceil((dueDateObj - today) / (1000 * 60 * 60 * 24));
        if (diffDays < 0) {
          daysChip.textContent = Math.abs(diffDays) + " days overdue";
          daysChip.className = "days-chip overdue";
        } else if (diffDays === 0) {
          daysChip.textContent = "Due today";
          daysChip.className = "days-chip";
        } else {
          daysChip.textContent = diffDays + " days left";
          daysChip.className = "days-chip";
        }
      }
    } else {
      daysChip.textContent = "No date";
      daysChip.className = "days-chip";
    }

    const payVal = document.getElementById("hero-payable-val");
    payVal.textContent = l1.payable_within_due_date != null ?
      Number(l1.payable_within_due_date).toLocaleString(undefined, { minimumFractionDigits: 0 }) :
      "Not on bill";

    const lateVal = document.getElementById("hero-late-val");
    lateVal.textContent = l1.payable_after_due_date != null ?
      Number(l1.payable_after_due_date).toLocaleString(undefined, { minimumFractionDigits: 0 }) :
      "Not on bill";

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

    if (stats.tax_share_pct != null && l1.total_charges != null && l1.total_taxes != null) {
      taxPill.textContent = "Taxes: " + stats.tax_share_pct + "%";
      const chargesPct = stats.charges_share_pct || (100 - stats.tax_share_pct);

      // Create Stacked Bar SVG
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
      rectTax.setAttribute("width", String(stats.tax_share_pct));
      rectTax.setAttribute("height", "8");
      rectTax.setAttribute("fill", "#10b981");
      rectTax.setAttribute("rx", "2");

      svg.appendChild(rectEnergy);
      svg.appendChild(rectTax);
      chartWrap.appendChild(svg);

      const expText = document.getElementById("stat-explanation-text");
      expText.textContent = "Electricity charges: PKR " + l1.total_charges.toLocaleString() + " (" + chargesPct.toFixed(1) + "%) | Taxes & duties: PKR " + l1.total_taxes.toLocaleString() + " (" + stats.tax_share_pct.toFixed(1) + "%).";
    } else {
      taxPill.textContent = "Not Itemized";
      const expText = document.getElementById("stat-explanation-text");
      expText.textContent = "Charges and taxes subtotals are not separately itemized on this bill.";
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
      emptyTd.textContent = "No itemized charges printed on bill (subtotal: PKR " + (l1.total_charges != null ? l1.total_charges.toLocaleString() : "N/A") + ")";
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
          tdAmt.textContent = "-PKR " + Math.abs(c.amount).toLocaleString(undefined, { minimumFractionDigits: 2 });
        } else {
          tdAmt.textContent = "PKR " + Number(c.amount).toLocaleString(undefined, { minimumFractionDigits: 2 });
        }

        tr.appendChild(tdName);
        tr.appendChild(tdAmt);
        tbodyCharges.appendChild(tr);
      });
    }
    const chargesBadge = document.getElementById("charges-subtotal-badge");
    chargesBadge.textContent = "Total: PKR " + (l1.total_charges != null ? l1.total_charges.toLocaleString() : "Not on bill");

    // 4. Itemized Taxes Table
    const taxes = l1.taxes || [];
    const tbodyTaxes = document.getElementById("tbody-taxes");
    tbodyTaxes.textContent = "";
    if (taxes.length === 0) {
      const emptyTr = document.createElement("tr");
      const emptyTd = document.createElement("td");
      emptyTd.setAttribute("colspan", "2");
      emptyTd.className = "text-muted";
      emptyTd.textContent = "No itemized taxes printed (total taxes: PKR " + (l1.total_taxes != null ? l1.total_taxes.toLocaleString() : "N/A") + ")";
      emptyTr.appendChild(emptyTd);
      tbodyTaxes.appendChild(emptyTr);
    } else {
      taxes.forEach(t => {
        const tr = document.createElement("tr");
        const tdName = document.createElement("td");
        tdName.textContent = TAX_LABELS[t.type] || t.type;

        const tdAmt = document.createElement("td");
        tdAmt.className = "col-num";
        tdAmt.textContent = "PKR " + Number(t.amount).toLocaleString(undefined, { minimumFractionDigits: 2 });

        tr.appendChild(tdName);
        tr.appendChild(tdAmt);
        tbodyTaxes.appendChild(tr);
      });
    }
    const taxesBadge = document.getElementById("taxes-subtotal-badge");
    taxesBadge.textContent = "Total: PKR " + (l1.total_taxes != null ? l1.total_taxes.toLocaleString() : "Not on bill");

    // 5. Usage History Chart (SVG)
    const historySec = document.getElementById("history-section");
    const historySvgWrap = document.getElementById("history-svg-wrapper");
    historySvgWrap.textContent = "";

    if (history && history.length > 0) {
      historySec.style.display = "flex";
      document.getElementById("history-months-badge").textContent = history.length + " recorded months";

      const validRows = history.filter(r => r.units != null && typeof r.units === "number");
      if (validRows.length > 0) {
        const maxU = Math.max(...validRows.map(r => r.units), 100);
        const svgW = 600;
        const svgH = 140;
        const barW = Math.max(16, (svgW / validRows.length) - 10);

        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", "100%");
        svg.setAttribute("height", "140");
        svg.setAttribute("viewBox", "0 0 " + svgW + " " + svgH);

        validRows.forEach((r, idx) => {
          const x = idx * (svgW / validRows.length) + 8;
          const barH = (r.units / maxU) * 90;
          const y = 100 - barH;

          // Bar
          const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
          rect.setAttribute("x", String(x));
          rect.setAttribute("y", String(y));
          rect.setAttribute("width", String(barW));
          rect.setAttribute("height", String(barH));
          rect.setAttribute("fill", r.units > 200 ? "var(--accent-warning)" : "var(--accent-info)");
          rect.setAttribute("rx", "3");

          // Text Units
          const txtUnits = document.createElementNS("http://www.w3.org/2000/svg", "text");
          txtUnits.setAttribute("x", String(x + barW / 2));
          txtUnits.setAttribute("y", String(y - 4));
          txtUnits.setAttribute("text-anchor", "middle");
          txtUnits.setAttribute("font-size", "10");
          txtUnits.setAttribute("fill", "var(--text-muted)");
          txtUnits.textContent = String(r.units);

          // Text Month
          const txtMonth = document.createElementNS("http://www.w3.org/2000/svg", "text");
          txtMonth.setAttribute("x", String(x + barW / 2));
          txtMonth.setAttribute("y", "122");
          txtMonth.setAttribute("text-anchor", "middle");
          txtMonth.setAttribute("font-size", "9");
          txtMonth.setAttribute("fill", "var(--text-sub)");
          txtMonth.textContent = r.month.slice(-5);

          svg.appendChild(rect);
          svg.appendChild(txtUnits);
          svg.appendChild(txtMonth);
        });

        historySvgWrap.appendChild(svg);
      }
    } else {
      historySec.style.display = "none";
    }

    // 6. Reconciliation Notices
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

    // 7. Q&A View (Chat bubbles)
    const qaStream = document.getElementById("qa-chat-stream");
    qaStream.textContent = "";
    const entries = Object.entries(answers);
    if (entries.length === 0) {
      const p = document.createElement("p");
      p.className = "text-muted";
      p.textContent = "No Level 2 answers generated.";
      qaStream.appendChild(p);
    } else {
      entries.forEach(([qid, ansText]) => {
        const group = document.createElement("div");
        group.className = "qa-bubble-group";

        const qBubble = document.createElement("div");
        qBubble.className = "qa-question-bubble";
        qBubble.textContent = qid;

        const aBubble = document.createElement("div");
        aBubble.className = "qa-answer-bubble";

        const pAns = document.createElement("p");
        pAns.textContent = ansText;
        aBubble.appendChild(pAns);

        const footRow = document.createElement("div");
        footRow.className = "qa-footer-row";

        if (ansText.toLowerCase().includes("computed") || ansText.toLowerCase().includes("calculated") || ansText.toLowerCase().includes("%")) {
          const calcBadge = document.createElement("span");
          calcBadge.className = "badge-calculated";
          calcBadge.textContent = "✓ Calculated";
          footRow.appendChild(calcBadge);
        } else {
          const groundBadge = document.createElement("span");
          groundBadge.className = "text-muted";
          groundBadge.style.fontSize = "10px";
          groundBadge.textContent = "Grounded in bill";
          footRow.appendChild(groundBadge);
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
      // Find matching answer in current answers if exists
      if (lastDecodedPayload && lastDecodedPayload.answers) {
        // Switch to QA tab
        document.getElementById("tab-qa").click();
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
