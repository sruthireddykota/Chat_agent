import { useEffect, useState, useCallback } from "react";
import { BarChart3, Loader2, Gauge, RefreshCw, UploadCloud, Play, FileSpreadsheet } from "lucide-react";
import AppShell, { PageHeader } from "../components/AppShell.jsx";
import { Card, Button, ProgressBar } from "../components/ui.jsx";
import { api } from "../services/api.js";

const COLORS = ["bg-emerald-500", "bg-brand-500", "bg-violet-500", "bg-amber-500", "bg-rose-500"];

function labelize(key) {
  return key.replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// Metric values may be a 0–1 fraction or already a percentage / raw number.
function asFraction(v) {
  if (typeof v !== "number") return null;
  if (v >= 0 && v <= 1) return v;
  if (v > 1 && v <= 100) return v / 100;
  return null;
}

export default function RagEvaluation() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [questionFile, setQuestionFile] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [evaluating, setEvaluating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setMetrics(await api.getAverageMetrics());
    } catch {
      setError("Couldn't load metrics — is the API running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const runEvaluation = async () => {
    if (!questionFile) return;
    setEvaluating(true);
    setError(null);
    try {
      setEvaluation(await api.evaluateRagFile(questionFile));
      await load();
    } catch (e) {
      setError(e.message || "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  };

  const entries = metrics && typeof metrics === "object" ? Object.entries(metrics) : [];

  return (
    <AppShell>
      <PageHeader
        title="RAG Evaluation"
        subtitle="Average metrics for your retrieval-augmented generation pipeline."
        actions={
          <Button variant="secondary" onClick={load} disabled={loading}>
            {loading ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
            Refresh
          </Button>
        }
      />

      <Card className="mb-6 p-5">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
          <FileSpreadsheet size={17} className="text-brand-600" /> Evaluate questions from CSV
        </div>
        <p className="mb-4 text-sm text-slate-500">
          Upload a CSV with a <code>Questions</code>, <code>question</code>, or <code>Question</code> column.
          The RAG agent will answer each question and calculate the evaluation metrics.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex min-w-64 cursor-pointer items-center gap-3 rounded-lg border-2 border-dashed border-slate-300 px-4 py-3 text-sm hover:border-brand-400 hover:bg-brand-50/40">
            <UploadCloud size={20} className="text-slate-400" />
            <span className="truncate text-slate-600">{questionFile?.name || "Choose questions CSV"}</span>
            <input type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => setQuestionFile(e.target.files?.[0] || null)} />
          </label>
          <Button onClick={runEvaluation} disabled={!questionFile || evaluating}>
            {evaluating ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
            {evaluating ? "Evaluating…" : "Run evaluation"}
          </Button>
        </div>
      </Card>

      {evaluation && (
        <Card className="mb-6 overflow-hidden">
          <div className="border-b border-slate-100 px-5 py-3 text-sm font-semibold text-slate-700">
            Results for {evaluation.filename} · {evaluation.count} questions
          </div>
          <div className="grid gap-4 p-5 sm:grid-cols-3">
            {Object.entries(evaluation.averages || {}).map(([key, value], i) => (
              <div key={key} className="rounded-xl bg-slate-50 p-4">
                <div className="mb-1 text-sm text-slate-500">{key}</div>
                <div className="text-2xl font-bold text-slate-900">{Number(value).toFixed(3)}</div>
                <ProgressBar value={Number(value)} color={COLORS[i % COLORS.length]} />
              </div>
            ))}
          </div>
        </Card>
      )}

      {loading ? (
        <Card className="grid place-items-center p-16 text-center">
          <Loader2 size={30} className="animate-spin text-brand-600" />
          <p className="mt-4 text-sm text-slate-500">Loading metrics…</p>
        </Card>
      ) : error ? (
        <Card className="p-10 text-center text-sm text-red-600">{error}</Card>
      ) : entries.length === 0 ? (
        <Card className="grid place-items-center p-16 text-center">
          <div className="mb-3 grid h-14 w-14 place-items-center rounded-2xl bg-brand-50 text-brand-600">
            <BarChart3 size={26} />
          </div>
          <p className="font-semibold text-slate-700">No metrics yet</p>
          <p className="mt-1 max-w-sm text-sm text-slate-400">
            Run an evaluation on the backend; averages will appear here.
          </p>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {entries.map(([key, value], i) => {
            const frac = asFraction(value);
            return (
              <Card key={key} className="p-5">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-500">{labelize(key)}</span>
                  <Gauge size={16} className="text-slate-300" />
                </div>
                <div className="mb-2 text-3xl font-bold text-slate-900">
                  {frac != null ? (
                    <>{Math.round(frac * 100)}<span className="text-lg text-slate-400">%</span></>
                  ) : (
                    String(value)
                  )}
                </div>
                {frac != null && <ProgressBar value={frac} color={COLORS[i % COLORS.length]} />}
              </Card>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}
