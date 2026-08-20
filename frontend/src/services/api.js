import { API_URL } from "../config.js";

async function request(path, { method = "GET", body, params } = {}) {
  let url = `${API_URL}${path}`;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    if (qs) url += `?${qs}`;
  }
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  const token = window.localStorage.getItem("chat_agent_access_token");
  const res = await fetch(url, {
    method,
    headers: {
      ...(body && !isFormData ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? (isFormData ? body : JSON.stringify(body)) : undefined,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new Error(data?.detail || `${method} ${path} → ${res.status}`);
  }
  return data;
}

export const api = {
  // ── Health ─────────────────────────────────────────────────
  // GET /  and GET /health
  getRoot: () => request("/api/v1/"),
  getHealth: () => request("/api/v1/health"),

  // ── Sessions ──────────────────────────────────────────────
  // POST /session/create   body: { session_id, user_id }
  createSession: (session_id, user_id) =>
    request("/api/v1/session/create", { method: "POST", body: { session_id, user_id } }),
  // GET /sessions/{user_id}?limit=
  getSessions: (user_id, limit = 20) =>
    request(`/api/v1/sessions/${user_id}`, { params: { limit } }),
  // DELETE /session/delete?session_id=
  deleteSession: (session_id) =>
    request("/api/v1/session/delete", { method: "DELETE", params: { session_id } }),

  // ── Chat history / messages ───────────────────────────────
  // GET /chat/{session_id}?limit=
  getChatHistory: (session_id, limit = 50) =>
    request(`/api/v1/chat/${session_id}`, { params: { limit } }),
  getConversationCount: (session_id) =>
    request(`/api/v1/sessions/${session_id}/conversation-count`),
  getConversationMessages: (session_id, limit = 50) =>
    request(`/api/v1/sessions/${session_id}/conversation-messages`, { params: { limit } }),
  summarizeConversation: (session_id, messages) =>
    request(`/api/v1/sessions/${session_id}/summarize`, {
      method: "POST",
      body: { messages },
    }),
  replaceWithSummary: (session_id, summary) =>
    request(`/api/v1/sessions/${session_id}/replace-with-summary`, {
      method: "POST",
      body: { summary },
    }),


    
  // POST /message   body: message dict (server stamps `timestamp`)
  saveMessage: (message) =>
    request("/api/v1/message", { method: "POST", body: message }),
  // DELETE /chat/{session_id}
  clearChat: (session_id) =>
    request(`/api/v1/chat/${session_id}`, { method: "DELETE" }),
  // POST /agent/run   body: { query: { text, files }, session_id, user_id, agent_name }
  runAgent: (payload) =>
    request("/api/v1/agent/run", { method: "POST", body: payload }),

  streamAgent: async (payload, onEvent) => {
    const normalizedPayload = {
      query: {
        text: String(payload?.query?.text ?? ""),
        files: Array.isArray(payload?.query?.files) ? payload.query.files : [],
      },
      session_id: String(payload?.session_id ?? ""),
      user_id: String(payload?.user_id ?? "anonymous"),
      agent_name: String(payload?.agent_name || "generic").toLowerCase(),
    };

    const res = await fetch(`${API_URL}/api/v1/agent/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        ...(window.localStorage.getItem("chat_agent_access_token")
          ? { Authorization: `Bearer ${window.localStorage.getItem("chat_agent_access_token")}` }
          : {}),
      },
      body: JSON.stringify(normalizedPayload),
    });

    if (!res.ok || !res.body) {
      const text = await res.text();
      let data = null;
      try { data = text ? JSON.parse(text) : null; } catch { /* plain text error */ }
      throw new Error(data?.detail || text || `POST /api/v1/agent/stream → ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const event of events) {
          const line = event.split("\n").find((item) => item.startsWith("data:"));
          if (!line) continue;
          const envelope = JSON.parse(line.slice(5).trim());
          onEvent(envelope);
          if (envelope.type === "completed" || envelope.type === "error") return;
        }

        if (done) break;
      }
    } finally {
      reader.releaseLock();
    }
  },
  // GET /workspace/{session_id}
  getWorkspace: (session_id) => request(`/api/v1/workspace/${session_id}`),

  // ── Documents (Knowledge Management) ──────────────────────
  // GET /documents/get
  getDocuments: () => request("/api/v1/documents/get"),
  // POST /documents/store   body: document dict
  storeDocument: (document) =>
    request("/api/v1/documents/store", { method: "POST", body: document }),
  // DELETE /documents/{document_id}
  deleteDocument: (document_id) =>
    request(`/api/v1/documents/${document_id}`, { method: "DELETE" }),
  parseDocument: (file, options) => {
    const form = new FormData();
    form.append("file", file);
    form.append("options", JSON.stringify(options));
    return request("/api/v1/documents/parse", { method: "POST", body: form });
  },
  parseDocumentUrl: (urls, options) =>
    request("/api/v1/documents/parse-url", { method: "POST", body: { urls, options } }),
  generateChunks: (content) =>
    request("/api/v1/documents/chunks", { method: "POST", body: { content } }),
  generateEmbeddings: (chunks) =>
    request("/api/v1/documents/embeddings", { method: "POST", body: { chunks } }),
  storeDocumentEmbeddings: (payload) =>
    request("/api/v1/documents/store-embeddings", { method: "POST", body: payload }),

  // ── Users / auth ──────────────────────────────────────────
  // POST /user/login   body: { email_id, password }  → { success, user_id }
  login: (email_id, password) =>
    request("/api/v1/user/login", { method: "POST", body: { email_id, password } }),
  // GET /user/logout/{user_id}
  logout: (user_id) =>
    request(`/api/v1/user/logout/${user_id}`),
  // POST /users   body: user dict
  createUser: (user) => request("/api/v1/users", { method: "POST", body: user }),
  // GET /users/{email_id}
  getUser: (email_id) => request(`/api/v1/users/${email_id}`),
  // GET /admin?email_id=
  getAdmin: (email_id) => request("/api/v1/admin", { params: { email_id } }),
  // POST /users/status?user_id=&logged_in=   (query params, no body — matches
  // the server signature `update_user_status(user_id: str, logged_in: bool)`)
  updateUserStatus: (user_id, logged_in) =>
    request("/api/v1/users/status", { method: "POST", params: { user_id, logged_in } }),

  // ── Metrics (RAG Evaluation) ──────────────────────────────
  // GET /metrics/averages
  getAverageMetrics: () => request("/api/v1/metrics/averages"),
  evaluateRagFile: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/v1/metrics/evaluate", { method: "POST", body: form });
  },
};

export default api;
