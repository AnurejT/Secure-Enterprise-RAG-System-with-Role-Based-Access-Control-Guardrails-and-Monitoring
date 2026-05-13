# Celery + Redis Integration Implementation Plan

This plan details the migration of heavy synchronous operations (document ingestion, embeddings, and Ragas evaluation) to a distributed task queue architecture using Celery and Redis.

## User Review Required

> [!IMPORTANT]
> - **Redis Requirement**: You will need a Redis server running (default `localhost:6379`) or use the provided Docker Compose setup.
> - **Worker Process**: In addition to the Flask server, a separate Celery worker process must be started.
> - **Database Support**: Celery tasks will need to access the SQLAlchemy database (SQLite) for metrics and user data. This requires careful Flask app context management.

## Proposed Changes

### Core Infrastructure
#### [NEW] [celery_app.py](file:///c:/Users/anure/Desktop/enterprise_rag/backend/celery_app.py)
- Initialize Celery with Redis broker and result backend.
- Configure task serialization (JSON), retries, and time limits.

#### [NEW] [celery_worker.py](file:///c:/Users/anure/Desktop/enterprise_rag/backend/celery_worker.py)
- Entry point for starting the Celery worker with the Flask app context.

#### [MODIFY] [backend/core/config.py](file:///c:/Users/anure/Desktop/enterprise_rag/backend/core/config.py)
- Add `REDIS_URL` and Celery configuration variables.

### Task Implementation
#### [NEW] [backend/tasks/ingestion_tasks.py](file:///c:/Users/anure/Desktop/enterprise_rag/backend/tasks/ingestion_tasks.py)
- Implement `ingest_document_task` which wraps the existing `ingest_document` logic.
- Add support for updating task state (progress/status).

#### [NEW] [backend/tasks/eval_tasks.py](file:///c:/Users/anure/Desktop/enterprise_rag/backend/tasks/eval_tasks.py)
- Implement `run_ragas_eval_task` to replace the current thread-based evaluation.

### Backend Refactoring
#### [MODIFY] [backend/api/v1/routes.py](file:///c:/Users/anure/Desktop/enterprise_rag/backend/api/v1/routes.py)
- **Upload Endpoint**: Dispatch `ingest_document_task` and return `task_id`.
- **Query Endpoint**: Dispatch `run_ragas_eval_task` instead of `run_eval_async`.
- **[NEW] Status Endpoint**: Add `GET /api/tasks/<task_id>` to return status and progress.

#### [DELETE] [backend/workers/evaluation_worker.py](file:///c:/Users/anure/Desktop/enterprise_rag/backend/workers/evaluation_worker.py)
#### [DELETE] [backend/workers/ingestion_worker.py](file:///c:/Users/anure/Desktop/enterprise_rag/backend/workers/ingestion_worker.py)
- Replaced by Celery tasks.

### Frontend Integration
#### [MODIFY] [frontend_react/src/AdminDashboard.js](file:///c:/Users/anure/Desktop/enterprise_rag/frontend_react/src/AdminDashboard.js)
- Update `confirmUpload` to handle `task_id`.
- Implement polling logic for task status.
- Add UI indicators for "In Queue", "Processing", and "Completed/Failed".

### DevOps & Monitoring
#### [NEW] [docker-compose.yml](file:///c:/Users/anure/Desktop/enterprise_rag/docker-compose.yml)
- Define services for Redis, Flask API, Celery Worker, and React Frontend.

#### [MODIFY] [requirements.txt](file:///c:/Users/anure/Desktop/enterprise_rag/requirements.txt)
- Add `celery` and `redis`.

## Verification Plan

### Automated/Manual Verification
1. **Infrastructure**: Verify Redis connection and Celery worker startup.
2. **Asynchronous Ingestion**:
   - Upload a large PDF.
   - Verify API returns immediately with a `task_id`.
   - Monitor Celery worker logs to see processing.
   - Poll task status API to see progress.
   - Verify document appears in the file manager after completion.
3. **Asynchronous Evaluation**:
   - Perform a query.
   - Verify response is returned without waiting for Ragas evaluation.
   - Verify Ragas scores appear in the Monitoring tab after a short delay.
4. **Docker**: Verify full stack orchestration with `docker-compose up`.
