const form = document.querySelector("#auditForm");
const statusPanel = document.querySelector("#status");
const errorPanel = document.querySelector("#error");
const reportFrame = document.querySelector("#reportFrame");
const report = document.querySelector("#report");
const printButton = document.querySelector("#printButton");
const resetButton = document.querySelector("#resetButton");
const sampleButton = document.querySelector("#sampleButton");
const urlInput = document.querySelector("#url");
const submitButton = form.querySelector("button");

function setLoading(isLoading) {
  statusPanel.hidden = !isLoading;
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading
    ? "Audit in corso..."
    : "Avvia audit demo";
}

function showError(message) {
  errorPanel.hidden = false;
  errorPanel.textContent = message;
}

function clearError() {
  errorPanel.hidden = true;
  errorPanel.textContent = "";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();
  reportFrame.hidden = true;
  setLoading(true);

  const formData = new FormData(form);
  const payload = {
    url: formData.get("url"),
    device: formData.get("device"),
  };

  try {
    const response = await fetch("/api/audit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Audit non riuscito.");
    }

    report.srcdoc = result.html_report;
    reportFrame.hidden = false;
    reportFrame.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
});

printButton.addEventListener("click", () => {
  report.contentWindow.focus();
  report.contentWindow.print();
});

resetButton.addEventListener("click", () => {
  reportFrame.hidden = true;
  clearError();
  form.reset();
  urlInput.focus();
});

sampleButton.addEventListener("click", () => {
  urlInput.value = "https://www.python.org/";
  urlInput.focus();
});
