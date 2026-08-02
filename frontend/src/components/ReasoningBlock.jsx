import { useState } from "react";
import { Brain, ChevronRight } from "lucide-react";

// Collapsible "thinking" block for agent reasoning.
export default function ReasoningBlock({ text }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="my-1.5">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-600"
      >
        <ChevronRight
          size={13}
          className={`transition-transform ${open ? "rotate-90" : ""}`}
        />
        <Brain size={13} />
        Reasoning
      </button>
      {open && (
        <p className="mt-1.5 border-l-2 border-slate-200 pl-3 text-sm italic leading-relaxed text-slate-500">
          {text}
        </p>
      )}
    </div>
  );
}
