import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";

const API = "http://127.0.0.1:5000/api";

const NAV_ITEMS = [
  { id: "chat",       label: "Search Interface",    icon: <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg> },
  { id: "files",      label: "Document Management", icon: <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" /></svg> },
  { id: "approvals",  label: "Access Control",      icon: <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg> },
  { id: "guardrails", label: "Security Guardrails", icon: <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>, soon: true },
  { id: "dashboard",  label: "Monitoring",          icon: <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg> },
];

function formatRelativeTime(isoString) {
  if (!isoString) return "Just now";
  const date = new Date(isoString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) return "Just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hr ago`;
  return date.toLocaleDateString();
}

// ─── Approvals Panel ───────────────────────────────────────────────
function ApprovalsPanel({ user }) {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actioning, setActioning] = useState(null);

  const fetchPending = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/admin/pending`, {
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      setPending(res.data.pending || []);
    } catch (err) {
      console.error("Failed to fetch pending files", err);
    } finally {
      setLoading(false);
    }
  }, [user.token]);

  useEffect(() => { fetchPending(); }, [fetchPending]);

  const handleApprove = async (filename) => {
    setActioning(filename);
    try {
      await axios.post(`${API}/admin/approve/${filename}`, {}, {
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      setPending(prev => prev.filter(p => p.name !== filename));
    } catch (err) {
      alert("Failed to approve file");
    } finally {
      setActioning(null);
    }
  };

  const handleReject = async (filename) => {
    if (!window.confirm(`Are you sure you want to reject and delete "${filename}"?`)) return;
    setActioning(filename);
    try {
      await axios.delete(`${API}/admin/reject/${filename}`, {
        headers: { "Authorization": `Bearer ${user.token}` }
      });
      setPending(prev => prev.filter(p => p.name !== filename));
    } catch (err) {
      alert("Failed to reject file");
    } finally {
      setActioning(null);
    }
  };

  if (loading) return <div className="p-10 text-center text-[13px] font-bold text-gray-400 tracking-wide uppercase">Loading pending requests...</div>;

  return (
    <div className="space-y-6 max-w-[1200px] mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[28px] font-bold text-[#0a0a0a] tracking-tight leading-none mb-2">Pending Approvals</h2>
          <p className="text-[13px] text-gray-500 font-medium">Review documents uploaded by department users before they are indexed.</p>
        </div>
        <div className="bg-[#e8effd] text-[#2c52a0] border border-[#d1ddf7]/50 px-3 py-1.5 rounded-full text-[11px] font-bold shadow-sm tracking-wide">
          {pending.length} Waiting
        </div>
      </div>

      {pending.length === 0 ? (
        <div className="bg-white rounded-[4px] border border-gray-200 p-16 text-center shadow-sm">
          <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center text-gray-400 mx-auto mb-4 border border-gray-200">
             <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 13l4 4L19 7" /></svg>
          </div>
          <h3 className="text-[16px] font-bold text-[#0a0a0a] mb-1">No Pending Requests</h3>
          <p className="text-[13px] text-gray-500 font-medium">All department uploads have been processed.</p>
        </div>
      ) : (
        <div className="bg-white rounded-[4px] border border-gray-200 shadow-sm overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200 bg-[#fafafa]">
                <th className="px-5 py-3 text-[10px] font-bold text-gray-500 tracking-widest uppercase">Document</th>
                <th className="px-5 py-3 text-[10px] font-bold text-gray-500 tracking-widest uppercase">Context</th>
                <th className="px-5 py-3 text-[10px] font-bold text-gray-500 tracking-widest uppercase text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {pending.map((file) => (
                <tr key={file.name} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-[#f4f5f5] rounded-[4px] flex items-center justify-center text-gray-500 border border-gray-200 shrink-0">
                         <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                      </div>
                      <div>
                        <div className="font-bold text-[#0a0a0a] text-[13px] flex items-center gap-2">
                          {file.name}
                          <span className="text-[9px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded uppercase tracking-wider">{file.size_kb} KB</span>
                        </div>
                        <div className="text-[11px] text-gray-500 mt-0.5">Uploaded {formatRelativeTime(file.uploaded_at)}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <div className="text-[12px] font-bold text-[#0a0a0a] capitalize">{file.role}</div>
                    <div className="text-[10px] text-gray-400 font-medium">By: {file.uploaded_by}</div>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button 
                        onClick={() => handleReject(file.name)}
                        disabled={!!actioning}
                        className="px-3 py-1.5 text-[11px] font-bold text-red-600 bg-red-50 hover:bg-red-100 border border-red-100 rounded-[4px] transition-colors disabled:opacity-50 tracking-wide"
                      >
                        REJECT
                      </button>
                      <button 
                        onClick={() => handleApprove(file.name)}
                        disabled={!!actioning}
                        className="px-4 py-1.5 bg-[#0a0a0a] text-white rounded-[4px] text-[11px] font-bold hover:bg-gray-800 transition-colors disabled:opacity-50 tracking-wide shadow-sm"
                      >
                        {actioning === file.name ? "PROCESSING..." : "APPROVE & INDEX"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Score progress bar ─────────────────────────────────────────
function ScoreBar({ label, value, color }) {
  const pct = value != null ? Math.round(value * 100) : null;
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11px] font-bold text-gray-500 tracking-wide uppercase">{label}</span>
        <span className="text-[13px] font-bold text-[#0a0a0a]">
          {pct != null ? `${pct}%` : "—"}
        </span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-[6px] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
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
    <div className="space-y-6 max-w-[1400px] mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[28px] font-bold text-[#0a0a0a] tracking-tight leading-none mb-2">Monitoring & Evaluation</h2>
          <p className="text-[13px] text-gray-500 font-medium">Live Ragas metrics, token usage, and query traces.</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-200 text-[#0a0a0a] text-[11px] font-bold rounded-[4px] hover:bg-gray-50 transition-colors shadow-sm tracking-wide"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          SYNC {lastRefresh && <span className="text-gray-400 font-medium ml-1">· {lastRefresh}</span>}
        </button>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-gray-400">
          <div className="w-6 h-6 border-2 border-gray-200 border-t-[#0a0a0a] rounded-full animate-spin"></div>
          <span className="text-[11px] font-bold tracking-widest uppercase">Acquiring Telemetry...</span>
        </div>
      ) : (
        <>
          {/* ── Top stat chips ── */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { label: "TOTAL QUERIES",    value: ragas.total_queries ?? 0 },
              { label: "TOTAL TOKENS",     value: tokens.total_tokens?.toLocaleString() ?? "0" },
              { label: "EST. COST (USD)",  value: `$${tokens.total_cost_usd?.toFixed(5) ?? "0.00000"}` },
              { label: "LLM CALLS",        value: tokens.call_count ?? 0 },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-[4px] border border-gray-200 shadow-sm p-5 hover:border-gray-300 transition-colors">
                <div className="text-[10px] font-bold text-gray-500 tracking-widest mb-4">{s.label}</div>
                <div className="text-[26px] font-bold text-[#0a0a0a] leading-none">{s.value}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* ── Ragas scores ── */}
            <div className="bg-white rounded-[4px] border border-gray-200 shadow-sm p-6">
              <h3 className="font-bold text-[#0a0a0a] text-[15px] tracking-tight mb-1">Ragas Quality Scores</h3>
              <p className="text-[11px] font-medium text-gray-500 mb-6">Averaged across all evaluated queries.</p>
              {ragas.total_queries === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <p className="text-[13px] font-bold text-gray-400 uppercase tracking-wide">No Telemetry</p>
                </div>
              ) : (
                <>
                  <ScoreBar label="Answer Relevancy"  value={ragas.avg_answer_relevancy}  color="#0a0a0a" />
                  <ScoreBar label="Faithfulness"       value={ragas.avg_faithfulness}      color="#0a0a0a" />
                  <ScoreBar label="Context Relevancy"  value={ragas.avg_context_relevancy} color="#0a0a0a" />
                  <p className="text-[10px] font-bold text-gray-400 mt-5 uppercase tracking-widest text-right">Based on {ragas.total_queries} evaluations</p>
                </>
              )}
            </div>

            {/* ── Token breakdown ── */}
            <div className="bg-white rounded-[4px] border border-gray-200 shadow-sm p-6">
              <h3 className="font-bold text-[#0a0a0a] text-[15px] tracking-tight mb-1">Token Efficiency Overview</h3>
              <p className="text-[11px] font-medium text-gray-500 mb-6">Current session aggregates.</p>
              <div className="space-y-2">
                {[
                  { label: "Prompt Tokens",     value: tokens.prompt_tokens?.toLocaleString()     ?? "0" },
                  { label: "Completion Tokens", value: tokens.completion_tokens?.toLocaleString() ?? "0" },
                  { label: "Total Tokens",      value: tokens.total_tokens?.toLocaleString()      ?? "0" },
                ].map((t) => (
                  <div key={t.label} className="flex items-center justify-between px-4 py-3 rounded-[4px] bg-[#fafafa] border border-gray-100">
                    <span className="text-[12px] font-bold text-gray-600">{t.label}</span>
                    <span className="text-[14px] font-bold text-[#0a0a0a]">{t.value}</span>
                  </div>
                ))}
                <div className="flex items-center justify-between px-4 py-3 rounded-[4px] bg-[#0a0a0a] text-white mt-4 shadow-sm">
                  <span className="text-[12px] font-bold tracking-wide uppercase">Estimated Cost</span>
                  <span className="text-[15px] font-bold">${tokens.total_cost_usd?.toFixed(6) ?? "0.000000"}</span>
                </div>
              </div>
            </div>
          </div>

          {/* ── Query history ── */}
          <div className="bg-white rounded-[4px] border border-gray-200 shadow-sm overflow-hidden mt-6">
            <div className="px-5 py-4 border-b border-gray-200 bg-[#fafafa]">
              <h3 className="font-bold text-[#0a0a0a] text-[15px] tracking-tight">Recent Query Traces</h3>
              <p className="text-[11px] font-medium text-gray-500 mt-0.5">Last 15 evaluated queries.</p>
            </div>
            {history.length === 0 ? (
              <div className="text-center py-10">
                <p className="text-[13px] font-bold text-gray-400 uppercase tracking-wide">No Traces</p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {history.map((h, i) => {
                  const fmt = (v) => v != null ? `${Math.round(v * 100)}%` : "—";
                  return (
                    <li key={i} className="px-5 py-4 hover:bg-gray-50/50 transition-colors">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <p className="text-[13px] font-bold text-[#0a0a0a] truncate">{h.query_preview}</p>
                          <p className="text-[12px] text-gray-500 mt-0.5 truncate font-medium">{h.answer_preview}</p>
                        </div>
                        <div className="flex items-center gap-3 flex-shrink-0 text-[11px] font-bold text-gray-500">
                          <code className="bg-gray-100 text-[#0a0a0a] px-2 py-0.5 rounded-[2px]">{h.role.toUpperCase()}</code>
                          {h.total_tokens != null && <span>{h.total_tokens}tok</span>}
                          {h.latency_ms != null && <span>{Math.round(h.latency_ms)}ms</span>}
                        </div>
                      </div>
                      {!h.ragas_error && (
                        <div className="flex gap-4 mt-3">
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded uppercase tracking-wide">AR: {fmt(h.answer_relevancy)}</span>
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded uppercase tracking-wide">FF: {fmt(h.faithfulness)}</span>
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded uppercase tracking-wide">CR: {fmt(h.context_relevancy)}</span>
                          <span className="text-[10px] text-gray-400 font-medium ml-auto">{h.timestamp?.slice(11, 19)} UTC</span>
                        </div>
                      )}
                      {h.ragas_error && (
                        <p className="text-[11px] font-bold text-amber-600 mt-2 bg-amber-50 px-2 py-1 rounded inline-block">⚠️ Eval pending or failed</p>
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
  const [dragOver, setDragOver]           = useState(false);
  const [selectedRole, setSelectedRole]   = useState("finance");
  const [fileToUpload, setFileToUpload]   = useState(null);
  const [searchQuery, setSearchQuery]     = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);

  const fileInputRef = useRef(null);

  const roleOrder = ["finance", "hr", "marketing", "engineering", "general"];

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
      setUploadMsg({ type: "error", text: `Unsupported file type: ${ext}.` });
      return;
    }
    setFileToUpload(file);
  };

  const confirmUpload = async () => {
    const file = fileToUpload;
    setFileToUpload(null);
    setUploading(true);
    setUploadProgress(0);
    setUploadMsg({ type: "info", text: `Uploading "${file.name}"…` });
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("role", selectedRole);
    
    try {
      const res = await axios.post(`${API}/upload`, formData, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      
      const taskId = res.data.task_id;
      if (!taskId) {
        setUploadMsg({ type: "success", text: `✅ Uploaded successfully.` });
        fetchFiles();
        setUploading(false);
        return;
      }

      const poll = async () => {
        try {
          const sRes = await axios.get(`${API}/tasks/${taskId}`, {
            headers: { "Authorization": `Bearer ${token}` }
          });
          const { status, progress, message } = sRes.data;
          
          if (status === "SUCCESS" || status === "COMPLETED") {
            setUploadProgress(100);
            setUploadMsg({ type: "success", text: `✅ Indexed successfully.` });
            fetchFiles();
            setUploading(false);
          } else if (status === "FAILURE" || status === "FAILED") {
            setUploadMsg({ type: "error", text: `❌ Indexing failed.` });
            setUploading(false);
          } else {
            setUploadProgress(progress || 0);
            setUploadMsg({ type: "info", text: `⚙️ ${message || "Processing..."}` });
            setTimeout(poll, 1500);
          }
        } catch {
          setTimeout(poll, 3000);
        }
      };
      poll();

    } catch (err) {
      setUploadMsg({ type: "error", text: `❌ Upload failed.` });
      setUploading(false);
    }
  };

  const handleDelete = async (filename) => {
    setDeletingFile(filename);
    try {
      await axios.delete(`${API}/files/${encodeURIComponent(filename)}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      fetchFiles();
    } catch (err) {
      alert("Delete failed");
    } finally {
      setDeletingFile(null);
    }
  };

  const filteredFiles = files.filter(f => !searchQuery || f.name.toLowerCase().includes(searchQuery.toLowerCase()));

  const grouped = {};
  roleOrder.forEach(r => grouped[r] = []);
  filteredFiles.forEach(f => {
    const r = (f.role || "general").toLowerCase();
    if (grouped[r]) grouped[r].push(f);
  });

  const totalKb = files.reduce((s, f) => s + (f.size_kb || 0), 0);
  const totalSize = totalKb >= 1024 ? `${(totalKb / 1024).toFixed(1)} MB` : `${totalKb} KB`;

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto">

      {/* Page Title & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h2 className="text-[28px] font-bold text-[#0a0a0a] tracking-tight leading-none mb-2">Document Management</h2>
          <p className="text-[13px] text-gray-500 font-medium">Departmental isolation logic and ingestion workflows.</p>
        </div>
        {!loading && (
          <div className="flex gap-4">
            <div className="bg-white px-4 py-3 rounded-[4px] border border-gray-200 shadow-sm text-center min-w-[120px]">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Documents</div>
              <div className="text-[22px] font-bold text-[#0a0a0a] leading-none">{files.length}</div>
            </div>
            <div className="bg-white px-4 py-3 rounded-[4px] border border-gray-200 shadow-sm text-center min-w-[120px]">
              <div className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Storage</div>
              <div className="text-[22px] font-bold text-[#0a0a0a] leading-none">{totalSize}</div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Upload Card */}
        <div className="bg-white rounded-[4px] border border-gray-200 shadow-sm p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-[14px] font-bold text-[#0a0a0a] uppercase tracking-wide">Target Namespace</h3>
            <select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)}
              className="border border-gray-300 rounded-[2px] px-3 py-1.5 text-[12px] font-bold text-[#0a0a0a] focus:ring-1 focus:ring-[#0a0a0a] outline-none bg-white shadow-sm uppercase tracking-wide">
              {roleOrder.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files[0]); }}
            onClick={() => !uploading && fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-[4px] p-8 flex flex-col items-center justify-center
              cursor-pointer transition-colors
              ${dragOver ? "border-[#0a0a0a] bg-gray-50"
                : uploading ? "border-gray-200 bg-gray-50 opacity-70 cursor-not-allowed"
                : "border-gray-300 bg-[#fafafa] hover:border-gray-400"}`}
          >
            <input ref={fileInputRef} type="file" accept=".pdf,.docx,.csv,.xlsx,.md" className="hidden"
              onChange={(e) => handleUpload(e.target.files[0])} disabled={uploading} />
            {uploading ? (
              <div className="flex flex-col items-center gap-3 w-full px-4">
                <div className="w-8 h-8 border-2 border-gray-200 border-t-[#0a0a0a] rounded-full animate-spin"></div>
                <div className="text-[12px] font-bold text-[#0a0a0a] uppercase tracking-widest">{uploadProgress}%</div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                <div>
                  <span className="text-[13px] font-bold text-[#0a0a0a] tracking-wide">Click to browse</span>
                  <span className="text-[13px] text-gray-500 font-medium"> or drag and drop</span>
                </div>
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">PDF, DOCX, CSV, XLSX, MD</p>
              </div>
            )}
          </div>

          {fileToUpload && !uploading && (
            <div className="flex items-center justify-between bg-[#fafafa] border border-gray-200 p-3 rounded-[4px] shadow-sm">
              <div className="text-[12px] font-bold text-[#0a0a0a] truncate max-w-[200px] tracking-wide">{fileToUpload.name}</div>
              <div className="flex gap-2">
                <button onClick={() => setFileToUpload(null)} className="px-3 py-1.5 text-[11px] font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-50 rounded-[4px] tracking-wide">CANCEL</button>
                <button onClick={confirmUpload} className="px-3 py-1.5 text-[11px] font-bold text-white bg-[#0a0a0a] hover:bg-gray-800 rounded-[4px] tracking-wide shadow-sm">CONFIRM</button>
              </div>
            </div>
          )}

          {uploadMsg && (
            <div className={`p-3 rounded-[4px] text-[11px] font-bold text-center tracking-wide ${
              uploadMsg.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
              uploadMsg.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
              'bg-[#fafafa] text-[#0a0a0a] border border-gray-200'
            }`}>
              {uploadMsg.text}
            </div>
          )}
        </div>

        {/* Global Search */}
        <div className="bg-white rounded-[4px] border border-gray-200 shadow-sm p-6 flex flex-col justify-center">
          <h3 className="text-[14px] font-bold text-[#0a0a0a] uppercase tracking-wide mb-4">Global Index Search</h3>
          <div className="relative">
            <svg className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            <input
              type="text"
              placeholder="Search documents by name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-[4px] text-[13px] font-medium text-[#0a0a0a] placeholder-gray-400 focus:outline-none focus:border-[#0a0a0a] shadow-sm transition-colors"
            />
          </div>
        </div>

      </div>

      {/* Matrix view */}
      <div className="flex gap-4 overflow-x-auto pb-4 snap-x">
        {roleOrder.map(r => (
          <div key={r} className="min-w-[280px] w-full max-w-[320px] bg-[#fafafa] rounded-[4px] border border-gray-200 shadow-sm flex flex-col snap-start shrink-0">
            <div className="px-4 py-3 border-b border-gray-200 bg-white flex justify-between items-center rounded-t-[4px]">
              <h4 className="text-[12px] font-bold text-[#0a0a0a] uppercase tracking-widest">{r}</h4>
              <span className="bg-[#f4f5f5] text-gray-600 px-2 py-0.5 rounded text-[10px] font-bold border border-gray-200">{grouped[r].length}</span>
            </div>
            <div className="p-2 space-y-2 flex-1 overflow-y-auto max-h-[500px]">
              {grouped[r].length === 0 ? (
                <div className="p-4 text-center text-[11px] font-bold text-gray-400 uppercase tracking-widest mt-4">Empty</div>
              ) : (
                grouped[r].map(f => (
                  <div key={f.name} className="group bg-white p-3 rounded-[2px] border border-gray-200 shadow-sm hover:border-[#0a0a0a] transition-colors relative">
                    <div className="flex items-start gap-2.5">
                      <svg className="w-5 h-5 text-gray-400 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                      <div className="flex-1 min-w-0 pr-6">
                        <div className="text-[12px] font-bold text-[#0a0a0a] truncate tracking-wide" title={f.name}>{f.name}</div>
                        <div className="text-[10px] text-gray-500 font-medium mt-0.5">{fmtSize(f.size_kb)}</div>
                      </div>
                    </div>
                    <button 
                      onClick={() => handleDelete(f.name)}
                      disabled={deletingFile === f.name}
                      className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-red-600"
                    >
                      {deletingFile === f.name ? (
                        <div className="w-3.5 h-3.5 border-2 border-red-200 border-t-red-600 rounded-full animate-spin"></div>
                      ) : (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                      )}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Admin Dashboard ─────────────────────────────────────────
export default function AdminDashboard({ user, onLogout, onOpenChat }) {
  const [activeNav, setActiveNav] = useState("dashboard");
  const [stats, setStats] = useState([
    { label: "Indexed Documents", value: "—", icon: "📄", change: "...", color: "#3b82f6", bg: "#eff6ff" },
    { label: "Queries Today", value: "—", icon: "🔍", change: "...", color: "#10b981", bg: "#ecfdf5" },
    { label: "Active Departments", value: "—", icon: "🏢", change: "...", color: "#8b5cf6", bg: "#f5f3ff" },
    { label: "System Status", value: "Online", icon: "⚡", change: "100% uptime", color: "#f59e0b", bg: "#fffbeb" },
  ]);
  const [departments, setDepartments] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = useCallback(async () => {
    try {
      const headers = { "Authorization": `Bearer ${user.token}` };
      
      // 1. Stats
      try {
        const statsRes = await axios.get(`${API}/admin/stats`, { headers });
        const s = statsRes.data;
        setStats([
          { label: "Indexed Documents", value: s.total_docs, icon: "📄", change: "Live count", color: "#3b82f6", bg: "#eff6ff" },
          { label: "Queries Today", value: s.total_queries, icon: "🔍", change: "Evaluated", color: "#10b981", bg: "#ecfdf5" },
          { label: "Active Departments", value: s.active_departments, icon: "🏢", change: "All online", color: "#8b5cf6", bg: "#f5f3ff" },
          { label: "System Status", value: s.system_status, icon: "⚡", change: s.uptime || "100% uptime", color: "#f59e0b", bg: "#fffbeb" },
        ]);
      } catch (err) {
        console.error("Dashboard stats fetch error:", err);
      }

      // 2. Departments
      try {
        const deptsRes = await axios.get(`${API}/admin/departments`, { headers });
        setDepartments(deptsRes.data.departments || []);
      } catch (err) {
        console.error("Dashboard departments fetch error:", err);
      }

      // 3. Activity
      try {
        const activityRes = await axios.get(`${API}/admin/activity`, { headers });
        const mappedActivity = (activityRes.data.activity || []).map(a => ({
          ...a,
          time: formatRelativeTime(a.time),
          rawTime: a.time // keep for sorting
        }));
        
        // Ensure descending order (newest first)
        mappedActivity.sort((a, b) => b.rawTime.localeCompare(a.rawTime));
        
        setActivity(mappedActivity);
      } catch (err) {
        console.error("Dashboard activity fetch error:", err);
      }

    } catch (err) {
      console.error("Dashboard data fetch error (critical):", err);
    } finally {
      setLoading(false);
    }
  }, [user.token]);

  useEffect(() => {
    if (activeNav === "dashboard") {
      fetchDashboardData();
      const interval = setInterval(fetchDashboardData, 30_000);
      return () => clearInterval(interval);
    }
  }, [activeNav, fetchDashboardData]);

  const handleNav = (id) => {
    if (id === "chat")                          { onOpenChat(); return; }
    if (id === "analytics" || id === "settings") return;
    setActiveNav(id);
  };

  const now = new Date();
  const dateStr = now.toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" });

  const pageTitle = {
    dashboard:  "Admin Dashboard",
    files:      "Manage Files",
    monitoring: "Monitoring & Evaluation",
  }[activeNav] ?? "Admin Dashboard";

  return (
    <div className="flex min-h-screen bg-[#fafafa] font-sans text-gray-900">
      {/* ── Sidebar ── */}
      <aside className="w-[240px] flex-shrink-0 bg-[#f8f9fa] border-r border-gray-200 flex flex-col shadow-[1px_0_10px_rgba(0,0,0,0.02)] z-20">
        {/* Logo */}
        <div className="px-6 py-6 border-b border-gray-200 bg-[#f8f9fa]">
          <div className="flex items-center gap-3 mb-6">
             <div className="w-8 h-8 bg-[#0a0a0a] rounded flex items-center justify-center text-white shrink-0">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
             </div>
             <div className="flex-1 min-w-0">
               <div className="font-bold text-[#0a0a0a] leading-none tracking-tight text-[16px] truncate">SENTINEL</div>
               <div className="text-[10px] text-gray-500 font-medium tracking-wide mt-1 truncate">Enterprise RAG</div>
             </div>
          </div>
          <div className="border-t border-gray-200 -mx-6 mb-5"></div>
          <button className="w-full bg-[#0a0a0a] text-white py-2.5 rounded flex items-center justify-center gap-2 text-xs font-semibold hover:bg-gray-800 transition-colors shadow-sm">
            <span className="text-sm font-normal leading-none">+</span> New Analysis
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleNav(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded text-xs font-bold transition-all duration-150
                  ${isActive ? "bg-[#e5edff] text-[#2c52a0]" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"}
                  ${item.soon ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <span className={isActive ? "text-[#2c52a0]" : "text-gray-500"}>{item.icon}</span>
                <span className="flex-1 text-left tracking-wide">{item.label}</span>
                {item.soon && <span className="text-[9px] font-bold bg-gray-200/50 px-1.5 py-0.5 rounded">SOON</span>}
              </button>
            );
          })}
        </nav>

        {/* Footer Nav */}
        <div className="px-4 pb-6 pt-4 border-t border-gray-200 space-y-1">
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded text-xs font-bold text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors">
             <svg className="w-[18px] h-[18px] text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
             <span className="tracking-wide">Settings</span>
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2 rounded text-xs font-bold text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors">
             <svg className="w-[18px] h-[18px] text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
             <span className="tracking-wide">Support</span>
          </button>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#fafafa]">
        {/* Top bar */}
        <header className="bg-[#fafafa] border-b border-gray-200 px-8 flex items-center justify-between sticky top-0 z-10 h-[72px]">
          <h1 className="text-lg font-bold text-[#0a0a0a] tracking-tight">SENTINEL RAG</h1>
          <div className="flex items-center gap-6 h-full">
            <div className="flex items-center gap-2 bg-[#e8effd] text-[#2c52a0] px-3 py-1.5 rounded-full text-[11px] font-bold tracking-wide border border-[#d1ddf7]/50 shadow-sm">
              <div className="w-1.5 h-1.5 bg-[#2c52a0] rounded-full"></div>
              Security: Active
            </div>
            <div className="text-[11px] text-gray-600 font-bold tracking-wide">Role: {user.role === 'admin' ? 'Administrator' : user.role}</div>
            <div className="border-l border-gray-200 h-6"></div>
            <div className="flex items-center gap-4">
              <button className="text-gray-500 hover:text-black transition-colors"><svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg></button>
              <button className="text-gray-500 hover:text-black transition-colors relative">
                 <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
                 <div className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border-[1.5px] border-[#fafafa]"></div>
              </button>
              <div className="w-8 h-8 rounded bg-[#0f3b3b] flex items-center justify-center text-emerald-200 font-bold text-xs shadow-sm ml-2 relative overflow-hidden group cursor-pointer" onClick={onLogout} title="Logout">
                 <div className="absolute inset-0 bg-black/20 group-hover:bg-black/0 transition-colors"></div>
                 <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-y-auto">
          {activeNav === "dashboard" && (
            <div className="p-8 max-w-[1400px] mx-auto">
              <div className="mb-8">
                <h2 className="text-[28px] font-bold text-[#0a0a0a] tracking-tight leading-none mb-2">Admin Dashboard</h2>
                <p className="text-[13px] text-gray-500 font-medium">System oversight and real-time security telemetry.</p>
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
                {/* Stat Card 1 */}
                <div className="bg-white border border-gray-200 p-5 rounded-[4px] shadow-sm flex flex-col hover:border-gray-300 transition-colors">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-[10px] font-bold text-gray-500 tracking-widest">INDEXED DOCUMENTS</span>
                    <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                  </div>
                  <div className="flex items-center gap-2.5 mb-5">
                    <span className="text-[26px] font-bold text-[#0a0a0a] leading-none">{stats[0]?.value?.toLocaleString() || "1,204,892"}</span>
                    <span className="text-[10px] font-bold text-[#2c52a0] bg-[#e8effd] px-1.5 py-0.5 rounded leading-none">+12.4%</span>
                  </div>
                  <div className="mt-auto flex items-end gap-1 h-7">
                     <div className="flex-1 bg-[#dbeafe] h-[20%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[30%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[25%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[40%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[70%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[60%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[80%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#0a0a0a] h-[100%] rounded-[1px]"></div>
                  </div>
                </div>

                {/* Stat Card 2 */}
                <div className="bg-white border border-gray-200 p-5 rounded-[4px] shadow-sm flex flex-col hover:border-gray-300 transition-colors">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-[10px] font-bold text-gray-500 tracking-widest">TOTAL QUERIES (24H)</span>
                    <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                  </div>
                  <div className="flex items-center gap-2.5 mb-5">
                    <span className="text-[26px] font-bold text-[#0a0a0a] leading-none">{stats[1]?.value?.toLocaleString() || "48,302"}</span>
                    <span className="text-[10px] font-bold text-[#2c52a0] bg-[#e8effd] px-1.5 py-0.5 rounded leading-none">+5.1%</span>
                  </div>
                  <div className="mt-auto flex items-end gap-1 h-7">
                     <div className="flex-1 bg-[#dbeafe] h-[30%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[25%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[40%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[45%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[80%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[70%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[90%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#0a0a0a] h-[100%] rounded-[1px]"></div>
                  </div>
                </div>

                {/* Stat Card 3 */}
                <div className="bg-white border border-gray-200 p-5 rounded-[4px] shadow-sm flex flex-col hover:border-gray-300 transition-colors">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-[10px] font-bold text-gray-500 tracking-widest">SYSTEM HEALTH</span>
                    <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                  </div>
                  <div className="flex items-center gap-2.5 mb-5">
                    <span className="text-[26px] font-bold text-[#0a0a0a] leading-none">99.98%</span>
                    <span className="text-[10px] font-bold text-gray-600 bg-gray-100 px-1.5 py-0.5 rounded leading-none">Stable</span>
                  </div>
                  <div className="mt-auto h-7 flex items-center">
                    <div className="w-full bg-gray-100 h-1.5 rounded-full overflow-hidden">
                       <div className="bg-[#0a0a0a] h-full" style={{ width: '99.98%' }}></div>
                    </div>
                  </div>
                </div>

                {/* Stat Card 4 */}
                <div className="bg-white border border-gray-200 p-5 rounded-[4px] shadow-sm flex flex-col hover:border-gray-300 transition-colors">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-[10px] font-bold text-gray-500 tracking-widest">TOKEN EFFICIENCY</span>
                    <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                  </div>
                  <div className="flex items-center gap-2.5 mb-5">
                    <span className="text-[26px] font-bold text-[#0a0a0a] leading-none">0.94</span>
                    <span className="text-[10px] font-bold text-red-600 bg-red-50 px-1.5 py-0.5 rounded leading-none">-0.02</span>
                  </div>
                  <div className="mt-auto flex items-end gap-1 h-7">
                     <div className="flex-1 bg-[#dbeafe] h-[90%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[95%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[100%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[85%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[90%] rounded-[1px]"></div>
                     <div className="flex-1 bg-[#dbeafe] h-[80%] rounded-[1px]"></div>
                     <div className="flex-1 bg-red-600 h-[70%] rounded-[1px]"></div>
                  </div>
                </div>
              </div>

              {/* Main Matrix and Sidebar */}
              <div className="flex flex-col lg:flex-row gap-6">
                
                {/* Departmental Oversight Table */}
                <div className="flex-1 bg-white border border-gray-200 rounded-[4px] shadow-sm overflow-hidden flex flex-col">
                  <div className="p-5 border-b border-gray-200 flex justify-between items-center bg-white">
                    <div>
                      <h3 className="font-bold text-[#0a0a0a] text-[15px] tracking-tight">Departmental Oversight</h3>
                      <p className="text-[11px] text-gray-500 mt-0.5 font-medium">Data isolation status and usage metrics.</p>
                    </div>
                    <button className="flex items-center gap-2 border border-gray-200 px-3 py-1.5 rounded-[4px] text-[11px] text-gray-600 font-bold hover:bg-gray-50 transition-colors shadow-sm">
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/></svg> Filter
                    </button>
                  </div>
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-gray-200 bg-white">
                        <th className="px-5 py-3 text-[10px] font-bold text-gray-500 tracking-widest w-[30%]">DEPARTMENT</th>
                        <th className="px-5 py-3 text-[10px] font-bold text-gray-500 tracking-widest w-[30%]">ISOLATION STATUS</th>
                        <th className="px-5 py-3 text-[10px] font-bold text-gray-500 tracking-widest w-[25%]">QUERY VOLUME (7D)</th>
                        <th className="px-5 py-3 text-[10px] font-bold text-gray-500 tracking-widest w-[15%] text-right">RISK SCORE</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      
                      {/* Finance */}
                      <tr className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-[#f4f5f5] rounded-[4px] flex items-center justify-center text-gray-500 border border-gray-200 shrink-0">
                               <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" /></svg>
                            </div>
                            <div>
                              <div className="font-bold text-[#0a0a0a] text-[13px]">Finance</div>
                              <div className="text-[10px] text-gray-500 font-medium">L3 Restricted</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                           <span className="inline-flex items-center gap-1.5 bg-[#e8effd] text-[#2c52a0] border border-[#d1ddf7]/50 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide">
                             <span className="w-1.5 h-1.5 bg-[#2c52a0] rounded-full"></span> Secure Enclave
                           </span>
                        </td>
                        <td className="px-5 py-4">
                           <div className="flex items-end gap-0.5 h-4 w-[70px]">
                             <div className="flex-1 bg-[#dbeafe] h-[30%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[40%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[35%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[60%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[50%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[80%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#0a0a0a] h-[100%] rounded-[1px]"></div>
                           </div>
                        </td>
                        <td className="px-5 py-4 text-right font-bold text-[#0a0a0a] text-[13px]">0.02</td>
                      </tr>

                      {/* Engineering */}
                      <tr className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-[#f4f5f5] rounded-[4px] flex items-center justify-center text-gray-500 border border-gray-200 shrink-0">
                               <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                            </div>
                            <div>
                              <div className="font-bold text-[#0a0a0a] text-[13px]">Engineering</div>
                              <div className="text-[10px] text-gray-500 font-medium">L2 Internal</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                           <span className="inline-flex items-center gap-1.5 bg-[#f1f5f9] text-[#334155] border border-[#e2e8f0]/80 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide">
                             <span className="w-1.5 h-1.5 bg-[#475569] rounded-full"></span> Standard Isolation
                           </span>
                        </td>
                        <td className="px-5 py-4">
                           <div className="flex items-end gap-0.5 h-4 w-[70px]">
                             <div className="flex-1 bg-[#dbeafe] h-[40%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[50%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[45%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[70%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[60%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[90%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#0a0a0a] h-[100%] rounded-[1px]"></div>
                           </div>
                        </td>
                        <td className="px-5 py-4 text-right font-bold text-[#0a0a0a] text-[13px]">0.14</td>
                      </tr>

                      {/* HR */}
                      <tr className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-[#f4f5f5] rounded-[4px] flex items-center justify-center text-gray-500 border border-gray-200 shrink-0">
                               <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                            </div>
                            <div>
                              <div className="font-bold text-[#0a0a0a] text-[13px]">Human Resources</div>
                              <div className="text-[10px] text-gray-500 font-medium">L3 Restricted</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                           <span className="inline-flex items-center gap-1.5 bg-white text-red-600 border border-red-500 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide">
                             <span className="w-1.5 h-1.5 bg-red-600 rounded-full"></span> Audit Recommended
                           </span>
                        </td>
                        <td className="px-5 py-4">
                           <div className="flex items-end gap-0.5 h-4 w-[70px]">
                             <div className="flex-1 bg-[#dbeafe] h-[20%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[20%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[30%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[25%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[40%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[35%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dc2626] h-[100%] rounded-[1px]"></div>
                           </div>
                        </td>
                        <td className="px-5 py-4 text-right font-bold text-red-600 text-[13px]">0.87</td>
                      </tr>

                      {/* Marketing */}
                      <tr className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-[#f4f5f5] rounded-[4px] flex items-center justify-center text-gray-500 border border-gray-200 shrink-0">
                               <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" /></svg>
                            </div>
                            <div>
                              <div className="font-bold text-[#0a0a0a] text-[13px]">Marketing</div>
                              <div className="text-[10px] text-gray-500 font-medium">L1 Public</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-4">
                           <span className="inline-flex items-center gap-1.5 bg-[#f4f5f5] text-gray-600 border border-gray-200 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide">
                             <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span> Open Access
                           </span>
                        </td>
                        <td className="px-5 py-4">
                           <div className="flex items-end gap-0.5 h-4 w-[70px]">
                             <div className="flex-1 bg-[#dbeafe] h-[50%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[55%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[65%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[80%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[75%] rounded-[1px]"></div>
                             <div className="flex-1 bg-[#dbeafe] h-[90%] rounded-[1px]"></div>
                             <div className="flex-1 bg-gray-500 h-[100%] rounded-[1px]"></div>
                           </div>
                        </td>
                        <td className="px-5 py-4 text-right font-bold text-[#0a0a0a] text-[13px]">0.01</td>
                      </tr>

                    </tbody>
                  </table>
                </div>

                {/* Live Security Audit Sidebar */}
                <div className="w-full lg:w-[320px] xl:w-[360px] flex-shrink-0 bg-white border border-gray-200 rounded-[4px] shadow-sm flex flex-col h-[400px] lg:h-auto">
                  <div className="flex border-b border-gray-200 bg-white">
                     <button className="flex-1 py-3.5 text-[11px] font-bold text-[#0a0a0a] border-b-2 border-[#0a0a0a] tracking-wide">Live Security Audit</button>
                     <button className="flex-1 py-3.5 text-[11px] font-bold text-gray-500 hover:text-gray-900 border-b-2 border-transparent tracking-wide transition-colors">Resource Monitor</button>
                  </div>
                  <div className="flex-1 overflow-y-auto p-5 space-y-5">
                     
                     {/* Item 1 */}
                     <div className="flex gap-3">
                        <div className="w-6 h-6 rounded-full bg-red-50 flex items-center justify-center border border-red-100 shrink-0 mt-0.5">
                           <svg className="w-3 h-3 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>
                        </div>
                        <div>
                           <div className="text-[11px] font-bold text-[#0a0a0a] tracking-wide">Guardrail Triggered: PII Exfiltration</div>
                           <div className="text-[11px] text-gray-600 mt-1 leading-relaxed">Query attempt on HR DB intercepted. Access denied for user: j.doe.</div>
                           <div className="text-[10px] text-gray-400 font-medium mt-1.5">2 mins ago</div>
                        </div>
                     </div>
                     <div className="border-b border-gray-100"></div>

                     {/* Item 2 */}
                     <div className="flex gap-3">
                        <div className="w-6 h-6 rounded-full bg-[#e8effd] flex items-center justify-center border border-[#d1ddf7]/50 shrink-0 mt-0.5">
                           <svg className="w-3 h-3 text-[#2c52a0]" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                        </div>
                        <div>
                           <div className="text-[11px] font-bold text-[#0a0a0a] tracking-wide">Policy Update Applied</div>
                           <div className="text-[11px] text-gray-600 mt-1 leading-relaxed">'Finance Q3' vector index re-embedded with stringent L3 policy.</div>
                           <div className="text-[10px] text-gray-400 font-medium mt-1.5">14 mins ago</div>
                        </div>
                     </div>
                     <div className="border-b border-gray-100"></div>

                     {/* Item 3 */}
                     <div className="flex gap-3">
                        <div className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center border border-gray-200 shrink-0 mt-0.5">
                           <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                        </div>
                        <div>
                           <div className="text-[11px] font-bold text-[#0a0a0a] tracking-wide">System Sync Completed</div>
                           <div className="text-[11px] text-gray-600 mt-1 leading-relaxed">Routine sync of user roles from Active Directory successful.</div>
                           <div className="text-[10px] text-gray-400 font-medium mt-1.5">1 hr ago</div>
                        </div>
                     </div>
                     <div className="border-b border-gray-100"></div>

                     {/* Item 4 */}
                     <div className="flex gap-3">
                        <div className="w-6 h-6 rounded-full bg-red-50 flex items-center justify-center border border-red-100 shrink-0 mt-0.5">
                           <svg className="w-3 h-3 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                        </div>
                        <div>
                           <div className="text-[11px] font-bold text-[#0a0a0a] tracking-wide">High Query Volume Detected</div>
                           <div className="text-[11px] text-gray-600 mt-1 leading-relaxed">Anomalous spike in queries from API key segment 4a2b. Rate limiting engaged.</div>
                           <div className="text-[10px] text-gray-400 font-medium mt-1.5">3 hrs ago</div>
                        </div>
                     </div>

                  </div>
                  <div className="p-4 border-t border-gray-200 bg-[#fafafa]">
                     <button className="w-full py-2.5 bg-white border border-gray-200 hover:bg-gray-50 text-[11px] font-bold text-[#0a0a0a] rounded transition-colors tracking-wide shadow-sm">View Full Logs</button>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* ── Manage Files ── */}
          {activeNav === "files" && <div className="p-8"><FileManagerPanel token={user.token} /></div>}

          {/* ── Approvals ── */}
          {activeNav === "approvals" && <div className="p-8"><ApprovalsPanel user={user} /></div>}

          {/* ── Query Assistant ── */}
          {activeNav === "chat" && <div className="p-8">
             <div className="bg-white p-8 rounded shadow-sm border border-gray-200 text-center text-gray-500">Query Assistant content</div>
          </div>}

          {/* ── Monitoring ── */}
          {activeNav === "monitoring" && <div className="p-8"><MonitoringPanel token={user.token} /></div>}

          {/* ── Other sections stub ── */}
          {(activeNav !== "dashboard" && activeNav !== "files" && activeNav !== "approvals" && activeNav !== "chat" && activeNav !== "monitoring") && (
            <div className="flex flex-col items-center justify-center py-32 gap-4 text-gray-400">
              <div className="text-6xl opacity-20">🚧</div>
              <p className="text-lg font-bold text-[#0a0a0a]">Coming Soon</p>
              <p className="text-sm">This section is under development.</p>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}