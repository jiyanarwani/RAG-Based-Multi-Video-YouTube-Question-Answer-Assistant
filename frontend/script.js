const API_BASE = ""; // same-origin — FastAPI serves this from /

// ── DOM refs ──────────────────────────────────────────────────────────────────
const urlInput      = document.getElementById("url-input");
const addBtn        = document.getElementById("add-btn");
const addBtnLabel   = addBtn.querySelector(".add-btn-label");
const addBtnSpinner = addBtn.querySelector(".add-btn-spinner");
const addError      = document.getElementById("add-error");

const videoList     = document.getElementById("video-list");
const videoCount    = document.getElementById("video-count");

const messages      = document.getElementById("messages");
const emptyState    = document.getElementById("empty-state");

const questionEl    = document.getElementById("question");
const sendBtn       = document.getElementById("send-btn");
const resetBtn      = document.getElementById("reset-btn");

const modal         = document.getElementById("modal");
const modalText     = document.getElementById("modal-text");
const modalCancel   = document.getElementById("modal-cancel");
const modalConfirm  = document.getElementById("modal-confirm");

let pendingDelete   = null;

// ── API helper ────────────────────────────────────────────────────────────────
async function api(path, opts = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const body = await res.json();
      msg = body.detail || msg;
    } catch (_) {}
    throw new Error(msg);
  }
  return res.json();
}

// ── Escape HTML ───────────────────────────────────────────────────────────────
function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// ── Videos ────────────────────────────────────────────────────────────────────
async function loadVideos() {
  try {
    const data = await api("/api/videos");
    renderVideos(data.videos);
    videoCount.textContent = data.count;
  } catch (err) {
    console.error("Failed to load videos:", err);
  }
}

function renderVideos(videos) {
  if (!videos || videos.length === 0) {
    videoList.innerHTML = `
      <div class="library-empty">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="7" width="20" height="14" rx="2"/>
          <path d="M16 7V5a2 2 0 0 0-4 0v2"/>
          <line x1="12" y1="12" x2="12" y2="16"/>
          <line x1="10" y1="14" x2="14" y2="14"/>
        </svg>
        <p>No videos yet</p>
      </div>`;
    videoCount.textContent = "0";
    return;
  }

  videoList.innerHTML = "";
  videoCount.textContent = videos.length;

  for (const v of videos) {
    const item = document.createElement("div");
    item.className = "video-item";
    item.innerHTML = `
      <div class="v-thumb">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
      </div>
      <div class="v-meta">
        <div class="v-title">${escapeHtml(v.title || v.video_id)}</div>
        ${v.channel ? `<div class="v-channel">${escapeHtml(v.channel)}</div>` : ""}
      </div>
      <button class="v-delete" title="Remove video" aria-label="Remove ${escapeHtml(v.title || v.video_id)}">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
          <path d="M10 11v6M14 11v6"/>
        </svg>
      </button>
    `;
    item.querySelector(".v-delete").addEventListener("click", () => openDeleteModal(v));
    videoList.appendChild(item);
  }
}

// ── Add video ────────────────────────────────────────────────────────────────
// NOTE: We listen directly on the button click AND on Enter key in the input,
// rather than using a <form> submit, to avoid any browser form-submission
// edge-cases that were causing the original "Add Video" button to silently fail.

function setAddLoading(loading) {
  addBtn.disabled = loading;
  addBtnLabel.hidden = loading;
  addBtnSpinner.hidden = !loading;
}

function showAddError(msg) {
  addError.textContent = msg;
  addError.hidden = false;
}

function clearAddError() {
  addError.textContent = "";
  addError.hidden = true;
}

async function handleAddVideo() {
  const url = urlInput.value.trim();
  if (!url) {
    showAddError("Please paste a YouTube URL first.");
    return;
  }

  clearAddError();
  setAddLoading(true);

  try {
    await api("/api/videos", {
      method: "POST",
      body: JSON.stringify({ url }),
    });
    urlInput.value = "";
    await loadVideos();
  } catch (err) {
    showAddError("Failed to add video: " + err.message);
  } finally {
    setAddLoading(false);
  }
}

addBtn.addEventListener("click", handleAddVideo);

urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    handleAddVideo();
  }
});

// ── Delete modal ──────────────────────────────────────────────────────────────
function openDeleteModal(v) {
  pendingDelete = v;
  modalText.textContent = `"${v.title || v.video_id}" will be removed from the knowledge base.`;
  modal.classList.remove("hidden");
}

function closeModal() {
  modal.classList.add("hidden");
  pendingDelete = null;
}

modalCancel.addEventListener("click", closeModal);

modal.addEventListener("click", (e) => {
  if (e.target === modal) closeModal();
});

modalConfirm.addEventListener("click", async () => {
  if (!pendingDelete) return;
  const v = pendingDelete;
  closeModal();
  try {
    await api(`/api/videos/${v.video_id}`, { method: "DELETE" });
    await loadVideos();
  } catch (err) {
    alert("Failed to delete video: " + err.message);
  }
});

// ── Reset / clear ─────────────────────────────────────────────────────────────
resetBtn.addEventListener("click", async () => {
  if (!confirm("Clear the entire knowledge base? All indexed videos will be removed.")) return;
  try {
    await api("/api/reset", { method: "POST" });
    await loadVideos();
    clearMessages();
  } catch (err) {
    alert("Reset failed: " + err.message);
  }
});

// ── Chat messages ─────────────────────────────────────────────────────────────
function clearMessages() {
  messages.innerHTML = "";
  const es = document.createElement("div");
  es.className = "empty-state";
  es.id = "empty-state";
  es.innerHTML = `
    <div class="empty-icon">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    </div>
    <h2 class="empty-heading">Ask anything about your videos</h2>
    <p class="empty-sub">Add a YouTube URL on the left, then ask a question below.</p>
  `;
  messages.appendChild(es);
}

function removeEmptyState() {
  const es = messages.querySelector(".empty-state");
  if (es) es.remove();
}

function appendUserMessage(text) {
  removeEmptyState();
  const row = document.createElement("div");
  row.className = "msg-row user";
  row.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  messages.appendChild(row);
  scrollToBottom();
  return row;
}

function appendAssistantMessage(text, sources) {
  const row = document.createElement("div");
  row.className = "msg-row assistant";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.appendChild(bubble);

  if (sources && sources.length > 0) {
    const sourcesEl = document.createElement("div");
    sourcesEl.className = "sources";
    for (const src of sources) {
      const a = document.createElement("a");
      a.className = "source-card";
      a.href = src.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.innerHTML = `
        <div class="source-icon">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        </div>
        <div>
          <div class="s-title">${escapeHtml(src.title || src.video_id)}</div>
          ${src.channel ? `<div class="s-channel">${escapeHtml(src.channel)}</div>` : ""}
        </div>
      `;
      sourcesEl.appendChild(a);
    }
    row.appendChild(sourcesEl);
  }

  messages.appendChild(row);
  scrollToBottom();
  return row;
}

function appendThinkingIndicator() {
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.innerHTML = `
    <div class="bubble">
      <div class="thinking">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  messages.appendChild(row);
  scrollToBottom();
  return row;
}

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

// ── Chat submit ───────────────────────────────────────────────────────────────
questionEl.addEventListener("input", () => {
  questionEl.style.height = "auto";
  questionEl.style.height = Math.min(questionEl.scrollHeight, 200) + "px";
});

questionEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    submitQuestion();
  }
});

sendBtn.addEventListener("click", submitQuestion);

async function submitQuestion() {
  const q = questionEl.value.trim();
  if (!q) return;

  questionEl.value = "";
  questionEl.style.height = "auto";
  sendBtn.disabled = true;

  appendUserMessage(q);
  const thinking = appendThinkingIndicator();

  try {
    const data = await api("/api/ask", {
      method: "POST",
      body: JSON.stringify({ question: q }),
    });
    thinking.remove();
    appendAssistantMessage(data.answer, data.sources);
  } catch (err) {
    thinking.remove();
    appendAssistantMessage("Something went wrong: " + err.message, []);
  } finally {
    sendBtn.disabled = false;
    questionEl.focus();
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
loadVideos();
