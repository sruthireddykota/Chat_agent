import { Component } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useApp } from "./context/AppContext.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Chatbot from "./pages/Chatbot.jsx";
import KnowledgeManagement from "./pages/KnowledgeManagement.jsx";
import DocumentParser from "./pages/DocumentParser.jsx";
import WorkspaceExplorer from "./pages/WorkspaceExplorer.jsx";
import RagEvaluation from "./pages/RagEvaluation.jsx";

function Protected({ children }) {
  const { user } = useApp();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

class AppErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Frontend runtime error:", error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div className="grid min-h-screen place-items-center bg-slate-50 p-6">
        <div className="w-full max-w-lg rounded-2xl border border-red-200 bg-white p-6 shadow-card">
          <h1 className="text-lg font-bold text-red-700">The page could not be displayed</h1>
          <p className="mt-2 text-sm text-slate-600">
            A frontend error occurred while processing this action. Refresh the page and try again.
          </p>
          <pre className="mt-4 overflow-auto rounded-lg bg-red-50 p-3 text-xs text-red-800">
            {String(this.state.error?.message || this.state.error)}
          </pre>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
          >
            Reload page
          </button>
        </div>
      </div>
    );
  }
}

export default function App() {
  const { user } = useApp();
  return (
    <AppErrorBoundary>
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <Login />}
      />
      <Route
        path="/"
        element={
          <Protected>
            <Dashboard />
          </Protected>
        }
      />
      <Route
        path="/chat"
        element={
          <Protected>
            <Chatbot />
          </Protected>
        }
      />
      <Route
        path="/knowledge"
        element={
          <Protected>
            <KnowledgeManagement />
          </Protected>
        }
      />
      <Route
        path="/parser"
        element={
          <Protected>
            <DocumentParser />
          </Protected>
        }
      />
      <Route
        path="/workspace"
        element={
          <Protected>
            <WorkspaceExplorer />
          </Protected>
        }
      />
      <Route
        path="/rag-eval"
        element={
          <Protected>
            <RagEvaluation />
          </Protected>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </AppErrorBoundary>
  );
}
