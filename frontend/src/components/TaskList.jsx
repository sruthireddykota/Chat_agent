import { CheckCircle2, Circle, Loader2, ListTodo } from "lucide-react";

const STATUS = {
  completed: {
    Icon: CheckCircle2,
    cls: "text-emerald-500",
    text: "line-through text-slate-400",
  },
  in_progress: {
    Icon: Loader2,
    cls: "text-brand-500 animate-spin",
    text: "text-slate-800 font-medium",
  },
  pending: { Icon: Circle, cls: "text-slate-300", text: "text-slate-500" },
};

export default function TaskList({ tasks = [] }) {
  if (!tasks.length) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 px-6 py-10 text-center">
        <ListTodo size={28} className="text-slate-300" />
        <p className="text-sm text-slate-400">
          No tasks yet. The agent will add a plan here when it starts working.
        </p>
      </div>
    );
  }

  const done = tasks.filter((t) => t.status === "completed").length;

  return (
    <div className="p-3">
      <div className="mb-2 flex items-center justify-between px-1">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          Plan
        </span>
        <span className="text-[11px] font-medium text-slate-400">
          {done}/{tasks.length} done
        </span>
      </div>
      <div className="mb-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-emerald-500 transition-all"
          style={{ width: `${tasks.length ? (done / tasks.length) * 100 : 0}%` }}
        />
      </div>
      <ol className="space-y-1">
        {tasks.map((t, i) => {
          const s = STATUS[t.status] ?? STATUS.pending;
          return (
            <li
              key={t.id ?? i}
              className="flex items-start gap-2 rounded-lg px-2 py-1.5 hover:bg-slate-50"
            >
              <s.Icon size={16} className={`mt-0.5 shrink-0 ${s.cls}`} />
              <span className={`text-sm leading-snug ${s.text}`}>
                {t.subject}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
