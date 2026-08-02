import { useState } from "react";
import {
  Terminal,
  Wrench,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Loader2,
} from "lucide-react";

// Inline card for a single tool invocation or shell command in the chat stream.
export default function ToolCallCard({ block }) {
  const [open, setOpen] = useState(false);
  const isShell = block.kind === "shell";
  const Icon = isShell ? Terminal : Wrench;

  const statusIcon =
    block.status === "success" ? (
      <CheckCircle2 size={14} className="text-emerald-500" />
    ) : block.status === "error" ? (
      <XCircle size={14} className="text-red-500" />
    ) : (
      <Loader2 size={14} className="animate-spin text-brand-500" />
    );

  const title = isShell ? block.command : block.name;

  return (
    <div className="my-1.5 overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        <ChevronRight
          size={14}
          className={`shrink-0 text-slate-400 transition-transform ${
            open ? "rotate-90" : ""
          }`}
        />
        <Icon size={14} className="shrink-0 text-slate-500" />
        <span className="shrink-0 text-xs font-semibold text-slate-500">
          {isShell ? "shell" : block.name}
        </span>
        <code className="min-w-0 flex-1 truncate font-mono text-xs text-slate-700">
          {isShell ? block.command : JSON.stringify(block.args ?? {})}
        </code>
        {block.durationMs != null && (
          <span className="shrink-0 text-[11px] text-slate-400">
            {block.durationMs} ms
          </span>
        )}
        {statusIcon}
      </button>

      {open && (
        <div className="border-t border-slate-200 bg-slate-900 px-3 py-2">
          {!isShell && block.args && (
            <div className="mb-2 text-[11px] text-slate-400">
              <span className="text-slate-500">args:</span>{" "}
              <code className="font-mono">{JSON.stringify(block.args)}</code>
            </div>
          )}
          <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-[12px] leading-relaxed text-slate-100">
            {block.output}
          </pre>
        </div>
      )}
    </div>
  );
}
