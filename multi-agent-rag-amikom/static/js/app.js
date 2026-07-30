/**
 * Multi-Agent RAG AMIKOM — Main UI Script
 * PRD V1.2 Remediation: Sinkronisasi penuh ID DOM, navigasi, state, dan API contract.
 */

// ─── Global error boundary ─────────────────────────────────────────────────
window.onerror = (msg, src, line, col, err) => {
  console.error("[APP ERROR]", msg, src, line, col, err);
  showToast("Terjadi error pada aplikasi: " + msg, "error");
};
window.addEventListener("unhandledrejection", (e) => {
  console.error("[UNHANDLED REJECTION]", e.reason);
});

// ─── DOM Selectors (single contract) ─────────────────────────────────────────
const DOM = {
  // Input
  queryInput:    () => document.getElementById("query-input"),
  sendButton:    () => document.getElementById("send-button"),
  charCounter:   () => document.getElementById("char-counter"),
  // Messages
  messagesArea:  () => document.getElementById("messages-area"),
  welcomeContainer: () => document.getElementById("welcome-container"),
  // Sidebar status
  statusReadiness: () => document.getElementById("status-readiness"),
  statusBackend:   () => document.getElementById("status-backend"),
  statusFaiss:     () => document.getElementById("status-faiss"),
  statusSqlite:    () => document.getElementById("status-sqlite"),
  statusE5:        () => document.getElementById("status-e5"),
  // Navigation
  navItems:      () => document.querySelectorAll(".nav-item"),
  pages:         () => document.querySelectorAll(".page-content"),
  pageTitle:     () => document.getElementById("page-title"),
  // Controls
  menuToggle:    () => document.getElementById("menu-toggle"),
  sidebar:       () => document.getElementById("sidebar"),
  clearChatBtn:  () => document.getElementById("btn-clear-chat"),
  toggleSources: () => document.getElementById("btn-toggle-sources"),
  sourcesPanel:  () => document.getElementById("sources-panel"),
  closeSourcesBtn: () => document.getElementById("btn-close-sources"),
  sourcesContent:  () => document.getElementById("sources-content"),
  // Status page
  statusGrid:    () => document.getElementById("status-grid"),
  // Toast
  toastContainer: () => document.getElementById("toast-container"),
};

// ─── Initialization guard ─────────────────────────────────────────────────────
const REQUIRED_IDS = [
  "query-input", "send-button", "messages-area", "welcome-container",
  "char-counter", "status-readiness", "status-backend",
  "status-faiss", "status-sqlite", "status-e5",
  "sources-panel", "toast-container", "menu-toggle",
];

function checkRequiredElements() {
  const missing = REQUIRED_IDS.filter(id => !document.getElementById(id));
  if (missing.length > 0) {
    console.error("[INIT ERROR] Missing required DOM elements:", missing);
    document.body.insertAdjacentHTML("afterbegin",
      `<div style="position:fixed;top:0;left:0;right:0;background:#ef4444;color:#fff;
        padding:1rem;z-index:9999;font-family:monospace;font-size:0.85rem;">
        [INIT ERROR] Elemen DOM wajib tidak ditemukan: ${missing.join(", ")}
      </div>`
    );
    return false;
  }
  return true;
}

// ─── App State ────────────────────────────────────────────────────────────────
const STATE = {
  sessionId: crypto.randomUUID ? crypto.randomUUID() : ("sess-" + Date.now()),
  isLoading: false,
  currentPage: "chat",
  messageCount: 0,
};

// ─── Main Initialization ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  if (!checkRequiredElements()) return;

  initNavigation();
  initChat();
  initControls();
  fetchHealthAndReadiness();

  // Interval refresh status setiap 30 detik
  setInterval(fetchHealthAndReadiness, 30000);
});

// ─── Navigation ───────────────────────────────────────────────────────────────
const PAGE_TITLES = {
  chat:    "Chat Akademik",
  sources: "Sumber Dokumen",
  status:  "Status Sistem",
};

function initNavigation() {
  DOM.navItems().forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const page = item.dataset.page;
      if (page) navigateTo(page);
    });
    item.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        const page = item.dataset.page;
        if (page) navigateTo(page);
      }
    });
  });
}

function navigateTo(page) {
  STATE.currentPage = page;

  // Update nav active state
  DOM.navItems().forEach(item => {
    item.classList.toggle("active", item.dataset.page === page);
  });

  // Update page visibility
  DOM.pages().forEach(p => {
    p.classList.toggle("active", p.id === `page-${page}`);
  });

  // Update page title
  const titleEl = DOM.pageTitle();
  if (titleEl) titleEl.textContent = PAGE_TITLES[page] || page;

  // Close mobile sidebar
  const sidebar = DOM.sidebar();
  if (sidebar && window.innerWidth < 768) {
    sidebar.classList.remove("open");
  }

  // If navigating to status, refresh data
  if (page === "status") {
    fetchHealthAndReadiness(true);
  }
}

// ─── Chat Initialization ──────────────────────────────────────────────────────
function initChat() {
  const input = DOM.queryInput();
  const sendBtn = DOM.sendButton();

  if (!input || !sendBtn) {
    console.error("[INIT] chat input or send button not found");
    return;
  }

  // Char counter
  input.addEventListener("input", () => {
    const len = input.value.length;
    const counter = DOM.charCounter();
    if (counter) counter.textContent = len;
    sendBtn.disabled = len === 0 || STATE.isLoading;
    // Auto-resize
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 120) + "px";
  });

  // Enter = send, Shift+Enter = newline
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const query = input.value.trim();
      if (query && !STATE.isLoading) submitQuery(query);
    }
  });

  // Send button click
  sendBtn.addEventListener("click", () => {
    const query = DOM.queryInput()?.value.trim();
    if (query && !STATE.isLoading) submitQuery(query);
  });

  // Quick action buttons
  document.querySelectorAll(".quick-action-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const query = btn.getAttribute("data-query");
      if (query && !STATE.isLoading) submitQuery(query);
    });
    btn.addEventListener("keydown", (e) => {
      if ((e.key === "Enter" || e.key === " ") && !STATE.isLoading) {
        e.preventDefault();
        const query = btn.getAttribute("data-query");
        if (query) submitQuery(query);
      }
    });
  });
}

// ─── Controls (clear, sidebar, sources) ───────────────────────────────────────
function initControls() {
  // Mobile menu toggle
  DOM.menuToggle()?.addEventListener("click", () => {
    DOM.sidebar()?.classList.toggle("open");
  });

  // Clear chat
  DOM.clearChatBtn()?.addEventListener("click", clearChat);

  // Toggle sources panel
  DOM.toggleSources()?.addEventListener("click", () => {
    DOM.sourcesPanel()?.classList.toggle("open");
  });

  // Close sources panel
  DOM.closeSourcesBtn()?.addEventListener("click", () => {
    DOM.sourcesPanel()?.classList.remove("open");
  });
}

// ─── Query Submission ─────────────────────────────────────────────────────────
async function submitQuery(queryText) {
  if (STATE.isLoading) return;
  STATE.isLoading = true;
  STATE.messageCount++;

  const input = DOM.queryInput();
  const sendBtn = DOM.sendButton();
  const counter = DOM.charCounter();

  // Hide welcome screen
  const welcome = DOM.welcomeContainer();
  if (welcome) welcome.style.display = "none";

  // Append user message
  appendUserMessage(queryText);

  // Clear and disable input
  if (input) { input.value = ""; input.style.height = "auto"; }
  if (counter) counter.textContent = "0";
  if (sendBtn) sendBtn.disabled = true;

  // Show loading
  const loadingId = appendLoadingMessage();

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    const res = await fetch("/api/v1/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        query: queryText,
        session_id: STATE.sessionId,
        user_context: { cohort: "2025" },
        requested_mode: "AUTO",
      }),
    });

    clearTimeout(timeout);
    removeMessage(loadingId);

    const data = await res.json();

    if (res.ok) {
      appendBotMessage(data);
      renderCitations(data.citations || []);
    } else {
      const msg = data.message || data.detail || "Terjadi kesalahan pada server.";
      appendErrorMessage(msg);
    }
  } catch (e) {
    removeMessage(loadingId);
    if (e.name === "AbortError") {
      appendErrorMessage("Request timeout — server tidak merespons dalam 30 detik. Coba lagi.");
    } else {
      appendErrorMessage("Gagal terhubung ke server: " + e.message);
    }
  } finally {
    STATE.isLoading = false;
    if (sendBtn && input) sendBtn.disabled = input.value.length === 0;
  }
}

// ─── Message Renderers ────────────────────────────────────────────────────────
function appendUserMessage(text) {
  const area = DOM.messagesArea();
  if (!area) return;

  const el = document.createElement("div");
  el.className = "message user";
  el.innerHTML = `
    <div class="avatar user-avatar" aria-label="Pengguna">
      <i class="fas fa-user" aria-hidden="true"></i>
    </div>
    <div class="message-content">
      <p>${escapeHtml(text)}</p>
    </div>`;
  area.appendChild(el);
  area.scrollTop = area.scrollHeight;
}

function appendLoadingMessage() {
  const area = DOM.messagesArea();
  const id = "loading-" + Date.now();

  const el = document.createElement("div");
  el.className = "message bot loading-message";
  el.id = id;
  el.innerHTML = `
    <div class="avatar bot-avatar" aria-label="AI">
      <i class="fas fa-robot" aria-hidden="true"></i>
    </div>
    <div class="message-content">
      <div class="loading-dots">
        <span></span><span></span><span></span>
      </div>
      <p class="loading-text">Memproses pertanyaan Anda...</p>
    </div>`;
  area?.appendChild(el);
  area?.scrollTo({ top: area.scrollHeight, behavior: "smooth" });
  return id;
}

function removeMessage(id) {
  document.getElementById(id)?.remove();
}

const MODE_COLORS = {
  ANSWER:    { bg: "rgba(16,185,129,0.15)", border: "#10b981", text: "#34d399" },
  ABSTAIN:   { bg: "rgba(245,158,11,0.15)", border: "#f59e0b", text: "#fbbf24" },
  REFUSE:    { bg: "rgba(239,68,68,0.15)",  border: "#ef4444", text: "#fca5a5" },
  HANDOFF:   { bg: "rgba(99,102,241,0.15)", border: "#6366f1", text: "#a5b4fc" },
  ESCALATE:  { bg: "rgba(168,85,247,0.15)", border: "#a855f7", text: "#c084fc" },
  ASK_CONTEXT: { bg: "rgba(59,130,246,0.15)", border: "#3b82f6", text: "#93c5fd" },
  LIVE_CHECK_OR_ABSTAIN: { bg: "rgba(245,158,11,0.15)", border: "#f59e0b", text: "#fbbf24" },
};

function appendBotMessage(data) {
  const area = DOM.messagesArea();
  if (!area) return;

  const mode = data.mode || "ANSWER";
  const modeStyle = MODE_COLORS[mode] || MODE_COLORS.ANSWER;

  const agentTags = (data.agents || (data.agent_used ? [data.agent_used] : []))
    .map(a => `<span class="badge badge-agent">${escapeHtml(a)}</span>`).join("");

  const modeBadge = `<span class="badge badge-mode" style="background:${modeStyle.bg};color:${modeStyle.text};border-color:${modeStyle.border};">
    ${escapeHtml(mode)}
  </span>`;

  const backendBadge = data.retrieval_backend
    ? `<span class="badge badge-backend">${escapeHtml(data.retrieval_backend)}</span>` : "";

  const freshnessHtml = data.freshness_notice
    ? `<div class="freshness-notice"><i class="fas fa-exclamation-triangle" aria-hidden="true"></i> ${escapeHtml(data.freshness_notice)}</div>`
    : "";

  const handoffHtml = data.handoff
    ? `<div class="handoff-notice"><i class="fas fa-arrow-right" aria-hidden="true"></i> ${escapeHtml(data.handoff)}</div>` : "";

  const verificationHtml = data.verification && !data.verification.passed && data.verification.flags?.length
    ? `<div class="verification-flags"><i class="fas fa-shield-alt"></i> Flags: ${data.verification.flags.map(escapeHtml).join(", ")}</div>` : "";

  const latency = data.latency_ms != null ? `<span class="latency">${data.latency_ms}ms</span>` : "";

  const el = document.createElement("div");
  el.className = "message bot";
  el.innerHTML = `
    <div class="avatar bot-avatar" aria-label="AI">
      <i class="fas fa-robot" aria-hidden="true"></i>
    </div>
    <div class="message-content">
      <div class="answer-text">${escapeHtml(data.answer || "").replace(/\n/g, "<br>")}</div>
      ${freshnessHtml}
      ${handoffHtml}
      ${verificationHtml}
      <div class="meta-tags">
        ${modeBadge}
        ${agentTags}
        ${backendBadge}
        ${latency}
      </div>
    </div>`;
  area.appendChild(el);
  area.scrollTo({ top: area.scrollHeight, behavior: "smooth" });
}

function appendErrorMessage(text) {
  const area = DOM.messagesArea();
  if (!area) return;

  const el = document.createElement("div");
  el.className = "message bot error-message";
  el.innerHTML = `
    <div class="avatar error-avatar" aria-label="Error">
      <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
    </div>
    <div class="message-content error-content">
      <p>${escapeHtml(text)}</p>
    </div>`;
  area.appendChild(el);
  area.scrollTo({ top: area.scrollHeight, behavior: "smooth" });
}

// ─── Citations / Source Panel ─────────────────────────────────────────────────
function renderCitations(citations) {
  const content = DOM.sourcesContent();
  if (!content) return;

  if (!citations || citations.length === 0) {
    content.innerHTML = `
      <div class="sources-empty">
        <i class="fas fa-search" aria-hidden="true"></i>
        <p>Tidak ada sitasi untuk respons ini.</p>
      </div>`;
    return;
  }

  content.innerHTML = citations.map((cit, idx) => `
    <div class="citation-card" tabindex="0" role="article" aria-label="Sitasi ${idx + 1}">
      <div class="citation-index">[${idx + 1}]</div>
      <div class="citation-source">${escapeHtml(cit.title || cit.source_id || "—")}</div>
      <div class="citation-detail">
        <span class="detail-label">Source ID:</span>
        <span class="detail-value">${escapeHtml(cit.source_id || "—")}</span>
      </div>
      <div class="citation-detail">
        <span class="detail-label">Chunk ID:</span>
        <span class="detail-value">${escapeHtml(cit.chunk_id || "—")}</span>
      </div>
      <div class="citation-detail">
        <span class="detail-label">Locator:</span>
        <span class="detail-value">${escapeHtml(cit.locator || "—")}</span>
      </div>
    </div>
  `).join("");

  // Auto-open sources panel when there are citations
  DOM.sourcesPanel()?.classList.add("open");
}

// ─── Clear Chat ───────────────────────────────────────────────────────────────
function clearChat() {
  const area = DOM.messagesArea();
  const welcome = DOM.welcomeContainer();
  const sourcesContent = DOM.sourcesContent();
  const sourcesPanel = DOM.sourcesPanel();

  // Remove all messages
  if (area) {
    // Remove all children except welcome-container
    Array.from(area.children).forEach(child => {
      if (child.id !== "welcome-container") child.remove();
    });
  }

  // Show welcome screen
  if (welcome) welcome.style.display = "";

  // Clear sources
  if (sourcesContent) {
    sourcesContent.innerHTML = `
      <div class="sources-empty">
        <i class="fas fa-search" aria-hidden="true"></i>
        <p>Sumber akan muncul setelah Anda bertanya</p>
      </div>`;
  }
  sourcesPanel?.classList.remove("open");

  // Reset session
  STATE.sessionId = crypto.randomUUID ? crypto.randomUUID() : ("sess-" + Date.now());
  STATE.messageCount = 0;
  STATE.isLoading = false;

  const sendBtn = DOM.sendButton();
  if (sendBtn) sendBtn.disabled = true;

  showToast("Percakapan telah dihapus", "info");
}

// ─── Health & Readiness ───────────────────────────────────────────────────────
async function fetchHealthAndReadiness(updateStatusPage = false) {
  try {
    const [healthRes, readinessRes] = await Promise.allSettled([
      fetch("/api/v1/health"),
      fetch("/api/v1/readiness"),
    ]);

    let health = null, readiness = null;

    if (healthRes.status === "fulfilled" && healthRes.value.ok) {
      health = await healthRes.value.json();
    }
    if (readinessRes.status === "fulfilled" && readinessRes.value.ok) {
      readiness = await readinessRes.value.json();
    }

    updateSidebarStatus(health, readiness);

    if (updateStatusPage) {
      updateStatusPageGrid(health, readiness);
    }
  } catch (e) {
    console.warn("[STATUS] Failed to fetch health/readiness:", e);
    setStatusIndicator("status-readiness", "DEGRADED", "degraded");
  }
}

function updateSidebarStatus(health, readiness) {
  // Readiness badge
  const readinessBadge = DOM.statusReadiness();
  if (readinessBadge && readiness) {
    const status = readiness.status || (readiness.development_ready ? "DEV_READY" : "DEGRADED");
    const cls = status === "FINAL_READY" || status === "VALIDATED" ? "pass" :
                status === "DEGRADED" || status === "REMEDIATION_REQUIRED" ? "degraded" : "partial";
    readinessBadge.textContent = status;
    readinessBadge.className = `status-badge ${cls}`;
  } else if (readinessBadge) {
    readinessBadge.textContent = "UNKNOWN";
    readinessBadge.className = "status-badge degraded";
  }

  // Backend badge
  const backendBadge = DOM.statusBackend();
  if (backendBadge) {
    const backend = readiness?.runtime?.retrieval_backend || health?.retrieval_backend || "—";
    backendBadge.textContent = backend;
    const isFull = backend === "E5_FAISS";
    backendBadge.className = `status-badge ${isFull ? "pass" : backend === "BM25_FALLBACK" ? "degraded" : ""}`;
  }

  // Component indicators
  setStatusIndicator("status-faiss",
    readiness?.runtime?.faiss || health?.faiss, null, true);
  setStatusIndicator("status-sqlite",
    readiness?.runtime?.sqlite || health?.sqlite, null, true);
  setStatusIndicator("status-e5",
    readiness?.runtime?.e5 || health?.e5_model, null, true);
}

function setStatusIndicator(id, value, cls, isIndicator = false) {
  const el = document.getElementById(id);
  if (!el) return;

  if (isIndicator) {
    const icon = el.querySelector("i") || el;
    const pass = value === "PASS" || value === true;
    const missing = value === "MISSING" || value === false || value == null;
    icon.style.color = missing ? "#ef4444" : pass ? "#10b981" : "#f59e0b";
    icon.title = String(value || "UNKNOWN");
    return;
  }

  if (cls) el.className = `status-badge ${cls}`;
}

function updateStatusPageGrid(health, readiness) {
  const grid = DOM.statusGrid();
  if (!grid) return;

  const r = readiness || {};
  const h = health || {};

  const items = [
    { label: "Readiness Status", value: r.status || "UNKNOWN",
      pass: r.status === "FINAL_READY" || r.status === "VALIDATED" },
    { label: "Development Ready", value: r.development_ready ? "YES" : "NO", pass: !!r.development_ready },
    { label: "Implementation Validated", value: r.implementation_validated ? "YES" : "NO", pass: !!r.implementation_validated },
    { label: "UI Ready", value: r.ui_ready ? "YES" : "NO", pass: !!r.ui_ready },
    { label: "Final Ready", value: r.final_ready ? "YES" : "NO", pass: !!r.final_ready },
    { label: "Retrieval Backend", value: r.runtime?.retrieval_backend || h.retrieval_backend || "UNKNOWN",
      pass: (r.runtime?.retrieval_backend || h.retrieval_backend) === "E5_FAISS" },
    { label: "FAISS Index", value: r.runtime?.faiss || h.faiss || "UNKNOWN",
      pass: (r.runtime?.faiss || h.faiss) === "PASS" },
    { label: "SQLite DB", value: r.runtime?.sqlite || h.sqlite || "UNKNOWN",
      pass: (r.runtime?.sqlite || h.sqlite) === "PASS" },
    { label: "E5 Model", value: r.runtime?.e5 || h.e5_model || "UNKNOWN",
      pass: (r.runtime?.e5 || h.e5_model) === "PASS" },
    { label: "Corpus", value: r.runtime?.corpus || h.corpus || "UNKNOWN",
      pass: (r.runtime?.corpus || h.corpus) === "PASS" },
    { label: "Git Commit", value: (r.git_commit || h.git_commit || "—").slice(0, 8), pass: true },
  ];

  grid.innerHTML = items.map(item => `
    <div class="status-card-item">
      <div class="status-card-label">${escapeHtml(item.label)}</div>
      <div class="status-card-value ${item.pass ? "pass" : "fail"}">${escapeHtml(String(item.value))}</div>
    </div>
  `).join("");
}

// ─── Toast Notifications ──────────────────────────────────────────────────────
function showToast(message, type = "info") {
  const container = DOM.toastContainer();
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.setAttribute("role", "alert");
  toast.innerHTML = `
    <i class="fas fa-${type === "error" ? "exclamation-circle" : type === "info" ? "info-circle" : "check-circle"}" aria-hidden="true"></i>
    <span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  setTimeout(() => toast.classList.add("show"), 10);
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function escapeHtml(text) {
  if (text == null) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
