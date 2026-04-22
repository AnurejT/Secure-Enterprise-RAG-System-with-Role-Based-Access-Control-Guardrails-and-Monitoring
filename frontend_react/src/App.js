import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";
import Login from "./Login";
import AdminDashboard from "./AdminDashboard";

const API = "http://localhost:5000/api";

const ROLES = [
  { value: "employee",  label: "👤 Employee",  color: "#6366f1", canUpload: false },
  { value: "finance",   label: "💰 Finance",   color: "#10b981", canUpload: true  },
  { value: "marketing", label: "📣 Marketing", color: "#f59e0b", canUpload: true  },
  { value: "hr",        label: "🧑‍💼 HR",        color: "#8b5cf6", canUpload: true  },
  { value: "admin",     label: "🔐 Admin",     color: "#ef4444", canUpload: true  },
];

const ADMIN_ROLES    = ROLES;
const EMPLOYEE_ROLES = ROLES.filter((r) => r.value !== "admin");

function ChatApp({ user, onLogout, onBackToDashboard }) {
  const isAdmin = user.role === "admin";
  const [role, setRole]           = useState(user.role);
  const [query, setQuery]         = useState("");
  const [messages, setMessages]   = useState([]);
  const [loading, setLoading]     = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadMsg, setUploadMsg] = useState("");
  const [dragOver, setDragOver]   = useState(false);
  
  const fileInputRef = useRef(null);
  const chatEndRef   = useRef(null);

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
        
        // Handle final sources chunk
        if (chunk.includes("SOURCES_JSON:")) {
          const parts = chunk.split("SOURCES_JSON:");
          fullText += parts[0];
          try {
            const sources = JSON.parse(parts[1]);
            botMsg.sources = sources;
          } catch (e) {
            console.error("Failed to parse sources", e);
          }
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

  const uploadFile = async (file) => {
    if (!file) return;
    const ALLOWED = [".pdf", ".docx", ".csv", ".xlsx", ".md"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!ALLOWED.includes(ext)) {
      setUploadStatus("error");
      setUploadMsg(`Unsupported file type: ${ext}. Supported: PDF, DOCX, CSV, XLSX`);
      return;
    }

    setUploadStatus("uploading");
    setUploadMsg(`Uploading "${file.name}"…`);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("role", role);

    try {
      await axios.post(`${API}/upload`, formData, { 
        headers: { 
          "Content-Type": "multipart/form-data",
          "Authorization": `Bearer ${user.token}`
        } 
      });
      setUploadStatus("success");
      setUploadMsg(`✅ "${file.name}" uploaded & indexed!`);
    } catch (err) {
      setUploadStatus("error");
      setUploadMsg(`❌ Upload failed: ${err.response?.data?.error || err.message}`);
    }
  };

  const selectedRole = ROLES.find((r) => r.value === role);
  const canUpload    = selectedRole?.canUpload ?? false;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <span className="logo-icon">🧠</span>
          <span className="logo-text">Enterprise<br /><b>RAG System</b></span>
        </div>

        {isAdmin && onBackToDashboard && (
          <button onClick={onBackToDashboard} className="back-btn">← Dashboard</button>
        )}

        <div className="user-badge">
          <span style={{ fontSize: 22 }}>{isAdmin ? "🔐" : "👤"}</span>
          <div>
            <div className="user-badge-label">Logged in as</div>
            <div className="user-badge-email">{user.email}</div>
          </div>
        </div>

        <div className="section-title">Access Role</div>
        {isAdmin ? (
          <div className="role-list">
            {allowedRoles.map((r) => (
              <button
                key={r.value}
                className={`role-btn ${role === r.value ? "active" : ""}`}
                style={{ "--role-color": r.color }}
                onClick={() => setRole(r.value)}
              >
                {r.label}
              </button>
            ))}
          </div>
        ) : (
          <div className="locked-role">
            <span>🔒</span> locked to {selectedRole?.label}
          </div>
        )}

        <div className="section-title" style={{ marginTop: 28 }}>Upload Document</div>
        {canUpload ? (
          <div
            className={`drop-zone ${dragOver ? "drag-over" : ""} ${uploadStatus === "uploading" ? "uploading" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); uploadFile(e.dataTransfer.files[0]); }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input ref={fileInputRef} type="file" accept=".pdf,.docx,.csv,.xlsx,.md" style={{ display: "none" }} onChange={(e) => uploadFile(e.target.files[0])} />
            {uploadStatus === "uploading" ? "Processing..." : "Click or drag & drop PDF"}
          </div>
        ) : (
          <div className="upload-locked">🔒 Access Restricted</div>
        )}
        <div className="sidebar-footer">● Backend connected</div>
        <button onClick={onLogout} className="logout-btn-sidebar">← Logout</button>
      </aside>

      <main className="chat-area">
        <div className="chat-header">
          <div className="chat-title">Ask your enterprise documents</div>
          <div className="chat-subtitle">Querying as <span className="role-badge" style={{ background: selectedRole?.color }}>{selectedRole?.label}</span></div>
        </div>

        <div className="messages">
          {messages.length === 0 && <div className="empty-state">💬 Ask something to start...</div>}
          {messages.map((m, i) => (
            <div key={i} className={`msg-row ${m.type}`}>
              <div className="msg-avatar">{m.type === "user" ? "👤" : "🤖"}</div>
              <div className="msg-bubble">
                <div className="msg-text">{m.text}</div>
                {m.sources && m.sources.length > 0 && (
                  <div className="sources">
                    <span className="sources-label">Sources:</span>
                    {m.sources.map((s, si) => (
                      <span key={si} className="source-chip">
                        📎 {s.source ? s.source.split(/[/\\]/).pop() : "Doc"} (Page {s.page || '?'})
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && !messages[messages.length-1]?.text && (
            <div className="msg-row bot"><div className="msg-avatar">🤖</div><div className="msg-bubble typing"><span/><span/><span/></div></div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="input-bar">
          <textarea
            className="input-field"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask something..."
            rows={1}
            disabled={loading}
          />
          <button className="send-btn" onClick={sendQuery} disabled={loading || !query.trim()}>Send ↑</button>
        </div>
      </main>
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