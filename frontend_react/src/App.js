import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API = "http://localhost:5000/api";

const ROLES = [
  { value: "employee",  label: "👤 Employee",  color: "#6366f1", canUpload: false },
  { value: "finance",   label: "💰 Finance",   color: "#10b981", canUpload: true  },
  { value: "marketing", label: "📣 Marketing", color: "#f59e0b", canUpload: true  },
  { value: "hr",        label: "🧑‍💼 HR",        color: "#8b5cf6", canUpload: true  },
  { value: "admin",     label: "🔐 Admin",     color: "#ef4444", canUpload: true  },
];

export default function App() {
  const [query, setQuery] = useState("");
  const [role, setRole] = useState("employee");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // null | "uploading" | "success" | "error"
  const [uploadMsg, setUploadMsg] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const chatEndRef = useRef(null);

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
      const res = await axios.post(`${API}/query`, { query: trimmed, role });
      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text: res.data.answer,
          sources: res.data.sources || [],
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { type: "error", text: "⚠️ Failed to reach the server. Is the backend running?" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendQuery();
    }
  };

  const uploadFile = async (file) => {
    if (!file) return;
    if (!file.name.endsWith(".pdf")) {
      setUploadStatus("error");
      setUploadMsg("Only PDF files are supported.");
      return;
    }

    setUploadStatus("uploading");
    setUploadMsg(`Uploading "${file.name}"...`);

    const formData = new FormData();
    formData.append("file", file);

    try {
      await axios.post(`${API}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadStatus("success");
      setUploadMsg(`✅ "${file.name}" uploaded & indexed into vector DB!`);
    } catch (err) {
      setUploadStatus("error");
      setUploadMsg(`❌ Upload failed: ${err.response?.data?.error || err.message}`);
    }
  };

  const handleFileChange = (e) => uploadFile(e.target.files[0]);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    uploadFile(e.dataTransfer.files[0]);
  };

  const selectedRole = ROLES.find((r) => r.value === role);
  const canUpload = selectedRole?.canUpload ?? false;

  return (
    <div className="app">
      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="logo">
          <span className="logo-icon">🧠</span>
          <span className="logo-text">Enterprise<br /><b>RAG System</b></span>
        </div>

        {/* ROLE SELECTOR */}
        <div className="section-title">Access Role</div>
        <div className="role-list">
          {ROLES.map((r) => (
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

        {/* UPLOAD PANEL */}
        <div className="section-title" style={{ marginTop: 28 }}>Upload Document</div>

        {canUpload ? (
          <>
            <div
              className={`drop-zone ${dragOver ? "drag-over" : ""} ${uploadStatus === "uploading" ? "uploading" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                style={{ display: "none" }}
                onChange={handleFileChange}
              />
              {uploadStatus === "uploading" ? (
                <div className="upload-spinner">
                  <div className="spinner" />
                  <span>Processing...</span>
                </div>
              ) : (
                <>
                  <div className="upload-icon">📄</div>
                  <div className="upload-label">
                    {dragOver ? "Drop PDF here" : "Click or drag & drop PDF"}
                  </div>
                  <div className="upload-hint">PDF files only · Indexes into vector DB</div>
                </>
              )}
            </div>

            {uploadMsg && (
              <div className={`upload-msg ${uploadStatus}`}>{uploadMsg}</div>
            )}
          </>
        ) : (
          <div className="upload-locked">
            <div className="lock-icon">🔒</div>
            <div className="lock-title">Access Restricted</div>
            <div className="lock-sub">Employees cannot upload documents.<br />Switch to Finance, HR, Marketing, or Admin.</div>
          </div>
        )}

        <div className="sidebar-footer">
          <span className="status-dot" />
          Backend connected
        </div>
      </aside>

      {/* MAIN CHAT AREA */}
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
              <div className="msg-bubble typing">
                <span /><span /><span />
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* INPUT BAR */}
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
          <button
            className="send-btn"
            onClick={sendQuery}
            disabled={loading || !query.trim()}
          >
            {loading ? <div className="btn-spinner" /> : "Send ↑"}
          </button>
        </div>
      </main>
    </div>
  );
}