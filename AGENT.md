# AGENT.md — Secure Enterprise RAG System

> **For AI agents, collaborators, and future contributors.**
> This file is the authoritative context document for this project.
> Read this file **first** before making any changes. Update the [Changelog](#changelog) after every meaningful contribution.
> ⚠️ Also read [`RULES.md`](RULES.md) — it defines mandatory operating rules every agent must follow (ask before deleting, ask before restructuring, etc.).

---

## Project Overview

**Name:** Secure Enterprise RAG System with Role-Based Access Control, Guardrails, and Monitoring
**Stack:** Python 3.10, LangChain ecosystem, ChromaDB, Groq (Llama 3.1), HuggingFace Embeddings, Flask + Flask-CORS, React 18 (Create React App), Axios
**Interface:** REST API (`api/`) + React Web UI (`frontend_react/`) — CLI entry point (`app.py`) also retained
**Purpose:** A document QA system for enterprise use that restricts what information each user role can access, based on metadata attached to document chunks at ingestion time.

---

## Quick Start

```powershell
# ── BACKEND ──────────────────────────────────────────
# 1. Recreate venv (use `py`, not `python`, on this machine — python is not in global PATH)
py -m venv venv

# 2. Activate
.\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
# Copy .env.example → .env and fill in GROQ_API_KEY

# 5. Ingest documents
python ingest.py        # processes all PDFs in data/

# 6. Run the Flask API server
python -m api.app       # serves on http://localhost:5000

# ── FRONTEND ─────────────────────────────────────────
# In a separate terminal:
cd frontend_react
npm install
npm start               # React dev server on http://localhost:3000
```

> ⚠️ `venv/` and `vector_db/` are git-ignored. After cloning, always recreate the venv and re-run `ingest.py`.

---

## Achieved Goals ✅

### Phase 1 — Core RAG Pipeline
- [x] PDF ingestion with `PyPDFLoader` from `langchain-community`
- [x] Recursive text splitting: chunk_size=500, overlap=50
- [x] Embedding with `sentence-transformers/all-MiniLM-L6-v2` via `langchain-huggingface`
- [x] Vector storage and retrieval with **ChromaDB** (persisted to `vector_db/`)
- [x] Top-5 semantic similarity retrieval via `Chroma.as_retriever(k=5)`
- [x] LLM response generation via **Groq API** (`llama-3.1-8b-instant`, temperature=0)
- [x] Strict context-only system prompt — LLM will not hallucinate outside source docs

### Phase 2 — Role-Based Access Control (RBAC)
- [x] Chunk-level metadata tagging at ingest time (`role_allowed`, `department`, `source`)
- [x] `rbac_filter()` in `rbac/access_control.py` — filters docs by `role_allowed` list
- [x] Support for wildcard role `"all"` to allow cross-role documents
- [x] Case-insensitive role comparison
- [x] Guard clause: returns `"No information available"` when no docs pass RBAC filter
- [x] Role is entered dynamically per-session in CLI (not hardcoded)

### Phase 3 — Project Structure & DevOps
- [x] Modular package layout: `rag/`, `rbac/`, `services/`, `api/`, `models/`, `utils/`, `guardrails/`, `monitoring/`
- [x] `ingest.py` standalone batch runner for all PDFs in `data/`
- [x] `.gitignore` correctly excludes `venv/`, `vector_db/`, `.env`, `__pycache__/`, `.cache/`
- [x] `requirements.txt` generated and verified (all packages install successfully)
- [x] Git repo initialized and large files issue resolved (venv removed from tracking)
- [x] Project documentation: `AGENT.md` + `docs/PROJECT_STRUCTURE.md` + `RULES.md`

### Phase 4 — REST API (`api/`)
- [x] Flask app with CORS support (`api/app.py` — `Flask`, `flask_cors`)
- [x] Blueprint-based routing (`api/routes.py`)
- [x] `POST /api/query` — accepts `{ query, role }`, returns `{ answer, sources }`
- [x] `POST /api/upload` — accepts multipart PDF upload, saves to `data/`, ingests into vector DB
- [x] Stub files created: `api/auth.py`, `api/schemas.py` (ready for JWT auth and request validation)

### Phase 5 — Input & Output Guardrails (`guardrails/`)
- [x] `guardrails/filters.py` fully implemented:
  - **`is_malicious_query()`** — blocks queries containing sensitive patterns (password, credit card, CVV, SSN, bank account)
  - **`is_irrelevant_query()`** — blocks off-topic queries (movie, song, cricket, weather)
  - **`check_empty_context()`** — checks if retrieval returned no documents
  - **`enforce_output_constraints()`** — strips uncertain language ("i think", "maybe", "probably") from LLM output
  - **`input_guardrail()`** — combined gate: empty check + length limit (300 chars) + malicious + irrelevant
- [x] Guardrails integrated into `services/rag_service.py` as Step 1 of pipeline (before retrieval)
- [x] Service returns structured `{ answer, sources }` JSON — safe for API consumption

### Phase 6 — React Web UI (`frontend_react/`)
- [x] React 18 (Create React App) with Axios
- [x] **Sidebar** — role selector (Employee, Finance, Marketing, HR, Admin) with role-aware colors
- [x] **Chat area** — message history, user/bot/error message bubbles, auto-scroll to latest
- [x] **Typing indicator** — animated 3-dot loader while awaiting LLM response
- [x] **Source chips** — displays source document filenames returned from API below each bot response
- [x] **Upload panel** — drag-and-drop  or click-to-select PDF upload (role-gated: Employee role shows locked state)
- [x] **Role-gated upload** — only Finance, HR, Marketing, Admin roles can upload documents
- [x] **Empty state** — contextual message shown when no chat messages exist
- [x] **Responsive layout** — sidebar + main chat column layout with polished CSS (`App.css`)
- [x] Component stubs: `Chat.js`, `RoleSelector.js`, `Uploader.js` (main logic consolidated in `App.js`)

---

## Current Architecture

See [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) for the full annotated directory tree, module responsibility table, and data-flow diagram.

### Full Pipeline

```
User (Web UI) → POST /api/query { query, role }
  → input_guardrail()          [blocks malicious / irrelevant / empty queries]
  → get_relevant_docs()        [ChromaDB top-5 similarity search]
  → filter_docs_by_role()      [RBAC: filters by role_allowed metadata]
  → format context
  → get_llm_response()         [Groq Llama 3.1 8B]
  → enforce_output_constraints()
  → return { answer, sources }
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| Metadata-based RBAC (not query-time user auth) | Simpler to implement; enforced at retrieval, not application layer |
| ChromaDB local persistence | No external DB dependency; `vector_db/` is regenerated via `ingest.py` |
| Groq + Llama 3.1 8B | Fast inference, free tier available, fits enterprise demo budget |
| `all-MiniLM-L6-v2` embeddings | Balance of speed and semantic quality for document retrieval |
| Strict "context-only" prompt | Prevents hallucination — critical for enterprise trustworthiness |
| Blueprint-based Flask routing | Clean separation; ready to add auth middleware per-blueprint |
| React CRA (not Vite/Next) | Simplest setup for a demo-grade UI with no SSR requirements |
| Guardrails before retrieval | Fail fast — don't waste a ChromaDB call on a clearly bad query |

---

## Known Issues & Limitations

| Issue | Status | Notes |
|---|---|---|
| `role_allowed` is hardcoded to `["finance"]` in `ingestion.py` | ⚠️ Open | Should be passed dynamically per-document or read from a config/manifest |
| `config/settings.py` is empty | ⚠️ Open | `GROQ_API_KEY` loaded inline in `llm.py` — should centralise all env vars |
| `models/role.py` and `models/user.py` are empty stubs | ⚠️ Open | No dataclasses defined yet |
| `utils/logger.py` is empty | ⚠️ Open | All logging uses raw `print()` — needs structured logging |
| `utils/helpers.py` is empty | ⚠️ Open | Placeholder for shared utilities |
| `api/auth.py` is empty | ⚠️ Open | No JWT or API-key authentication yet |
| `api/schemas.py` is empty | ⚠️ Open | No request/response validation (e.g. Marshmallow/Pydantic) |
| `monitoring/` directory is empty | ⚠️ Open | No telemetry, audit logging, or latency tracking yet |
| Frontend `api.js` is empty | ⚠️ Open | Axios calls are made inline in `App.js`; should be extracted |
| Frontend not proxied to backend in dev | ⚠️ Info | Requires manual CORS handling; add `"proxy": "http://localhost:5000"` in `package.json` to simplify |
| `python` not in global PATH on dev machine | ℹ️ Info | Use `py` launcher or activate venv first |

---

## Planned Features (Roadmap)

### Near-Term
- [ ] **Dynamic RBAC metadata** — accept `role_allowed` as a parameter to `ingest_pdf()` or read from a YAML/JSON manifest file alongside each PDF
- [ ] **`config/settings.py`** — centralise all env vars, model names, chunk sizes, DB paths using `pydantic-settings` or plain dataclass
- [ ] **`models/user.py` + `models/role.py`** — define `User` dataclass and `Role` enum
- [ ] **`utils/logger.py`** — replace all `print()` with structured logging (Python `logging` module, JSON format)
- [ ] **`api/auth.py`** — JWT or API-key authentication; protect `/query` and `/upload` endpoints
- [ ] **`api/schemas.py`** — request/response validation with Pydantic or Marshmallow
- [ ] **Frontend `api.js`** — extract all Axios calls into a typed API client module

### Medium-Term
- [ ] **`monitoring/`** — request logging with timestamps, latency, role, query, doc count; persist to SQLite or a log file
- [ ] **Guardrails expansion** — add output toxicity scoring (e.g., Detoxify) and PII redaction
- [ ] **Multi-tenant vector collections** — separate ChromaDB collections per department
- [ ] **Streaming responses** — Groq streaming support via LangChain for real-time chat feel

### Long-Term
- [ ] **Evaluation harness** — RAG faithfulness + relevance scoring (RAGAS or custom)
- [ ] **Deployment** — Dockerise Flask API + React build; deploy to cloud (Render, Railway, or GCP)

---

## Dependencies

Full list in [`requirements.txt`](requirements.txt). Key packages:

| Package | Purpose |
|---|---|
| `langchain` + `langchain-core` | LangChain base framework |
| `langchain-community` | `PyPDFLoader` for PDF ingestion |
| `langchain-chroma` | ChromaDB integration |
| `langchain-groq` | Groq LLM integration |
| `langchain-huggingface` | HuggingFace embeddings |
| `langchain-text-splitters` | `RecursiveCharacterTextSplitter` |
| `pypdf` | PDF parsing backend |
| `chromadb` | Local vector database |
| `sentence-transformers` | Embedding model weights |
| `python-dotenv` | `.env` file loading |
| `flask` + `flask-cors` | REST API server |

**Frontend** (`frontend_react/package.json`):

| Package | Purpose |
|---|---|
| `react` + `react-dom` 18 | UI framework |
| `react-scripts` 5 | CRA build tooling |
| `axios` | HTTP client for API calls |

---

## Environment

| Variable | Description | Required |
|---|---|---|
| `GROQ_API_KEY` | Groq Cloud API key | ✅ |

Copy `.env.example` → `.env` and fill in the values. **Never commit `.env`.**

---

## Git & Repository

- **Remote:** GitHub — `AnurejT/Secure-Enterprise-RAG-System-with-Role-Based-Access-Control-Guardrails-and-Monitoring`
- **Branch:** `main`
- **Git-ignored:** `venv/`, `vector_db/`, `.env`, `__pycache__/`, `.cache/`, `*.log`, `node_modules/`
- **Large file fix:** venv was accidentally tracked and pushed; fixed by removing from Git history and updating `.gitignore`

---

## Changelog

> **Format:** `[YYYY-MM-DD] [Type] Description — Agent/Author`
> Types: `FEAT` | `FIX` | `REFACTOR` | `DOCS` | `DEVOPS` | `CHORE`

---

### 2026-04-18

- `[FEAT]` Built REST API layer (`api/app.py`, `api/routes.py`) — Flask + CORS, Blueprint routing, `POST /api/query` and `POST /api/upload` endpoints — Antigravity Agent
- `[FEAT]` Implemented `guardrails/filters.py` — input guardrail (malicious query, irrelevant query, length limit), context guardrail, and output constraint enforcement — Antigravity Agent
- `[REFACTOR]` Updated `services/rag_service.py` to integrate input guardrail as Step 1 of pipeline; returns structured `{ answer, sources }` JSON — Antigravity Agent
- `[FEAT]` Built React 18 Web UI (`frontend_react/`) — role selector sidebar, chat message area with typing indicator, source chips, role-gated drag-and-drop PDF uploader, polished CSS — Antigravity Agent
- `[DOCS]` Updated `AGENT.md` to reflect Phase 4–6 completions, revised Known Issues table, updated roadmap — Antigravity Agent

### 2026-04-17

- `[DEVOPS]` Recreated `venv/` using `py -m venv venv` after it was removed from Git tracking — Antigravity Agent
- `[DEVOPS]` Generated `requirements.txt` by scanning all project imports; all packages installed successfully — Antigravity Agent
- `[DOCS]` Created `AGENT.md` (this file) with full project context, achieved goals, known issues, and roadmap — Antigravity Agent
- `[DOCS]` Created `docs/PROJECT_STRUCTURE.md` with annotated directory tree, module table, and data-flow diagram — Antigravity Agent
- `[DOCS]` Created `RULES.md` — mandatory agent operating rules (deletion policy, folder structure policy, module boundaries, feature summary table) — Antigravity Agent
- `[DEVOPS]` Fixed Git push error caused by `venv/` being tracked (large files); updated `.gitignore` to permanently exclude `venv/`, `vector_db/`, `.env` — Antigravity Agent

### 2026-04-15

- `[FIX]` Fixed `ModuleNotFoundError` for `PyPDFLoader` — updated import to `langchain_community.document_loaders` — Antigravity Agent
- `[FIX]` Fixed `ModuleNotFoundError` for `ChatPromptTemplate` — updated import to `langchain_core.prompts` — Antigravity Agent

### Initial Build (pre-2026-04-15)

- `[FEAT]` Core RAG pipeline: PDF ingestion → chunking → embedding → ChromaDB storage
- `[FEAT]` Retriever: top-5 semantic similarity search
- `[FEAT]` LLM integration: Groq API with Llama 3.1 8B Instant
- `[FEAT]` RBAC: metadata-based document filtering by `role_allowed` field
- `[FEAT]` Service layer: `rag_service.py` orchestrating full pipeline
- `[FEAT]` CLI entry point: `app.py` with dynamic role input and error handling
- `[FEAT]` Batch ingestor: `ingest.py` for processing all PDFs in `data/`
- `[FEAT]` Modular project structure scaffolded: `rag/`, `rbac/`, `services/`, `api/`, `models/`, `utils/`, `guardrails/`, `monitoring/`

---

*Last updated: 2026-04-18 by Antigravity Agent*
