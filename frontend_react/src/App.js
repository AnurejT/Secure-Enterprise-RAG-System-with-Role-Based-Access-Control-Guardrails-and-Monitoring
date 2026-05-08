import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";
import Login from "./Login";
import AdminDashboard from "./AdminDashboard";

const API = "http://localhost:5000/api";

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
  const chatEndRef   = useRef(null);
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
                onClick={() => handleRoleSwitch(r.value)}
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

        <div className="sidebar-footer">● Backend connected</div>
        <button onClick={onLogout} className="logout-btn-sidebar">← Logout</button>
      </aside>

      <main className="chat-area">
        <div className="chat-header">
          <div>
            <div className="chat-title">Ask your enterprise documents</div>
            <div className="chat-subtitle">Querying as <span className="role-badge" style={{ background: selectedRole?.color }}>{selectedRole?.label}</span></div>
          </div>
          <button className="clear-btn" onClick={() => setShowClearConfirm(true)}>🗑️ Clear Chat</button>
        </div>

        <div className="messages">
          {messages.length === 0 && <div className="empty-state">💬 Ask something to start...</div>}
          {messages.map((m, i) => (
            m.type === "system" ? (
              <div key={i} className="role-switch-divider">
                <span className="role-switch-line" />
                <span className="role-switch-label">{m.text}</span>
                <span className="role-switch-line" />
              </div>
            ) : (
            <div key={i} className={`msg-row ${m.type}`}>
              <div className="msg-avatar">{m.type === "user" ? "👤" : "🤖"}</div>
              <div className="msg-bubble">
                <div className="msg-text">{m.text}</div>
                {m.sources && m.sources.length > 0 && (
                  <div className="sources">
                    <span className="sources-label">Sources:</span>
                    {m.sources.map((s, si) => (
                      <span key={si} className="source-chip">
                        📎 {s.source ? s.source.split(/[/\\]/).pop() : "Doc"} {s.page !== undefined ? `(Page ${s.page})` : ""}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            )
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

      {/* ── Role-switch floating toast ── */}
      {roleToast && (
        <div className="role-toast" style={{ borderColor: roleToast.color, boxShadow: `0 8px 32px ${roleToast.color}33` }}>
          <span className="role-toast-dot" style={{ background: roleToast.color }} />
          <span>Switched to <strong style={{ color: roleToast.color }}>{roleToast.label}</strong> context</span>
          <span className="role-toast-sub">Queries now scoped to {roleToast.label} documents</span>
        </div>
      )}

      {/* ── Role-switch confirmation dialog ── */}
      {pendingRole && (() => {
        const from = ROLES.find((r) => r.value === role);
        const to   = ROLES.find((r) => r.value === pendingRole);
        return (
          <div className="role-confirm-overlay">
            <div className="role-confirm-card">
              <div className="role-confirm-icon">🔀</div>
              <h3 className="role-confirm-title">Switch Department Context?</h3>
              <p className="role-confirm-desc">
                You are about to switch from
                <span className="role-confirm-badge" style={{ background: from?.color }}>{from?.label}</span>
                to
                <span className="role-confirm-badge" style={{ background: to?.color }}>{to?.label}</span>
              </p>
              <p className="role-confirm-sub">All new queries will be scoped to <strong>{to?.label}</strong> documents.</p>
              <div className="role-confirm-actions">
                <button className="role-confirm-no" onClick={cancelRoleSwitch}>Cancel</button>
                <button className="role-confirm-yes" style={{ background: to?.color }} onClick={confirmRoleSwitch}>Yes, Switch</button>
              </div>
            </div>
          </div>
        );
      })()}
      {/* ── Clear history confirmation dialog ── */}
      {showClearConfirm && (
        <div className="role-confirm-overlay">
          <div className="role-confirm-card">
            <div className="role-confirm-icon" style={{ color: "#ef4444" }}>🗑️</div>
            <h3 className="role-confirm-title">Clear All Chat History?</h3>
            <p className="role-confirm-desc">
              This will permanently delete all messages for your account.
            </p>
            <p className="role-confirm-sub"><strong>This action cannot be undone.</strong></p>
            <div className="role-confirm-actions">
              <button className="role-confirm-no" onClick={() => setShowClearConfirm(false)}>Cancel</button>
              <button className="role-confirm-yes" style={{ background: "#ef4444" }} onClick={clearHistory}>Yes, Clear Everything</button>
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