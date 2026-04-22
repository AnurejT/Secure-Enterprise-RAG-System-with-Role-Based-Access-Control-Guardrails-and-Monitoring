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
  { name: "Finance",   icon: "💰", role: "finance",   color: "#10b981", accessLevel: "L3 Restricted", docTypes: "Invoices, Reports, Budgets", queryCount: 28, status: "Secure" },
  { name: "HR",        icon: "🧑‍💼", role: "hr",        color: "#8b5cf6", accessLevel: "L2 Internal",   docTypes: "Policies, Payroll, CVs",     queryCount: 15, status: "Active" },
  { name: "Marketing", icon: "📣", role: "marketing", color: "#f59e0b", accessLevel: "L1 Public",     docTypes: "Campaigns, Data, Ads",       queryCount: 42, status: "Active" },
  { name: "Employee",  icon: "👤", role: "employee",  color: "#6366f1", accessLevel: "L1 Public",     docTypes: "General Info, Manuals",      queryCount: 94, status: "Active" },
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
  { id: "monitoring",label: "Monitoring",      icon: "📊" },
  { id: "settings",  label: "Settings",        icon: "⚙️",  soon: true },
];

// ─── Score progress bar ─────────────────────────────────────────
function ScoreBar({ label, value, color }) {
  const pct = value != null ? Math.round(value * 100) : null;
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-bold" style={{ color }}>
          {pct != null ? `${pct}%` : "—"}
        </span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2.5">
        <div
          className="h-2.5 rounded-full transition-all duration-500"
          style={{ width: pct != null ? `${pct}%` : "0%", background: color }}
        />
      </div>
    </div>
  );
}

// ─── Monitoring Panel ─────────────────────────────────────────────
function MonitoringPanel({ token }) {
  const [metrics, setMetrics]   = useState(null);
  const [history, setHistory]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [mRes, hRes] = await Promise.all([
        axios.get(`${API}/monitoring/metrics`, { headers: { "Authorization": `Bearer ${token}` } }),
        axios.get(`${API}/monitoring/history?n=15`, { headers: { "Authorization": `Bearer ${token}` } }),
      ]);
      setMetrics(mRes.data);
      setHistory(hRes.data.history || []);
      setLastRefresh(new Date().toLocaleTimeString());
    } catch {
      // backend may not have monitoring yet
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30_000); // auto-refresh every 30s
    return () => clearInterval(interval);
  }, [fetchData]);

  const ragas  = metrics?.ragas  || {};
  const tokens = metrics?.tokens || {};

  const scoreColor = (v) => {
    if (v == null) return "#9ca3af";
    if (v >= 0.75) return "#10b981";
    if (v >= 0.5)  return "#f59e0b";
    return "#ef4444";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-1">Monitoring & Evaluation</h2>
          <p className="text-sm text-gray-500">Live Ragas metrics, token usage, and query traces</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-1.5 text-xs text-blue-600 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg border border-blue-100 font-medium transition-all"
        >
          🔄 Refresh {lastRefresh && <span className="text-gray-400">· {lastRefresh}</span>}
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 gap-3 text-gray-400">
          <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
          <span className="text-sm">Loading metrics…</span>
        </div>
      ) : (
        <>
          {/* ── Top stat chips ── */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: "Total Queries",    value: ragas.total_queries ?? 0,                        icon: "🔍", color: "#3b82f6", bg: "#eff6ff" },
              { label: "Total Tokens",     value: tokens.total_tokens?.toLocaleString() ?? "0",    icon: "⚡", color: "#8b5cf6", bg: "#f5f3ff" },
              { label: "Est. Cost (USD)",  value: `$${tokens.total_cost_usd?.toFixed(5) ?? "0.00000"}`, icon: "💰", color: "#10b981", bg: "#ecfdf5" },
              { label: "LLM Calls",        value: tokens.call_count ?? 0,                          icon: "📡", color: "#f59e0b", bg: "#fffbeb" },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-3" style={{ background: s.bg }}>{s.icon}</div>
                <div className="text-xl font-extrabold text-gray-900">{s.value}</div>
                <div className="text-xs font-semibold text-gray-500 mt-0.5">{s.label}</div>
              </div>
            ))}
          </div>

          {/* ── Ragas scores ── */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h3 className="font-bold text-gray-900 mb-1">📈 Ragas Quality Scores</h3>
              <p className="text-xs text-gray-400 mb-5">Averaged across all evaluated queries · Auto-updated after each response</p>
              {ragas.total_queries === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <div className="text-3xl mb-2">🧪</div>
                  <p className="text-sm">No queries evaluated yet.</p>
                  <p className="text-xs mt-1">Ask a question in the Query Assistant to generate metrics.</p>
                </div>
              ) : (
                <>
                  <ScoreBar label="Answer Relevancy"  value={ragas.avg_answer_relevancy}  color={scoreColor(ragas.avg_answer_relevancy)} />
                  <ScoreBar label="Faithfulness"       value={ragas.avg_faithfulness}      color={scoreColor(ragas.avg_faithfulness)} />
                  <ScoreBar label="Context Relevancy"  value={ragas.avg_context_relevancy} color={scoreColor(ragas.avg_context_relevancy)} />
                  <p className="text-xs text-gray-400 mt-4">Based on {ragas.total_queries} evaluated queries</p>
                </>
              )}
            </div>

            {/* ── Token breakdown ── */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <h3 className="font-bold text-gray-900 mb-1">💰 Token Usage & Cost</h3>
              <p className="text-xs text-gray-400 mb-5">Groq llama-3.1-8b-instant · Resets on server restart</p>
              <div className="space-y-3">
                {[
                  { label: "Prompt Tokens",     value: tokens.prompt_tokens?.toLocaleString()     ?? "0", color: "#6366f1" },
                  { label: "Completion Tokens", value: tokens.completion_tokens?.toLocaleString() ?? "0", color: "#10b981" },
                  { label: "Total Tokens",      value: tokens.total_tokens?.toLocaleString()      ?? "0", color: "#3b82f6" },
                ].map((t) => (
                  <div key={t.label} className="flex items-center justify-between px-4 py-3 rounded-xl bg-gray-50">
                    <span className="text-sm font-medium text-gray-700">{t.label}</span>
                    <span className="text-sm font-bold" style={{ color: t.color }}>{t.value}</span>
                  </div>
                ))}
                <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-green-50 border border-green-100">
                  <span className="text-sm font-semibold text-green-800">Estimated Cost</span>
                  <span className="text-sm font-bold text-green-700">${tokens.total_cost_usd?.toFixed(6) ?? "0.000000"}</span>
                </div>
              </div>
            </div>
          </div>

          {/* ── Per-role breakdown ── */}
          {ragas.by_role && Object.keys(ragas.by_role).length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-50">
                <h3 className="font-bold text-gray-900">Role-Level Breakdown</h3>
                <p className="text-xs text-gray-400 mt-0.5">Ragas averages per department</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      <th className="px-6 py-3 text-left">Role</th>
                      <th className="px-6 py-3 text-center">Queries</th>
                      <th className="px-6 py-3 text-center">Answer Relevancy</th>
                      <th className="px-6 py-3 text-center">Faithfulness</th>
                      <th className="px-6 py-3 text-center">Context Relevancy</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {Object.entries(ragas.by_role).map(([role, d]) => {
                      const fmt = (v) => v != null ? `${Math.round(v * 100)}%` : "—";
                      return (
                        <tr key={role} className="hover:bg-gray-50/60">
                          <td className="px-6 py-3"><code className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded font-mono">{role}</code></td>
                          <td className="px-6 py-3 text-center font-semibold text-gray-700">{d.count}</td>
                          <td className="px-6 py-3 text-center" style={{ color: scoreColor(d.avg_answer_relevancy) }}>{fmt(d.avg_answer_relevancy)}</td>
                          <td className="px-6 py-3 text-center" style={{ color: scoreColor(d.avg_faithfulness) }}>{fmt(d.avg_faithfulness)}</td>
                          <td className="px-6 py-3 text-center" style={{ color: scoreColor(d.avg_context_relevancy) }}>{fmt(d.avg_context_relevancy)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ── Query history ── */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="px-6 py-5 border-b border-gray-50">
              <h3 className="font-bold text-gray-900">🔎 Recent Query Traces</h3>
              <p className="text-xs text-gray-400 mt-0.5">Last 15 evaluated queries — newest first</p>
            </div>
            {history.length === 0 ? (
              <div className="text-center py-10 text-gray-400">
                <div className="text-3xl mb-2">📭</div>
                <p className="text-sm">No query traces yet.</p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-50">
                {history.map((h, i) => {
                  const fmt = (v) => v != null ? `${Math.round(v * 100)}%` : "—";
                  const c   = (v) => v != null ? scoreColor(v) : "#9ca3af";
                  return (
                    <li key={i} className="px-6 py-4 hover:bg-gray-50/60 transition-colors">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-gray-800 truncate">{h.query_preview}</p>
                          <p className="text-xs text-gray-400 mt-0.5 truncate">{h.answer_preview}</p>
                        </div>
                        <div className="flex items-center gap-3 flex-shrink-0 text-xs">
                          <code className="bg-gray-100 text-gray-500 px-2 py-0.5 rounded font-mono">{h.role}</code>
                          {h.total_tokens != null && (
                            <span className="text-gray-400">{h.total_tokens}tok</span>
                          )}
                          {h.latency_ms != null && (
                            <span className="text-gray-400">{Math.round(h.latency_ms)}ms</span>
                          )}
                        </div>
                      </div>
                      {!h.ragas_error && (
                        <div className="flex gap-4 mt-2">
                          <span style={{ color: c(h.answer_relevancy) }} className="text-xs font-medium">AR: {fmt(h.answer_relevancy)}</span>
                          <span style={{ color: c(h.faithfulness) }} className="text-xs font-medium">FF: {fmt(h.faithfulness)}</span>
                          <span style={{ color: c(h.context_relevancy) }} className="text-xs font-medium">CR: {fmt(h.context_relevancy)}</span>
                          <span className="text-xs text-gray-300">{h.timestamp?.slice(11, 19)} UTC</span>
                        </div>
                      )}
                      {h.ragas_error && (
                        <p className="text-xs text-amber-500 mt-1">⚠️ Eval pending or failed: {h.ragas_error?.slice(0, 60)}</p>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function fmtSize(kb) {
  if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`;
  return `${kb} KB`;
}

// ─── File Manager Panel ───────────────────────────────────────────
function FileManagerPanel({ token }) {
  const [files, setFiles]                 = useState([]);
  const [loading, setLoading]             = useState(true);
  const [uploading, setUploading]         = useState(false);
  const [uploadMsg, setUploadMsg]         = useState(null);
  const [deletingFile, setDeletingFile]   = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [dragOver, setDragOver]           = useState(false);
  const [selectedRole, setSelectedRole]   = useState("employee");
  const [fileToUpload, setFileToUpload]   = useState(null);
  const [searchQuery, setSearchQuery]     = useState("");
  
  // States used by sorting/filtering remnants in JSX (kept for compatibility)
  const [filterDept, setFilterDept]       = useState("all");
  const [sortKey, setSortKey]             = useState("name");
  const [sortDir, setSortDir]             = useState("asc");

  const fileInputRef = useRef(null);

  const ROLE_META = {
    finance:   { label: "Finance",    icon: "💰", color: "#10b981", bg: "#ecfdf5", border: "#a7f3d0", text: "#065f46" },
    hr:        { label: "HR",         icon: "🧑‍💼", color: "#8b5cf6", bg: "#f5f3ff", border: "#ddd6fe", text: "#4c1d95" },
    marketing: { label: "Marketing",  icon: "📣", color: "#f59e0b", bg: "#fffbeb", border: "#fde68a", text: "#78350f" },
    employee:  { label: "Employee",   icon: "👤", color: "#6366f1", bg: "#eef2ff", border: "#c7d2fe", text: "#3730a3" },
    admin:     { label: "Admin Only", icon: "🔐", color: "#3b82f6", bg: "#eff6ff", border: "#bfdbfe", text: "#1e3a8a" },
  };
  const roleOrder = ["finance", "hr", "marketing", "employee", "admin"];

  const msgColors = {
    success: "bg-green-50 text-green-700 border-green-200",
    error:   "bg-red-50 text-red-700 border-red-200",
    info:    "bg-blue-50 text-blue-700 border-blue-200",
  };

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/files`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      setFiles(res.data.files || []);
    } catch {
      setFiles([]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchFiles(); }, [fetchFiles]);

  const handleUpload = (file) => {
    if (!file) return;
    const ALLOWED = [".pdf", ".docx", ".csv", ".xlsx", ".md"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!ALLOWED.includes(ext)) {
      setUploadMsg({ type: "error", text: `Unsupported file type: ${ext}. Supported: PDF, DOCX, CSV, XLSX` });
      return;
    }

    setFileToUpload(file);
  };

  const cancelUpload = () => setFileToUpload(null);

  const confirmUpload = async () => {
    const file = fileToUpload;
    setFileToUpload(null);
    setUploading(true);
    setUploadMsg({ type: "info", text: `Uploading & indexing "${file.name}"…` });
    const formData = new FormData();
    formData.append("file", file);
    formData.append("role", selectedRole);
    try {
      await axios.post(`${API}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data", "Authorization": `Bearer ${token}` }
      });
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
      await axios.delete(`${API}/files/${encodeURIComponent(filename)}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      setUploadMsg({ type: "success", text: `🗑️ "${filename}" deleted successfully.` });
      fetchFiles();
    } catch (err) {
      setUploadMsg({ type: "error", text: `❌ Delete failed: ${err.response?.data?.error || err.message}` });
    } finally {
      setDeletingFile(null);
    }
  };

  // ── Logic for Column-Based Table ──
  const filteredFiles = files.filter(f => !searchQuery || f.name.toLowerCase().includes(searchQuery.toLowerCase()));

  const grouped = {};
  roleOrder.forEach(r => grouped[r] = []);
  filteredFiles.forEach(f => {
    const r = (f.role || "employee").toLowerCase();
    if (grouped[r]) grouped[r].push(f);
  });

  const maxRows = Math.max(...roleOrder.map(r => grouped[r].length), 1);
  const totalKb = files.reduce((s, f) => s + (f.size_kb || 0), 0);
  const totalSize = totalKb >= 1024 ? `${(totalKb / 1024).toFixed(1)} MB` : `${totalKb} KB`;
  const activeDepts = roleOrder.filter(r => grouped[r].length > 0);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      {/* Page Title & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-1">Manage Files</h2>
          <p className="text-sm text-gray-500">Organize documents into department-based vertical columns.</p>
        </div>
        {!loading && (
          <div className="flex gap-4">
            <div className="bg-white px-4 py-2 rounded-xl border border-gray-100 shadow-sm text-center">
              <div className="text-xs font-bold text-gray-400 uppercase tracking-widest">Documents</div>
              <div className="text-lg font-black text-blue-600">{files.length}</div>
            </div>
            <div className="bg-white px-4 py-2 rounded-xl border border-gray-100 shadow-sm text-center">
              <div className="text-xs font-bold text-gray-400 uppercase tracking-widest">Total Size</div>
              <div className="text-lg font-black text-gray-700">{totalSize}</div>
            </div>
          </div>
        )}
      </div>

      {/* ── Top Section: Upload & Search ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        {/* Upload Card */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-sm font-bold text-gray-700">📤 Push New Document</label>
            <select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-xs font-bold focus:ring-2 focus:ring-blue-500 outline-none bg-gray-50">
              <option value="finance">Finance</option>
              <option value="hr">HR</option>
              <option value="marketing">Marketing</option>
              <option value="employee">Employee</option>
              <option value="admin">Admin Only</option>
            </select>
          </div>

          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files[0]); }}
            onClick={() => !uploading && fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center
              cursor-pointer transition-all duration-200 select-none
              ${dragOver ? "border-blue-400 bg-blue-50 scale-[1.01]"
                : uploading ? "border-blue-300 bg-blue-50/60 cursor-not-allowed"
                : "border-gray-200 bg-gray-50 hover:border-blue-300 hover:bg-blue-50/40"}`}
          >
            <input ref={fileInputRef} type="file" accept=".pdf,.docx,.csv,.xlsx,.md" className="hidden"
              onChange={(e) => handleUpload(e.target.files[0])} disabled={uploading} />
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                <span className="text-blue-600 font-bold text-xs uppercase tracking-widest">Indexing...</span>
              </div>
            ) : (
              <>
                <div className="text-3xl mb-2">📄</div>
                <p className="text-gray-700 font-bold text-sm tracking-tight">{dragOver ? "Drop to Index" : "Click to Upload PDF"}</p>
                <p className="text-gray-400 text-[10px] mt-1 font-semibold uppercase tracking-wider">Indexed into ChromaDB with metadata</p>
              </>
            )}
          </div>
        </div>

        {/* Messaging & Search */}
        <div className="space-y-4 flex flex-col">
          {uploadMsg ? (
            <div className={`px-4 py-4 rounded-2xl text-sm font-bold border shadow-sm flex items-start gap-3 flex-1 ${msgColors[uploadMsg.type]}`}>
              <span className="text-lg">{uploadMsg.type === 'success' ? '✅' : uploadMsg.type === 'error' ? '❌' : 'ℹ️'}</span>
              <div className="flex-1">{uploadMsg.text}</div>
              <button onClick={() => setUploadMsg(null)} className="opacity-40 hover:opacity-100 italic px-2">hide</button>
            </div>
          ) : (
            <div className="bg-indigo-600 rounded-2xl p-6 text-white shadow-lg flex-1 relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-8 transform translate-x-4 -translate-y-4 rotate-12 opacity-10 group-hover:rotate-0 transition-transform duration-700">
                <svg className="w-32 h-32" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
              </div>
              <h4 className="text-lg font-black mb-1">Knowledge Guard</h4>
              <p className="text-indigo-100 text-xs font-semibold leading-relaxed max-w-[240px]">Ensuring zero-trust document retrieval through role-based metadata filtering.</p>
            </div>
          )}

          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-lg">🔍</span>
            <input
              type="text"
              placeholder="Search across all departments..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white border border-gray-100 shadow-sm rounded-2xl pl-12 pr-4 py-4 text-sm font-bold placeholder-gray-300 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
          </div>
        </div>
      </div>

      {/* ── Department-Column Matrix Table ── */}
      <div className="bg-white rounded-[2rem] border border-gray-100 shadow-2xl overflow-hidden min-h-[500px]">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-40 gap-4">
            <div className="w-14 h-14 border-4 border-blue-100 border-t-blue-600 rounded-full animate-spin" />
            <span className="text-gray-300 font-black text-[10px] uppercase tracking-[0.2em]">Synchronizing Repository</span>
          </div>
        ) : files.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 gap-6 grayscale opacity-40">
            <div className="text-8xl">📦</div>
            <div className="text-center">
              <p className="text-lg font-black text-gray-900 uppercase tracking-widest mb-1">Knowledge Void</p>
              <p className="text-sm font-bold text-gray-400">Upload documents to populate the neural index.</p>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto overflow-y-hidden">
            <table className="w-full border-collapse table-fixed min-w-[1000px]">
              <thead>
                <tr>
                  {roleOrder.map((role) => {
                    const cfg = ROLE_META[role];
                    return (
                      <th key={role} className="border-b border-gray-50 px-6 py-6 bg-gray-50/30 text-center">
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-2xl mb-1">{cfg.icon}</span>
                          <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none">Department</span>
                          <span className="text-sm font-black text-gray-900" style={{ color: cfg.color }}>{cfg.label}</span>
                          <span className="text-[10px] font-bold text-gray-400 bg-white border border-gray-100 px-2.2 py-0.5 rounded-full mt-1">
                            {grouped[role].length} Files
                          </span>
                        </div>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {Array.from({ length: maxRows }).map((_, rowIndex) => (
                  <tr key={rowIndex} className="group/row">
                    {roleOrder.map((role) => {
                      const file = grouped[role][rowIndex];
                      const isDeleting = deletingFile === file?.name;

                      if (!file) return <td key={role} className="p-2 border-l first:border-l-0 border-gray-50/50" />;

                      return (
                        <td key={role} className="p-3 align-top border-l first:border-l-0 border-gray-50/50">
                          <div className={`relative p-4 rounded-3xl border transition-all duration-300 group/card animate-in zoom-in-95
                            ${confirmDelete === file.name ? 'border-red-200 bg-red-50 ring-4 ring-red-100/50' : 'border-gray-50 bg-gray-50/50 hover:bg-white hover:shadow-xl hover:border-gray-200 hover:-translate-y-1'}`}>
                            
                            <div className="flex items-start justify-between gap-3 mb-3">
                              <div className="w-9 h-9 rounded-2xl bg-white shadow-sm flex items-center justify-center text-lg border border-gray-50">📄</div>
                              {isDeleting ? (
                                <div className="w-5 h-5 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin mt-1" />
                              ) : confirmDelete === file.name ? (
                                <div className="flex gap-2 animate-in slide-in-from-right-4">
                                  <button onClick={() => setConfirmDelete(null)} className="text-[10px] font-black text-gray-500 hover:text-black uppercase">No</button>
                                  <button onClick={() => handleDelete(file.name)} className="text-[10px] font-black text-red-600 hover:text-red-800 uppercase">Delete</button>
                                </div>
                              ) : (
                                <button
                                  onClick={() => setConfirmDelete(file.name)}
                                  className="opacity-0 group-hover/card:opacity-100 text-gray-300 hover:text-red-500 transition-all text-sm leading-none p-1"
                                >✕</button>
                              )}
                            </div>

                            <div className="min-w-0">
                              <p className="text-[12px] font-black text-gray-900 leading-[1.3] mb-2 line-clamp-2 cursor-help" title={file.name}>
                                {file.name}
                              </p>
                              
                              <div className="flex items-center justify-between border-t border-gray-100 pt-2.5 mt-2">
                                <span className="text-[9px] font-black text-gray-400 uppercase tracking-wider">{fmtSize(file.size_kb)}</span>
                                <span className="flex items-center gap-1.5 text-[9px] font-black text-emerald-600 uppercase tracking-widest">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                                  Ready
                                </span>
                              </div>
                            </div>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Footer / Refresh */}
      <div className="flex justify-between items-center px-4">
        <div className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">
          Refreshed: {new Date().toLocaleTimeString()}
        </div>
        <button
          onClick={fetchFiles}
          disabled={loading}
          className="group flex items-center gap-3 px-8 py-4 bg-white border-2 border-gray-100 shadow-xl rounded-2xl text-[10px] font-black text-gray-600 uppercase tracking-widest hover:border-blue-600 hover:text-blue-600 active:scale-95 transition-all"
        >
          <span className={`transition-transform duration-500 ${loading ? 'animate-spin' : 'group-hover:rotate-180'}`}>🔄</span>
          Force Sync
        </button>
      </div>

      {/* ── Ingest Confirmation Overlay ── */}
      {fileToUpload && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-gray-900/80 backdrop-blur-xl p-6 animate-in fade-in duration-500">
          <div className="bg-white rounded-[2.5rem] shadow-2xl p-10 w-full max-w-md border border-white/20 animate-in zoom-in-95 duration-500">
            <div className="w-20 h-20 bg-blue-50 text-blue-600 rounded-3xl flex items-center justify-center text-4xl mb-8 mx-auto shadow-inner shadow-blue-100">📤</div>
            <h3 className="text-2xl font-black text-gray-900 text-center mb-3 tracking-tight">Confirm Knowledge Ingestion</h3>
            <p className="text-base text-gray-500 text-center mb-10 font-medium leading-relaxed px-2">
              You are pushing <span className="text-gray-900 font-bold block mt-1 italic">"{fileToUpload.name}"</span> 
              to the <span className="inline-flex items-center gap-1.5 text-blue-600 font-black uppercase tracking-tighter bg-blue-50 px-3 py-1 rounded-full text-xs">{ROLE_META[selectedRole].icon} {ROLE_META[selectedRole].label}</span> department.
            </p>
            <div className="grid grid-cols-2 gap-5">
              <button onClick={cancelUpload}
                className="px-6 py-5 bg-gray-100 hover:bg-gray-200 text-gray-500 font-black text-xs uppercase tracking-[0.2em] rounded-2xl transition-all">
                Cancel
              </button>
              <button onClick={confirmUpload}
                className="px-6 py-5 bg-blue-600 hover:bg-blue-700 text-white font-black text-xs uppercase tracking-[0.2em] rounded-2xl shadow-2xl shadow-blue-200 transition-all active:scale-95">
                Ingest Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Admin Dashboard ─────────────────────────────────────────
export default function AdminDashboard({ user, onLogout, onOpenChat }) {
  const [activeNav, setActiveNav] = useState("dashboard");
  const [fileCount, setFileCount] = useState("—");

  // Live file count for the stats card
  useEffect(() => {
    axios.get(`${API}/files`, { headers: { "Authorization": `Bearer ${user.token}` } })
      .then((res) => setFileCount(String(res.data.files?.length ?? "—")))
      .catch(() => {});
  }, [activeNav, user.token]);

  const handleNav = (id) => {
    if (id === "chat")                          { onOpenChat(); return; }
    if (id === "analytics" || id === "settings") return;
    setActiveNav(id);
  };

  const liveStats = STATS.map((s) =>
    s.label === "Indexed Documents" ? { ...s, value: fileCount } : s
  );

  const now = new Date();
  const dateStr = now.toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" });

  const pageTitle = {
    dashboard:  "Admin Dashboard",
    files:      "Manage Files",
    monitoring: "Monitoring & Evaluation",
  }[activeNav] ?? "Admin Dashboard";

  return (
    <div className="flex min-h-screen bg-gray-50 font-sans">

      {/* ── Sidebar ── */}
      <aside className="w-60 flex-shrink-0 bg-white border-r border-gray-100 flex flex-col shadow-sm">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-gray-100">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center text-white text-base font-extrabold shadow-sm">E</div>
            <div>
              <div className="text-sm font-extrabold text-gray-900 leading-tight">EnterpriseRAG</div>
              <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">Admin Console</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV_ITEMS.map((item) => {
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNav(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all duration-150
                  ${isActive ? "bg-blue-600 text-white shadow-sm" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"}
                  ${item.soon ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <span className="text-base">{item.icon}</span>
                <span className="flex-1 text-left">{item.label}</span>
                {item.soon && <span className="text-[9px] font-bold bg-black/10 px-1.5 py-0.5 rounded-full">SOON</span>}
              </button>
            );
          })}
        </nav>

        {/* User card */}
        <div className="px-3 pb-4">
          <div className="bg-gray-50 rounded-2xl px-3 py-3 flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-extrabold flex-shrink-0">
              {(user.username || "A")[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold text-gray-900 truncate">{user.username || "Admin"}</div>
              <div className="text-[10px] font-semibold text-blue-600 uppercase tracking-wide">{user.role || "admin"}</div>
            </div>
            <button onClick={onLogout} title="Logout"
              className="text-gray-400 hover:text-red-500 transition-colors text-base ml-auto">⏏</button>
          </div>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 flex flex-col min-w-0">

        {/* Top bar */}
        <header className="bg-white border-b border-gray-100 px-8 py-4 flex items-center justify-between sticky top-0 z-10 shadow-sm">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{pageTitle}</h1>
            <p className="text-xs text-gray-400 mt-0.5">{dateStr}</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              System Online
            </div>
            <button onClick={onLogout}
              className="text-xs text-gray-500 hover:text-red-500 bg-gray-50 hover:bg-red-50 border border-gray-200 hover:border-red-200 px-3 py-1.5 rounded-lg font-semibold transition-all">
              Logout
            </button>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 px-8 py-6 overflow-y-auto">

          {/* ── Dashboard ── */}
          {activeNav === "dashboard" && (
            <div className="space-y-6">

              {/* Stats row */}
              <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                {liveStats.map((s) => (
                  <div key={s.label} className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                    <div className="flex justify-between items-start mb-3">
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl" style={{ background: s.bg }}>{s.icon}</div>
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">{s.change}</span>
                    </div>
                    <div className="text-2xl font-extrabold text-gray-900 mb-0.5">{s.value}</div>
                    <div className="text-xs font-semibold text-gray-500">{s.label}</div>
                  </div>
                ))}
              </div>

              {/* Departments table + Activity */}
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

                {/* Departments */}
                <div className="xl:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                  <div className="px-6 py-5 border-b border-gray-50">
                    <h3 className="font-bold text-gray-900">Department Overview</h3>
                    <p className="text-xs text-gray-400 mt-0.5">Role-based access and document isolation status</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50 text-xs font-bold text-gray-400 uppercase tracking-wider border-b border-gray-100">
                          <th className="px-6 py-3 text-left">Department</th>
                          <th className="px-6 py-3 text-left">Document Types</th>
                          <th className="px-6 py-3 text-center">Queries</th>
                          <th className="px-6 py-3 text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {DEPARTMENTS.map((dept) => (
                          <tr key={dept.name} className="hover:bg-gray-50/60 transition-colors">
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2.5">
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base"
                                  style={{ background: dept.color + "20", color: dept.color }}>{dept.icon}</div>
                                <div>
                                  <div className="font-semibold text-gray-900 text-sm">{dept.name}</div>
                                  <div className="text-[10px] font-medium text-gray-400">{dept.accessLevel}</div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <p className="text-xs text-gray-500 max-w-[220px] leading-relaxed">{dept.docTypes}</p>
                            </td>
                            <td className="px-6 py-4 text-center">
                              <span className="text-sm font-bold text-gray-800">{dept.queryCount}</span>
                            </td>
                            <td className="px-6 py-4 text-center">
                              <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
                                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />{dept.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Activity feed */}
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
                  <div className="px-5 py-5 border-b border-gray-50">
                    <h3 className="font-bold text-gray-900">Recent Activity</h3>
                    <p className="text-xs text-gray-400 mt-0.5">Live system audit trail</p>
                  </div>
                  <ul className="divide-y divide-gray-50 px-1">
                    {ACTIVITY.map((a, i) => (
                      <li key={i} className="px-4 py-3.5 hover:bg-gray-50/60 transition-colors rounded-xl">
                        <div className="flex items-start gap-3">
                          <div className="w-7 h-7 rounded-lg flex items-center justify-center text-sm flex-shrink-0"
                            style={{ background: a.color + "15", color: a.color }}>{a.icon}</div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-gray-800 leading-snug">{a.text}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded" style={{ background: a.color + "15", color: a.color }}>{a.label}</span>
                              <span className="text-[10px] text-gray-400">{a.time}</span>
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* ── Manage Files ── */}
          {activeNav === "files" && <FileManagerPanel token={user.token} />}

          {/* ── Monitoring ── */}
          {activeNav === "monitoring" && <MonitoringPanel token={user.token} />}

          {/* ── Settings / Analytics stubs ── */}
          {(activeNav === "settings" || activeNav === "analytics") && (
            <div className="flex flex-col items-center justify-center py-32 gap-4 text-gray-400">
              <div className="text-6xl opacity-20">🚧</div>
              <p className="text-lg font-bold text-gray-500">Coming Soon</p>
              <p className="text-sm">This section is under development.</p>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
