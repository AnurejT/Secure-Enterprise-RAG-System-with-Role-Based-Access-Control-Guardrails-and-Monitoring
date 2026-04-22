import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";
import Login from "./Login";
import AdminDashboard from "./AdminDashboard";

const API = "http://localhost:5000/api";

// All roles — only admin can switch between them inside ChatApp
const ROLES = [
  { value: "employee",  label: "👤 Employee",  color: "#6366f1", canUpload: false },
  { value: "finance",   label: "💰 Finance",   color: "#10b981", canUpload: true  },
  { value: "marketing", label: "📣 Marketing", color: "#f59e0b", canUpload: true  },
  { value: "hr",        label: "🧑‍💼 HR",        color: "#8b5cf6", canUpload: true  },
  { value: "admin",     label: "🔐 Admin",     color: "#ef4444", canUpload: true  },
];

const ADMIN_ROLES    = ROLES;
const EMPLOYEE_ROLES = ROLES.filter((r) => r.value !== "admin");

// ─────────────────────────────────────────────
// ChatApp — used by employees AND admin (via dashboard)
// ─────────────────────────────────────────────
function ChatApp({ user, onLogout, onBackToDashboard }) {
  const isAdmin = user.role === "admin";

  // Employees: locked to their login role. Admins: can switch.
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

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendQuery = async () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    setMessages((prev) => [...prev, { type: "user", text: trimmed }]);
    setQuery("");
    setLoading(true);
    try {
      const res = await axios.post(`${API}/query`, { query: trimmed, role }, {
        headers: {
          "Authorization": `Bearer ${user.token}`
        }
      });
      setMessages((prev) => [...prev, { type: "bot", text: res.data.answer, sources: res.data.sources || [] }]);
    } catch {
      setMessages((prev) => [...prev, { type: "error", text: "⚠️ Failed to reach the server. Is the backend running?" }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendQuery(); }
  };

  const uploadFile = async (file) => {
    if (!file) return;
    if (!file.name.endsWith(".pdf")) { setUploadStatus("error"); setUploadMsg("Only PDF files are supported."); return; }
    setUploadStatus("uploading");
    setUploadMsg(`Uploading "${file.name}"…`);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("role", role); // 🔥 CRITICAL FIX: append role

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
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="logo">
          <span className="logo-icon">🧠</span>
          <span className="logo-text">Enterprise<br /><b>RAG System</b></span>
        </div>

        {/* Back to dashboard — admin only */}
        {isAdmin && onBackToDashboard && (
          <button
            onClick={onBackToDashboard}
            style={{
              display: "flex", alignItems: "center", gap: 8,
              background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: 10, padding: "9px 14px", color: "rgba(255,255,255,0.7)",
              fontSize: 13, cursor: "pointer", fontWeight: 500, transition: "all 0.2s",
              width: "100%", marginBottom: 14,
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.14)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.07)")}
          >
            ← Dashboard
          </button>
        )}

        {/* User badge */}
        <div style={{
          background: "rgba(255,255,255,0.08)", borderRadius: 12,
          padding: "10px 14px", marginBottom: 20,
          display: "flex", alignItems: "center", gap: 10,
        }}>
          <span style={{ fontSize: 22 }}>{isAdmin ? "🔐" : "👤"}</span>
          <div>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.55)", fontWeight: 500 }}>Logged in as</div>
            <div style={{ fontSize: 13, color: "#fff", fontWeight: 600 }}>{user.email}</div>
          </div>
        </div>

        {/* ROLE selector / locked display */}
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
          /* Employee: role locked to their department login */
          <div style={{
            background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 10, padding: "10px 14px",
            display: "flex", alignItems: "center", gap: 10,
          }}>
            <span style={{ fontSize: 18 }}>🔒</span>
            <div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", fontWeight: 500, marginBottom: 2 }}>Role locked</div>
              <div style={{ fontSize: 13, color: "#fff", fontWeight: 600 }}>
                {selectedRole?.label ?? user.role}
              </div>
            </div>
          </div>
        )}

        {/* UPLOAD */}
        <div className="section-title" style={{ marginTop: 28 }}>Upload Document</div>

        {canUpload ? (
          <>
            <div
              className={`drop-zone ${dragOver ? "drag-over" : ""} ${uploadStatus === "uploading" ? "uploading" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => { e.preventDefault(); setDragOver(false); uploadFile(e.dataTransfer.files[0]); }}
              onClick={() => fileInputRef.current?.click()}
            >
              <input ref={fileInputRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={(e) => uploadFile(e.target.files[0])} />
              {uploadStatus === "uploading" ? (
                <div className="upload-spinner"><div className="spinner" /><span>Processing...</span></div>
              ) : (
                <>
                  <div className="upload-icon">📄</div>
                  <div className="upload-label">{dragOver ? "Drop PDF here" : "Click or drag & drop PDF"}</div>
                  <div className="upload-hint">PDF files only · Indexes into vector DB</div>
                </>
              )}
            </div>
            {uploadMsg && <div className={`upload-msg ${uploadStatus}`}>{uploadMsg}</div>}
          </>
        ) : (
          <div className="upload-locked">
            <div className="lock-icon">🔒</div>
            <div className="lock-title">Access Restricted</div>
            <div className="lock-sub">
              {isAdmin
                ? "Switch to a role with upload access above."
                : "Employees cannot upload documents."}
            </div>
          </div>
        )}

        <div className="sidebar-footer">
          <span className="status-dot" />Backend connected
        </div>

        <button
          onClick={onLogout}
          style={{
            marginTop: 10, width: "100%", padding: "9px 0",
            background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 10, color: "rgba(255,255,255,0.6)", fontSize: 13,
            cursor: "pointer", fontWeight: 500, transition: "all 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.13)")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.07)")}
        >
          ← Logout
        </button>
      </aside>

      {/* CHAT AREA */}
      <main className="chat-area">
        <div className="chat-header">
          <div>
            <div className="chat-title">Ask your enterprise documents</div>
            <div className="chat-subtitle">
              Querying as&nbsp;
              <span className="role-badge" style={{ background: selectedRole?.color }}>
                {selectedRole?.label}
              </span>
            </div>
          </div>
        </div>

        <div className="messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">💬</div>
              <div className="empty-title">No messages yet</div>
              <div className="empty-sub">
                {canUpload
                  ? "Upload a PDF in the sidebar → then ask questions about it"
                  : "Ask questions about the enterprise knowledge base"}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`msg-row ${m.type}`}>
              <div className="msg-avatar">
                {m.type === "user" ? "👤" : m.type === "error" ? "⚠️" : "🤖"}
              </div>
              <div className="msg-bubble">
                <div className="msg-text">{m.text}</div>
                {m.sources && m.sources.length > 0 && (
                  <div className="sources">
                    <span className="sources-label">Sources:</span>
                    {m.sources.map((s, si) => (
                      <span key={si} className="source-chip">
                        📎 {s.source ? s.source.split(/[/\\]/).pop() : `Chunk ${si + 1}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="msg-row bot">
              <div className="msg-avatar">🤖</div>
              <div className="msg-bubble typing"><span /><span /><span /></div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* INPUT */}
        <div className="input-bar">
          <textarea
            className="input-field"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask something about your documents… (Enter to send)"
            rows={1}
            disabled={loading}
          />
          <button className="send-btn" onClick={sendQuery} disabled={loading || !query.trim()}>
            {loading ? <div className="btn-spinner" /> : "Send ↑"}
          </button>
        </div>
      </main>
    </div>
  );
}

// ─────────────────────────────────────────────
// Root App — routing state machine
// ─────────────────────────────────────────────
export default function App() {
  const [user, setUser]         = useState(null);        // null = not logged in
  const [adminPage, setAdminPage] = useState("dashboard"); // admin sub-page: "dashboard" | "chat"

  const handleLogin = (userData) => {
    setUser(userData);
    setAdminPage("dashboard");
  };

  const handleLogout = () => {
    setUser(null);
    setAdminPage("dashboard");
  };

  // ── Not logged in ── show Login
  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  // ── Admin ── show Dashboard or Chat
  if (user.role === "admin") {
    if (adminPage === "chat") {
      return (
        <ChatApp
          user={user}
          onLogout={handleLogout}
          onBackToDashboard={() => setAdminPage("dashboard")}
        />
      );
    }
    return (
      <AdminDashboard
        user={user}
        onLogout={handleLogout}
        onOpenChat={() => setAdminPage("chat")}
      />
    );
  }

  // ── Employee / Finance / HR / Marketing ── go straight to Chat
  return <ChatApp user={user} onLogout={handleLogout} onBackToDashboard={null} />;
}