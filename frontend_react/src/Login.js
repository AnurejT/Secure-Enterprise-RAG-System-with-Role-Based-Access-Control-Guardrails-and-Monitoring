import { useState } from "react";
import axios from "axios";

const API = "http://localhost:5000/api/auth";

// ─── SVG Icons ────────────────────────────────────────────────────
function LockCloudIcon() {
  return (
    <svg viewBox="0 0 80 60" className="w-20 h-16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M60 28a10 10 0 00-9.97-10 14 14 0 00-27.56 3A10 10 0 0014 30.5a10 10 0 0010 10h35a10 10 0 001-20"
        fill="url(#cloudGrad)" opacity="0.9" />
      <rect x="30" y="33" width="20" height="15" rx="3" fill="#1d4ed8" />
      <path d="M34 33v-4a6 6 0 0112 0v4" stroke="#1d4ed8" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      <circle cx="40" cy="40" r="2.5" fill="white" />
      <rect x="38.5" y="40" width="3" height="4" rx="1" fill="white" />
      <defs>
        <linearGradient id="cloudGrad" x1="0" y1="0" x2="80" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#bfdbfe" />
          <stop offset="100%" stopColor="#6366f1" stopOpacity="0.4" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function AdminIcon() {
  return (
    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-lg mx-auto mb-5">
      <svg viewBox="0 0 40 40" className="w-10 h-10" fill="none">
        <circle cx="20" cy="14" r="7" fill="white" opacity="0.95" />
        <path d="M6 36c0-7.7 6.3-14 14-14s14 6.3 14 14" stroke="white" strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.95" />
        <path d="M28 2l5 2.5v5c0 3.5-2 6.5-5 8-3-1.5-5-4.5-5-8V4.5L28 2z" fill="#fbbf24" />
        <path d="M27 8.5l1.5 1.5 3-3" stroke="white" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

function EmployeeIcon() {
  const bg = "#6366f1";
  return (
    <div
      className="w-20 h-20 rounded-full flex items-center justify-center shadow-lg mx-auto mb-5 transition-all duration-300"
      style={{ background: `linear-gradient(135deg, ${bg}cc, ${bg})` }}
    >
      <span style={{ fontSize: 36 }}>👤</span>
    </div>
  );
}

// ─── Shared input field ───────────────────────────────────────────
function InputField({ id, label, type = "text", value, onChange, placeholder, error, autoComplete }) {
  const [show, setShow] = useState(false);
  const isPassword = type === "password";
  return (
    <div className="mb-4">
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
      <div className="relative">
        <input
          id={id}
          type={isPassword && show ? "text" : type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete || (isPassword ? "current-password" : "off")}
          className={`w-full px-4 py-3 rounded-xl border ${
            error ? "border-red-400 bg-red-50" : "border-gray-200 bg-gray-50"
          } text-gray-800 placeholder-gray-400 text-sm
          focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent
          transition-all duration-200 hover:border-blue-300`}
        />
        {isPassword && (
          <button type="button" onClick={() => setShow((s) => !s)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs font-medium select-none"
            tabIndex={-1}>{show ? "Hide" : "Show"}</button>
        )}
      </div>
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
}

// ─── Auth card ───────────────────────────────────────────────────
function AuthCard({ type, onLogin }) {
  const isAdmin = type === "admin";

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors]     = useState({});
  const [loading, setLoading]   = useState(false);
  const [shake, setShake]       = useState(false);

  const validate = () => {
    const e = {};
    if (!email.trim()) e.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = "Enter a valid email";
    if (!password) e.password = "Password is required";
    return e;
  };

  const triggerShake = (msg) => {
    setErrors((p) => ({ ...p, form: msg }));
    setShake(true);
    setTimeout(() => setShake(false), 600);
  };

  const handleSubmit = async (ev) => {
    ev.preventDefault();
    const e = validate();
    if (Object.keys(e).length) { setErrors(e); return; }
    setErrors({});
    setLoading(true);
    try {
      const res = await axios.post(`${API}/login`, {
        email: email.trim().toLowerCase(),
        password,
      });
      onLogin({ ...res.data.user, token: res.data.token });
    } catch (err) {
      setLoading(false);
      const msg = err.response?.data?.error || "Something went wrong. Please try again.";
      triggerShake(msg);
    }
  };

  const accentColor = isAdmin
    ? { from: "#2563eb", to: "#4338ca" }
    : { from: "#6366f1", to: "#4f46e5" };

  return (
    <div
      className={`bg-white rounded-2xl shadow-xl w-full flex-1 border border-gray-100
        transition-all duration-300 hover:shadow-2xl hover:-translate-y-1
        ${shake ? "animate-shake" : ""}`}
      style={{ minWidth: 300, overflow: "hidden" }}
    >
      {/* Removed Mode Tab Bar (Sign In / Sign Up) */}

      <div className="p-8">
        {isAdmin ? <AdminIcon /> : <EmployeeIcon />}

        {/* Title */}
        <h2 className="text-xl font-bold text-center mb-1 text-gray-900">
          {isAdmin ? "Admin Sign In" : "Employee Sign In"}
        </h2>
        <p className="text-center text-xs text-gray-400 mb-5">
          {isAdmin ? "Full system access & management" : "Access your department knowledge base"}
        </p>


        <form onSubmit={handleSubmit} noValidate>

          <InputField
            id={`${type}-email`}
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setErrors((p) => ({ ...p, email: "" })); }}
            placeholder={isAdmin ? "admin@company.com" : "you@company.com"}
            error={errors.email}
            autoComplete="email"
          />

            <InputField
              id={`${type}-password`}
              label="Password"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setErrors((p) => ({ ...p, password: "" })); }}
              placeholder="Enter your password"
              error={errors.password}
              autoComplete="current-password"
            />

            {errors.form && (
              <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 px-4 py-2.5 rounded-xl text-center">
                {errors.form}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3.5 rounded-xl font-semibold text-white text-sm
                shadow-md hover:shadow-lg transition-all duration-200 active:scale-95
                disabled:opacity-60 disabled:cursor-not-allowed
                flex items-center justify-center gap-2 mt-1`}
              style={{
                background: `linear-gradient(135deg, ${accentColor.from}, ${accentColor.to})`,
              }}
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Signing in…
                </>
              ) : (
                <>
                  {isAdmin ? "🔐 Sign In as Admin" : `👤 Sign In`}
                </>
              )}
            </button>
        </form>

        {/* Removed switch action */}
      </div>
    </div>
  );
}

// ─── Main Login page ──────────────────────────────────────────────
export default function Login({ onLogin }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex flex-col">
      {/* Header */}
      <header className="w-full pt-12 pb-6 flex flex-col items-center px-4">
        <div className="mb-5"><LockCloudIcon /></div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight text-center leading-tight">
          Secure AI Knowledge Assistant
        </h1>
        <p className="mt-2.5 text-gray-500 text-base sm:text-lg text-center max-w-md">
          Sign in or create a new account to get started
        </p>
        <div className="mt-6 h-px w-24 bg-gradient-to-r from-transparent via-blue-300 to-transparent" />
      </header>

      {/* Cards */}
      <main className="flex-1 flex items-start justify-center px-4 pb-14">
        <div className="flex flex-col sm:flex-row gap-6 w-full max-w-2xl justify-center items-stretch mt-4">
          <AuthCard type="admin"    onLogin={onLogin} />
          <AuthCard type="employee" onLogin={onLogin} />
        </div>
      </main>

      <footer className="pb-6 text-center text-xs text-gray-400">
        © 2026 Secure AI Knowledge Assistant · Enterprise Edition
      </footer>

      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          20% { transform: translateX(-6px); }
          40% { transform: translateX(6px); }
          60% { transform: translateX(-4px); }
          80% { transform: translateX(4px); }
        }
        .animate-shake { animation: shake 0.5s ease-in-out; }
      `}</style>
    </div>
  );
}
