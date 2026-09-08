const form = document.querySelector("#review-form");
const fileInput = document.querySelector("#document");
const fileDrop = document.querySelector("#file-drop");
const fileTitle = document.querySelector("#file-title");
const fileDetail = document.querySelector("#file-detail");
const claimInput = document.querySelector("#claim");
const claimCount = document.querySelector("#claim-count");
const verifyButton = document.querySelector("#verify-button");
const sampleButton = document.querySelector("#sample-button");
const statusRegion = document.querySelector("#status-region");
const statusTitle = document.querySelector("#status-title");
const statusCopy = document.querySelector("#status-copy");
const errorRegion = document.querySelector("#error-region");
const errorMessage = document.querySelector("#error-message");
const errorRequest = document.querySelector("#error-request");
const resultRegion = document.querySelector("#result-region");
const reloadButton = document.querySelector("#reload-review");

let selectedFile = null;
let uploadedDocumentId = null;
let currentReviewId = null;

function setSelectedFile(file) {
  selectedFile = file || null;
  uploadedDocumentId = null;
  if (!selectedFile) {
    fileTitle.textContent = "Choose a source file";
    fileDetail.textContent = "or drop it here";
    return;
  }
  fileTitle.textContent = selectedFile.name;
  fileDetail.textContent = formatBytes(selectedFile.size);
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function showStatus(title, copy) {
  errorRegion.hidden = true;
  statusTitle.textContent = title;
  statusCopy.textContent = copy;
  statusRegion.hidden = false;
}

function setBusy(isBusy) {
  verifyButton.disabled = isBusy;
  sampleButton.disabled = isBusy;
  fileInput.disabled = isBusy;
  claimInput.disabled = isBusy;
  verifyButton.querySelector("span").textContent = isBusy ? "Verifying…" : "Run verification";
}

function showError(error) {
  statusRegion.hidden = true;
  resultRegion.hidden = true;
  errorMessage.textContent = error.message || "Please check the source and try again.";
  errorRequest.textContent = error.requestId ? `Request reference: ${error.requestId}` : "";
  errorRequest.hidden = !error.requestId;
  errorRegion.hidden = false;
  errorRegion.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function apiRequest(url, options = {}) {
  const response = await fetch(url, options);
  const requestId = response.headers.get("X-Request-ID");
  let body;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (!response.ok) {
    const error = new Error(body?.error?.message || "The service could not complete the request.");
    error.requestId = body?.error?.request_id || requestId;
    throw error;
  }
  return body;
}

async function uploadSource() {
  const data = new FormData();
  data.append("file", selectedFile);
  const document = await apiRequest("/documents", { method: "POST", body: data });
  uploadedDocumentId = document.document_id;
  return document;
}

async function createReview() {
  return apiRequest("/reviews", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: uploadedDocumentId, claim: claimInput.value.trim() }),
  });
}

function renderReview(review) {
  currentReviewId = review.review_id;
  document.querySelector("#verdict-label").textContent = review.verdict.replaceAll("_", " ");
  document.querySelector("#verdict-label").className = `verdict-label ${review.verdict.toLowerCase().replaceAll("_", "-")}`;
  document.querySelector("#review-claim").textContent = review.claim;
  document.querySelector("#review-reasoning").textContent = review.reasoning;
  document.querySelector("#review-id").textContent = review.review_id;
  document.querySelector("#review-model").textContent = review.model;
  document.querySelector("#review-created").textContent = new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium", timeStyle: "short"
  }).format(new Date(review.created_at));

  const evidenceList = document.querySelector("#evidence-list");
  evidenceList.replaceChildren();
  document.querySelector("#evidence-count").textContent = `${review.evidence.length} passage${review.evidence.length === 1 ? "" : "s"}`;
  if (!review.evidence.length) {
    const empty = document.createElement("p");
    empty.className = "empty-evidence";
    empty.textContent = "No passage was strong enough to establish or contradict the claim. This is a deliberate outcome, not a missing result.";
    evidenceList.append(empty);
  } else {
    for (const evidence of review.evidence) {
      const item = document.createElement("article");
      item.className = "evidence-item";
      const header = document.createElement("header");
      const location = document.createElement("span");
      location.textContent = `Page ${evidence.page} · ${evidence.evidence_id}`;
      const score = document.createElement("span");
      score.textContent = `Relevance ${evidence.retrieval_score.toFixed(3)}`;
      header.append(location, score);
      const quote = document.createElement("blockquote");
      quote.textContent = evidence.text;
      item.append(header, quote);
      evidenceList.append(item);
    }
  }

  statusRegion.hidden = true;
  errorRegion.hidden = true;
  resultRegion.hidden = false;
  const url = new URL(window.location.href);
  url.searchParams.set("review", review.review_id);
  window.history.replaceState({}, "", url);
  resultRegion.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadSavedReview(reviewId, { scroll = true } = {}) {
  showStatus("Loading the saved review", "Reading the persisted review artifact from storage.");
  try {
    const review = await apiRequest(`/reviews/${encodeURIComponent(reviewId)}`);
    renderReview(review);
    if (!scroll) window.scrollTo({ top: 0 });
  } catch (error) {
    showError(error);
  }
}

fileInput.addEventListener("change", () => setSelectedFile(fileInput.files[0]));
claimInput.addEventListener("input", () => { claimCount.textContent = `${claimInput.value.length.toLocaleString()} / 2,000`; });

for (const eventName of ["dragenter", "dragover"]) {
  fileDrop.addEventListener(eventName, (event) => {
    event.preventDefault();
    fileDrop.classList.add("dragging");
  });
}
for (const eventName of ["dragleave", "drop"]) {
  fileDrop.addEventListener(eventName, (event) => {
    event.preventDefault();
    fileDrop.classList.remove("dragging");
  });
}
fileDrop.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (file) setSelectedFile(file);
});

sampleButton.addEventListener("click", async () => {
  setBusy(true);
  try {
    const response = await fetch("/samples/sample_report.txt");
    if (!response.ok) throw new Error("The sample source is not available.");
    const content = await response.blob();
    const file = new File([content], "sample_report.txt", { type: "text/plain" });
    setSelectedFile(file);
    claimInput.value = "Revenue increased by 27 percent in the second quarter.";
    claimInput.dispatchEvent(new Event("input"));
    claimInput.focus();
    errorRegion.hidden = true;
  } catch (error) {
    showError(error);
  } finally {
    setBusy(false);
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedFile) {
    showError(new Error("Choose a TXT or text-based PDF source before running the review."));
    fileInput.focus();
    return;
  }
  if (claimInput.value.trim().length < 3) {
    showError(new Error("Enter one specific claim with at least three characters."));
    claimInput.focus();
    return;
  }

  try {
    await runCurrentReview();
  } catch (error) {
    showError(error);
  }
});

async function runCurrentReview() {
  setBusy(true);
  resultRegion.hidden = true;
  try {
    if (!uploadedDocumentId) {
      showStatus("Preparing the source", "Extracting text, preserving page references, and storing the source artifact.");
      await uploadSource();
    }
    showStatus("Checking the claim", "Retrieving relevant passages and asking the verifier for a grounded decision.");
    const review = await createReview();
    renderReview(review);
    return review;
  } finally {
    setBusy(false);
  }
}

reloadButton.addEventListener("click", () => {
  if (currentReviewId) loadSavedReview(currentReviewId);
});

async function checkHealth() {
  const indicator = document.querySelector(".service-status");
  try {
    const response = await fetch("/health");
    if (!response.ok) throw new Error();
    indicator.classList.add("ready");
    document.querySelector("#service-status").textContent = "Service ready";
  } catch {
    indicator.classList.add("unavailable");
    document.querySelector("#service-status").textContent = "Service unavailable";
  }
}

checkHealth();
const reviewFromUrl = new URL(window.location.href).searchParams.get("review");
if (reviewFromUrl) loadSavedReview(reviewFromUrl, { scroll: false });

function registerModelTool() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  const lifecycle = new AbortController();
  const registration = context.registerTool(
    {
      name: "verify_text_claim",
      title: "Verify a text claim",
      description: "Store a plain-text source, verify one factual claim against it, save the grounded review, and display the result in this workspace.",
      inputSchema: {
        type: "object",
        properties: {
          sourceText: { type: "string", minLength: 1, maxLength: 500000 },
          claim: { type: "string", minLength: 3, maxLength: 2000 },
          filename: { type: "string", minLength: 1, maxLength: 250 },
        },
        required: ["sourceText", "claim"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: true },
      async execute(input) {
        if (!input || typeof input.sourceText !== "string" || typeof input.claim !== "string") {
          throw new Error("sourceText and claim are required strings.");
        }
        const sourceText = input.sourceText.trim();
        const claim = input.claim.trim();
        const requestedName = typeof input.filename === "string" ? input.filename.trim() : "agent_source.txt";
        const filename = requestedName.endsWith(".txt") && !/[\\/\u0000-\u001f]/.test(requestedName)
          ? requestedName
          : "agent_source.txt";
        if (!sourceText || sourceText.length > 500000) throw new Error("sourceText must contain 1 to 500,000 characters.");
        if (claim.length < 3 || claim.length > 2000) throw new Error("claim must contain 3 to 2,000 characters.");

        setSelectedFile(new File([sourceText], filename, { type: "text/plain" }));
        claimInput.value = claim;
        claimInput.dispatchEvent(new Event("input"));
        try {
          const review = await runCurrentReview();
          return {
            reviewId: review.review_id,
            verdict: review.verdict,
            reasoning: review.reasoning,
            evidenceCount: review.evidence.length,
          };
        } catch (error) {
          showError(error);
          throw error;
        }
      },
    },
    { signal: lifecycle.signal },
  );
  Promise.resolve(registration).catch(() => {});
}

registerModelTool();
