"""
backend/core/audit.py
Audit logging — records user access events to audit_log.txt.
Moved from utils/audit.py.
"""
import datetime


def log_access(user_role: str, query: str, docs: list) -> None:
    """Append an access record to audit_log.txt."""
    with open("audit_log.txt", "a") as f:
        f.write("\n====================\n")
        f.write(f"Time: {datetime.datetime.now()}\n")
        f.write(f"Role: {user_role}\n")
        f.write(f"Query: {query}\n")
        f.write(f"Docs Used: {len(docs)}\n")
        for d in docs:
            f.write(f"- {d.metadata.get('department')} | {d.metadata.get('source')}\n")
