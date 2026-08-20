import iconMark from "../../assets/agentic-platform-icon-mark.svg";

export default function Logo({ compact = false }) {
  return (
    <div className="flex items-center gap-2.5 select-none">
      <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-soft">
        <img src={iconMark} alt="Agentic Platform" className="h-9 w-9 rounded-xl" />
      </div>
      {!compact && (
        <div className="leading-tight">
          <div className="text-[15px] font-bold text-slate-900">ChatAgent</div>
          <div className="text-[11px] font-medium text-slate-400">
            Multi-Agent Platform
          </div>
        </div>
      )}
    </div>
  );
}
