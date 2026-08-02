import { Link } from "react-router-dom";
import { FolderTree, MessageSquare, Boxes } from "lucide-react";
import AppShell, { PageHeader } from "../components/AppShell.jsx";
import { Card } from "../components/ui.jsx";
import FileExplorerPanel from "../components/FileExplorerPanel.jsx";
import { useApp } from "../context/AppContext.jsx";

export default function WorkspaceExplorer() {
  const { selectedAgent, sessions, currentSessionId } = useApp();
  const currentSession = sessions.find((s) => s.id === currentSessionId);
  const files = currentSession?.files ?? {};

  if (selectedAgent !== "Coder") {
    return (
      <AppShell>
        <Card className="mx-auto mt-10 max-w-lg p-8 text-center">
          <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-xl bg-amber-50 text-amber-600">
            <FolderTree size={24} />
          </div>
          <h2 className="text-lg font-bold text-slate-900">
            Workspace Explorer is only available for the Coder agent
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Switch to the Coder agent in the chat to generate and browse
            workspace files.
          </p>
          <Link
            to="/chat"
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
          >
            <MessageSquare size={16} /> Go to Chat
          </Link>
        </Card>
      </AppShell>
    );
  }

  const fileCount = Object.keys(files).length;

  return (
    <AppShell>
      <PageHeader
        title="Workspace Explorer"
        subtitle={
          <span className="flex items-center gap-2">
            <Boxes size={14} className="text-slate-400" />
            {fileCount} {fileCount === 1 ? "file" : "files"} · session{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">
              {currentSessionId ?? "—"}
            </code>
          </span>
        }
        actions={
          <Link
            to="/chat"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            <MessageSquare size={16} /> Back to Chat
          </Link>
        }
      />

      <FileExplorerPanel files={files} className="h-[calc(100vh-12rem)]" />
    </AppShell>
  );
}
