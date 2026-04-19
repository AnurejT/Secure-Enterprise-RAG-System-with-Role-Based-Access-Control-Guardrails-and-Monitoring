import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";

const API = "http://localhost:5000/api";

// ─── Static data ──────────────────────────────────────────────────
const STATS = [
  { label: "Indexed Documents", value: "—",      icon: "📄", change: "Live count", color: "#3b82f6", bg: "#eff6ff" },
  { label: "Queries Today",     value: "47",      icon: "🔍", change: "+12 vs yesterday", color: "#10b981", bg: "#ecfdf5" },
  { label: "Active Departments",value: "4",       icon: "🏢", change: "All online",    color: "#8b5cf6", bg: "#f5f3ff" },
  { label: "System Status",     value: "Online",  icon: "⚡", change: "100% uptime",  color: "#f59e0b", bg: "#fffbeb" },
];

const DEPARTMENTS = [
  { name: "Finance",   icon: "💰", role: "finance",   color: "#10b981", accessLevel: "Restricted", docTypes: "Financial Reports, Balance Sheets, Budgets",                queryCount: 19, status: "Active" },
  { name: "HR",        icon: "🧑‍💼", role: "hr",        color: "#8b5cf6", accessLevel: "Restricted", docTypes: "HR Policies, Employee Records, Leave Guidelines",            queryCount: 11, status: "Active" },
  { name: "Marketing", icon: "📣", role: "marketing", color: "#f59e0b", accessLevel: "Restricted", docTypes: "Campaign Materials, Market Research, Analytics",             queryCount: 9,  status: "Active" },
  { name: "Employee",  icon: "👤", role: "employee",  color: "#6366f1", accessLevel: "Standard",   docTypes: "Company Guidelines, Announcements, Policies",               queryCount: 8,  status: "Active" },
];

const ACTIVITY = [
  { time: "2 min ago",  icon: "🔍", text: "Finance user queried: Q4 budget projections",   label: "Query",  color: "#3b82f6" },
  { time: "5 min ago",  icon: "🔍", text: "HR user queried: Leave policy 2026 update",     label: "Query",  color: "#3b82f6" },
  { time: "12 min ago", icon: "📄", text: "Document uploaded: Annual_Report_2025.pdf",      label: "Upload", color: "#10b981" },
  { time: "18 min ago", icon: "🔍", text: "Marketing queried: Campaign ROI metrics",       label: "Query",  color: "#3b82f6" },
  { time: "1 hr ago",   icon: "🔐", text: "Admin logged in from 10.86.38.207",              label: "Auth",   color: "#f59e0b" },
  { time: "2 hr ago",   icon: "📄", text: "Document uploaded: HR_Policy_v3.pdf",            label: "Upload", color: "#10b981" },
];

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard",       icon: "🏠" },
  { id: "chat",      label: "Query Assistant", icon: "💬" },
  { id: "files",     label: "Manage Files",    icon: "🗂️" },
  { id: "analytics", label: "Analytics",       icon: "📊", soon: true },
  { id: "settings",  label: "Settings",        icon: "⚙️",  soon: true },
];

// ─── File size formatter ──────────────────────────────────────────
function fmtSize(kb) {
  if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`;
  return `${kb} KB`;
}

// ─── File Manager Panel ───────────────────────────────────────────
function FileManagerPanel() {
  const [files, setFiles]               = useState([]);
  const [loading, setLoading]           = useState(true);
  const [uploading, setUploading]       = useState(false);
  const [uploadMsg, setUploadMsg]       = useState(null); // {type, text}
  const [deletingFile, setDeletingFile] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null); // filename waiting confirm
  const [dragOver, setDragOver]         = useState(false);
  const fileInputRef = useRef(null);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/files`);
      setFiles(res.data.files || []);
    } catch {
      setFiles([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchFiles(); }, [fetchFiles]);

  const handleUpload = async (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadMsg({ type: "error", text: "Only PDF files are supported." });
      return;
    }
    setUploading(true);
    setUploadMsg({ type: "info", text: `Uploading & indexing "${file.name}"…` });
    const formData = new FormData();
    formData.append("file", file);
    try {
      await axios.post(`${API}/upload`, formData, { headers: { "Content-Type": "multipart/form-data" } });
      setUploadMsg({ type: "success", text: `✅ "${file.name}" uploaded & indexed successfully!` });
      fetchFiles();
    } catch (err) {
      setUploadMsg({ type: "error", text: `❌ Upload failed: ${err.response?.data?.error || err.message}` });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (filename) => {
    setDeletingFile(filename);
    setConfirmDelete(null);
    try {
      await axios.delete(`${API}/files/${encodeURIComponent(filename)}`);
      setUploadMsg({ type: "success", text: `🗑️ "${filename}" deleted and removed from vector DB.` });
      fetchFiles();
    } catch (err) {
      setUploadMsg({ type: "error", text: `❌ Delete failed: ${err.response?.data?.error || err.message}` });
    } finally {
      setDeletingFile(null);
    }
  };

  const msgColors = {
    success: "bg-green-50 text-green-700 border-green-200",
    error:   "bg-red-50 text-red-700 border-red-200",
    info:    "bg-blue-50 text-blue-700 border-blue-200",
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-1">Manage Files</h2>
        <p className="text-sm text-gray-500">Upload new PDFs or delete existing ones from the knowledge base.</p>
      </div>

      {/* ── Upload Drop Zone ── */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files[0]); }}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center
          cursor-pointer transition-all duration-200 select-none
          ${dragOver ? "border-blue-400 bg-blue-50 scale-[1.01]"
            : uploading ? "border-blue-300 bg-blue-50/60 cursor-not-allowed"
            : "border-gray-200 bg-gray-50 hover:border-blue-300 hover:bg-blue-50/40"}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => handleUpload(e.target.files[0])}
          disabled={uploading}
        />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <svg className="animate-spin h-10 w-10 text-blue-500" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            <span className="text-blue-600 font-medium text-sm">Indexing document into vector DB…</span>
          </div>
        ) : (
          <>
            <div className="text-5xl mb-3">📤</div>
            <p className="text-gray-700 font-semibold text-base">
              {dragOver ? "Drop PDF here" : "Click or drag & drop PDF to upload"}
            </p>
            <p className="text-gray-400 text-sm mt-1">PDF files only · Auto-indexed with RBAC metadata</p>
          </>
        )}
      </div>

      {/* ── Status message ── */}
      {uploadMsg && (
        <div className={`px-4 py-3 rounded-xl text-sm font-medium border ${msgColors[uploadMsg.type]}`}>
          {uploadMsg.text}
        </div>
      )}

      {/* ── File List ── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-50 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-gray-900">Uploaded Files</h3>
            <p className="text-xs text-gray-400 mt-0.5">{files.length} PDF{files.length !== 1 ? "s" : ""} in knowledge base</p>
          </div>
          <button
            onClick={fetchFiles}
            className="text-xs text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 
              px-3 py-1.5 rounded-lg border border-blue-100 font-medium transition-all duration-150 flex items-center gap-1.5"
          >
            🔄 Refresh
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16 gap-3 text-gray-400">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            <span className="text-sm">Loading files…</span>
          </div>
        ) : files.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400 gap-2">
            <div className="text-4xl opacity-40">📂</div>
            <p className="text-sm font-medium">No PDFs uploaded yet</p>
            <p className="text-xs">Upload a file above to get started</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-50">
            {files.map((f) => {
              const isDeleting = deletingFile === f.name;
              const isConfirming = confirmDelete === f.name;
              return (
                <li
                  key={f.name}
                  className={`flex items-center gap-4 px-6 py-4 transition-colors
                    ${isDeleting ? "bg-red-50/40" : "hover:bg-gray-50/70"}`}
                >
                  {/* File icon */}
                  <div className="w-10 h-10 rounded-xl bg-red-50 border border-red-100 flex items-center justify-center text-xl flex-shrink-0">
                    📄
                  </div>

                  {/* Name & size */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{f.name}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{fmtSize(f.size_kb)}</p>
                  </div>

                  {/* Role tag inferred from filename */}
                  <span className="hidden sm:inline-block text-xs bg-gray-100 text-gray-500 px-2.5 py-1 rounded-full font-medium">
                    PDF
                  </span>

                  {/* Actions */}
                  {isDeleting ? (
                    <div className="flex items-center gap-1.5 text-red-400 text-xs">
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                      </svg>
                      Deleting…
                    </div>
                  ) : isConfirming ? (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-red-600 font-medium">Are you sure?</span>
                      <button
                        onClick={() => handleDelete(f.name)}
                        className="text-xs px-3 py-1.5 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 transition-colors"
                      >
                        Delete
                      </button>
                      <button
                        onClick={() => setConfirmDelete(null)}
                        className="text-xs px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setConfirmDelete(f.name)}
                      className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-600
                        bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded-lg border border-red-100
                        hover:border-red-200 font-medium transition-all duration-150"
                      title={`Delete ${f.name}`}
                    >
                      🗑️ Delete
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

// ─── Main Admin Dashboard ─────────────────────────────────────────
export default function AdminDashboard({ user, onLogout, onOpenChat }) {
  const [activeNav, setActiveNav] = useState("dashboard");
  const [fileCount, setFileCount] = useState("—");

  // Live file count for the stats card
  useEffect(() => {
    axios.get(`${API}/files`)
      .then((res) => setFileCount(String(res.data.files?.length ?? "—")))
      .catch(() => {});
  }, [activeNav]); // refresh when switching tabs

  const handleNav = (id) => {
    if (id === "chat")                          { onOpenChat(); return; }
    if (id === "analytics" || id === "settings") return; // coming soon
    setActiveNav(id);
  };

  const liveStats = STATS.map((s) =>
    s.label === "Indexed Documents" ? { ...s, value: fileCount } : s
  );

  const now = new Date();
  const dateStr = now.toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" });

  const pageTitle = { dashboard: "Admin Dashboard", files: "Manage Files" }[activeNav] ?? "Admin Dashboard";

  return (
    <div className="flex min-h-screen bg-gray-50 font-sans">

      {/* ── Sidebar ── */}
      <aside className="w-64 flex-shrink-0 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 text-white flex flex-col min-h-screen shadow-2xl">
        {/* Logo */}
        <div className="px-6 py-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-500 flex items-center justify-center text-xl shadow">🧠</div>
            <div>
              <div className="text-xs text-white/50 font-medium leading-none">Enterprise</div>
              <div className="text-sm font-bold leading-tight">RAG System</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = activeNav === item.id;
            const isSoon   = item.soon;
            return (
              <button
                key={item.id}
                onClick={() => handleNav(item.id)}
                disabled={isSoon}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200
                  ${isActive
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-900/40"
                    : isSoon
                      ? "text-white/25 cursor-not-allowed"
                      : "text-white/70 hover:bg-white/10 hover:text-white"}`}
              >
                <span className="text-lg">{item.icon}</span>
                <span className="flex-1 text-left">{item.label}</span>
                {item.id === "chat" && (
                  <span className="text-xs bg-blue-500/30 text-blue-200 px-2 py-0.5 rounded-full">Open</span>
                )}
                {isSoon && (
                  <span className="text-xs text-white/30 italic">soon</span>
                )}
              </button>
            );
          })}
        </nav>

        {/* User info */}
        <div className="px-4 pb-4 border-t border-white/10 pt-4 space-y-3">
          <div className="flex items-center gap-3 px-3 py-2.5 bg-white/5 rounded-xl">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-400 to-indigo-600 flex items-center justify-center text-lg">🔐</div>
            <div className="overflow-hidden">
              <div className="text-xs text-white/40 font-medium">Administrator</div>
              <div className="text-sm font-semibold text-white truncate">{user.email}</div>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="w-full py-2.5 rounded-xl text-sm font-medium text-white/50 hover:text-white
              bg-white/5 hover:bg-red-500/20 border border-white/10 hover:border-red-400/30 transition-all duration-200"
          >
            ← Logout
          </button>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 overflow-y-auto">

        {/* Top bar */}
        <div className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-100 px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{pageTitle}</h1>
            <p className="text-xs text-gray-400 mt-0.5">{dateStr}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-xs text-emerald-600 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full font-medium">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse inline-block" />
              System Online
            </span>
            <button
              onClick={onOpenChat}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600
                text-white text-sm font-semibold rounded-xl shadow hover:shadow-md
                hover:from-blue-700 hover:to-indigo-700 transition-all duration-200"
            >
              💬 Query Assistant
            </button>
          </div>
        </div>

        {/* ── File Manager view ── */}
        {activeNav === "files" && (
          <div className="px-8 py-8">
            <FileManagerPanel />
          </div>
        )}

        {/* ── Dashboard view ── */}
        {activeNav === "dashboard" && (
          <div className="px-8 py-8 space-y-8">

            {/* Welcome banner */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl px-8 py-7 text-white shadow-lg">
              <p className="text-blue-100 text-sm font-medium mb-1">Welcome back 👋</p>
              <h2 className="text-2xl font-bold">Good {now.getHours() < 12 ? "Morning" : now.getHours() < 18 ? "Afternoon" : "Evening"}, Admin</h2>
              <p className="text-blue-200 text-sm mt-2">
                You have full access to all departments and system management.
                {" "}<button onClick={onOpenChat} className="underline hover:text-white transition-colors">Open Query Assistant →</button>
              </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 xl:grid-cols-4 gap-5">
              {liveStats.map((s) => (
                <div key={s.label}
                  className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-11 h-11 rounded-xl flex items-center justify-center text-2xl"
                      style={{ background: s.bg }}>
                      {s.icon}
                    </div>
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full"
                      style={{ background: s.bg, color: s.color }}>
                      Live
                    </span>
                  </div>
                  <div className="text-2xl font-extrabold text-gray-900 mb-0.5">{s.value}</div>
                  <div className="text-xs font-semibold text-gray-500 mb-1">{s.label}</div>
                  <div className="text-xs font-medium" style={{ color: s.color }}>{s.change}</div>
                </div>
              ))}
            </div>

            {/* Two-column section */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

              {/* Department access table */}
              <div className="xl:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="px-6 py-5 border-b border-gray-50 flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-gray-900">Department Access Control</h3>
                    <p className="text-xs text-gray-400 mt-0.5">RBAC metadata managed by the retrieval layer</p>
                  </div>
                  <span className="text-xs text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full font-medium border border-blue-100">
                    4 Active
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        <th className="px-6 py-3 text-left">Department</th>
                        <th className="px-6 py-3 text-left">Role Tag</th>
                        <th className="px-6 py-3 text-left">Queries</th>
                        <th className="px-6 py-3 text-left">Access</th>
                        <th className="px-6 py-3 text-left">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {DEPARTMENTS.map((d) => (
                        <tr key={d.role} className="hover:bg-gray-50/60 transition-colors">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2.5">
                              <span className="w-8 h-8 rounded-lg flex items-center justify-center text-base"
                                style={{ background: d.color + "18" }}>
                                {d.icon}
                              </span>
                              <div>
                                <div className="font-semibold text-gray-800">{d.name}</div>
                                <div className="text-xs text-gray-400 truncate max-w-[140px]">{d.docTypes}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <code className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-md font-mono">{d.role}</code>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-gray-100 rounded-full h-1.5 w-20">
                                <div className="h-1.5 rounded-full" style={{ width: `${(d.queryCount / 20) * 100}%`, background: d.color }} />
                              </div>
                              <span className="text-xs font-semibold text-gray-600">{d.queryCount}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-xs font-medium px-2.5 py-1 rounded-full"
                              style={{ background: d.color + "18", color: d.color }}>
                              {d.accessLevel}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600">
                              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                              Active
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Recent Activity */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="px-6 py-5 border-b border-gray-50">
                  <h3 className="font-bold text-gray-900">Recent Activity</h3>
                  <p className="text-xs text-gray-400 mt-0.5">Latest system events</p>
                </div>
                <div className="px-4 py-4 space-y-1 max-h-[400px] overflow-y-auto">
                  {ACTIVITY.map((a, i) => (
                    <div key={i} className="flex items-start gap-3 px-2 py-3 rounded-xl hover:bg-gray-50 transition-colors">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base flex-shrink-0"
                        style={{ background: a.color + "18" }}>
                        {a.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-gray-700 leading-snug">{a.text}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-gray-400">{a.time}</span>
                          <span className="text-xs font-medium px-1.5 py-0.5 rounded"
                            style={{ background: a.color + "18", color: a.color }}>
                            {a.label}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h3 className="font-bold text-gray-900 mb-1">Quick Actions</h3>
              <p className="text-xs text-gray-400 mb-5">Jump to frequently used admin tasks</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {[
                  { label: "Query Assistant", icon: "💬", desc: "Ask questions across all docs",       action: onOpenChat,                        color: "#3b82f6", bg: "#eff6ff" },
                  { label: "Manage Files",    icon: "🗂️", desc: "Upload & delete knowledge base PDFs", action: () => setActiveNav("files"),        color: "#10b981", bg: "#ecfdf5" },
                  { label: "Analytics",       icon: "📊", desc: "View usage & query stats",            action: null, soon: true,                   color: "#8b5cf6", bg: "#f5f3ff" },
                  { label: "Audit Logs",      icon: "📋", desc: "Review system access logs",           action: null, soon: true,                   color: "#f59e0b", bg: "#fffbeb" },
                ].map((qa) => (
                  <button
                    key={qa.label}
                    onClick={qa.action || undefined}
                    disabled={!qa.action}
                    className={`text-left p-4 rounded-xl border transition-all duration-200 group
                      ${qa.action ? "hover:shadow-md hover:-translate-y-0.5 cursor-pointer" : "cursor-not-allowed opacity-50"}`}
                    style={{ background: qa.bg, borderColor: qa.color + "30" }}
                  >
                    <div className="text-2xl mb-2">{qa.icon}</div>
                    <div className="text-sm font-semibold text-gray-800 mb-0.5">{qa.label}</div>
                    <div className="text-xs text-gray-500">{qa.desc}</div>
                    {qa.soon && <div className="text-xs font-medium mt-2" style={{ color: qa.color }}>Coming soon</div>}
                  </button>
                ))}
              </div>
            </div>

          </div>
        )}
      </main>
    </div>
  );
}
