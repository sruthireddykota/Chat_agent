import TopBar from "./TopBar.jsx";

export default function AppShell({ children, maxWidth = "max-w-[1400px]" }) {
  return (
    <div className="min-h-screen">
      <TopBar />
      <main className={`mx-auto w-full ${maxWidth} px-4 py-6 sm:px-6`}>
        {children}
      </main>
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
