import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  FileSpreadsheet,
  FileType,
  Search,
  Trash2,
  Plus,
  RefreshCw,
  Loader2,
} from "lucide-react";
import AppShell, { PageHeader } from "../components/AppShell.jsx";
import { Card, Badge, Button } from "../components/ui.jsx";
import { api } from "../services/api.js";

const TYPE_ICON = {
  pdf: { icon: FileText, tint: "bg-red-50 text-red-600" },
  xlsx: { icon: FileSpreadsheet, tint: "bg-emerald-50 text-emerald-600" },
  csv: { icon: FileSpreadsheet, tint: "bg-emerald-50 text-emerald-600" },
  docx: { icon: FileType, tint: "bg-brand-50 text-brand-600" },
};

const norm = (d, i) => ({
  id: d.document_id || d.id || String(i),
  name: d.document_name || d.name || "Untitled",
  type: (d.document_type || d.type || "").toLowerCase(),
  chunks: d.chunk_count ?? d.chunks ?? null,
  uploadedBy: d.uploaded_by || d.uploadedBy || "—",
  tags: d.tags || [],
  date: (d.timestamp || d.date || "").toString().slice(0, 10),
});

export default function KnowledgeManagement() {
  const [docs, setDocs] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await api.getDocuments();
      setDocs((Array.isArray(rows) ? rows : []).map(norm));
    } catch {
      setError("Couldn't load documents — is the API running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const remove = async (id) => {
    setDocs((p) => p.filter((d) => d.id !== id));
    try { await api.deleteDocument(id); } catch { load(); }
  };

  const filtered = docs.filter((d) => d.name.toLowerCase().includes(q.toLowerCase()));
  const totalChunks = docs.reduce((a, d) => a + (d.chunks || 0), 0);

  return (
    <AppShell>
      <PageHeader
        title="Knowledge Management"
        subtitle="Documents indexed in your vector store."
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={load}>
              <RefreshCw size={16} /> Refresh
            </Button>
            <Link to="/parser">
              <Button><Plus size={16} /> Parse new document</Button>
            </Link>
          </div>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <Card className="flex items-center gap-4 p-5">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-brand-50 text-brand-600"><FileText size={20} /></div>
          <div><div className="text-2xl font-bold text-slate-900">{docs.length}</div><div className="text-sm text-slate-500">Documents</div></div>
        </Card>
        <Card className="flex items-center gap-4 p-5">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-violet-50 text-violet-600"><FileType size={20} /></div>
          <div><div className="text-2xl font-bold text-slate-900">{totalChunks || "—"}</div><div className="text-sm text-slate-500">Total chunks</div></div>
        </Card>
        <Card className="flex items-center gap-4 p-5">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-emerald-50 text-emerald-600"><FileSpreadsheet size={20} /></div>
          <div><div className="text-2xl font-bold text-slate-900">1</div><div className="text-sm text-slate-500">Collections</div></div>
        </Card>
      </div>

      <div className="relative mb-4 max-w-sm">
        <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search documents…"
          className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-3 text-sm outline-none focus:border-brand-400 focus:ring-4 focus:ring-brand-100" />
      </div>

      <Card className="overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center gap-2 p-10 text-sm text-slate-500">
            <Loader2 size={18} className="animate-spin" /> Loading documents…
          </div>
        ) : error ? (
          <div className="p-10 text-center text-sm text-red-600">{error}</div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-5 py-3 font-semibold">Document</th>
                <th className="px-5 py-3 font-semibold">Chunks</th>
                <th className="px-5 py-3 font-semibold">Tags</th>
                <th className="px-5 py-3 font-semibold">Uploaded by</th>
                <th className="px-5 py-3 font-semibold">Date</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((d) => {
                const T = TYPE_ICON[d.type] || TYPE_ICON.docx;
                return (
                  <tr key={d.id} className="hover:bg-slate-50/70">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-3">
                        <div className={`grid h-9 w-9 place-items-center rounded-lg ${T.tint}`}><T.icon size={16} /></div>
                        <div>
                          <div className="font-medium text-slate-800">{d.name}</div>
                          <div className="text-xs uppercase text-slate-400">{d.type || "—"}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3">{d.chunks != null ? <Badge color="violet">{d.chunks}</Badge> : "—"}</td>
                    <td className="px-5 py-3">
                      <div className="flex flex-wrap gap-1">
                        {(d.tags || []).map((t) => <Badge key={t} color="gray">{t}</Badge>)}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-slate-600">{d.uploadedBy}</td>
                    <td className="px-5 py-3 text-slate-500">{d.date || "—"}</td>
                    <td className="px-5 py-3 text-right">
                      <button onClick={() => remove(d.id)} className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-500" title="Remove">
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr><td colSpan={6} className="px-5 py-10 text-center text-slate-400">No documents found.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </Card>
    </AppShell>
  );
}
