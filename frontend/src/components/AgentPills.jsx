import { AGENTS } from "../data/mockData.js";

export default function AgentPills({ value, onChange }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {AGENTS.map((a) => {
        const active = value === a.id;
        return (
          <button
            key={a.id}
            onClick={() => onChange(a.id)}
            title={a.desc}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
              active
                ? "bg-brand-600 text-white shadow-sm"
                : "bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
            }`}
          >
            {a.label}
          </button>
        );
      })}
    </div>
  );
}
