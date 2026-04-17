# AGENT.md — Secure Enterprise RAG System

> **For AI agents, collaborators, and future contributors.**
> This file is the authoritative context document for this project.
> Read this file **first** before making any changes. Update the [Changelog](#changelog) after every meaningful contribution.
> ⚠️ Also read [`RULES.md`](RULES.md) — it defines mandatory operating rules every agent must follow (ask before deleting, ask before restructuring, etc.).

---

## Project Overview

**Name:** Secure Enterprise RAG System with Role-Based Access Control, Guardrails, and Monitoring
**Stack:** Python 3.10, LangChain ecosystem, ChromaDB, Groq (Llama 3.1), HuggingFace Embeddings, Flask
**Interface:** CLI (interactive loop) — REST API and Web UI are planned but not yet built
**Purpose:** A document QA system for enterprise use that restricts what information each user role can access, based on metadata attached to document chunks at ingestion time.

---

## Quick Start

```powershell
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

# 6. Run the app
python app.py           # interactive CLI with role prompt
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
- [x] Project documentation: `AGENT.md` + `docs/PROJECT_STRUCTURE.md`

---

## Current Architecture

See [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) for the full annotated directory tree, module responsibility table, and data-flow diagram.

### Pipeline Summary

```
User (query + role) → Retrieve top-5 docs → RBAC filter → Guard → LLM (Groq) → Response
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| Metadata-based RBAC (not query-time user auth) | Simpler to implement; enforced at retrieval, not application layer |
| ChromaDB local persistence | No external DB dependency; `vector_db/` is regenerated via `ingest.py` |
| Groq + Llama 3.1 8B | Fast inference, free tier available, fits enterprise demo budget |
| `all-MiniLM-L6-v2` embeddings | Balance of speed and semantic quality for document retrieval |
| Strict "context-only" prompt | Prevents hallucination — critical for enterprise trustworthiness |

---

## Known Issues & Limitations

| Issue | Status | Notes |
|---|---|---|
| `role_allowed` is hardcoded to `["finance"]` in `ingestion.py` | ⚠️ Open | Should be passed dynamically per-document or read from a config/manifest |
| No REST API yet | ⚠️ Planned | `api/` directory is empty |
| No web frontend yet | ⚠️ Planned | `frontend/` directory is empty |
| `guardrails/` is empty | ⚠️ Planned | No input sanitisation or output safety checks yet |
| `monitoring/` is empty | ⚠️ Planned | No telemetry, audit logging, or latency tracking yet |
| `config/settings.py` is an empty stub | ⚠️ Planned | `GROQ_API_KEY` loaded inline in `llm.py` — should centralise |
| `models/role.py` and `models/user.py` are empty stubs | ⚠️ Planned | No dataclasses defined yet |
| `utils/logger.py` is empty | ⚠️ Planned | All logging uses raw `print()` — needs structured logging |
| `python` not in global PATH on dev machine | ℹ️ Info | Use `py` launcher or activate venv first |

---

## Planned Features (Roadmap)

### Near-Term
- [ ] **Dynamic RBAC metadata** — accept `role_allowed` as a parameter to `ingest_pdf()` or read from a YAML/JSON manifest file alongside each PDF
- [ ] **`config/settings.py`** — centralise all env vars, model names, chunk sizes, DB paths
- [ ] **`models/user.py` + `models/role.py`** — define `User` dataclass and `Role` enum
- [ ] **`utils/logger.py`** — replace all `print()` with structured logging (e.g., Python `logging` module)

### Medium-Term
- [ ] **REST API (`api/`)** — Flask endpoints: `/ingest`, `/query`, `/roles`
- [ ] **Authentication layer** — JWT or API-key auth tied to `User` model
- [ ] **`guardrails/`** — input sanitisation (prompt injection protection) + output toxicity filter
- [ ] **`monitoring/`** — request logging with timestamps, latency, role, query, doc count

### Long-Term
- [ ] **Web UI (`frontend/`)** — chat interface with role selector
- [ ] **Multi-tenant support** — separate vector collections per department
- [ ] **Streaming responses** — Groq streaming support via LangChain
- [ ] **Evaluation harness** — RAG faithfulness + relevance scoring (RAGAS or custom)

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
| `flask` + `flask-cors` | (Planned) REST API server |

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
- **Git-ignored:** `venv/`, `vector_db/`, `.env`, `__pycache__/`, `.cache/`, `*.log`
- **Large file fix:** venv was accidentally tracked and pushed; fixed by removing from Git history and updating `.gitignore`

---

## Changelog

> **Format:** `[YYYY-MM-DD] [Type] Description — Agent/Author`
> Types: `FEAT` | `FIX` | `REFACTOR` | `DOCS` | `DEVOPS` | `CHORE`

---

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

*Last updated: 2026-04-17 by Antigravity Agent*
