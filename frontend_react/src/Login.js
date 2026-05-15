import { useState } from "react";
import axios from "axios";

const API = "http://127.0.0.1:5000/api/auth";

// ─── SVG Icons ────────────────────────────────────────────────────
function BrandLogo() {
  return (
    <div className="flex flex-col items-center justify-center mb-8">
      <div className="w-12 h-12 bg-[#0a0a0a] rounded-[4px] flex items-center justify-center text-white mb-4 shadow-sm">
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
      </div>
      <h1 className="text-[#0a0a0a] text-[22px] font-bold tracking-tight text-center leading-tight">
        SENTINEL <br/>
        <span className="text-[11px] text-gray-500 font-medium tracking-widest uppercase mt-1 block">Enterprise RAG</span>
      </h1>
    </div>
  );
}

function CustomInput({ id, label, type, value, onChange, placeholder, error, showForgot }) {
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const isPasswordField = id === "password";
  
  const currentType = isPasswordField ? (isPasswordVisible ? "text" : "password") : type;

  return (
    <div className={`mb-5 relative`}>
      <label className="block text-[11px] font-bold text-gray-500 tracking-wide uppercase mb-1.5">{label}</label>
      <div className="relative">
        <input
          id={id}
          type={currentType}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`w-full px-3.5 py-2.5 rounded-[4px] border ${
            error ? "border-red-500 bg-red-50 text-red-900" : "border-gray-300 focus:border-[#0a0a0a]"
          } text-[#0a0a0a] placeholder-gray-400 text-[13px] font-medium focus:outline-none focus:ring-1 focus:ring-[#0a0a0a] transition-colors pr-10`}
        />
        
        {isPasswordField && (
          <button
            type="button"
            onClick={() => setIsPasswordVisible(!isPasswordVisible)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#0a0a0a] transition-colors p-1"
          >
            {isPasswordVisible ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
            )}
          </button>
        )}
      </div>
      {error && <p className="text-[11px] font-bold text-red-500 mt-1.5">{error}</p>}
      {showForgot && (
        <div className="text-right mt-2">
          <a href="#" className="text-[11px] text-gray-500 font-bold hover:text-[#0a0a0a] transition-colors">
            Forgot Password?
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
      onLogin({ ...res.data.user, token: res.data.access_token });
    } catch (err) {
      setLoading(false);
      const msg = err.response?.data?.error || "Invalid credentials.";
      setErrors({ form: msg });
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-[#fafafa] font-sans">
      <div className="w-full max-w-[400px]">
        <BrandLogo />

        <div className="bg-white rounded-[4px] border border-gray-200 shadow-sm p-8">
          
          {/* Tab Selector */}
          <div className="flex mb-8 border border-gray-200 rounded-[4px] p-1 bg-gray-50">
            <button 
              type="button"
              onClick={() => { setActiveTab("general"); setErrors({}); }}
              className={`flex-1 py-2 text-[12px] font-bold rounded-[3px] transition-colors ${
                !isAdmin ? "bg-white text-[#0a0a0a] shadow-sm border border-gray-200/60" : "text-gray-500 hover:text-[#0a0a0a]"
              }`}
            >
              Standard Sign In
            </button>
            <button 
              type="button"
              onClick={() => { setActiveTab("admin"); setErrors({}); }}
              className={`flex-1 py-2 text-[12px] font-bold rounded-[3px] transition-colors ${
                isAdmin ? "bg-white text-[#0a0a0a] shadow-sm border border-gray-200/60" : "text-gray-500 hover:text-[#0a0a0a]"
              }`}
            >
              Administrator
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} noValidate>
            <CustomInput
              id="email"
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setErrors((p) => ({ ...p, email: "" })); }}
              placeholder={isAdmin ? "admin@sentinel.local" : "user@department.local"}
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
              <div className="text-center text-[12px] font-bold text-red-500 mb-4 bg-red-50 border border-red-200 py-2 rounded-[4px]">{errors.form}</div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#0a0a0a] hover:bg-gray-800 text-white font-bold py-3 text-[13px] rounded-[4px] mt-4 transition-colors disabled:opacity-70 tracking-wide"
            >
              {loading ? "AUTHENTICATING..." : "SIGN IN"}
            </button>
          </form>

        </div>
        
        <p className="text-center text-[11px] font-bold text-gray-400 mt-8 tracking-wide">
          SECURED BY SENTINEL RAG
        </p>
      </div>
    </div>
  );
}
