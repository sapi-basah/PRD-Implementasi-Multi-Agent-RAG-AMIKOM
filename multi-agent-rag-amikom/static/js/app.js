document.addEventListener("DOMContentLoaded", () => {
  const chatInput = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  const chatMessages = document.getElementById("chat-messages");
  const sourcesContent = document.getElementById("sources-content");
  const charCount = document.getElementById("char-count");
  const readinessBadge = document.getElementById("readiness-badge");

  // Load readiness status
  fetchReadiness();

  // Handle textarea input & char count
  chatInput?.addEventListener("input", () => {
    const len = chatInput.value.length;
    if (charCount) charCount.textContent = len;
    if (sendBtn) sendBtn.disabled = len === 0;
  });

  // Handle Enter / Shift+Enter
  chatInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (chatInput.value.trim()) {
        sendQuery(chatInput.value.trim());
      }
    }
  });

  sendBtn?.addEventListener("click", () => {
    if (chatInput.value.trim()) {
      sendQuery(chatInput.value.trim());
    }
  });

  // Quick action buttons
  document.querySelectorAll(".quick-action-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const query = btn.getAttribute("data-query");
      if (query) {
        sendQuery(query);
      }
    });
  });

  async function fetchReadiness() {
    try {
      const res = await fetch("/api/v1/readiness");
      const data = await res.json();
      if (readinessBadge) {
        readinessBadge.textContent = data.development_ready?.status
          ? `DEV_READY (${data.retrieval_backend})`
          : "DEGRADED";
        readinessBadge.className = `badge ${
          data.development_ready?.status ? "dev" : "bm25"
        }`;
      }
    } catch (e) {
      console.warn("Failed to fetch readiness", e);
    }
  }

  async function sendQuery(queryText) {
    // Hide welcome box if visible
    const welcomeBox = document.querySelector(".welcome-box");
    if (welcomeBox) welcomeBox.style.display = "none";

    // Append user message
    appendUserMessage(queryText);
    chatInput.value = "";
    if (charCount) charCount.textContent = "0";
    if (sendBtn) sendBtn.disabled = true;

    // Append loading indicator
    const loadingId = appendLoadingMessage();

    try {
      const res = await fetch("/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryText }),
      });

      const data = await res.json();
      removeMessage(loadingId);

      if (res.ok) {
        appendBotMessage(data);
        renderSources(data.citations || []);
      } else {
        appendErrorMessage(data.detail || "Terjadi kesalahan pada server.");
      }
    } catch (e) {
      removeMessage(loadingId);
      appendErrorMessage("Gagal terhubung ke server: " + e.message);
    }
  }

  function appendUserMessage(text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message user";
    msgDiv.innerHTML = `
      <div class="avatar"><i class="fas fa-user"></i></div>
      <div class="message-content">
        <p>${escapeHtml(text)}</p>
      </div>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendLoadingMessage() {
    const id = "loading-" + Date.now();
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot";
    msgDiv.id = id;
    msgDiv.innerHTML = `
      <div class="avatar"><i class="fas fa-robot"></i></div>
      <div class="message-content">
        <p><i class="fas fa-spinner fa-spin"></i> Memproses pertanyaan Anda...</p>
      </div>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
  }

  function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function appendBotMessage(data) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot";

    const agentTag = data.agent_used
      ? `<span class="badge">${escapeHtml(data.agent_used)}</span>`
      : "";
    const modeTag = data.mode
      ? `<span class="badge dev">Mode: ${escapeHtml(data.mode)}</span>`
      : "";
    const backendTag = data.retrieval_backend
      ? `<span class="badge bm25">${escapeHtml(data.retrieval_backend)}</span>`
      : "";
    const freshnessNotice = data.freshness_notice
      ? `<div style="margin-top:0.5rem; font-size:0.8rem; color:#f59e0b;"><i class="fas fa-exclamation-triangle"></i> ${escapeHtml(data.freshness_notice)}</div>`
      : "";

    msgDiv.innerHTML = `
      <div class="avatar"><i class="fas fa-robot"></i></div>
      <div class="message-content">
        <p>${escapeHtml(data.answer).replace(/\n/g, "<br>")}</p>
        ${freshnessNotice}
        <div class="meta-tags">
          ${agentTag}
          ${modeTag}
          ${backendTag}
          <span style="font-size:0.75rem; color:#94a3b8; align-self:center;">${data.latency_ms || 0}ms</span>
        </div>
      </div>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendErrorMessage(text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot";
    msgDiv.innerHTML = `
      <div class="avatar" style="background:#ef4444;"><i class="fas fa-exclamation-triangle"></i></div>
      <div class="message-content" style="border-color:#ef4444;">
        <p style="color:#fca5a5;">${escapeHtml(text)}</p>
      </div>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function renderSources(citations) {
    if (!sourcesContent) return;

    if (!citations || citations.length === 0) {
      sourcesContent.innerHTML = `
        <div class="sources-empty">
          <i class="fas fa-search"></i>
          <p>Tidak ada sitasi dokumen untuk respon ini.</p>
        </div>
      `;
      return;
    }

    let html = "";
    citations.forEach((cit, idx) => {
      html += `
        <div class="citation-card">
          <div style="font-weight:600; color:#818cf8; margin-bottom:0.25rem;">[${idx + 1}] Source: ${escapeHtml(cit.source_id)}</div>
          <div style="font-size:0.8rem; color:#cbd5e1;">Chunk ID: ${escapeHtml(cit.chunk_id)}</div>
          <div style="font-size:0.75rem; color:#94a3b8;">Locator: ${escapeHtml(cit.locator)}</div>
        </div>
      `;
    });

    sourcesContent.innerHTML = html;
  }

  function escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
