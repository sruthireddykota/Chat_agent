import { Plus, Eraser, Trash2 } from "lucide-react";
import AgentPills from "./AgentPills.jsx";

export default function ChatSidebar({
  sessions,
  currentSessionId,
  selectedAgent,
  onSelectAgent,
  onSelectSession,
  onNewChat,
  onClearChat,
  onDeleteSession,
}) {
  return (
    <aside className="hidden h-[calc(100vh-8rem)] w-52 shrink-0 flex-col rounded-2xl border border-slate-200 bg-white lg:flex">
      <div className="border-b border-slate-100 p-3">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Select Agent
        </div>
        <AgentPills value={selectedAgent} onChange={onSelectAgent} />
        <div className="mt-3 flex gap-2">
          <button
            onClick={onNewChat}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-brand-50 px-3 py-2 text-sm font-semibold text-brand-700 hover:bg-brand-100"
          >
            <Plus size={15} /> New
          </button>
          <button
            onClick={onClearChat}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-700 hover:bg-amber-100"
          >
            <Eraser size={15} /> Clear
          </button>
        </div>
      </div>
      <div className="flex-1 space-y-1 overflow-y-auto p-3">
        <div className="px-1 pb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
          Sessions
        </div>
        {sessions.map((s) => {
          const active = s.id === currentSessionId;
          return (
            <div
              key={s.id}
              className={`group flex items-center gap-1 rounded-lg px-2 py-2 text-sm transition ${
                active
                  ? "bg-brand-50 text-brand-800"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <button
                onClick={() => onSelectSession(s.id)}
                className="flex flex-1 items-center gap-2 truncate text-left"
              >
                <span
                  className={`h-2 w-2 shrink-0 rounded-full ${
                    active ? "bg-brand-500" : "bg-slate-300"
                  }`}
                />
                <span className="truncate">{s.title || "New Chat"}</span>
              </button>
              <button
                onClick={() => onDeleteSession(s.id)}
                className="rounded p-1 text-slate-300 opacity-0 hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
                title="Delete session"
              >
                <Trash2 size={14} />
              </button>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
