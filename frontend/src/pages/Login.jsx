import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Mail, Lock, User, X, ArrowRight, Sparkles, Loader2 } from "lucide-react";
import iconMark from "../../assets/agentic-platform-icon-mark.svg";
import { useApp } from "../context/AppContext.jsx";
import { api } from "../services/api.js";
import { Button } from "../components/ui.jsx";
import bcrypt from "bcryptjs";

const uuid = () =>
  (crypto.randomUUID && crypto.randomUUID()) ||
  "u-" + Math.random().toString(36).slice(2);

function Field({ icon: Icon, ...props }) {
  return (
    <div className="relative">
      <Icon size={17} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
      <input
        {...props}
        className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
      />
    </div>
  );
}

function SignupDialog({ onClose }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (username.length <= 6) return setMsg({ t: "err", m: "Username should be greater than 6 characters" });
    if (password.length < 8) return setMsg({ t: "err", m: "Password must be at least 8 characters" });
    if (!/[A-Z]/.test(password)) return setMsg({ t: "err", m: "Password must contain at least one uppercase letter" });
    if (!/[^A-Za-z0-9]/.test(password)) return setMsg({ t: "err", m: "Password must contain at least one symbol" });
    if (email.length <= 10) return setMsg({ t: "err", m: "Email ID should be greater than 10 characters" });
    setBusy(true);
    try {
      // Match Python bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).
      // Login still sends the raw password because the backend verifies it
      // with bcrypt.checkpw against this stored hash.
      const hashedPassword = await bcrypt.hash(password, 12);
      const res = await api.createUser({
        username,
        user_id: uuid(),
        email_id: email,
        password: hashedPassword,
        logged_in: false,
        last_logged_in: null,
      });
      if (res && res.status === "error") setMsg({ t: "err", m: res.message || "Sign up failed" });
      else setMsg({ t: "ok", m: "Sign up successful — you can now log in." });
    } catch (error) {
      const detail = String(error?.message || "");
      const isInternalError = /^error\b/i.test(detail) || /failed to fetch|network error/i.test(detail);
      setMsg({
        t: "err",
        m: isInternalError ? "Sign up failed" : detail || "Sign up failed",
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-900/40 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-soft animate-fade-in-up">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">Create account</h2>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-3">
          <Field icon={User} placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
          <Field icon={Mail} placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Field icon={Lock} type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {msg && (
            <div className={`rounded-lg px-3 py-2 text-sm ${msg.t === "ok" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
              {msg.m}
            </div>
          )}
          <Button className="w-full" size="lg" onClick={submit} disabled={busy}>
            {busy ? <Loader2 size={16} className="animate-spin" /> : null} Sign Up
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function Login() {
  const { login } = useApp();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [showSignup, setShowSignup] = useState(false);

  const submit = async () => {
    if (email.length <= 10) return setError("Email ID should be greater than 10 characters");
    if (password.length <= 8) return setError("Password should be greater than 8 characters");
    setError(null);
    setBusy(true);
    try {
      const res = await api.login(email, password);
      if (res?.success) {
        // The backend already flips logged_in=true and returns the user_id.
        login({
          username: email.split("@")[0],
          email,
          user_id: res.user_id,
          role: res.role || "user",
          access_token: res.access_token,
        });
        navigate("/");
      } else {
        setError(res?.message || "Login failed");
      }
    } catch (e) {
      const m = String(e?.message || "");
      setError(
        m.includes("404")
          ? "User not found"
          : m.includes("401")
          ? "Invalid email or password"
          : "Login failed"
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-gradient-to-br from-brand-700 via-brand-600 to-brand-800 lg:block">
        <div className="absolute -left-24 -top-24 h-80 w-80 rounded-full bg-white/10 blur-2xl" />
        <div className="absolute -bottom-24 -right-10 h-96 w-96 rounded-full bg-white/10 blur-3xl" />
        <div className="relative flex h-full flex-col justify-between p-12 text-white">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-white/15 backdrop-blur">
              <img src={iconMark} alt="Agentic Platform" className="h-11 w-11 rounded-xl" />
            </div>
            <span className="text-lg font-bold">ChatAgent</span>
          </div>
          <div>
            <h1 className="max-w-md text-4xl font-extrabold leading-tight">Agent Platform</h1>
            <p className="mt-4 max-w-md text-brand-100">
              Chat with generic, coding, research, and RAG agents. Parse documents into a vector store and evaluate your retrieval pipeline — all in one place.
            </p>
          </div>
          <p className="text-sm text-brand-200">© 2026 ChatAgent Platform</p>
        </div>
      </div>

      <div className="flex items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-sm">
          <div className="mb-1 inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
            <Sparkles size={13} /> Welcome back
          </div>
          <h2 className="mb-1 mt-3 text-2xl font-bold text-slate-900">Sign in to your workspace</h2>
          <p className="mb-6 text-sm text-slate-500">Enter your credentials to access the platform.</p>

          <div className="space-y-3">
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">Email ID</label>
              <Field icon={Mail} placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold text-slate-600">Password</label>
              <Field icon={Lock} type="password" placeholder="••••••••" value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submit()} />
            </div>

            {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

            <Button size="lg" className="mt-1 w-full" onClick={submit} disabled={busy}>
              {busy ? <Loader2 size={16} className="animate-spin" /> : null} Log in <ArrowRight size={16} />
            </Button>

            <p className="pt-2 text-center text-sm text-slate-500">
              Don&apos;t have an account?{" "}
              <button onClick={() => setShowSignup(true)} className="font-semibold text-brand-600 hover:underline">
                Sign up
              </button>
            </p>
          </div>
        </div>
      </div>

      {showSignup && <SignupDialog onClose={() => setShowSignup(false)} />}
    </div>
  );
}
