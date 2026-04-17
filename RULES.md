# RULES.md — Agent Operating Rules

> **This file defines the rules every AI agent MUST follow when working on this project.**
> Read [`AGENT.md`](AGENT.md) first for project context, then read this file before doing any work.
> The owner (user) may add new rules at any time — always re-read this file at the start of each session.

---

## 🔴 Hard Rules — Never Violate

These are non-negotiable. Violating them is not acceptable under any circumstance.

### R1 — Ask Before Deleting Essential Files

> **Before deleting any essential file or directory, you MUST stop and ask the user for explicit confirmation. Do not proceed until confirmed.**

#### What Counts as "Essential"

| Classification | Files / Paths | Why |
|---|---|---|
| 🔴 **Critical** | `.env`, `AGENT.md`, `RULES.md`, `requirements.txt` | Project identity, secrets, rules |
| 🔴 **Critical** | `data/*.pdf` | Source documents — cannot be regenerated |
| 🔴 **Critical** | All `*.py` source files | Application logic |
| 🟠 **Important** | `vector_db/` | Expensive to rebuild — requires re-running `ingest.py` |
| 🟠 **Important** | `docs/` and any `.md` files | Documentation and context |
| 🟡 **Caution** | Empty stub files (`config/settings.py`, `models/*.py`, `utils/*.py`) | Intentional scaffolding — stubs are not junk |
| 🟢 **Lower risk** | `__pycache__/`, `.cache/`, `*.pyc` | Safely auto-generated; still confirm before mass-deleting |

#### Required Confirmation Format

Before deleting, the agent must ask in this exact structure:

```
⚠️ DELETE CONFIRMATION REQUIRED
File(s): <path(s)>
Reason:  <why you want to delete it>
Risk:    <what is lost if deleted>
Proceed? (yes / no)
```

- If the user says **yes** → proceed with deletion and log it in `AGENT.md` changelog.
- If the user says **no** → do not delete; suggest alternatives if applicable.
- If the user is unreachable → **do not delete**. Err on the side of caution.

---

### R2 — Ask Before Changing Folder Structure

> **Before adding, renaming, moving, or removing any directory, you MUST ask the user first.**

- This includes:
  - Creating new top-level directories
  - Renaming existing directories (e.g. `rag/` → `core/`)
  - Moving files between directories
  - Deleting empty stub directories (`api/`, `guardrails/`, `monitoring/`, etc.)
- These stubs exist intentionally as placeholders for planned features — do not remove them.
- If a structural change is necessary, propose it clearly and wait for approval.

---

### R3 — Never Commit Secrets

> **Never write, suggest committing, or hardcode API keys, passwords, or tokens in source files.**

- `GROQ_API_KEY` and any future credentials must only ever live in `.env`.
- `.env` is git-ignored — keep it that way.
- If you need to add a new environment variable, add it to `.env.example` with a placeholder value only.

---

### R4 — Never Overwrite AGENT.md or RULES.md Without Appending

> **Do not replace the contents of `AGENT.md` or `RULES.md` wholesale.**

- These are living documents. Always **append** to the Changelog (`AGENT.md`) and **append** to the rules list (`RULES.md`).
- If a section needs significant restructuring, propose the changes first.

---

## 🟡 Strong Guidelines — Follow Unless Given Explicit Permission

### G1 — Always Update AGENT.md Changelog After Changes

- After any meaningful change (new feature, bug fix, refactor, docs update), add a changelog entry to `AGENT.md`.
- Format: `- [YYYY-MM-DD] [TYPE] Description — Agent/Author`
- Types: `FEAT` | `FIX` | `REFACTOR` | `DOCS` | `DEVOPS` | `CHORE`

---

### G2 — Prefer Appending Over Replacing

- When editing source files, make targeted edits — do not rewrite entire files unless required.
- When adding new functionality to an existing module, extend it cleanly rather than replacing it.

---

### G3 — Respect the Established Module Boundaries

- Keep the separation of concerns intact:

  | Layer | Location | Responsibility |
  |---|---|---|
  | Ingestion | `rag/ingestion.py` | Load PDFs, chunk, tag metadata |
  | Embeddings | `rag/embeddings.py` | Embedding model only |
  | Vector DB | `rag/vector_store.py` | Chroma create/load only |
  | Retrieval | `rag/retriever.py` | Similarity search only |
  | LLM | `rag/llm.py` | LLM call + prompt only |
  | RBAC | `rbac/access_control.py` | Role filtering only |
  | Orchestration | `services/rag_service.py` | Glue the pipeline together |
  | Entry point | `app.py` | CLI only — no business logic |

- Do not put business logic in `app.py`. Do not put LLM calls in `retriever.py`. Etc.

---

### G4 — Do Not Hardcode Values That Should Be Config

- Model names, chunk sizes, overlap, top-k, DB paths, temperature — these belong in `config/settings.py` (once implemented), not scattered across files.
- For now, note any hardcoded values as technical debt in `AGENT.md` Known Issues.

---

### G5 — Provide a Summary for Any Major Feature

- When implementing a feature that spans multiple files, always provide:
  1. A short description of what was built
  2. Which files were created or changed
  3. How to test/verify it works
- Either add this to `AGENT.md` or mention it clearly in your response.

---

### G6 — Use `py` Not `python` on This Machine

- On the developer's Windows machine, `python` is not in the global PATH.
- Always use `py` to invoke Python outside of venv, e.g.: `py -m venv venv`
- Inside an activated venv, `python` works normally.

---

### G7 — Dependencies Must Go in `requirements.txt`

- Any new package introduced must be added to `requirements.txt`.
- Do not install packages silently without updating the requirements file.

---

## 🟢 Preferences — Best Effort

### P1 — Prefer Explicit Over Implicit

- Use explicit imports (not wildcard `from x import *`).
- Use explicit metadata keys (not magic strings scattered everywhere — centralise in `config/` when built).

### P2 — Preserve All Existing Comments and Docstrings

- Do not strip comments or docstrings when editing code, even if they seem redundant.
- If a comment is wrong or outdated, update it — don't delete it silently.

### P3 — Log, Don't Print (Once `utils/logger.py` Is Implemented)

- Currently the project uses `print()` for all output.
- Once `utils/logger.py` is built, migrate all `print()` calls to structured logging.
- Do not add new `print()` statements after that point.

### P4 — Test Before Claiming It Works

- If you write new code, verify it runs (or explain why you couldn't run it and what to expect).
- Do not say "this should work" without rational basis — flag uncertainty explicitly.

---

## Summary of Major Features (As of 2026-04-17)

> A quick reference for new agents entering the project mid-way.

| Feature | Status | Location |
|---|---|---|
| PDF ingestion pipeline | ✅ Complete | `rag/ingestion.py`, `ingest.py` |
| Text chunking (500/50) | ✅ Complete | `rag/ingestion.py` |
| HuggingFace embeddings (MiniLM-L6-v2) | ✅ Complete | `rag/embeddings.py` |
| ChromaDB vector store (local) | ✅ Complete | `rag/vector_store.py` |
| Semantic retrieval (top-5) | ✅ Complete | `rag/retriever.py` |
| Groq LLM (Llama 3.1 8B Instant) | ✅ Complete | `rag/llm.py` |
| Context-only strict prompt | ✅ Complete | `rag/llm.py` |
| RBAC metadata filter | ✅ Complete | `rbac/access_control.py` |
| Service orchestration layer | ✅ Complete | `services/rag_service.py` |
| CLI interactive entry point | ✅ Complete | `app.py` |
| Git hygiene + `.gitignore` | ✅ Complete | `.gitignore` |
| `requirements.txt` | ✅ Complete | `requirements.txt` |
| REST API | ❌ Not started | `api/` (empty) |
| Web frontend | ❌ Not started | `frontend/` (empty) |
| Guardrails | ❌ Not started | `guardrails/` (empty) |
| Monitoring / telemetry | ❌ Not started | `monitoring/` (empty) |
| Centralised config | ❌ Not started | `config/settings.py` (stub) |
| User/Role data models | ❌ Not started | `models/` (stubs) |
| Structured logging | ❌ Not started | `utils/logger.py` (stub) |
| Dynamic RBAC metadata at ingest | ⚠️ Partial | Hardcoded to `finance` in `ingestion.py` |

---

## Adding New Rules

> **Owner:** Add new rules below this line. Use the same format as above.
> Include a date and short description for traceability.

<!-- NEW RULES GO HERE -->

---

*Last updated: 2026-04-17 — R1 expanded with essential file classifications and required confirmation format*
