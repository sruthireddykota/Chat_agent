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

export default function App() {
  const { user } = useApp();
  return (
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
  );
}
