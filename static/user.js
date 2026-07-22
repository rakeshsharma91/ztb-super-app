/* =============================================================================
 * user.js — ZTB Super App: User-Facing Pages
 * Covers: Landing Page, Assessment Flow, Results Page, Utilities
 * ============================================================================= */

"use strict";

/* =============================================================================
 * SECTION 6 — UTILITIES
 * Shared helpers used across all pages. Defined first so every other section
 * can reference them freely.
 * ============================================================================= */

/**
 * fetchAPI — centralised fetch wrapper.
 * Always sends / expects JSON.  On HTTP 401 it hard-redirects to "/" so the
 * user is returned to the landing page whenever a session expires.
 *
 * @param {string} url    - Endpoint path, e.g. "/user/questions"
 * @param {string} method - HTTP verb ("GET", "POST", …)
 * @param {Object} [body] - Optional request body; serialised to JSON if present
 * @returns {Promise<any>} Resolved with parsed JSON on success
 */
async function fetchAPI(url, method = "GET", body = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" },
  };

  if (body !== null) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);

  /* Redirect unauthenticated / expired sessions back to the root landing page */
  if (response.status === 401) {
    window.location.href = "/";
    return;
  }

  if (!response.ok) {
    /* Bubble up a descriptive error so callers can show a toast */
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return response.json();
}

/**
 * showSpinner — shows or hides a full-page loading overlay.
 * Expects a #loading-overlay element in the DOM (display:flex / display:none).
 *
 * @param {boolean} show - true = visible, false = hidden
 */
function showSpinner(show) {
  const overlay = document.getElementById("loading-overlay");
  if (!overlay) return; /* graceful no-op if the element is absent */
  overlay.style.display = show ? "flex" : "none";
}

/**
 * showToast — displays a transient notification banner.
 * Creates a toast element, appends it to #toast-container (or <body>),
 * and auto-removes it after 3 seconds.
 *
 * @param {string} message - Human-readable message text
 * @param {"success"|"error"|"info"} [type="info"] - Visual style variant
 */
function showToast(message, type = "info") {
  /* Resolve (or lazily create) the toast container */
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    /* Position fixed, top-right — base styling applied via class */
    container.style.cssText =
      "position:fixed;top:1rem;right:1rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem;";
    document.body.appendChild(container);
  }

  /* Build the individual toast element */
  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.setAttribute("role", "alert");
  toast.setAttribute("aria-live", "assertive");

  /* Map type to a simple emoji prefix for quick visual scanning */
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  toast.textContent = `${icons[type] || ""} ${message}`;

  /* Inline fallback styles so toasts work even without an external stylesheet */
  const colours = {
    success: "#d1fae5",   /* emerald-100 */
    error:   "#fee2e2",   /* red-100 */
    info:    "#dbeafe",   /* blue-100 */
  };
  toast.style.cssText = `
    background:${colours[type] || colours.info};
    border:1px solid #ccc;
    border-radius:0.375rem;
    padding:0.75rem 1rem;
    font-size:0.9rem;
    max-width:320px;
    box-shadow:0 2px 8px rgba(0,0,0,.15);
    transition:opacity 0.3s ease;
  `;

  container.appendChild(toast);

  /* Auto-dismiss after 3 seconds with a brief fade */
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}


/* =============================================================================
 * SECTION 1 — LANDING PAGE
 * Bootstrapped when the page containing #start-form is loaded.
 * ============================================================================= */

/**
 * showFieldError — renders a red error message directly below an input field.
 * Inserts a <span> with class "field-error" after the target element.
 * Calling it again on the same field replaces the previous message.
 *
 * @param {string} fieldId  - The id attribute of the input element
 * @param {string} message  - Error text to display
 */
function showFieldError(fieldId, message) {
  const field = document.getElementById(fieldId);
  if (!field) return;

  /* Remove any pre-existing error for this field */
  const existing = field.parentElement.querySelector(".field-error");
  if (existing) existing.remove();

  /* Create and insert the error span */
  const errorSpan = document.createElement("span");
  errorSpan.className = "field-error";
  errorSpan.setAttribute("role", "alert");
  errorSpan.style.cssText = "color:#dc2626;font-size:0.8rem;display:block;margin-top:0.25rem;";
  errorSpan.textContent = message;

  /* Insert immediately after the field so it visually follows it */
  field.insertAdjacentElement("afterend", errorSpan);

  /* Highlight the field border red */
  field.style.borderColor = "#dc2626";
}

/**
 * clearFieldErrors — removes every field-error message from the form and
 * resets any red border styling applied by showFieldError.
 */
function clearFieldErrors() {
  /* Remove all error spans */
  document.querySelectorAll(".field-error").forEach((el) => el.remove());

  /* Reset border colour on all inputs and selects */
  document.querySelectorAll("input, select, textarea").forEach((el) => {
    el.style.borderColor = "";
  });
}

/**
 * startAssessment — submit handler for #start-form on the landing page.
 * Validates required fields, POSTs to /user/start, stores session data,
 * then navigates to /user/assessment.
 *
 * @param {Event} e - The form submit event
 */
async function startAssessment(e) {
  e.preventDefault();
  clearFieldErrors();

  /* --- Field validation --- */
  const customerNameInput = document.getElementById("customer_name");
  const seNameInput       = document.getElementById("se_name");
  let valid = true;

  if (!customerNameInput || !customerNameInput.value.trim()) {
    showFieldError("customer_name", "Customer name is required.");
    valid = false;
  }

  if (!seNameInput || !seNameInput.value.trim()) {
    showFieldError("se_name", "SE name is required.");
    valid = false;
  }

  if (!valid) return;

  const customerName = customerNameInput.value.trim();
  const seName       = seNameInput.value.trim();

  /* --- Show loading state on the submit button --- */
  const submitBtn = e.target.querySelector('[type="submit"]');
  let originalBtnText = "";
  if (submitBtn) {
    originalBtnText         = submitBtn.textContent;
    submitBtn.textContent   = "Starting…";
    submitBtn.disabled      = true;
  }

  try {
    /* POST to the server to create / initialise the assessment session */
    await fetchAPI("/user/start", "POST", { customer_name: customerName, se_name: seName });

    /* Persist identifiers so the assessment page can display them */
    sessionStorage.setItem("customer_name", customerName);
    sessionStorage.setItem("se_name",       seName);

    /* Navigate to the assessment flow */
    window.location.href = "/user/assessment";
  } catch (err) {
    showToast(`Failed to start assessment: ${err.message}`, "error");

    /* Restore button to its original state on failure */
    if (submitBtn) {
      submitBtn.textContent = originalBtnText;
      submitBtn.disabled    = false;
    }
  }
}

/**
 * initLandingPage — wires up the landing page once the DOM is ready.
 * Attaches the startAssessment handler to #start-form.
 */
function initLandingPage() {
  const form = document.getElementById("start-form");
  if (!form) return; /* not on the landing page */
  form.addEventListener("submit", startAssessment);
}


/* =============================================================================
 * SECTION 2 — ASSESSMENT PAGE: DATA LOADING
 * Reads session data, fetches questions from the API, bootstraps the step
 * renderer.
 * ============================================================================= */

/**
 * loadQuestions — fetches the question set from /user/questions.
 * Populates window.assessmentData and triggers rendering of the first step.
 *
 * The server returns an array shaped like:
 *   [ { category: "Cloud Adoption", questions: [ {question_id, text, options_type, options, info_only}, … ] }, … ]
 */
async function loadQuestions() {
  showSpinner(true);

  try {
    const categories = await fetchAPI("/user/questions");

    /* Initialise shared state object used by all rendering / navigation functions */
    window.assessmentData = {
      categories:   categories,   /* full question structure from the server */
      currentIndex: 0,            /* which category step is active           */
      responses:    {},           /* keyed by question_id → value(s)         */
    };

    renderStep(0);
  } catch (err) {
    showToast(`Could not load questions: ${err.message}`, "error");
  } finally {
    showSpinner(false);
  }
}

/**
 * initAssessmentPage — bootstraps the assessment page on DOMContentLoaded.
 * Guards against missing session data (redirects to landing if absent),
 * injects the user's name into the navbar, then triggers question loading.
 */
function initAssessmentPage() {
  /* Guard: must have arrived via the landing page */
  const customerName = sessionStorage.getItem("customer_name");
  const seName       = sessionStorage.getItem("se_name");

  if (!customerName || !seName) {
    window.location.href = "/";
    return;
  }

  /* Display identifiers in the navbar if placeholder elements are present */
  const navCustomer = document.getElementById("nav-customer-name");
  const navSE       = document.getElementById("nav-se-name");
  if (navCustomer) navCustomer.textContent = customerName;
  if (navSE)       navSE.textContent       = seName;

  /* Kick off data fetch */
  loadQuestions();
}


/* =============================================================================
 * SECTION 3 — ASSESSMENT PAGE: STEP RENDERING
 * Converts a single category entry into an interactive card-based form step.
 * ============================================================================= */

/**
 * buildQuestionCard — constructs the DOM node for one question.
 * Handles four question types: select_all (checkboxes), select_one (radios),
 * textbox (textarea), and info_only (plain text, no input).
 *
 * @param {Object} question - A single question object from the API payload
 * @param {*}      saved    - Previously saved response (string, array, or undefined)
 * @returns {HTMLElement} A <div class="question-card"> element ready to insert
 */
function buildQuestionCard(question, saved) {
  const card = document.createElement("div");
  card.className = "question-card";
  card.dataset.questionId = question.question_id;

  /* --- Question text / label --- */
  const label = document.createElement("p");
  label.className = "question-text";
  label.textContent = question.text;
  card.appendChild(label);

  /* --- info_only: render question text only, no inputs --- */
  if (question.info_only) {
    card.classList.add("question-card--info");
    return card; /* early return — no input elements needed */
  }

  const inputsWrapper = document.createElement("div");
  inputsWrapper.className = "question-inputs";

  /* --- select_all: checkboxes --- */
  if (question.options_type === "select_all") {
    (question.options || []).forEach((option) => {
      const optionId  = `q${question.question_id}_opt_${option.value ?? option}`;
      const optValue  = option.value ?? option;
      const optLabel  = option.label ?? option;
      const isChecked = Array.isArray(saved) && saved.includes(optValue);

      const wrapper = document.createElement("label");
      wrapper.className = "option-label";
      wrapper.htmlFor   = optionId;

      const checkbox       = document.createElement("input");
      checkbox.type        = "checkbox";
      checkbox.id          = optionId;
      checkbox.name        = `question_${question.question_id}`;
      checkbox.value       = optValue;
      checkbox.checked     = isChecked;
      checkbox.className   = "option-input";

      wrapper.appendChild(checkbox);
      wrapper.appendChild(document.createTextNode(` ${optLabel}`));
      inputsWrapper.appendChild(wrapper);
    });
  }

  /* --- select_one: radio buttons --- */
  else if (question.options_type === "select_one") {
    (question.options || []).forEach((option) => {
      const optionId  = `q${question.question_id}_opt_${option.value ?? option}`;
      const optValue  = option.value ?? option;
      const optLabel  = option.label ?? option;
      const isChecked = saved === optValue;

      const wrapper = document.createElement("label");
      wrapper.className = "option-label";
      wrapper.htmlFor   = optionId;

      const radio      = document.createElement("input");
      radio.type       = "radio";
      radio.id         = optionId;
      radio.name       = `question_${question.question_id}`;
      radio.value      = optValue;
      radio.checked    = isChecked;
      radio.className  = "option-input";

      wrapper.appendChild(radio);
      wrapper.appendChild(document.createTextNode(` ${optLabel}`));
      inputsWrapper.appendChild(wrapper);
    });
  }

  /* --- textbox: free-text textarea --- */
  else if (question.options_type === "textbox") {
    const textarea         = document.createElement("textarea");
    textarea.id            = `question_${question.question_id}`;
    textarea.name          = `question_${question.question_id}`;
    textarea.rows          = 4;
    textarea.className     = "question-textarea";
    textarea.placeholder   = "Enter your response…";
    textarea.value         = saved ?? "";
    inputsWrapper.appendChild(textarea);
  }

  card.appendChild(inputsWrapper);
  return card;
}

/**
 * renderStep — renders the category at the given index into #assessment-step.
 * Updates progress bar, step counter, category heading, question cards, and
 * the Prev / Next / Submit navigation buttons.
 *
 * @param {number} index - Zero-based index into assessmentData.categories
 */
function renderStep(index) {
  const { categories, responses } = window.assessmentData;
  const total    = categories.length;
  const category = categories[index];

  /* Keep currentIndex in sync */
  window.assessmentData.currentIndex = index;

  /* --- Progress bar --- */
  const progressBar = document.getElementById("progress-bar");
  if (progressBar) {
    progressBar.style.width = `${((index + 1) / total) * 100}%`;
    progressBar.setAttribute("aria-valuenow", index + 1);
    progressBar.setAttribute("aria-valuemax", total);
  }

  /* --- Step counter text --- */
  const stepCounter = document.getElementById("step-counter");
  if (stepCounter) {
    stepCounter.textContent = `Step ${index + 1} of ${total}`;
  }

  /* --- Category heading --- */
  const categoryHeading = document.getElementById("category-heading");
  if (categoryHeading) {
    categoryHeading.textContent = category.category;
  }

  /* --- Question cards --- */
  const stepContainer = document.getElementById("assessment-step");
  if (stepContainer) {
    /* Clear previous step's cards */
    stepContainer.innerHTML = "";

    (category.questions || []).forEach((question) => {
      const saved = responses[question.question_id];
      const card  = buildQuestionCard(question, saved);
      stepContainer.appendChild(card);
    });
  }

  /* --- Navigation button visibility ---
   *  - Prev: hidden on the first step
   *  - Next: shown on all steps except the last
   *  - Submit: shown only on the last step
   */
  const prevBtn   = document.getElementById("btn-prev");
  const nextBtn   = document.getElementById("btn-next");
  const submitBtn = document.getElementById("btn-submit");

  if (prevBtn)   prevBtn.style.display   = index === 0          ? "none"   : "inline-block";
  if (nextBtn)   nextBtn.style.display   = index < total - 1    ? "inline-block" : "none";
  if (submitBtn) submitBtn.style.display = index === total - 1  ? "inline-block" : "none";
}


/* =============================================================================
 * SECTION 4 — ASSESSMENT PAGE: NAVIGATION
 * Persists responses before moving between steps; handles final submission.
 * ============================================================================= */

/**
 * saveCurrentResponses — reads all active inputs on the current step and
 * stores their values into window.assessmentData.responses, keyed by
 * question_id (parsed from the element's name attribute).
 *
 * - Checkboxes    → array of checked values
 * - Radio buttons → single string value of the selected option
 * - Textareas     → trimmed string value
 */
function saveCurrentResponses() {
  const { categories, currentIndex, responses } = window.assessmentData;
  const category = categories[currentIndex];

  (category.questions || []).forEach((question) => {
    const qId   = question.question_id;
    const name  = `question_${qId}`;

    if (question.info_only) return; /* info-only questions have no input */

    if (question.options_type === "select_all") {
      /* Collect every checked checkbox for this question */
      const checked = Array.from(
        document.querySelectorAll(`input[name="${name}"]:checked`)
      ).map((el) => el.value);
      responses[qId] = checked;

    } else if (question.options_type === "select_one") {
      /* Single selected radio value */
      const selected = document.querySelector(`input[name="${name}"]:checked`);
      responses[qId] = selected ? selected.value : null;

    } else if (question.options_type === "textbox") {
      const textarea = document.getElementById(`question_${qId}`);
      responses[qId] = textarea ? textarea.value.trim() : "";
    }
  });
}

/**
 * nextStep — saves the current step's responses, advances the index, and
 * renders the next category step.
 */
function nextStep() {
  const { categories, currentIndex } = window.assessmentData;

  saveCurrentResponses();

  if (currentIndex < categories.length - 1) {
    renderStep(currentIndex + 1);
    /* Scroll back to the top of the assessment area for long pages */
    document.getElementById("assessment-step")?.scrollIntoView({ behavior: "smooth" });
  }
}

/**
 * prevStep — saves the current step's responses, decrements the index, and
 * renders the previous category step.
 */
function prevStep() {
  const { currentIndex } = window.assessmentData;

  saveCurrentResponses();

  if (currentIndex > 0) {
    renderStep(currentIndex - 1);
    document.getElementById("assessment-step")?.scrollIntoView({ behavior: "smooth" });
  }
}

/**
 * submitAssessment — saves remaining responses, then POSTs the full response
 * map to /user/submit.  On success it hands off to showResults().
 * On failure it surfaces a toast and re-enables the submit button.
 */
async function submitAssessment() {
  saveCurrentResponses();

  const submitBtn = document.getElementById("btn-submit");
  if (submitBtn) {
    submitBtn.textContent = "Submitting…";
    submitBtn.disabled    = true;
  }

  showSpinner(true);

  try {
    const payload = {
      customer_name: sessionStorage.getItem("customer_name"),
      se_name:       sessionStorage.getItem("se_name"),
      responses:     window.assessmentData.responses,
    };

    const result = await fetchAPI("/user/submit", "POST", payload);
    showResults(result);
  } catch (err) {
    showToast(`Submission failed: ${err.message}`, "error");

    if (submitBtn) {
      submitBtn.textContent = "Submit";
      submitBtn.disabled    = false;
    }
  } finally {
    showSpinner(false);
  }
}


/* =============================================================================
 * SECTION 5 — RESULTS PAGE
 * Renders the summary table, key counts, download control, and restart link.
 * ============================================================================= */

/**
 * showResults — receives the server response from /user/submit and transforms
 * the assessment view into a results panel.
 *
 * Expected shape of `data`:
 * {
 *   summary: [ { question_id, question_text, response, category }, … ],
 *   total_questions_answered: number,
 *   value_props_matched:      number,
 *   assets_matched:           number
 * }
 *
 * @param {Object} data - Parsed JSON from the /user/submit success response
 */
function showResults(data) {
  /* Hide the active assessment UI */
  const assessmentArea = document.getElementById("assessment-area");
  if (assessmentArea) assessmentArea.style.display = "none";

  /* Locate or create the results panel */
  let resultsPanel = document.getElementById("results-panel");
  if (!resultsPanel) {
    resultsPanel = document.createElement("section");
    resultsPanel.id        = "results-panel";
    resultsPanel.className = "results-panel";
    /* Insert after the assessment area (or append to main) */
    const main = document.querySelector("main") || document.body;
    main.appendChild(resultsPanel);
  }

  resultsPanel.style.display = "block";
  resultsPanel.innerHTML     = ""; /* clear stale content */

  /* --- Heading --- */
  const heading = document.createElement("h2");
  heading.textContent = "Assessment Complete";
  heading.className   = "results-heading";
  resultsPanel.appendChild(heading);

  /* --- Counts summary bar --- */
  const counts = document.createElement("div");
  counts.className = "results-counts";
  counts.innerHTML = `
    <div class="results-count-item">
      <span class="count-value">${data.total_questions_answered ?? "—"}</span>
      <span class="count-label">Questions Answered</span>
    </div>
    <div class="results-count-item">
      <span class="count-value">${data.value_props_matched ?? "—"}</span>
      <span class="count-label">Value Props Matched</span>
    </div>
    <div class="results-count-item">
      <span class="count-value">${data.assets_matched ?? "—"}</span>
      <span class="count-label">Assets Matched</span>
    </div>
  `;
  resultsPanel.appendChild(counts);

  /* --- Summary table --- */
  if (Array.isArray(data.summary) && data.summary.length > 0) {
    const tableWrapper       = document.createElement("div");
    tableWrapper.className   = "results-table-wrapper";
    tableWrapper.style.overflowX = "auto"; /* horizontal scroll on small screens */

    const table   = document.createElement("table");
    table.className = "results-table";
    table.innerHTML = `
      <thead>
        <tr>
          <th>Category</th>
          <th>Question</th>
          <th>Response</th>
        </tr>
      </thead>
    `;

    const tbody = document.createElement("tbody");

    data.summary.forEach((row) => {
      const tr = document.createElement("tr");

      /* Format array responses (select_all) as a comma-separated list */
      const responseText = Array.isArray(row.response)
        ? row.response.join(", ")
        : row.response ?? "—";

      tr.innerHTML = `
        <td>${escapeHTML(row.category      ?? "")}</td>
        <td>${escapeHTML(row.question_text ?? "")}</td>
        <td>${escapeHTML(responseText)}</td>
      `;
      tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    tableWrapper.appendChild(table);
    resultsPanel.appendChild(tableWrapper);
  }

  /* --- Action buttons --- */
  const actionsDiv       = document.createElement("div");
  actionsDiv.className   = "results-actions";

  /* Download report button */
  const downloadBtn      = document.createElement("button");
  downloadBtn.textContent = "📥 Download Report (Excel)";
  downloadBtn.className   = "btn btn--primary";
  downloadBtn.onclick     = downloadReport;

  /* Start New Assessment button */
  const newBtn      = document.createElement("button");
  newBtn.textContent = "🔄 Start New Assessment";
  newBtn.className   = "btn btn--secondary";
  newBtn.onclick     = () => {
    /* Clear session state so the landing page starts fresh */
    sessionStorage.removeItem("customer_name");
    sessionStorage.removeItem("se_name");
    window.location.href = "/";
  };

  actionsDiv.appendChild(downloadBtn);
  actionsDiv.appendChild(newBtn);
  resultsPanel.appendChild(actionsDiv);
}

/**
 * downloadReport — triggers a file-download of the Excel report
 * generated by the server at GET /user/export.
 * Uses a temporary anchor element to honour the Content-Disposition filename.
 */
async function downloadReport() {
  showSpinner(true);

  try {
    const response = await fetch("/user/export", {
      method:  "GET",
      headers: { "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
    });

    if (response.status === 401) {
      window.location.href = "/";
      return;
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    /* Convert response to a Blob and create an object URL for download */
    const blob        = await response.blob();
    const downloadUrl = URL.createObjectURL(blob);

    /* Derive filename from the Content-Disposition header, or fall back to default */
    const disposition = response.headers.get("Content-Disposition") || "";
    const fileMatch   = disposition.match(/filename[^;=\n]*=(?:(\\?['"])(.*?)\1|(?:[^\s]+'.*?')?([^;\n]*))/i);
    const filename    = fileMatch ? (fileMatch[2] || fileMatch[3] || "report.xlsx").trim() : "report.xlsx";

    const anchor   = document.createElement("a");
    anchor.href    = downloadUrl;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();

    /* Clean up the temporary anchor and object URL */
    anchor.remove();
    URL.revokeObjectURL(downloadUrl);

    showToast("Report downloaded successfully.", "success");
  } catch (err) {
    showToast(`Download failed: ${err.message}`, "error");
  } finally {
    showSpinner(false);
  }
}


/* =============================================================================
 * PRIVATE HELPERS
 * ============================================================================= */

/**
 * escapeHTML — sanitises a string for safe insertion into innerHTML.
 * Prevents XSS when rendering server-supplied or user-supplied text.
 *
 * @param {string} str - Raw string to escape
 * @returns {string} HTML-safe string
 */
function escapeHTML(str) {
  return String(str)
    .replace(/&/g,  "&amp;")
    .replace(/</g,  "&lt;")
    .replace(/>/g,  "&gt;")
    .replace(/"/g,  "&quot;")
    .replace(/'/g,  "&#39;");
}


/* =============================================================================
 * BOOT — DOMContentLoaded dispatcher
 * Detects which page is active (landing or assessment) and runs the matching
 * initialiser.  Both initialisers are no-ops if their key element is absent,
 * so this single handler is safe to include on every user-facing page.
 * ============================================================================= */
document.addEventListener("DOMContentLoaded", () => {
  /* Landing page: identified by the presence of #start-form */
  if (document.getElementById("start-form")) {
    initLandingPage();
  }

  /* Assessment page: identified by the presence of #assessment-step */
  if (document.getElementById("assessment-step")) {
    initAssessmentPage();
  }

  /* Wire navigation buttons (present on the assessment page template) */
  const btnPrev   = document.getElementById("btn-prev");
  const btnNext   = document.getElementById("btn-next");
  const btnSubmit = document.getElementById("btn-submit");

  if (btnPrev)   btnPrev.addEventListener("click",   prevStep);
  if (btnNext)   btnNext.addEventListener("click",   nextStep);
  if (btnSubmit) btnSubmit.addEventListener("click", submitAssessment);
});
