import { useEffect, useState } from "react";
import { Gauge, ListTodo, FolderTree, ChevronDown } from "lucide-react";
import TaskList from "./TaskList.jsx";
import FileExplorerPanel from "./FileExplorerPanel.jsx";
import { CONTEXT_WINDOW } from "../data/mockData.js";

// Compact, collapsible token-usage section pinned to the bottom of the panel.
function MetricsFooter({ usage }) {
  const [open, setOpen] = useState(false);
  const input = usage?.input ?? 0;
  const output = usage?.output ?? 0;
  const total = input + output;
  const pct = Math.min(100, (total / CONTEXT_WINDOW) * 100);

  return (
    <div className="border-t border-slate-200 bg-slate-50/60">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        <Gauge size={13} className="shrink-0 text-slate-400" />
        <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          Tokens
        </span>
        <span className="ml-auto text-xs font-semibold text-slate-600">
          {total.toLocaleString()}
        </span>
        <ChevronDown
          size={13}
          className={`text-slate-400 transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {open && (
        <div className="px-3 pb-3">
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: "Input", value: input, cls: "text-slate-700" },
              { label: "Output", value: output, cls: "text-brand-600" },
              { label: "Total", value: total, cls: "text-slate-900" },
            ].map((m) => (
              <div key={m.label} className="rounded-lg bg-white px-2 py-1.5">
                <div className={`text-sm font-bold ${m.cls}`}>
                  {m.value.toLocaleString()}
                </div>
                <div className="text-[10px] uppercase tracking-wide text-slate-400">
                  {m.label}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-2">
            <div className="mb-1 flex justify-between text-[10px] text-slate-400">
              <span>context window</span>
              <span>{CONTEXT_WINDOW.toLocaleString()}</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full rounded-full bg-brand-500 transition-all"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AgentActivityPanel({
  tasks,
  usage,
  files = {},
  isCoder = false,
  className = "",
}) {
  const [tab, setTab] = useState("tasks");
  useEffect(() => {
    if (!isCoder) setTab("tasks");
  }, [isCoder]);

  return (
    <div
      className={`flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white ${className}`}
    >
      {/* Header / tabs — tasks get top billing */}
      {isCoder ? (
        <div className="flex gap-1 border-b border-slate-200 px-2 pt-2">
          {[
            { id: "tasks", label: "Tasks", Icon: ListTodo },
            { id: "files", label: "Files", Icon: FolderTree },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 rounded-t-lg px-3 py-2 text-sm font-semibold transition ${
                tab === t.id
                  ? "border-b-2 border-brand-500 text-brand-700"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <t.Icon size={15} /> {t.label}
            </button>
          ))}
        </div>
      ) : (
        <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700">
          <ListTodo size={16} className="text-brand-500" /> Tasks
        </div>
      )}

      {/* Main content */}
      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === "files" && isCoder ? (
          <FileExplorerPanel
            files={files}
            className="h-full rounded-none border-0"
          />
        ) : (
          <TaskList tasks={tasks} />
        )}
      </div>

      {/* Compact metrics at the bottom */}
      <MetricsFooter usage={usage} />
    </div>
  );
}
