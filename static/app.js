// WTQ Utility Bill Decoder - Frontend Application Logic

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const dropzonePrompt = document.getElementById("dropzone-prompt");
  const previewContainer = document.getElementById("preview-container");
  const previewImg = document.getElementById("bill-preview-img");
  const btnChangeImage = document.getElementById("btn-change-image");
  const btnDecode = document.getElementById("btn-decode");
  const btnDecodeText = document.getElementById("btn-decode-text");
  const decodeSpinner = document.getElementById("decode-spinner");
  const statusMsg = document.getElementById("status-msg");
  const emptyState = document.getElementById("empty-state");
  const resultsContent = document.getElementById("results-content");
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabViews = document.querySelectorAll(".tab-view");
  const sampleChips = document.querySelectorAll(".chip");
  const btnCopyJson = document.getElementById("btn-copy-json");

  // State
  let currentFile = null;
  let currentDecodedData = null;

  // Drag and Drop Events
  ["dragenter", "dragover"].forEach(event => {
    dropzone.addEventListener(event, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(event => {
    dropzone.addEventListener(event, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  });

  dropzone.addEventListener("click", (e) => {
    if (e.target !== btnChangeImage && !previewContainer.contains(e.target)) {
      fileInput.click();
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  btnChangeImage.addEventListener("click", (e) => {
    e.stopPropagation();
    resetUpload();
    fileInput.click();
  });

  function resetUpload() {
    currentFile = null;
    fileInput.value = "";
    previewImg.src = "";
    previewContainer.style.display = "none";
    dropzonePrompt.style.display = "block";
    btnDecode.disabled = true;
    hideStatus();
  }

  function handleFileSelection(file) {
    if (!file.type.match("image/png") && !file.type.match("image/jpeg")) {
      showStatus("Please upload a PNG or JPEG bill image.", "error");
      return;
    }
    if (file.size > 15 * 1024 * 1024) {
      showStatus("File exceeds 15 MB limit.", "error");
      return;
    }

    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      dropzonePrompt.style.display = "none";
      previewContainer.style.display = "flex";
      btnDecode.disabled = false;
      hideStatus();
    };
    reader.readAsDataURL(file);
  }

  // Sample Chips
  sampleChips.forEach(chip => {
    chip.addEventListener("click", async () => {
      const sampleName = chip.getAttribute("data-sample");
      showStatus(`Loading sample ${sampleName}...`, "info");
      try {
        const resp = await fetch(`/sample-bills/${sampleName}`);
        if (!resp.ok) throw new Error("Could not load sample");
        const blob = await resp.blob();
        const file = new File([blob], sampleName, { type: blob.type || "image/png" });
        handleFileSelection(file);
      } catch (err) {
        showStatus(`Failed to load sample: ${err.message}`, "error");
      }
    });
  });

  // Tab switching
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      tabBtns.forEach(b => b.classList.remove("active"));
      tabViews.forEach(v => v.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(targetId).classList.add("active");
    });
  });

  // Status message helpers
  function showStatus(text, type) {
    statusMsg.textContent = text;
    statusMsg.className = `status-msg ${type}`;
    statusMsg.style.display = "block";
  }

  function hideStatus() {
    statusMsg.style.display = "none";
  }

  // Copy JSON
  btnCopyJson.addEventListener("click", () => {
    if (currentDecodedData) {
      const jsonStr = JSON.stringify(currentDecodedData.level1, null, 2);
      navigator.clipboard.writeText(jsonStr).then(() => {
        btnCopyJson.textContent = "✓ Copied!";
        setTimeout(() => { btnCopyJson.textContent = "📋 Copy JSON"; }, 2000);
      });
    }
  });

  // Decode Action
  btnDecode.addEventListener("click", async () => {
    if (!currentFile) return;

    btnDecode.disabled = true;
    btnDecodeText.textContent = "Decoding Bill with Gemini 3.5 Flash-Lite...";
    decodeSpinner.style.display = "inline-block";
    showStatus("Extracting Level 1 fields and precomputing deterministic stats...", "info");

    const formData = new FormData();
    formData.append("file", currentFile);

    try {
      const response = await fetch("/api/decode", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error (${response.status})`);
      }

      const data = await response.json();
      currentDecodedData = data;
      renderResults(data);
      hideStatus();
    } catch (err) {
      showStatus(`Error: ${err.message}`, "error");
    } finally {
      btnDecode.disabled = false;
      btnDecodeText.textContent = "⚡ Decode Utility Bill";
      decodeSpinner.style.display = "none";
    }
  });

  function renderResults(data) {
    const l1 = data.level1 || {};
    const stats = data.stats || {};
    const answers = data.answers || {};
    const warnings = data.warnings || [];

    // Hide empty state, show results
    emptyState.style.display = "none";
    resultsContent.style.display = "flex";

    // 1. Metric Cards
    document.getElementById("val-provider").textContent = l1.provider || "Unknown";
    document.getElementById("val-tariff").textContent = l1.tariff ? `Tariff: ${l1.tariff}` : "Tariff: N/A";

    document.getElementById("val-month").textContent = l1.bill_month || "-";
    document.getElementById("val-issue-date").textContent = l1.issue_date ? `Issue: ${l1.issue_date}` : "Issue: -";

    document.getElementById("val-units").textContent = l1.units_consumed != null ? `${l1.units_consumed} kWh` : "-";
    const prev = l1.previous_reading != null ? l1.previous_reading : "-";
    const curr = l1.current_reading != null ? l1.current_reading : "-";
    document.getElementById("val-readings").textContent = `Readings: ${prev} → ${curr}`;

    document.getElementById("val-payable").textContent = l1.payable_within_due_date != null ? `PKR ${l1.payable_within_due_date.toLocaleString()}` : "-";
    document.getElementById("val-due-date").textContent = l1.due_date ? `Due: ${l1.due_date}` : "Due: -";

    // 2. Tax Share Banner
    if (stats.tax_share_pct != null) {
      document.getElementById("stat-tax-headline").textContent = `Tax Share: ${stats.tax_share_pct}% of current bill`;
      document.getElementById("stat-tax-detail").textContent = `${stats.tax_share_text || ""}. Total taxes: PKR ${l1.total_taxes || 0} out of current bill PKR ${l1.current_bill || 0}.`;
    } else {
      document.getElementById("stat-tax-headline").textContent = "Tax Share: Unavailable";
      document.getElementById("stat-tax-detail").textContent = "Total taxes or current bill not itemized on bill.";
    }

    // 3. Charges Table
    const charges = l1.charges || [];
    const tbodyCharges = document.getElementById("tbody-charges");
    tbodyCharges.innerHTML = "";
    if (charges.length === 0) {
      tbodyCharges.innerHTML = `<tr><td colspan="2" class="text-muted">No itemized charge rows</td></tr>`;
    } else {
      charges.forEach(c => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td><strong>${escapeHtml(c.type)}</strong></td>
          <td class="text-right">${c.amount < 0 ? "-" : ""}PKR ${Math.abs(c.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
        `;
        tbodyCharges.appendChild(row);
      });
    }
    document.getElementById("badge-total-charges").textContent = `Total: PKR ${l1.total_charges != null ? l1.total_charges.toLocaleString() : "N/A"}`;

    // 4. Taxes Table
    const taxes = l1.taxes || [];
    const tbodyTaxes = document.getElementById("tbody-taxes");
    tbodyTaxes.innerHTML = "";
    if (taxes.length === 0) {
      tbodyTaxes.innerHTML = `<tr><td colspan="2" class="text-muted">No itemized tax rows (combined tax: PKR ${l1.total_taxes || 0})</td></tr>`;
    } else {
      taxes.forEach(t => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td><strong>${escapeHtml(t.type)}</strong></td>
          <td class="text-right">PKR ${t.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
        `;
        tbodyTaxes.appendChild(row);
      });
    }
    document.getElementById("badge-total-taxes").textContent = `Total: PKR ${l1.total_taxes != null ? l1.total_taxes.toLocaleString() : "N/A"}`;

    // 5. Reconciliation Notices
    const notesCard = document.getElementById("notes-card");
    const warnList = document.getElementById("warnings-list");
    warnList.innerHTML = "";
    if (warnings.length > 0) {
      notesCard.style.display = "block";
      warnings.forEach(w => {
        const li = document.createElement("li");
        li.textContent = w;
        warnList.appendChild(li);
      });
    } else {
      notesCard.style.display = "none";
    }

    // 6. Q&A View
    const qaContainer = document.getElementById("qa-container");
    qaContainer.innerHTML = "";
    const questionEntries = Object.entries(answers);
    if (questionEntries.length === 0) {
      qaContainer.innerHTML = `<p class="text-muted">No answers generated.</p>`;
    } else {
      questionEntries.forEach(([qid, ans]) => {
        const card = document.createElement("div");
        card.className = "qa-card";
        card.innerHTML = `
          <div class="qa-question">
            <span>❓</span>
            <strong>${escapeHtml(qid)}</strong>
          </div>
          <p class="qa-answer">${escapeHtml(ans)}</p>
        `;
        qaContainer.appendChild(card);
      });
    }

    // 7. Raw JSON View
    document.getElementById("raw-json-code").textContent = JSON.stringify(l1, null, 2);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
