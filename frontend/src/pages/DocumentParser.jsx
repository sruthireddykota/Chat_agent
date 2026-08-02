import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, ChevronDown, FileText, Loader2, Settings2, Trash2, UploadCloud } from "lucide-react";
import AppShell, { PageHeader } from "../components/AppShell.jsx";
import { Badge, Button, Card, Toggle } from "../components/ui.jsx";
import { api } from "../services/api.js";

const uuid = () => (crypto.randomUUID ? crypto.randomUUID() : `d-${Math.random().toString(36).slice(2)}`);

export default function DocumentParser() {
  const [file, setFile] = useState(null);
  const [urls, setUrls] = useState("");
  const [format, setFormat] = useState("md");
  const [options, setOptions] = useState({ ocr: false, table: true, picture: true, code: false, formula: false, image_scale: 2, table_mode: "fast" });
  const [parsed, setParsed] = useState(null);
  const [chunks, setChunks] = useState(null);
  const [embeddings, setEmbeddings] = useState(null);
  const [busy, setBusy] = useState(null);
  const [message, setMessage] = useState(null);
  const [docs, setDocs] = useState([]);

  const loadDocs = useCallback(async () => {
    try { setDocs(await api.getDocuments() || []); } catch { /* API may be unavailable */ }
  }, []);
  useEffect(() => { loadDocs(); }, [loadDocs]);

  const setOption = (key) => (value) => setOptions((current) => ({ ...current, [key]: value }));

  const process = async () => {
    if (!file) return;
    setBusy("process"); setMessage(null); setParsed(null); setChunks(null); setEmbeddings(null);
    try {
      const result = await api.parseDocument(file, { format, ...options });
      setParsed({ ...result, document_id: result.document_id || uuid() });
      setMessage({ type: "success", text: "Document processed successfully." });
    } catch (error) {
      setMessage({ type: "error", text: error.message || "Document processing failed." });
    } finally { setBusy(null); }
  };

  const processUrls = async () => {
    const list = urls.split("\n").map((url) => url.trim()).filter(Boolean);
    if (!list.length) return;
    setBusy("url"); setMessage(null); setParsed(null); setChunks(null); setEmbeddings(null);
    try {
      const result = await api.parseDocumentUrl(list, { format, ...options });
      setParsed({ ...result, document_id: result.document_id || uuid() });
      setMessage({ type: "success", text: "URL document processed successfully." });
    } catch (error) { setMessage({ type: "error", text: error.message || "URL processing failed." }); }
    finally { setBusy(null); }
  };

  const createChunks = async () => {
    setBusy("chunks"); setMessage(null);
    try { setChunks((await api.generateChunks(parsed.content)).chunks || []); }
    catch (error) { setMessage({ type: "error", text: error.message || "Chunk generation failed." }); }
    finally { setBusy(null); }
  };

  const createEmbeddings = async () => {
    setBusy("embeddings"); setMessage(null);
    try { setEmbeddings((await api.generateEmbeddings(chunks)).embeddings || []); }
    catch (error) { setMessage({ type: "error", text: error.message || "Embedding generation failed." }); }
    finally { setBusy(null); }
  };

  const store = async () => {
    setBusy("store"); setMessage(null);
    try {
      const documentName = file?.name || parsed.filename;
      await api.storeDocumentEmbeddings({ chunks, embeddings, document_name: documentName, document_id: parsed.document_id });
      await api.storeDocument({
        document_id: parsed.document_id,
        document_name: documentName,
        document_type: documentName.split(".").pop()?.toLowerCase() || "",
        uploaded_by: "Admin",
        tags: [],
        timestamp: new Date().toISOString(),
        chunk_count: chunks.length,
      });
      setMessage({ type: "success", text: "Chunks and embeddings stored in Qdrant; metadata saved." });
      loadDocs();
    } catch (error) { setMessage({ type: "error", text: error.message || "Storage failed." }); }
    finally { setBusy(null); }
  };

  const clear = () => { setFile(null); setParsed(null); setChunks(null); setEmbeddings(null); setMessage(null); };

  return (
    <AppShell>
      <PageHeader title="Document Parser" subtitle="Upload, parse, chunk, embed, and store documents in the knowledge base." />
      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        <Card className="p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-700"><Settings2 size={16} className="text-slate-400" /> Parse Settings</div>
          <label className="mb-1.5 block text-xs font-semibold text-slate-600">Output format</label>
          <div className="relative mb-4">
            <select value={format} onChange={(e) => setFormat(e.target.value)} className="w-full appearance-none rounded-lg border border-slate-200 bg-white px-3 py-2 pr-9 text-sm">
              {['md', 'json', 'html', 'text'].map((value) => <option key={value}>{value}</option>)}
            </select><ChevronDown size={16} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" />
          </div>
          <div className="divide-y divide-slate-100 border-y border-slate-100">
            <Toggle label="Enable OCR" checked={options.ocr} onChange={setOption("ocr")} />
            <Toggle label="Table extraction" checked={options.table} onChange={setOption("table")} />
            <Toggle label="Picture description" checked={options.picture} onChange={setOption("picture")} />
            <Toggle label="Code enrichment" checked={options.code} onChange={setOption("code")} />
            <Toggle label="Formula enrichment" checked={options.formula} onChange={setOption("formula")} />
          </div>
        </Card>

        <div>
          <Card className="p-6">
            <label className="group flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center hover:border-brand-400 hover:bg-brand-50/40">
              <UploadCloud size={30} className="text-slate-400 group-hover:text-brand-500" />
              <div className="text-sm font-medium text-slate-700">{file ? file.name : "Click to upload a document"}</div>
              <div className="text-xs text-slate-400">PDF, DOCX, XLSX, CSV, JPEG, PNG</div>
              <input type="file" accept=".pdf,.docx,.xlsx,.csv,.jpeg,.jpg,.png" className="hidden" onChange={(e) => { setFile(e.target.files?.[0] || null); setParsed(null); setChunks(null); setEmbeddings(null); }} />
            </label>
            <div className="mt-4 flex gap-2">
              <Button onClick={process} disabled={!file || busy}>{busy === "process" ? <Loader2 size={16} className="animate-spin" /> : <UploadCloud size={16} />} Process document</Button>
              <Button variant="danger" onClick={clear}>Clear</Button>
            </div>
            {message && <div className={`mt-4 rounded-xl border px-4 py-3 text-sm ${message.type === "error" ? "border-red-200 bg-red-50 text-red-700" : "border-emerald-200 bg-emerald-50 text-emerald-700"}`}>{message.text}</div>}
          </Card>

          <Card className="mt-6 p-5">
            <h3 className="mb-2 text-sm font-semibold text-slate-700">Process document URLs</h3>
            <textarea value={urls} onChange={(e) => setUrls(e.target.value)} placeholder="https://example.com/document.pdf\nhttps://example.com/report.docx" className="h-24 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-brand-400" />
            <Button className="mt-3" variant="secondary" onClick={processUrls} disabled={!urls.trim() || busy}>{busy === "url" ? <Loader2 size={16} className="animate-spin" /> : null} Process URLs</Button>
          </Card>

          {parsed && <Card className="mt-6 p-5">
            <div className="mb-3 flex flex-wrap items-center gap-2"><Badge color="blue">{parsed.status || "success"}</Badge><span className="text-sm font-semibold text-slate-700">{parsed.filename}</span><span className="text-xs text-slate-400">{Number(parsed.processing_time || 0).toFixed(2)}s</span></div>
            <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-4 text-xs text-slate-700">{parsed.content}</pre>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button variant="secondary" onClick={createChunks} disabled={busy || !parsed.content}>{busy === "chunks" ? <Loader2 size={16} className="animate-spin" /> : null} Generate chunks</Button>
              {chunks && <Badge color="blue">{chunks.length} chunks</Badge>}
              <Button variant="secondary" onClick={createEmbeddings} disabled={busy || !chunks?.length}>{busy === "embeddings" ? <Loader2 size={16} className="animate-spin" /> : null} Generate embeddings</Button>
              {embeddings && <Badge color="violet">{embeddings.length} embeddings</Badge>}
              <Button variant="success" onClick={store} disabled={busy || !embeddings?.length}>{busy === "store" ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />} Store embeddings</Button>
            </div>
          </Card>}

          {docs.length > 0 && <Card className="mt-6 overflow-hidden"><div className="border-b border-slate-100 px-5 py-3 text-sm font-semibold text-slate-700">Stored documents ({docs.length})</div><ul className="divide-y divide-slate-100">{docs.map((doc, index) => { const id = doc.document_id || String(index); return <li key={id} className="flex items-center gap-3 px-5 py-3 text-sm"><FileText size={16} className="text-slate-400" /><span className="flex-1 truncate">{doc.document_name || "Untitled"}</span><Badge color="gray">{doc.document_type || "file"}</Badge><button onClick={async () => { await api.deleteDocument(id); loadDocs(); }} className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-500"><Trash2 size={15} /></button></li>; })}</ul></Card>}
        </div>
      </div>
    </AppShell>
  );
}
