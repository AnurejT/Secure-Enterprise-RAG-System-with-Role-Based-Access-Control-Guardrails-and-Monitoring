import { useState } from "react";
import axios from "axios";

const API = "http://localhost:5000/api/auth";

// ─── SVG Icons ────────────────────────────────────────────────────
function BrandLogo() {
  return (
    <div className="flex flex-col items-center justify-center mb-8">
      <svg width="80" height="80" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Abstract AI / Network Node */}
        <circle cx="50" cy="50" r="40" stroke="white" strokeWidth="1.5" strokeDasharray="4 4" fill="transparent" opacity="0.6"/>
        <circle cx="50" cy="50" r="25" stroke="white" strokeWidth="2" fill="transparent" />
        <circle cx="50" cy="25" r="5" fill="white" />
        <circle cx="75" cy="50" r="5" fill="white" />
        <circle cx="50" cy="75" r="5" fill="white" />
        <circle cx="25" cy="50" r="5" fill="white" />
        <circle cx="50" cy="50" r="8" fill="white" />
        <path d="M50 25 L50 42 M75 50 L58 50 M50 75 L50 58 M25 50 L42 50" stroke="white" strokeWidth="2" opacity="0.8"/>
      </svg>
      <h1 className="text-white text-xl font-semibold tracking-wider mt-4 shadow-sm text-center">
        ENTERPRISE KNOWLEDGE <br/>
        <span className="font-light opacity-90 text-lg">AI ASSISTANT</span>
      </h1>
    </div>
  );
}

function TabIconGeneral() {
  // SVG approximating the "Patient" icon with a sling from the image
  return (
    <svg width="60" height="60" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="30" r="15" fill="#fca5a5" />
      {/* Shirt */}
      <path d="M25 80 C 25 50, 75 50, 75 80" fill="#38bdf8" />
      {/* Sling */}
      <path d="M25 80 L 75 50 L 75 60 L 25 90 Z" fill="#e0f2fe" opacity="0.9" />
      <rect x="40" y="60" width="20" height="20" fill="#fca5a5" />
    </svg>
  );
}

function TabIconAdmin() {
  // SVG approximating the doctor icon from the image
  return (
    <svg width="60" height="60" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="30" r="15" fill="#fed7aa" />
      {/* Coat */}
      <path d="M30 80 C 30 50, 70 50, 70 80" fill="#f1f5f9" />
      {/* Stethoscope */}
      <path d="M40 55 L 45 70 L 55 70 L 60 55" stroke="#38bdf8" strokeWidth="3" fill="none" />
      <circle cx="45" cy="70" r="4" fill="#38bdf8" />
    </svg>
  );
}

function CustomInput({ id, label, type, value, onChange, placeholder, error, showForgot }) {
  // Only show label if it's the email field as per the reference image
  const showLabel = label === "Email";
  const isValid = value.length > 0 && !error;

  return (
    <div className={`mb-6 relative ${showForgot ? "mb-8" : ""}`}>
      {showLabel && (
        <div className="absolute -top-3 right-4 bg-[#22d3ee] text-white text-xs px-3 py-0.5 rounded-sm shadow-sm z-10 font-medium tracking-wide">
          {label}
        </div>
      )}
      <div className="relative">
        <input
          id={id}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`w-full px-4 py-3.5 rounded border ${
            error ? "border-red-400 bg-red-50" : "border-gray-200"
          } text-gray-800 placeholder-gray-500 text-sm focus:outline-none focus:border-[#22d3ee] transition-colors`}
        />
        {/* Valid checkmark */}
        {isValid && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 bg-[#4ade80] rounded-full p-0.5">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
          </div>
        )}
      </div>
      {error && <p className="text-xs text-red-500 mt-1 absolute">{error}</p>}
      {showForgot && (
        <div className="text-right mt-2">
          <a href="#" className="text-xs text-gray-500 font-semibold hover:text-[#22d3ee] transition-colors">
            Forget Password
          </a>
        </div>
      )}
    </div>
  );
}

// ─── Main Login page ──────────────────────────────────────────────
export default function Login({ onLogin }) {
  const [activeTab, setActiveTab] = useState("general");
  const isAdmin = activeTab === "admin";

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors]     = useState({});
  const [loading, setLoading]   = useState(false);

  const validate = () => {
    const e = {};
    if (!email.trim()) e.email = "Email required";
    if (!password) e.password = "Password required";
    return e;
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
      const msg = err.response?.data?.error || "Invalid credentials.";
      setErrors({ form: msg });
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 relative" style={{ background: "linear-gradient(135deg, #0ea5e9, #22d3ee)" }}>
      
      {/* Decorative background circle */}
      <div className="absolute top-[-10%] right-[-10%] w-96 h-96 bg-[#38bdf8] rounded-full opacity-50 blur-3xl"></div>
      
      <div className="relative z-10 w-full max-w-[400px]">
        <BrandLogo />

        <div className="bg-white rounded shadow-2xl p-6 relative">
          
          {/* Tab Selector */}
          <div className="flex gap-4 mb-8">
            
            {/* Admin Tab */}
            <div 
              onClick={() => { setActiveTab("admin"); setErrors({}); }}
              className={`flex-1 flex flex-col items-center justify-center py-5 border rounded cursor-pointer relative transition-all duration-300 ${
                isAdmin ? "border-gray-200 shadow-md" : "border-gray-100 opacity-60 hover:opacity-100"
              }`}
            >
              <TabIconAdmin />
              <span className="text-[#38bdf8] font-semibold mt-3 text-sm tracking-wide">Admin Sign In</span>
              
              {isAdmin && (
                <div className="absolute -bottom-3 right-0 -mr-2 bg-[#0ea5e9] rounded-full p-1 border-4 border-white shadow-sm z-20">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                </div>
              )}
            </div>

            {/* General Tab */}
            <div 
              onClick={() => { setActiveTab("general"); setErrors({}); }}
              className={`flex-1 flex flex-col items-center justify-center py-5 border rounded cursor-pointer relative transition-all duration-300 ${
                !isAdmin ? "border-gray-200 shadow-md" : "border-gray-100 opacity-60 hover:opacity-100"
              }`}
            >
              <TabIconGeneral />
              <span className="text-[#38bdf8] font-semibold mt-3 text-sm tracking-wide">Sign In</span>
              
              {!isAdmin && (
                <div className="absolute -bottom-3 right-0 -mr-2 bg-[#0ea5e9] rounded-full p-1 border-4 border-white shadow-sm z-20">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                </div>
              )}
            </div>

          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} noValidate>
            <CustomInput
              id="email"
              label="Email"
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setErrors((p) => ({ ...p, email: "" })); }}
              placeholder={isAdmin ? "admin@company.com" : "you@company.com"}
              error={errors.email}
            />

            <CustomInput
              id="password"
              label="Password"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setErrors((p) => ({ ...p, password: "" })); }}
              placeholder="••••••••••••"
              error={errors.password}
              showForgot={true}
            />

            {errors.form && (
              <div className="text-center text-sm text-red-500 mb-4">{errors.form}</div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#38bdf8] hover:bg-[#0ea5e9] text-white font-semibold py-3.5 rounded mt-2 transition-colors disabled:opacity-70 tracking-wide shadow-md"
            >
              {loading ? "Signing in..." : "Login"}
            </button>
          </form>

        </div>
      </div>
    </div>
  );
}
