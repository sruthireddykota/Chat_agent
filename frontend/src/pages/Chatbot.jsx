import { useState, useRef, useEffect, useCallback } from "react";
import {
  Plus,
  Eraser,
  Send,
  X,
  PanelRightOpen,
  PanelRightClose,
  PanelLeftOpen,
  PanelLeftClose,
  Bot,
  Activity,
  Paperclip,
  Loader2,
} from "lucide-react";
import AppShell from "../components/AppShell.jsx";
import { Badge } from "../components/ui.jsx";
import AgentPills from "../components/AgentPills.jsx";
import ChatSidebar from "../components/ChatSidebar.jsx";
import ChatMessage from "../components/ChatMessage.jsx";
import PlanPrompt from "../components/PlanPrompt.jsx";
import AgentActivityPanel from "../components/AgentActivityPanel.jsx";
import { useApp } from "../context/AppContext.jsx";
import { useAgentChat } from "../hooks/useAgentChat.js";
import { api } from "../services/api.js";

const uid = () => "s-" + Math.random().toString(36).slice(2, 8);

export default function Chatbot() {
  const {
    user,
    selectedAgent,
    setSelectedAgent,
    sessions,
    setSessions,
    currentSessionId,
    setCurrentSessionId,
  } = useApp();

  const [input, setInput] = useState("");
  const [attachment, setAttachment] = useState(null);
  const [summarizing, setSummarizing] = useState(false);
  const [summaryError, setSummaryError] = useState(null);
  const [showPanel, setShowPanel] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [panelWidth, setPanelWidth] = useState(400);
  const scrollRef = useRef(null);
  const rowRef = useRef(null);
  const draggingRef = useRef(false);
  const fileInputRef = useRef(null);

  const isCoder = selectedAgent === "Coder";
  const userId = user?.user_id || user?.email || "anonymous";

  // Load history for a session from the API (falls back to empty on error).
  const historyLoader = useCallback(async (sid) => {
    try {
      const rows = await api.getChatHistory(sid);
      return (rows || []).map((m) => ({
        role: m.role,
        content: m.content,
        image: m.sources || undefined,
      }));
    } catch {
      return [];
    }
  }, []);

  const {
    running,
    messages,
    tasks,
    usage,
    prompt,
    startRun,
    respond,
    clear,
  } = useAgentChat(currentSessionId, { historyLoader });

  const usageTotal = (usage?.input ?? 0) + (usage?.output ?? 0);

  const loadWorkspace = useCallback(async (sid) => {
    if (!sid) return;
    try {
      const result = await api.getWorkspace(sid);
      setSessions((previous) => previous.map((session) => (
        session.id === sid ? { ...session, files: result?.files || {} } : session
      )));
    } catch {
      // Workspace is only available for sessions handled by the Coder agent.
    }
  }, [setSessions]);

  const refreshSessions = useCallback(async () => {
    try {
      const rows = await api.getSessions(userId);
      setSessions((previous) => rows.map((session) => {
        const existing = previous.find((item) => item.id === session.session_id);
        return {
          id: session.session_id,
          title: session.title || "New Chat",
          agent: session.agent_name || existing?.agent || "Sample",
          files: existing?.files || {},
        };
      }));
    } catch {
      // Keep the current session list if the API is temporarily unavailable.
    }
  }, [setSessions, userId]);

  useEffect(() => {
    if (isCoder && currentSessionId) loadWorkspace(currentSessionId);
  }, [currentSessionId, isCoder, loadWorkspace]);

  // Load the session list from the API on mount (fallback: keep whatever's in context).
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const rows = await api.getSessions(userId);
        if (alive && rows?.length) {
          setSessions(rows.map((s) => ({
            id: s.session_id,
            title: s.title || "New Chat",
            agent: s.agent_name || "Sample",
            files: {},
          })));
          if (!currentSessionId) setCurrentSessionId(rows[0].session_id);
        } else if (alive && !currentSessionId) {
          const sid = uid();
          const session = { id: sid, title: "New Chat", agent: selectedAgent, files: {} };
          setSessions([session]);
          setCurrentSessionId(sid);
          try { await api.createSession(sid, userId); } catch { /* local fallback remains usable */ }
        }
      } catch {
        /* backend not up — keep mock sessions */
      }
    })();
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  useEffect(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  }, [messages.length, running, summarizing, summaryError]);

  // Resizable activity panel.
  const onDragMove = useCallback((e) => {
    if (!draggingRef.current || !rowRef.current) return;
    const rect = rowRef.current.getBoundingClientRect();
    setPanelWidth(Math.min(640, Math.max(300, rect.right - e.clientX)));
  }, []);
  const stopDrag = useCallback(() => {
    draggingRef.current = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }, []);
  useEffect(() => {
    window.addEventListener("mousemove", onDragMove);
    window.addEventListener("mouseup", stopDrag);
    return () => {
      window.removeEventListener("mousemove", onDragMove);
      window.removeEventListener("mouseup", stopDrag);
    };
  }, [onDragMove, stopDrag]);
  const startDrag = () => {
    draggingRef.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  const newChat = async () => {
    const sid = uid();
    const session = { id: sid, title: "New Chat", agent: selectedAgent, files: {} };
    setSessions([session, ...sessions]);
    setCurrentSessionId(sid);
    try { await api.createSession(sid, userId); } catch { /* offline ok */ }
  };

  const clearChat = async () => {
    clear();
    try { await api.clearChat(currentSessionId); } catch { /* offline ok */ }
  };

  const deleteSession = async (id) => {
    const remaining = sessions.filter((s) => s.id !== id);
    setSessions(remaining);
    if (id === currentSessionId) setCurrentSessionId(remaining[0]?.id ?? null);
    try { await api.deleteSession(id); } catch { /* offline ok */ }
  };

  const AGENT_MAP = {
    Generic: "generic",
    Coder: "coder",
    Researcher: "researcher",
    RAG: "rag",
  };

  const send = async () => {
    const text = input.trim();
    if ((!text && !attachment) || running || summarizing) return;
    let sid = currentSessionId;
    if (!sid) {
      sid = uid();
      const session = { id: sid, title: "New Chat", agent: selectedAgent, files: {} };
      setSessions((previous) => [session, ...previous]);
      setCurrentSessionId(sid);
      try { await api.createSession(sid, userId); } catch { /* agent can still use the generated id */ }
    }
    const files = attachment ? [attachment] : [];
    // The message has been submitted; clear the composer immediately while
    // the conversation summary or agent response is being processed.
    setInput("");
    setAttachment(null);
    setSummaryError(null);
    setSummarizing(true);
    try {
      const countResult = await api.getConversationCount(sid);
      const count = Number(countResult?.count || 0);

      if (count >= 7) {
        const conversationResult = await api.getConversationMessages(sid, count);
        const conversationMessages = conversationResult?.messages || [];
        const summaryResult = await api.summarizeConversation(sid, conversationMessages);
        if (!summaryResult?.summary) throw new Error("Conversation summary was empty.");
        await api.replaceWithSummary(sid, summaryResult.summary);
      }
    } catch (error) {
      setSummaryError(error?.message || "Could not summarize the conversation.");
      setSummarizing(false);
      return;
    }
    setSummarizing(false);

    await startRun({
      type: "run",
      query: text || "Please analyze the attached file.",
      session_id: sid,
      agent_name: AGENT_MAP[selectedAgent], 
      user_id: userId,
      files,
      metadata: {},
    });
    await refreshSessions();
    await loadWorkspace(sid);
  };

  const selectAttachment = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const [, data] = String(reader.result).split(",");
      setAttachment({ name: file.name, type: file.type || "application/octet-stream", data });
    };
    reader.readAsDataURL(file);
    event.target.value = "";
  };

  const activityProps = {
    tasks,
    usage,
    files: sessions.find((s) => s.id === currentSessionId)?.files ?? {},
    isCoder,
  };

  return (
    <AppShell maxWidth="max-w-none">
      <div ref={rowRef} className="flex gap-4">
        {showSidebar && (
          <ChatSidebar
            sessions={sessions}
            currentSessionId={currentSessionId}
            selectedAgent={selectedAgent}
            onSelectAgent={setSelectedAgent}
            onSelectSession={setCurrentSessionId}
            onNewChat={newChat}
            onClearChat={clearChat}
            onDeleteSession={deleteSession}
          />
        )}

        <section className="flex h-[calc(100vh-8rem)] min-w-0 flex-1 flex-col rounded-2xl border border-slate-200 bg-white">
          <div className="flex items-center justify-between gap-2 border-b border-slate-100 px-4 py-3 sm:px-5">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowSidebar((v) => !v)}
                className="hidden rounded-lg border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50 lg:block"
                title={showSidebar ? "Collapse sidebar" : "Expand sidebar"}
              >
                {showSidebar ? <PanelLeftClose size={17} /> : <PanelLeftOpen size={17} />}
              </button>
              <h2 className="text-lg font-bold text-brand-700">Chat Agent</h2>
              <Badge color={isCoder ? "green" : "blue"}>{selectedAgent}</Badge>
            </div>
            <div className="flex items-center gap-2">
              {usageTotal > 0 && (
                <span className="hidden items-center gap-1 rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-semibold text-slate-600 sm:inline-flex">
                  <Activity size={13} className="text-brand-500" />
                  {usageTotal.toLocaleString()} tok
                </span>
              )}
              <button
                onClick={() => setShowPanel((v) => !v)}
                className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-semibold transition ${
                  showPanel
                    ? "border-brand-200 bg-brand-50 text-brand-700"
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {showPanel ? <PanelRightClose size={15} /> : <PanelRightOpen size={15} />}
                Activity
              </button>
            </div>
          </div>

          <div
            className={`flex flex-wrap items-center gap-2 border-b border-slate-100 px-4 py-2 sm:px-5 ${
              showSidebar ? "lg:hidden" : ""
            }`}
          >
            <AgentPills value={selectedAgent} onChange={setSelectedAgent} />
            <div className="ml-auto flex gap-1.5">
              <button onClick={newChat} className="flex items-center gap-1.5 rounded-lg bg-brand-50 px-2.5 py-1.5 text-xs font-semibold text-brand-700 hover:bg-brand-100">
                <Plus size={14} /> New
              </button>
              <button onClick={clearChat} className="flex items-center gap-1.5 rounded-lg bg-amber-50 px-2.5 py-1.5 text-xs font-semibold text-amber-700 hover:bg-amber-100">
                <Eraser size={14} /> Clear
              </button>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-5">
            {messages.length > 0 ? (
              messages.map((m, i) => (
                <ChatMessage key={i} message={m} onAnswer={(v) => prompt && respond(prompt.request_id, v)} />
              ))
            ) : (
              <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
                <div className="grid h-14 w-14 place-items-center rounded-2xl bg-brand-50 text-brand-600">
                  <Bot size={26} />
                </div>
                <div>
                  <p className="font-semibold text-slate-700">Start a conversation</p>
                  <p className="max-w-sm text-sm text-slate-400">
                    You&apos;re chatting with the <b className="text-slate-600">{selectedAgent}</b>{" "}
                    agent. It streams its plan, tool calls, and tasks as it works.
                  </p>
                </div>
              </div>
            )}

            {/* Clarification / approval prompt (pinned to the end of the thread) */}
            {prompt && (
              <div className="flex gap-3">
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand-600 text-white">
                  <Bot size={16} />
                </div>
                <div className="min-w-0 flex-1">
                  <PlanPrompt
                    plan={
                      prompt.kind === "approval"
                        ? { kind: "approval", summary: prompt.summary }
                        : { kind: "clarification", questions: prompt.questions }
                    }
                    onAnswer={(v) => respond(prompt.request_id, v)}
                  />
                </div>
              </div>
            )}

            {summarizing && (
              <div className="flex gap-3">
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-brand-600 text-white">
                  <Bot size={16} />
                </div>
                <div className="flex items-center gap-2 rounded-2xl border border-brand-100 bg-brand-50 px-4 py-3 text-sm text-brand-700">
                  <Loader2 size={15} className="animate-spin" />
                  Summarizing our conversation, please wait…
                </div>
              </div>
            )}

            {summaryError && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {summaryError}
              </div>
            )}

            {running && !summarizing && !prompt && !messages.some((message) => message.streaming) && (
              <div className="flex gap-3">
                <div className="grid h-8 w-8 place-items-center rounded-full bg-brand-600 text-white">
                  <Bot size={16} />
                </div>
                <div className="flex items-center gap-1 rounded-2xl border border-slate-200 bg-white px-4 py-3">
                  <span className="typing-dot h-2 w-2 rounded-full bg-slate-400" />
                  <span className="typing-dot h-2 w-2 rounded-full bg-slate-400" style={{ animationDelay: "0.2s" }} />
                  <span className="typing-dot h-2 w-2 rounded-full bg-slate-400" style={{ animationDelay: "0.4s" }} />
                </div>
              </div>
            )}
          </div>

          <div className="border-t border-slate-100 p-4">
            {attachment && (
              <div className="mb-2 flex items-center gap-2 rounded-lg border border-brand-100 bg-brand-50 px-3 py-2 text-xs text-brand-700">
                <Paperclip size={14} />
                <span className="min-w-0 flex-1 truncate">{attachment.name}</span>
                <button type="button" onClick={() => setAttachment(null)} className="font-bold hover:text-brand-900">×</button>
              </div>
            )}
            <div className="flex items-end gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.pdf,.txt,.csv,.json,.md,.py,.js,.jsx,.ts,.tsx"
                className="hidden"
                onChange={selectAttachment}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={running || summarizing}
                className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-50"
                title="Attach a file"
              >
                <Paperclip size={18} />
              </button>
              <textarea
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder={summarizing ? "Summarizing our conversation…" : running ? "Agent is working…" : "Enter your query…"}
                className="max-h-32 flex-1 resize-none rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
              />
              <button
                onClick={send}
                disabled={(!input.trim() && !attachment) || running || summarizing}
                className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-brand-600 text-white transition hover:bg-brand-700 disabled:bg-brand-300"
                title="Send"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        </section>

        {showPanel && (
          <>
            <div
              onMouseDown={startDrag}
              className="hidden w-1.5 shrink-0 cursor-col-resize items-center justify-center rounded-full bg-transparent hover:bg-brand-200 lg:flex"
              title="Drag to resize"
            >
              <div className="h-10 w-1 rounded-full bg-slate-300" />
            </div>
            <div className="hidden shrink-0 flex-col lg:flex" style={{ width: panelWidth }}>
              <div className="mb-2 flex items-center gap-2 px-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                <Activity size={13} /> Agent activity
              </div>
              <AgentActivityPanel {...activityProps} className="h-[calc(100vh-9.75rem)]" />
            </div>
          </>
        )}
      </div>

      {showPanel && (
        <div className="mt-4 lg:hidden">
          <div className="mb-2 flex items-center gap-2 px-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
            <Activity size={13} /> Agent activity
          </div>
          <AgentActivityPanel {...activityProps} className="h-[70vh]" />
        </div>
      )}
    </AppShell>
  );
}
