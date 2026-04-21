# utils/audit.py

import datetime


def log_access(user_role, query, docs):
    with open("audit_log.txt", "a") as f:
        f.write("\n====================\n")
        f.write(f"Time: {datetime.datetime.now()}\n")
        f.write(f"Role: {user_role}\n")
        f.write(f"Query: {query}\n")
        f.write(f"Docs Used: {len(docs)}\n")

        for d in docs:
            f.write(f"- {d.metadata.get('department')} | {d.metadata.get('source')}\n")