import { useState } from "react";
import {
  HelpCircle,
  ClipboardCheck,
  Check,
  Send,
  ThumbsUp,
  Pencil,
} from "lucide-react";

// Inline prompt for the agent's clarification questions or approval request.
// Clarifications: choice chips + a free-form box (choices always allow free-form).
// Approval: plan summary with Approve / Request changes.
export default function PlanPrompt({ plan, resolved, answer, onAnswer }) {
  const isApproval = plan.kind === "approval";
  const [picks, setPicks] = useState({});
  const [freeText, setFreeText] = useState("");

  if (resolved) {
    return (
      <div className="my-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5">
        <div className="flex items-center gap-2 text-sm text-emerald-800">
          <Check size={15} className="shrink-0" />
          <span className="font-medium">
            {isApproval ? "Approved" : "Answered"}:
          </span>
          <span className="truncate">{answer}</span>
        </div>
      </div>
    );
  }

  if (isApproval) {
    return (
      <div className="my-2 rounded-xl border border-brand-200 bg-brand-50/60 p-4">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-brand-800">
          <ClipboardCheck size={16} /> Approval needed
        </div>
        <pre className="mb-3 whitespace-pre-wrap font-sans text-sm text-slate-700">
          {plan.summary}
        </pre>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onAnswer("Approved — proceed")}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-emerald-700"
          >
            <ThumbsUp size={15} /> Approve &amp; run
          </button>
          <button
            onClick={() => onAnswer("Requested changes")}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            <Pencil size={15} /> Request changes
          </button>
        </div>
      </div>
    );
  }

  const questions = plan.questions ?? [];
  const allAnswered = questions.every((_, i) => picks[i]) || freeText.trim();

  const submit = () => {
    if (!allAnswered) return;
    const parts = questions.map((q, i) => picks[i]).filter(Boolean);
    if (freeText.trim()) parts.push(freeText.trim());
    onAnswer(parts.join("; "));
  };

  return (
    <div className="my-2 rounded-xl border border-brand-200 bg-brand-50/60 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-brand-800">
        <HelpCircle size={16} /> A few questions first
      </div>

      <div className="space-y-3">
        {questions.map((q, i) => (
          <div key={i}>
            <div className="mb-1.5 text-sm font-medium text-slate-700">
              {q.message}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {(q.choices ?? []).map((c) => {
                const on = picks[i] === c;
                return (
                  <button
                    key={c}
                    onClick={() =>
                      setPicks((p) => ({ ...p, [i]: on ? undefined : c }))
                    }
                    className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                      on
                        ? "bg-brand-600 text-white shadow-sm"
                        : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    {c}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex items-end gap-2">
        <input
          value={freeText}
          onChange={(e) => setFreeText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="…or type your own answer"
          className="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
        />
        <button
          onClick={submit}
          disabled={!allAnswered}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-brand-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:bg-brand-300"
        >
          <Send size={15} /> Continue
        </button>
      </div>
    </div>
  );
}
