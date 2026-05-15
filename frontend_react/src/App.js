import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";
import Login from "./Login";
import AdminDashboard from "./AdminDashboard";

const API = "http://127.0.0.1:5000/api";

const ROLES = [
  { value: "general",     label: "👤 General",     color: "#6366f1", canUpload: false },
  { value: "finance",     label: "💰 Finance",     color: "#10b981", canUpload: true  },
  { value: "marketing",   label: "📣 Marketing",   color: "#f59e0b", canUpload: true  },
  { value: "hr",          label: "🧑‍💼 HR",          color: "#8b5cf6", canUpload: true  },
  { value: "engineering", label: "⚙️ Engineering", color: "#0ea5e9", canUpload: true  },
  { value: "admin",       label: "🔐 Admin",       color: "#ef4444", canUpload: true  },
];

const ADMIN_ROLES    = ROLES;
const EMPLOYEE_ROLES = ROLES.filter((r) => r.value !== "admin");

function ChatApp({ user, onLogout, onBackToDashboard }) {
  const isAdmin = user.role === "admin";
  const [role, setRole]           = useState(user.role);
  const [query, setQuery]         = useState("");
  const [messages, setMessages]   = useState([]);
  const [loading, setLoading]     = useState(false);
  const [roleToast, setRoleToast] = useState(null);
  const [pendingRole, setPendingRole] = useState(null); // role awaiting confirmation
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  
  // New Upload State
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadMsg, setUploadMsg] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const chatEndRef   = useRef(null);
  const inputRef     = useRef(null);
  const toastTimerRef = useRef(null);

  const allowedRoles = isAdmin ? ADMIN_ROLES : EMPLOYEE_ROLES.filter((r) => r.value === user.role);

  // 1. Fetch History on Mount
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get(`${API}/history`, {
          headers: { "Authorization": `Bearer ${user.token}` }
        });
        if (res.data.history) setMessages(res.data.history);
      } catch (err) {
        console.error("Failed to fetch history", err);
      }
    };
    fetchHistory();
  }, [user.token]);

  // 2. Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Upload Logic ──
  const handleUpload = async (file) => {
    if (!file || uploading) return;
    
    const ALLOWED = [".pdf", ".docx", ".csv", ".xlsx", ".md"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!ALLOWED.includes(ext)) {
      setUploadMsg({ type: "error", text: `Unsupported: ${ext}. Use PDF, DOCX, CSV, MD.` });
      setTimeout(() => setUploadMsg(null), 5000);
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadMsg({ type: "info", text: `Uploading ${file.name}...` });

    const formData = new FormData();
    formData.append("file", file);
    formData.append("role", role); // Locks to current context role (which for users is their dept)

    try {
      const res = await axios.post(`${API}/upload`, formData, {
        headers: { "Authorization": `Bearer ${user.token}` }
      });

      const taskId = res.data.task_id;
      if (!taskId) {
        const msg = res.data.status === "pending" 
          ? "✅ Uploaded! Awaiting admin approval." 
          : "✅ Upload complete!";
        setUploadMsg({ type: "success", text: msg });
        setUploading(false);
        setTimeout(() => setUploadMsg(null), 5000);
        return;
      }

      // Poll Task Status
      const poll = async () => {
        try {
          const sRes = await axios.get(`${API}/tasks/${taskId}`, {
            headers: { "Authorization": `Bearer ${user.token}` }
          });
          const { status, progress, message } = sRes.data;
          if (status === "SUCCESS") {
            setUploadProgress(100);
            setUploadMsg({ type: "success", text: "✅ Document indexed!" });
            setUploading(false);
            setTimeout(() => setUploadMsg(null), 3000);
          } else if (status === "FAILURE") {
            setUploadMsg({ type: "error", text: "❌ Indexing failed." });
            setUploading(false);
          } else {
            setUploadProgress(progress || 0);
            setUploadMsg({ type: "info", text: message || "Processing..." });
            setTimeout(poll, 1500);
          }
        } catch {
          setUploading(false);
        }
      };
      poll();
    } catch (err) {
      setUploadMsg({ type: "error", text: "❌ Upload failed." });
      setUploading(false);
    }
  };

  // 3. Streaming Query Implementation
  const sendQuery = async () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    // Add user message immediately
    const userMsg = { type: "user", text: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setLoading(true);

    // Placeholder for bot message
    let botMsg = { type: "bot", text: "", sources: [] };
    setMessages((prev) => [...prev, botMsg]);

    try {
      const response = await fetch(`${API}/query_stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${user.token}`
        },
        body: JSON.stringify({ query: trimmed, role })
      });

      if (!response.ok) throw new Error("Stream request failed");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        
        // Handle metadata chunk
        if (chunk.includes("SOURCES_JSON:")) {
          const [textBefore, jsonStr] = chunk.split("SOURCES_JSON:");
          fullText += textBefore;
          try {
            botMsg.sources = JSON.parse(jsonStr.trim());
          } catch (e) {
            console.error("Failed to parse sources", e);
          }
        } else if (chunk.includes("---CORRECTION---")) {
          // Post-stream grounding check failed — replace entire answer
          const corrected = chunk.split("---CORRECTION---")[1];
          fullText = corrected;
        } else {
          fullText += chunk;
        }

        // Update current bot message in state
        botMsg.text = fullText;
        setMessages((prev) => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1] = { ...botMsg };
          return newMsgs;
        });
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { type: "error", text: "⚠️ Connection lost or server error." };
        return newMsgs;
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendQuery(); }
  };

  const handleRoleSwitch = (newRole) => {
    if (newRole === role) return;
    setPendingRole(newRole); // show confirmation dialog
  };

  const confirmRoleSwitch = () => {
    if (!pendingRole) return;
    const newRoleMeta = ROLES.find((r) => r.value === pendingRole);
    setMessages((prev) => [
      ...prev,
      { type: "system", text: `🔀 Context switched to ${newRoleMeta?.label} — queries now scoped to ${newRoleMeta?.label} documents.` }
    ]);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setRoleToast({ label: newRoleMeta?.label, color: newRoleMeta?.color });
    toastTimerRef.current = setTimeout(() => setRoleToast(null), 3500);
    setRole(pendingRole);
    setPendingRole(null);
    // Explicitly focus the input after switch
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const cancelRoleSwitch = () => setPendingRole(null);
  
  const clearHistory = async () => {
    try {
      await axios.delete(`${API}/history`, {
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      setMessages([]);
      setShowClearConfirm(false);
    } catch (err) {
      console.error("Failed to clear history", err);
      alert("Failed to clear history");
    }
  };

  const selectedRole = ROLES.find((r) => r.value === role);

  return (
    <div className="flex min-h-screen bg-[#fafafa] font-sans text-[#0a0a0a]">
      {/* ── Sidebar ── */}
      <aside className="w-[240px] flex-shrink-0 bg-[#f8f9fa] border-r border-gray-200 flex flex-col shadow-[1px_0_10px_rgba(0,0,0,0.02)] z-20">
        {/* Logo */}
        <div className="px-6 py-6 border-b border-gray-200 bg-[#f8f9fa]">
          <div className="flex items-center gap-3 mb-6">
             <div className="w-8 h-8 bg-[#0a0a0a] rounded flex items-center justify-center text-white shrink-0 shadow-sm">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
             </div>
             <div className="flex-1 min-w-0">
               <div className="font-bold text-[#0a0a0a] leading-none tracking-tight text-[16px] truncate">SENTINEL</div>
               <div className="text-[10px] text-gray-500 font-medium tracking-wide mt-1 truncate">Enterprise RAG</div>
             </div>
          </div>
          <div className="border-t border-gray-200 -mx-6 mb-5"></div>
          
          {isAdmin && onBackToDashboard ? (
            <button onClick={onBackToDashboard} className="w-full bg-white border border-gray-200 text-[#0a0a0a] py-2 rounded flex items-center justify-center gap-2 text-[11px] font-bold hover:bg-gray-50 transition-colors shadow-sm tracking-wide">
              ← BACK TO DASHBOARD
            </button>
          ) : (
            <div className="flex items-center gap-3 bg-white border border-gray-200 px-3 py-2 rounded shadow-sm">
              <div className="w-6 h-6 rounded bg-[#f4f5f5] flex items-center justify-center text-[12px]">👤</div>
              <div className="flex-1 min-w-0">
                <div className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">LOGGED IN AS</div>
                <div className="text-[11px] font-bold text-[#0a0a0a] truncate tracking-wide">{user.email}</div>
              </div>
            </div>
          )}
        </div>

        {/* Roles / Context */}
        <div className="flex-1 px-4 py-4 overflow-y-auto">
          <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3 px-2">Department Context</div>
          {isAdmin ? (
            <div className="space-y-1">
              {allowedRoles.map((r) => (
                <button
                  key={r.value}
                  onClick={() => handleRoleSwitch(r.value)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded text-[12px] font-bold transition-all duration-150 border ${
                    role === r.value 
                      ? "bg-white border-gray-200 text-[#0a0a0a] shadow-sm" 
                      : "bg-transparent border-transparent text-gray-500 hover:bg-gray-100 hover:text-[#0a0a0a]"
                  }`}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: r.color }}></span>
                  <span className="flex-1 text-left tracking-wide">{r.label.replace(/^.*?\s/, '')}</span>
                  {role === r.value && <span className="text-[9px] font-bold bg-gray-100 px-1.5 py-0.5 rounded text-gray-500">ACTIVE</span>}
                </button>
              ))}
            </div>
          ) : (
            <div className="px-2">
              <div className="flex items-center gap-2 bg-white border border-gray-200 p-2.5 rounded shadow-sm">
                 <span className="text-[14px]">🔒</span>
                 <span className="text-[11px] font-bold text-gray-500 tracking-wide">Locked to {selectedRole?.label.replace(/^.*?\s/, '')}</span>
              </div>
            </div>
          )}

          {/* Upload Section */}
          {!isAdmin && (
            <div className="mt-8">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3 px-2">Document Ingestion</div>
              <div 
                className={`border-2 border-dashed rounded-[4px] p-4 text-center cursor-pointer transition-colors ${
                  dragOver ? "border-[#0a0a0a] bg-gray-50" : "border-gray-200 hover:border-gray-300 bg-white"
                } ${uploading ? "opacity-70 pointer-events-none" : ""}`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files[0]); }}
                onClick={() => !uploading && fileInputRef.current?.click()}
              >
                <input 
                  ref={fileInputRef} type="file" className="hidden" 
                  onChange={(e) => handleUpload(e.target.files[0])} disabled={uploading}
                />
                {uploading ? (
                  <div className="flex flex-col items-center gap-2">
                    <div className="w-4 h-4 border-2 border-gray-200 border-t-[#0a0a0a] rounded-full animate-spin"></div>
                    <span className="text-[11px] font-bold text-[#0a0a0a]">{uploadProgress}% Uploading...</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-1.5">
                    <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                    <span className="text-[11px] font-bold text-gray-500 tracking-wide">Drop or Click to Upload</span>
                  </div>
                )}
              </div>
              {uploadMsg && (
                <div className={`mt-2 p-2 rounded text-[10px] font-bold text-center tracking-wide ${
                  uploadMsg.type === 'error' ? 'bg-red-50 text-red-600 border border-red-100' :
                  uploadMsg.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' :
                  'bg-blue-50 text-blue-700 border border-blue-100'
                }`}>
                  {uploadMsg.text}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Nav */}
        <div className="p-4 border-t border-gray-200">
          <button onClick={onLogout} className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded text-[11px] font-bold text-gray-500 hover:bg-gray-100 hover:text-[#0a0a0a] transition-colors tracking-wide">
             LOGOUT
          </button>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#fafafa]">
        {/* Top bar */}
        <header className="bg-[#fafafa] border-b border-gray-200 px-8 flex items-center justify-between sticky top-0 z-10 h-[72px] shrink-0">
          <h1 className="text-lg font-bold text-[#0a0a0a] tracking-tight flex items-center gap-3">
             SENTINEL RAG
             <span className="bg-white border border-gray-200 px-2.5 py-0.5 rounded-full text-[10px] text-gray-500 tracking-wide shadow-sm">Query Interface</span>
          </h1>
          <div className="flex items-center gap-6 h-full">
            <div className="flex items-center gap-2 bg-[#e8effd] text-[#2c52a0] px-3 py-1.5 rounded-full text-[11px] font-bold tracking-wide border border-[#d1ddf7]/50 shadow-sm">
              <div className="w-1.5 h-1.5 bg-[#2c52a0] rounded-full"></div>
              Security: Active
            </div>
            <div className="text-[11px] text-gray-600 font-bold tracking-wide flex items-center gap-2">
               Role: 
               <span className="bg-white border border-gray-200 px-2 py-0.5 rounded shadow-sm text-[#0a0a0a]">{user.role === 'admin' ? 'Administrator' : user.role}</span>
            </div>
          </div>
        </header>

        {/* Chat Header Details */}
        <div className="px-8 py-5 border-b border-gray-100 flex justify-between items-center bg-white shrink-0 shadow-sm z-0">
          <div>
             <h2 className="text-[15px] font-bold text-[#0a0a0a] tracking-tight">Active Context: {selectedRole?.label.replace(/^.*?\s/, '')}</h2>
             <p className="text-[11px] font-medium text-gray-500 mt-0.5">Queries are strictly scoped to this department's isolated vector store.</p>
          </div>
          <button onClick={() => setShowClearConfirm(true)} className="border border-gray-200 bg-[#fafafa] hover:bg-red-50 hover:text-red-600 hover:border-red-200 text-gray-500 px-3 py-1.5 rounded text-[11px] font-bold transition-colors tracking-wide flex items-center gap-1.5 shadow-sm">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            CLEAR LOGS
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6">
          {messages.length === 0 && (
             <div className="h-full flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 bg-white border border-gray-200 rounded-full flex items-center justify-center shadow-sm mb-4">
                   <svg className="w-8 h-8 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                </div>
                <h3 className="text-[14px] font-bold text-[#0a0a0a] tracking-wide mb-1">System Ready</h3>
                <p className="text-[12px] text-gray-500 font-medium max-w-[300px]">Type your query below. All responses are verified against ground-truth documents.</p>
             </div>
          )}

          {messages.map((m, i) => (
            m.type === "system" ? (
              <div key={i} className="flex items-center gap-4 py-2">
                <div className="flex-1 border-t border-gray-200"></div>
                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{m.text}</span>
                <div className="flex-1 border-t border-gray-200"></div>
              </div>
            ) : (
            <div key={i} className={`flex gap-4 ${m.type === "user" ? "flex-row-reverse" : "flex-row"}`}>
              {/* Avatar */}
              <div className={`w-8 h-8 rounded shrink-0 flex items-center justify-center shadow-sm border ${
                 m.type === "user" ? "bg-[#0a0a0a] text-white border-[#0a0a0a]" : 
                 m.type === "error" ? "bg-red-50 text-red-500 border-red-100" : 
                 "bg-white text-emerald-600 border-gray-200"
              }`}>
                 {m.type === "user" ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                 ) : (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                 )}
              </div>
              
              {/* Bubble */}
              <div className={`max-w-[75%] rounded-[4px] p-4 shadow-sm border ${
                 m.type === "user" ? "bg-[#0a0a0a] text-white border-[#0a0a0a]" :
                 m.type === "error" ? "bg-red-50 text-red-800 border-red-200" :
                 "bg-white text-[#0a0a0a] border-gray-200"
              }`}>
                <div className="text-[13px] leading-relaxed whitespace-pre-wrap font-medium">{m.text}</div>
                
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-gray-100/20">
                    <span className={`text-[10px] font-bold uppercase tracking-widest mr-2 ${m.type==='user'?'text-gray-300':'text-gray-400'}`}>SOURCES:</span>
                    <div className="flex flex-wrap gap-2 mt-1.5">
                    {m.sources.map((s, si) => (
                      <span key={si} className={`inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-bold tracking-wide border ${
                         m.type==='user' ? 'bg-gray-800 border-gray-700 text-gray-200' : 'bg-[#fafafa] border-gray-200 text-gray-600'
                      }`}>
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                        {s.source ? s.source.split(/[\/\\]/).pop() : "Doc"} {s.page !== undefined ? `(Pg ${s.page})` : ""}
                      </span>
                    ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            )
          ))}
          {loading && !messages[messages.length-1]?.text && (
            <div className="flex gap-4">
              <div className="w-8 h-8 rounded bg-white text-emerald-600 border border-gray-200 flex items-center justify-center shadow-sm">
                 <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              </div>
              <div className="bg-white border border-gray-200 p-4 rounded-[4px] shadow-sm flex items-center gap-1.5">
                 <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
                 <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.15s" }}></div>
                 <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.3s" }}></div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-6 bg-white border-t border-gray-200 shrink-0 z-10 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.02)]">
          <div className="max-w-4xl mx-auto flex items-end gap-3 bg-[#fafafa] border border-gray-300 rounded-[4px] p-2 focus-within:border-[#0a0a0a] transition-colors shadow-sm">
            <textarea
              ref={inputRef}
              className="flex-1 bg-transparent resize-none outline-none py-2 px-2 text-[13px] font-medium text-[#0a0a0a] placeholder-gray-400 max-h-[120px] overflow-y-auto"
              value={query}
              onChange={(e) => {
                 setQuery(e.target.value);
                 e.target.style.height = 'auto';
                 e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
              }}
              onKeyDown={handleKeyDown}
              placeholder="Query the enterprise knowledge base..."
              rows={1}
              disabled={loading}
            />
            <button 
              className="mb-1 shrink-0 bg-[#0a0a0a] hover:bg-gray-800 text-white rounded px-4 py-2 text-[11px] font-bold tracking-wide transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2" 
              onClick={(e) => { e.stopPropagation(); sendQuery(); }} 
              disabled={loading || !query.trim()}
            >
              EXECUTE
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
            </button>
          </div>
          <div className="max-w-4xl mx-auto mt-2 flex justify-between items-center text-[10px] font-bold text-gray-400 tracking-wide">
             <span>Press ENTER to send, SHIFT+ENTER for new line</span>
             <span className="flex items-center gap-1">
               <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
               SYSTEM GROUNDING ACTIVE
             </span>
          </div>
        </div>
      </main>

      {/* ── Role-switch floating toast ── */}
      {roleToast && (
        <div className="fixed bottom-6 right-6 bg-white border border-gray-200 p-4 rounded-[4px] shadow-lg flex flex-col gap-1 z-50 animate-bounce" style={{ borderLeftWidth: '4px', borderLeftColor: roleToast.color }}>
          <span className="text-[12px] font-bold text-[#0a0a0a] tracking-wide flex items-center gap-2">
             <span className="w-2 h-2 rounded-full" style={{ background: roleToast.color }}></span>
             Context Switched: {roleToast.label.replace(/^.*?\s/, '')}
          </span>
          <span className="text-[10px] text-gray-500 font-medium">Data isolation boundaries updated successfully.</span>
        </div>
      )}

      {/* ── Role-switch confirmation dialog ── */}
      {pendingRole && (() => {
        const from = ROLES.find((r) => r.value === role);
        const to   = ROLES.find((r) => r.value === pendingRole);
        return (
          <div className="fixed inset-0 bg-[#0a0a0a]/50 flex items-center justify-center z-50 backdrop-blur-sm p-4">
            <div className="bg-white border border-gray-200 rounded-[4px] shadow-2xl w-full max-w-md overflow-hidden">
              <div className="p-6">
                <div className="w-12 h-12 bg-blue-50 border border-blue-100 text-blue-600 rounded flex items-center justify-center mb-4">
                   <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
                </div>
                <h3 className="text-[18px] font-bold text-[#0a0a0a] tracking-tight mb-2">Switch Data Context?</h3>
                <p className="text-[13px] text-gray-600 font-medium mb-4 leading-relaxed">
                  You are changing the active isolation boundary.
                </p>
                <div className="flex items-center gap-3 bg-[#fafafa] border border-gray-200 p-3 rounded mb-6">
                   <span className="bg-white border border-gray-200 px-2.5 py-1 rounded text-[11px] font-bold shadow-sm">{from?.label.replace(/^.*?\s/, '')}</span>
                   <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                   <span className="bg-white border border-gray-200 px-2.5 py-1 rounded text-[11px] font-bold shadow-sm">{to?.label.replace(/^.*?\s/, '')}</span>
                </div>
              </div>
              <div className="bg-[#fafafa] px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
                <button className="px-4 py-2 bg-white border border-gray-300 text-[#0a0a0a] text-[11px] font-bold rounded hover:bg-gray-50 transition-colors tracking-wide" onClick={cancelRoleSwitch}>CANCEL</button>
                <button className="px-4 py-2 bg-[#0a0a0a] text-white text-[11px] font-bold rounded hover:bg-gray-800 transition-colors tracking-wide shadow-sm" onClick={confirmRoleSwitch}>CONFIRM SWITCH</button>
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── Clear history confirmation dialog ── */}
      {showClearConfirm && (
        <div className="fixed inset-0 bg-[#0a0a0a]/50 flex items-center justify-center z-50 backdrop-blur-sm p-4">
          <div className="bg-white border border-gray-200 rounded-[4px] shadow-2xl w-full max-w-md overflow-hidden">
            <div className="p-6">
              <div className="w-12 h-12 bg-red-50 border border-red-100 text-red-600 rounded flex items-center justify-center mb-4">
                 <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
              </div>
              <h3 className="text-[18px] font-bold text-[#0a0a0a] tracking-tight mb-2">Purge Security Logs?</h3>
              <p className="text-[13px] text-gray-600 font-medium mb-1 leading-relaxed">
                This action will permanently delete all session queries and interactions.
              </p>
              <p className="text-[11px] font-bold text-red-600 tracking-wide mt-3">WARNING: THIS ACTION CANNOT BE UNDONE</p>
            </div>
            <div className="bg-[#fafafa] px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button className="px-4 py-2 bg-white border border-gray-300 text-[#0a0a0a] text-[11px] font-bold rounded hover:bg-gray-50 transition-colors tracking-wide" onClick={() => setShowClearConfirm(false)}>CANCEL</button>
              <button className="px-4 py-2 bg-red-600 text-white text-[11px] font-bold rounded hover:bg-red-700 transition-colors tracking-wide shadow-sm" onClick={clearHistory}>PURGE LOGS</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [user, setUser]         = useState(null);
  const [adminPage, setAdminPage] = useState("dashboard");

  const handleLogin = (userData) => { setUser(userData); setAdminPage("dashboard"); };
  const handleLogout = () => { setUser(null); setAdminPage("dashboard"); };

  if (!user) return <Login onLogin={handleLogin} />;
  if (user.role === "admin") {
    if (adminPage === "chat") return <ChatApp user={user} onLogout={handleLogout} onBackToDashboard={() => setAdminPage("dashboard")} />;
    return <AdminDashboard user={user} onLogout={handleLogout} onOpenChat={() => setAdminPage("chat")} />;
  }
  return <ChatApp user={user} onLogout={handleLogout} onBackToDashboard={null} />;
}