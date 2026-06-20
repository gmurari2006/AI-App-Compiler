const state = {
  activeTab: "schema",
  status: null,
  results: null,
  logs: [],
};

const elements = {
  compilerStatus: document.querySelector("#compilerStatus"),
  projectName: document.querySelector("#projectName"),
  pipelineGrid: document.querySelector("#pipelineGrid"),
  apiCount: document.querySelector("#apiCount"),
  tableCount: document.querySelector("#tableCount"),
  pageCount: document.querySelector("#pageCount"),
  fileCount: document.querySelector("#fileCount"),
  emptyState: document.querySelector("#emptyState"),
  resultsPanel: document.querySelector("#resultsPanel"),
  tabContent: document.querySelector("#tabContent"),
  tabs: document.querySelectorAll(".tab"),
  downloadButton: document.querySelector("#downloadButton"),
  generateForm: document.querySelector("#generateForm"),
  promptInput: document.querySelector("#promptInput"),
  generateButton: document.querySelector("#generateButton"),
  formMessage: document.querySelector("#formMessage"),
};

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = data.detail || data.message || "Request failed";
    throw new Error(message);
  }

  return data;
}

async function loadLogs() {
  try {
    const data = await requestJson("/logs");
    state.logs = data.logs || [];
  } catch {
    state.logs = [];
  }
}

function setLoading(isLoading) {
  elements.generateButton.disabled = isLoading;
  elements.generateButton.querySelector("span").textContent = isLoading ? "Generating" : "Generate";
}

function setMessage(message, isError = false) {
  elements.formMessage.textContent = message || "";
  elements.formMessage.classList.toggle("error", isError);
}

function updateMetrics(metrics) {
  elements.apiCount.textContent = metrics.apis;
  elements.tableCount.textContent = metrics.tables;
  elements.pageCount.textContent = metrics.pages;
  elements.fileCount.textContent = metrics.files;
}

function updateStatus(status) {
  state.status = status;
  elements.compilerStatus.textContent = status.generated ? "Generated project available" : "No project generated yet";
  elements.projectName.textContent = status.projectName || "";
  elements.projectName.classList.toggle("hidden", !status.projectName);
  elements.downloadButton.classList.toggle("disabled", !status.generated);
  elements.downloadButton.setAttribute("aria-disabled", String(!status.generated));
  updateMetrics(status.metrics);
  renderPipeline(status.stages);
}

function renderPipeline(stages) {
  elements.pipelineGrid.innerHTML = stages
    .map((stage, index) => {
      const statusClass = stage.status === "complete" ? "complete" : "pending";
      return `
        <article class="stage-card ${statusClass}">
          <span class="stage-index">${index + 1}</span>
          <h3>${escapeHtml(stage.name)}</h3>
          <small>${escapeHtml(stage.status)}</small>
        </article>
      `;
    })
    .join("");
}

function updateResults(results) {
  state.results = results;

  if (!results.generated) {
    elements.emptyState.classList.remove("hidden");
    elements.resultsPanel.classList.add("hidden");
    elements.tabContent.innerHTML = "";
    return;
  }

  elements.emptyState.classList.add("hidden");
  elements.resultsPanel.classList.remove("hidden");
  renderActiveTab();
}

function renderActiveTab() {
  if (!state.results || !state.results.generated) {
    return;
  }

  elements.tabs.forEach((tab) => {
    const isActive = tab.dataset.tab === state.activeTab;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
  });

  if (state.activeTab === "structure") {
  renderStructure(state.results.tabs.structure);
  return;
}

if (state.activeTab === "logs") {
  renderLogs();
  return;
}

renderFiles(state.results.tabs[state.activeTab] || []);

  renderFiles(state.results.tabs[state.activeTab] || []);
}

function renderFiles(files) {
  if (!files.length) {
    elements.tabContent.innerHTML =
      `<p class="empty-note">${emptyMessageForTab(state.activeTab)}</p>`;
    return;
  }

  const firstFile = files[0];

  elements.tabContent.innerHTML = `
    <div class="file-explorer">

      <div class="file-sidebar">
        ${files
          .map(
            (file, index) => `
              <div
                class="file-item ${index === 0 ? "active" : ""}"
                data-index="${index}"
              >
                ${escapeHtml(file.path)}
              </div>
            `
          )
          .join("")}
      </div>

      <div class="file-viewer">
        <div class="file-header">
          ${escapeHtml(firstFile.path)}
        </div>

        <pre id="code-viewer">
<code>${escapeHtml(firstFile.content)}</code>
        </pre>
      </div>

    </div>
  `;

  document.querySelectorAll(".file-item").forEach((item) => {
    item.addEventListener("click", () => {

      document
        .querySelectorAll(".file-item")
        .forEach((x) => x.classList.remove("active"));

      item.classList.add("active");

      const file = files[Number(item.dataset.index)];

      document.querySelector(".file-header").textContent =
        file.path;

      document.querySelector("#code-viewer code").textContent =
        file.content;
    });
  });
}
function renderStructure(structure) {
  if (!structure) {
    elements.tabContent.innerHTML = `<p class="empty-note">No project structure found in generated_app.</p>`;
    return;
  }

  elements.tabContent.innerHTML = `
    <article class="file-block">
      <header class="file-title">
        <span>generated_app</span>
        <span>tree</span>
      </header>
      <pre><code>${escapeHtml(structure)}</code></pre>
    </article>
  `;
}

function renderLogs() {
  if (!state.logs.length) {
    elements.tabContent.innerHTML =
      `<p class="empty-note">No compiler logs available.</p>`;
    return;
  }

  elements.tabContent.innerHTML = `
    <article class="file-block">
      <header class="file-title">
        <span>Compiler Logs</span>
        <span>${state.logs.length} entries</span>
      </header>
      <pre><code>${escapeHtml(state.logs.join("\n"))}</code></pre>
    </article>
  `;
}

function emptyMessageForTab(tab) {
  const messages = {
    schema: "No schema files found in generated_app.",
    backend: "No backend files found in generated_app/backend.",
    frontend: "No frontend files found in generated_app/frontend.",
    logs: "No log files found in generated_app.",
  };
  return messages[tab] || "No generated files found.";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function refreshDashboard() {
  const [status, results] = await Promise.all([
    requestJson("/status"),
    requestJson("/results")
  ]);

  updateStatus(status);
  updateResults(results);

  await loadLogs();
}

async function handleGenerate(event) {
  event.preventDefault();
  const prompt = elements.promptInput.value.trim();

  if (!prompt) {
    setMessage("Prompt is required.", true);
    return;
  }

  setLoading(true);
  setMessage("");

  try {
    const response = await requestJson("/generate", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    });
    updateStatus(response.status);
    updateResults(response.results);

    await loadLogs();

    setMessage(response.message, !response.ok);
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    setLoading(false);
  }
}

function bindEvents() {
  elements.generateForm.addEventListener("submit", handleGenerate);
  elements.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      state.activeTab = tab.dataset.tab;
      renderActiveTab();
    });
  });
}

bindEvents();
refreshDashboard().catch((error) => {
  elements.compilerStatus.textContent = "Unable to load project status";
  setMessage(error.message, true);
});
