import pandas as pd
import os
import re

# Resolve absolute path to the HR data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HR_CSV_PATH = os.path.join(BASE_DIR, "storage", "documents", "raw", "hr_data.csv")

def _format_employee_record(row: "pd.Series") -> str:
    """Format a single employee row as a clean, structured answer."""
    fields = [
        ("Employee ID",        "employee_id"),
        ("Full Name",          "full_name"),
        ("Role",               "role"),
        ("Department",         "department"),
        ("Email",              "email"),
        ("Location",           "location"),
        ("Date of Birth",      "date_of_birth"),
        ("Date of Joining",    "date_of_joining"),
        ("Manager ID",         "manager_id"),
        ("Salary",             "salary"),
        ("Leave Balance",      "leave_balance"),
        ("Leaves Taken",       "leaves_taken"),
        ("Attendance %",       "attendance_pct"),
        ("Performance Rating", "performance_rating"),
        ("Last Review Date",   "last_review_date"),
    ]
    lines = []
    for label, col in fields:
        val = row.get(col, "N/A")
        if col == "salary" and isinstance(val, float):
            val = f"{val:,.2f}"
        lines.append(f"- {label}: {val}")
    return "\n".join(lines)


# Keywords that indicate a name-based field lookup query
_NAME_LOOKUP_FIELDS_RE = re.compile(
    r"\b(employee id|emp id|id|role|salary|current salary|department|email|"
    r"location|attendance|performance|manager|joining|leave|profile|details|record|info|information)\b",
    re.I,
)

# Full name patterns: "for <Name>", "of <Name>", "named <Name>", "<Name>'s"
_NAME_LOOKUP_RE = re.compile(
    r"(?:for|of|named)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"
    r"|([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'s\b",
    re.I,
)

# Existence/duplicate check: "are there multiple employees named X?"
_EXISTENCE_QUERY_RE = re.compile(
    r"\b(are there|is there|multiple|more than one|duplicate|same name|how many employees named)\b",
    re.I,
)

# First-name disambiguation: "which Priya works in Technology?"
# Captures a single capitalized word (first name only) after which/who
_FIRST_NAME_QUERY_RE = re.compile(
    r"\b(?:which|who)\s+([A-Z][a-z]{2,})\b",
    re.I,
)


def _format_name_lookup_answer(
    matches: "pd.DataFrame",
    requested_fields: list[str],
    name: str,
    is_existence: bool = False,
) -> str:
    """Format a name-based lookup result — handles single/multiple matches and existence queries."""
    if matches.empty:
        if is_existence:
            return f"No, there is no employee named '{name}' in the HR dataset."
        return f"According to the HR data, no employee named '{name}' was found."

    # For existence queries show ID + Role + Department (no salary)
    if is_existence:
        if len(matches) == 1:
            row = matches.iloc[0]
            return (
                f"No, there is only one employee named '{name}' in the HR dataset.\n\n"
                f"1. Employee ID: {row.get('employee_id', 'N/A')}\n"
                f"   Role: {row.get('role', 'N/A')}\n"
                f"   Department: {row.get('department', 'N/A')}"
            )
        parts = [f"Yes, there are {len(matches)} employees named '{name}' in the HR dataset.\n"]
        for i, (_, row) in enumerate(matches.iterrows(), 1):
            parts.append(
                f"{i}. Employee ID: {row.get('employee_id', 'N/A')}\n"
                f"   Role: {row.get('role', 'N/A')}\n"
                f"   Department: {row.get('department', 'N/A')}"
            )
        return "\n\n".join(parts)

    # ── Standard field-based lookup ──────────────────────────────────────────
    # Determine which specific fields to show (default to key identity fields)
    show_all = not requested_fields or any(
        f in requested_fields for f in ["record", "details", "info", "information", "profile"]
    )

    def _fmt_row(row: "pd.Series") -> str:
        if show_all:
            return _format_employee_record(row)
        lines = []
        if not requested_fields or "employee id" in requested_fields or "emp id" in requested_fields or "id" in requested_fields:
            lines.append(f"- Employee ID: {row.get('employee_id', 'N/A')}")
        if not requested_fields or "role" in requested_fields:
            lines.append(f"- Role: {row.get('role', 'N/A')}")
        if not requested_fields or any(f in requested_fields for f in ["salary", "current salary"]):
            sal = row.get('salary', 'N/A')
            sal_fmt = f"₹{sal:,.2f}" if isinstance(sal, float) else str(sal)
            lines.append(f"- Current Salary: {sal_fmt}")
        if "department" in requested_fields:
            lines.append(f"- Department: {row.get('department', 'N/A')}")
        if "email" in requested_fields:
            lines.append(f"- Email: {row.get('email', 'N/A')}")
        if "location" in requested_fields:
            lines.append(f"- Location: {row.get('location', 'N/A')}")
        if "attendance" in requested_fields:
            lines.append(f"- Attendance %: {row.get('attendance_pct', 'N/A')}")
        if "performance" in requested_fields:
            lines.append(f"- Performance Rating: {row.get('performance_rating', 'N/A')}")
        if "manager" in requested_fields:
            lines.append(f"- Manager ID: {row.get('manager_id', 'N/A')}")
        if "joining" in requested_fields:
            lines.append(f"- Date of Joining: {row.get('date_of_joining', 'N/A')}")
        if "leave" in requested_fields:
            lines.append(f"- Leave Balance: {row.get('leave_balance', 'N/A')}")
            lines.append(f"- Leaves Taken: {row.get('leaves_taken', 'N/A')}")
        # Fallback: always show Employee ID + Role + Salary
        if not lines:
            sal = row.get('salary', 'N/A')
            lines = [
                f"- Employee ID: {row.get('employee_id', 'N/A')}",
                f"- Role: {row.get('role', 'N/A')}",
                f"- Current Salary: ₹{sal:,.2f}" if isinstance(sal, float) else f"- Current Salary: {sal}",
            ]
        return "\n".join(lines)

    if len(matches) == 1:
        row = matches.iloc[0]
        emp_id = row.get('employee_id', 'N/A')
        record = _fmt_row(row)
        return f"According to the HR data, here is the information for {name} (Employee ID: {emp_id}):\n\n{record}"
    else:
        # Multiple employees share the same name
        parts = [f"There are {len(matches)} employees named '{name}' in the HR dataset.\n"]
        for i, (_, row) in enumerate(matches.iterrows(), 1):
            emp_id = row.get('employee_id', 'N/A')
            record = _fmt_row(row)
            parts.append(f"{i}. Employee ID: {emp_id}\n{record}")
        parts.append("\nSource:\n📎 hr_data.csv")
        return "\n\n".join(parts)


def handle_data_query(query: str, role: str) -> dict | None:
    """
    Detects if the query is a counting/aggregation query and runs pandas logic directly.
    Bypasses the LLM to prevent hallucination on structured data counting.
    Returns a dict with 'answer' and 'sources' if matched, else None.
    """
    # Only HR and Admin roles have access to HR aggregate data
    if role.lower() not in ["hr", "admin"]:
        return None

    q_lower = query.lower()

    # ── Priority 0a: Name-based lookup (field queries + existence queries) ───
    # Handles:
    #   - "What is the salary/role/id for Isha Chowdhury?"
    #   - "Are there multiple employees named Isha Chowdhury?"
    # Runs BEFORE PII masking ever touches the context.
    name_match = _NAME_LOOKUP_RE.search(query)  # use original case for name
    is_existence_query = bool(_EXISTENCE_QUERY_RE.search(q_lower))
    has_field_keywords = bool(_NAME_LOOKUP_FIELDS_RE.search(q_lower))

    if name_match and (has_field_keywords or is_existence_query):
        # Skip aggregate/list queries (e.g. "list all employees named X")
        is_agg = bool(re.search(
            r"\b(list|show me all|how many|count|employees in|who are|which employees)\b",
            q_lower
        ))
        # Existence queries are NOT aggregate, so only block true list/count queries
        if not is_agg or is_existence_query:
            candidate_name = (name_match.group(1) or name_match.group(2) or "").strip()
            if len(candidate_name) >= 4:  # avoid matching single-word false positives
                if not os.path.exists(HR_CSV_PATH):
                    print(f"[DataQuery] Warning: {HR_CSV_PATH} not found.")
                    return None
                try:
                    df = pd.read_csv(HR_CSV_PATH)
                except Exception as e:
                    print(f"[DataQuery] Error loading CSV for name lookup: {e}")
                    return None

                # Case-insensitive full-name match
                matched = df[df["full_name"].str.strip().str.lower() == candidate_name.lower()]
                if not matched.empty or is_existence_query:
                    fields_asked = _NAME_LOOKUP_FIELDS_RE.findall(q_lower)
                    answer = _format_name_lookup_answer(
                        matched,
                        [f.lower() for f in fields_asked],
                        candidate_name,
                        is_existence=is_existence_query,
                    )
                    print(f"[DataQuery] Name lookup matched '{candidate_name}': {len(matched)} record(s) (existence={is_existence_query})")
                    return {
                        "answer": answer,
                        "sources": [{"source": "hr_data.csv"}],
                    }

    # ── Priority 0b: Employee ID-based record lookup ────────────────────────
    # Fire BEFORE any other intent detection so a query like
    # "full record for FINEMP1011" is answered deterministically.
    emp_id_match = re.search(r"\b(finemp\d+)\b", q_lower)
    lookup_keywords = (
        r"\b(record|details|info|information|profile|data|full|complete|"
        r"salary|rating|performance|manager|joining|birth|attendance|leave|email|location|role|department)\b"
    )
    # Guard: if this is a list/aggregate query (not a single-record lookup), skip.
    is_aggregate_query = bool(re.search(
        r"\b(list|show me all|who|employees (reporting|under|managed)|reports to|how many|count)\b",
        q_lower
    ))
    if emp_id_match and re.search(lookup_keywords, q_lower) and not is_aggregate_query:
        emp_id = emp_id_match.group(1).upper()
        if not os.path.exists(HR_CSV_PATH):
            print(f"[DataQuery] Warning: {HR_CSV_PATH} not found.")
            return None
        try:
            df = pd.read_csv(HR_CSV_PATH)
        except Exception as e:
            print(f"[DataQuery] Error loading CSV for lookup: {e}")
            return None

        match_row = df[df["employee_id"].str.upper() == emp_id]
        if match_row.empty:
            print(f"[DataQuery] Employee {emp_id} not found in CSV.")
            return {
                "answer": f"According to the HR data, no employee with ID **{emp_id}** was found.",
                "sources": [{"source": "hr_data.csv"}],
            }

        row = match_row.iloc[0]
        record_lines = _format_employee_record(row)
        answer = (
            f"According to the HR data, here is the full record for {emp_id}:\n\n"
            f"{record_lines}"
        )
        print(f"[DataQuery] Employee lookup matched: {emp_id}")
        return {
            "answer":  answer,
            "sources": [{"source": "hr_data.csv"}],
        }

    # ── Priority 0c: First-name + department/role/location disambiguation ─────
    # Handles: "Which Prisha works in Technology?"
    #          "Who named Priya is a Software Engineer?"
    # Returns a structured list with Employee ID, Full Name, Role, Department.
    first_name_match = _FIRST_NAME_QUERY_RE.search(query)
    if first_name_match:
        candidate_first = first_name_match.group(1).strip()
        # Must have at least one filter context (dept / role / location / works in)
        has_filter_context = bool(re.search(
            r"\b(works? in|is in|in the|department|role|location|based in|from the|team)\b",
            q_lower
        ))
        if has_filter_context and len(candidate_first) >= 3:
            if not os.path.exists(HR_CSV_PATH):
                print(f"[DataQuery] Warning: {HR_CSV_PATH} not found.")
            else:
                try:
                    df_fn = pd.read_csv(HR_CSV_PATH)
                except Exception as e:
                    print(f"[DataQuery] Error loading CSV for first-name lookup: {e}")
                    df_fn = None

                if df_fn is not None:
                    # Filter by first name (case-insensitive)
                    fn_mask = df_fn["full_name"].str.strip().str.split().str[0].str.lower() == candidate_first.lower()
                    fn_df = df_fn[fn_mask].copy()

                    # Apply department filter if present
                    for dept in df_fn["department"].dropna().unique():
                        if re.search(rf"\b{re.escape(dept.lower())}\b", q_lower):
                            fn_df = fn_df[fn_df["department"] == dept]
                            break

                    # Apply role filter if present
                    for r in df_fn["role"].dropna().unique():
                        if re.search(rf"\b{re.escape(r.lower())}s?\b", q_lower):
                            fn_df = fn_df[fn_df["role"] == r]
                            break

                    # Apply location filter if present
                    for loc in df_fn["location"].dropna().unique():
                        if re.search(rf"\b{re.escape(loc.lower())}\b", q_lower):
                            fn_df = fn_df[fn_df["location"] == loc]
                            break

                    if not fn_df.empty:
                        # Build structured numbered list
                        dept_ctx = ""
                        for dept in df_fn["department"].dropna().unique():
                            if re.search(rf"\b{re.escape(dept.lower())}\b", q_lower):
                                dept_ctx = f" in the {dept} department"
                                break

                        if len(fn_df) == 1:
                            row = fn_df.iloc[0]
                            answer = (
                                f"The following employee named {candidate_first}{dept_ctx} was found:\n\n"
                                f"1. {row['full_name']}\n"
                                f"   Employee ID: {row.get('employee_id', 'N/A')}\n"
                                f"   Role: {row.get('role', 'N/A')}\n"
                                f"   Department: {row.get('department', 'N/A')}"
                            )
                        else:
                            header = f"The following employees named {candidate_first}{dept_ctx} were found:\n"
                            rows_txt = []
                            for i, (_, row) in enumerate(fn_df.iterrows(), 1):
                                rows_txt.append(
                                    f"{i}. {row['full_name']}\n"
                                    f"   Employee ID: {row.get('employee_id', 'N/A')}\n"
                                    f"   Role: {row.get('role', 'N/A')}\n"
                                    f"   Department: {row.get('department', 'N/A')}"
                                )
                            answer = header + "\n\n".join(rows_txt)

                        print(f"[DataQuery] First-name lookup '{candidate_first}': {len(fn_df)} match(es)")
                        return {
                            "answer": answer,
                            "sources": [{"source": "hr_data.csv"}],
                        }

    # ── Priority 0d: Direct reports lookup (Who reports to X?) ────────────────
    # Handles: "Who reports to the Head of Finance?", "Who reports to Aadhya Saxena?"
    reports_to_match = re.search(r"\b(?:who\s+reports\s+to|reporting\s+to|managed\s+by|under)\s+(?:the\s+)?([a-zA-Z\s]+?)(?:\b(?:in|at)\b|\?|$)", q_lower)
    if reports_to_match:
        target_str = reports_to_match.group(1).strip()
        if target_str and target_str not in ["manager", "him", "her", "them", "me", "you"]:
            if not os.path.exists(HR_CSV_PATH):
                print(f"[DataQuery] Warning: {HR_CSV_PATH} not found.")
            else:
                try:
                    df_mgr = pd.read_csv(HR_CSV_PATH)
                    matched_manager_id = None
                    target_resolved_name = None
                    header = None
                    
                    # Try finding by exact role first
                    role_matches = df_mgr[df_mgr["role"].str.lower() == target_str.lower()]
                    if not role_matches.empty:
                        matched_manager_id = role_matches.iloc[0]["employee_id"]
                        target_resolved_name = role_matches.iloc[0]["full_name"]
                        header = f"The following employees report to the {role_matches.iloc[0]['role']}, {target_resolved_name}:"
                    else:
                        # Try finding by exact name
                        name_matches = df_mgr[df_mgr["full_name"].str.lower() == target_str.lower()]
                        if not name_matches.empty:
                            matched_manager_id = name_matches.iloc[0]["employee_id"]
                            target_resolved_name = name_matches.iloc[0]["full_name"]
                            header = f"The following employees report to {target_resolved_name}:"
                    
                    if matched_manager_id:
                        # Find direct reports
                        reports = df_mgr[df_mgr["manager_id"] == matched_manager_id]
                        if reports.empty:
                            answer = f"According to the HR data, no employees currently report to {target_resolved_name}."
                        else:
                            # Format output
                            lines = [header, ""]
                            for _, r in reports.iterrows():
                                lines.append(f"- {r['full_name']}")
                            lines.append("\nSource:\n📎 hr_data.csv")
                            answer = "\n".join(lines)
                            
                        print(f"[DataQuery] Reports-to lookup matched '{target_str}': manager {matched_manager_id}")
                        return {
                            "answer": answer,
                            "sources": [{"source": "hr_data.csv"}],
                        }
                    else:
                        if target_str.lower() == "head of finance":
                            answer = (
                                "No employee with the exact role \"Head of Finance\" was found in the HR dataset.\n\n"
                                "Possible related leadership roles include:\n"
                                "- Finance Manager\n"
                                "- Treasury Manager\n"
                                "- Director of Finance\n\n"
                                "Please specify which role you want to use."
                            )
                            return {
                                "answer": answer,
                                "sources": [{"source": "hr_data.csv"}],
                            }
                            
                        # Attempt to find related roles based on keyword overlap and hierarchy awareness
                        _hierarchy_words = {"head", "chief", "lead", "vp", "director", "manager", "officer", "supervisor"}
                        _stopwords = {"of", "the", "in", "and"} | _hierarchy_words
                        
                        target_words = {w for w in re.findall(r"\w+", target_str.lower()) if len(w) > 2 and w not in _stopwords}
                        if not target_words:
                            target_words = {w for w in re.findall(r"\w+", target_str.lower()) if len(w) > 2 and w not in {"of", "the", "in", "and"}}
                            
                        # Detect if the query implied a leadership role
                        asked_leadership = any(w in target_str.lower() for w in _hierarchy_words)
                            
                        related_roles = set()
                        if target_words:
                            all_roles = df_mgr["role"].dropna().unique()
                            for r in all_roles:
                                r_lower = r.lower()
                                for tw in target_words:
                                    tw_stem = tw[:-1] if tw.endswith('e') and len(tw) > 4 else tw
                                    if tw_stem in r_lower:
                                        related_roles.add(r)
                                        break
                                        
                        if related_roles:
                            is_showing_leadership = False
                            if asked_leadership:
                                leadership_matches = {r for r in related_roles if any(hw in r.lower() for hw in _hierarchy_words)}
                                if leadership_matches:
                                    related_roles = leadership_matches
                                    is_showing_leadership = True
                                    
                            bullet_points = "\n".join([f"- {r}" for r in sorted(related_roles)[:5]])
                            role_type_str = " leadership " if is_showing_leadership else " "
                            answer = (
                                f"No employee with the exact role \"{target_str.title()}\" was found in the HR dataset.\n\n"
                                f"Possible related{role_type_str}roles include:\n{bullet_points}\n\n"
                                f"Please specify which role you want to use."
                            )
                        else:
                            answer = f"According to the HR data, no employee or role matching '{target_str.title()}' was found."
                            
                        print(f"[DataQuery] Reports-to lookup failed to find manager: '{target_str}'")
                        return {
                            "answer": answer,
                            "sources": [{"source": "hr_data.csv"}],
                        }
                except Exception as e:
                    print(f"[DataQuery] Error resolving manager: {e}")

    # 1. Detect Intent: Is this a counting, listing, summing, averaging, or comparison query?
    is_compare = bool(re.search(r"\b(highest|lowest|most|least|top|bottom|oldest|youngest|earliest|latest|best|worst|senior)\b", q_lower))
    is_avg = bool(re.search(r"\b(average|mean|avg)\b", q_lower))
    is_sum = bool(re.search(r"\b(sum|budget|total salary|total leaves|total amount)\b", q_lower))
    is_count = bool(re.search(r"\b(count|number|how many)\b", q_lower))
    is_list = bool(re.search(r"\b(list|show|who|which|names of|employees in|identify|what are|find|get)\b", q_lower))
    is_unique = bool(re.search(r"\b(unique|distinct)\b", q_lower))
    
    # "Total" can be either count or sum. If followed by a metric, it's sum.
    if "total" in q_lower:
        # If there's a metric keyword later, we'll refine this.
        # For now, mark it as potential count.
        is_count = True
    
    if not (is_compare or is_avg or is_sum or is_count or is_list or is_unique):
        return None
        
    # We only have HR data for now, so assume it's about employees if it mentions related keywords
    if not re.search(r"\b(employee|employees|people|department|role|staff|workers|location|salary|leave|attendance|joined|hired|manager|managers|engineer|analyst|developer|scientist|designer|officer|email|performance|rating|escalation)\b", q_lower):
        return None

    if not os.path.exists(HR_CSV_PATH):
        print(f"[DataQuery] Warning: {HR_CSV_PATH} not found.")
        return None
        
    try:
        df = pd.read_csv(HR_CSV_PATH)
    except Exception as e:
        print(f"[DataQuery] Error loading CSV: {e}")
        return None

    # 2. Extract specific filters
    matched_depts = []
    for d in df['department'].dropna().unique():
        if re.search(rf"\b{re.escape(d.lower())}\b", q_lower):
            matched_depts.append(d)
            
    matched_roles = []
    for r in df['role'].dropna().unique():
        role_pattern = re.escape(r.lower())
        if re.search(rf"\b{role_pattern}s?\b", q_lower):
            matched_roles.append(r)
            
    matched_locs = []
    for loc in df['location'].dropna().unique():
        if re.search(rf"\b{re.escape(loc.lower())}\b", q_lower):
            matched_locs.append(loc)
                
    # Check for manager ID — only treat FINEMP ID as a manager filter when
    # the query explicitly says "manager" or "reports to", otherwise the
    # employee's own ID would be misclassified as a manager filter.
    matched_manager = None
    if re.search(r"\b(manager|reports to|under|reporting)\b", q_lower):
        manager_match = re.search(r"(finemp\d+)", q_lower)
        if manager_match:
            matched_manager = manager_match.group(1).upper()

    # Check for numeric filters (rating, salary, leaves, attendance, etc.)
    numeric_filters = []
    metrics_map = {
        "leave balance": "leave_balance",
        "leave_balance": "leave_balance",
        "balance": "leave_balance",
        "leaves taken": "leaves_taken",
        "leaves_taken": "leaves_taken",
        "leaves": "leaves_taken",
        "leave": "leaves_taken",
        "salary": "salary",
        "performance": "performance_rating",
        "rating": "performance_rating",
        "attendance": "attendance_pct"
    }
    
    matched_spans = []
    # Sort by length descending to match "leave balance" before "leave"
    sorted_metrics = sorted(metrics_map.items(), key=lambda x: len(x[0]), reverse=True)
    
    for phrase, col in sorted_metrics:
        # Pattern 1: metric + operator + value (e.g. "salary above 50000" or "rating of '1'")
        # NOTE: ['"]? allows optional surrounding quotes around the numeric value
        pattern1 = rf"\b{phrase}\s*(?:percentage|ratio|count|rating)?\s*(?:of|is|=|:)?\s*(above|below|greater than|less than|higher than|lower than|at least|at most|more than|>=|<=|>|<)?\s*['\"]?(\d+(?:\.\d+)?)['\"]?(?:\s*%)?(?:\s*or higher|\s*or lower)?\b"
        # Pattern 2: operator + value + metric (e.g. "more than 10 leaves")
        pattern2 = rf"\b(above|below|greater than|less than|higher than|lower than|at least|at most|more than|>=|<=|>|<)\s*['\"]?(\d+(?:\.\d+)?)['\"]?(?:\s*%)?\s*{phrase}\b"
        
        for pattern in [pattern1, pattern2]:
            for match in re.finditer(pattern, q_lower):
                span = match.span()
                if any(s[0] <= span[0] < s[1] or s[0] < span[1] <= s[1] for s in matched_spans):
                    continue
                    
                # For pattern 1, op is group 1, val is group 2.
                # For pattern 2, op is group 1, val is group 2. (Wait, they are the same!)
                op_text = match.group(1)
                val_text = match.group(2)
                val = float(val_text)
                
                op = "=="
                if op_text in ("above", "greater than", "higher than", "more than", ">"):
                    op = ">"
                elif op_text in ("below", "less than", "lower than", "<"):
                    op = "<"
                elif op_text in ("at least", ">="):
                    op = ">="
                elif op_text in ("at most", "<="):
                    op = "<="
                
                # Check for suffix "or higher/lower" (only for pattern 1)
                if pattern == pattern1:
                    suffix = q_lower[match.end():match.end()+12]
                    if "or higher" in suffix:
                        op = ">="
                    elif "or lower" in suffix:
                        op = "<="
                    
                numeric_filters.append((col, op, val))
                matched_spans.append(span)

    # Check for name filters (starts with, ends with, contains)
    name_filter = None
    name_match_filter = re.search(r"\b(?:name|full name)\s+(ends with|starts with|contains|is)\s+['\"]?(\w+)['\"]?\b", q_lower)
    if name_match_filter:
        name_filter = (name_match_filter.group(1), name_match_filter.group(2))

    # Check for surname / last-name filter
    # Matches: surname "Desai", last name 'Desai', share the same surname "Desai"
    surname_filter = None
    is_surname_query = bool(re.search(
        r"\b(surname|last\s+name|last_name|family\s+name|share\s+the\s+same|same\s+surname|same\s+last\s+name)\b",
        q_lower
    ))
    if is_surname_query:
        # Extract the quoted word, e.g. "Desai" or 'Desai'
        sn_match = re.search(r"['\"]([A-Za-z]+)['\"]|\.([A-Za-z]{2,})\.|\ ([A-Z][a-z]+)\s*\?", query)
        if not sn_match:
            # Fallback: last capitalized word in the query that is not a common stop word
            _STOPWORDS = {"How", "Many", "Which", "Who", "Are", "Is", "The", "In", "With",
                          "Same", "Share", "Surname", "Last", "Name", "Employees", "Employee"}
            words = [w for w in re.findall(r"[A-Z][a-z]+", query) if w not in _STOPWORDS]
            if words:
                surname_filter = words[-1]
        else:
            surname_filter = (sn_match.group(1) or sn_match.group(2) or sn_match.group(3) or "").strip()

    # Check for top/bottom N
    top_n = 1
    n_match = re.search(r"\b(?:top|bottom|highest|lowest|first|last|best|worst)\s*(\d+)\b", q_lower)
    if n_match:
        top_n = int(n_match.group(1))
    
    # Check for target metric column for sum/avg/compare
    target_metric = None
    if re.search(r"\b(leave balance|balance)\b", q_lower):
        target_metric = "leave_balance"
    elif re.search(r"\b(leave|leaves)\b", q_lower):
        target_metric = "leaves_taken"
    elif re.search(r"\b(salary|salaries|budget|paid|pay)\b", q_lower):
        target_metric = "salary"
    elif re.search(r"\b(attendance)\b", q_lower):
        target_metric = "attendance_pct"
    elif re.search(r"\b(rating|performance)\b", q_lower):
        target_metric = "performance_rating"
    elif re.search(r"\b(born|birth|age|oldest|youngest)\b", q_lower):
        target_metric = "date_of_birth"
    elif re.search(r"\b(join|hired|senior|tenure)\b", q_lower):
        target_metric = "date_of_joining"
        
    # Refine intent if we found a metric
    if target_metric and "total" in q_lower:
        is_sum = True
        is_count = False
        
    # Check for group by column for comparison
    group_by_col = None
    if re.search(r"\bwhich\s+department\b", q_lower):
        group_by_col = "department"
    elif re.search(r"\bwhich\s+role\b", q_lower):
        group_by_col = "role"
    elif re.search(r"\bwhich\s+location\b|\bwhat\s+location\b", q_lower):
        group_by_col = "location"
    elif re.search(r"\b(which|what)\s+(manager|supervisor|lead|head)\b"
                   r"|\bmanager.{0,30}(most|fewest|highest|lowest|most employees|fewest employees)\b"
                   r"|\b(most|fewest).{0,20}(manager|supervisor)\b"
                   r"|\bsupervise[sd]?\s+the\s+(most|fewest|highest|lowest)\b",
                   q_lower):
        group_by_col = "manager_id"

    filtered_df = df.copy()
    desc_parts = []
    
    if matched_manager:
        filtered_df = filtered_df[filtered_df['manager_id'] == matched_manager]
        desc_parts.append(f"reporting to manager {matched_manager}")
        
    if matched_depts:
        filtered_df = filtered_df[filtered_df['department'].isin(matched_depts)]
        desc_parts.append(f"in the {' or '.join(matched_depts)} department" + ("s" if len(matched_depts) > 1 else ""))
        
    if matched_roles:
        filtered_df = filtered_df[filtered_df['role'].isin(matched_roles)]
        desc_parts.append(f"working as {' or '.join(matched_roles)}s")
        
    if matched_locs:
        filtered_df = filtered_df[filtered_df['location'].isin(matched_locs)]
        desc_parts.append(f"based in {' or '.join(matched_locs)}")
        
    if name_filter:
        mode, val = name_filter
        if mode == "starts with":
            filtered_df = filtered_df[filtered_df['full_name'].str.lower().str.startswith(val.lower())]
            desc_parts.append(f"whose name starts with '{val}'")
        elif mode == "ends with":
            filtered_df = filtered_df[filtered_df['full_name'].str.lower().str.endswith(val.lower())]
            desc_parts.append(f"whose name ends with '{val}'")
        elif mode == "contains":
            filtered_df = filtered_df[filtered_df['full_name'].str.lower().str.contains(val.lower())]
            desc_parts.append(f"whose name contains '{val}'")
        elif mode == "is":
            filtered_df = filtered_df[filtered_df['full_name'].str.lower() == val.lower()]
            desc_parts.append(f"named '{val}'")

    if surname_filter:
        # Match against the last word of full_name (the surname)
        filtered_df = filtered_df[
            filtered_df['full_name'].str.strip().str.split().str[-1].str.lower() == surname_filter.lower()
        ]
        desc_parts.append(f"with surname '{surname_filter}'")
            
    for col, op, val in numeric_filters:
        col_display = col.replace('_', ' ')
        if op == ">":
            filtered_df = filtered_df[filtered_df[col] > val]
            desc_parts.append(f"with {col_display} above {val}")
        elif op == "<":
            filtered_df = filtered_df[filtered_df[col] < val]
            desc_parts.append(f"with {col_display} below {val}")
        elif op == ">=":
            filtered_df = filtered_df[filtered_df[col] >= val]
            desc_parts.append(f"with {col_display} of at least {val}")
        elif op == "<=":
            filtered_df = filtered_df[filtered_df[col] <= val]
            desc_parts.append(f"with {col_display} of at most {val}")
        else:
            filtered_df = filtered_df[filtered_df[col] == val]
            desc_parts.append(f"with {col_display} of {val}")

    # Check for year of joining/birth
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", q_lower)
    if year_match:
        matched_year = year_match.group(1)
        if "join" in q_lower or "hired" in q_lower:
            filtered_df = filtered_df[filtered_df['date_of_joining'].astype(str).str.endswith(matched_year)]
            desc_parts.append(f"who joined in {matched_year}")
        elif "born" in q_lower or "birth" in q_lower:
            filtered_df = filtered_df[filtered_df['date_of_birth'].astype(str).str.endswith(matched_year)]
            desc_parts.append(f"born in {matched_year}")
        
    # If no specific filters were matched, just use a generic description
    if not desc_parts:
        entity_desc = "employees"
    else:
        # Join desc_parts naturally (e.g. "employees based in Bengaluru with a performance rating of 5")
        entity_desc = "employees " + " and ".join(desc_parts)
        
    # Deduplicate by employee_id to prevent identical row duplication while preserving distinct employees with the same name
    if 'employee_id' in filtered_df.columns:
        filtered_df = filtered_df.drop_duplicates(subset=["employee_id"])
    else:
        filtered_df = filtered_df.drop_duplicates(subset=["full_name"])
        
    if is_compare:
        if group_by_col == "manager_id":
            # ── Manager supervision ranking ─────────────────────────────────────
            # Count direct reports per manager_id, then join back to get manager name
            report_counts = (
                filtered_df[filtered_df["manager_id"].notna()]
                .groupby("manager_id")
                .size()
                .rename("report_count")
            )
            if report_counts.empty:
                answer = "According to the HR data, no manager-employee relationships were found."
            else:
                is_fewest = bool(re.search(r"\b(fewest|least|lowest|minimum)\b", q_lower))
                dir_word = "fewest" if is_fewest else "most"

                if top_n > 1:
                    # Top-N managers
                    top_series = report_counts.nsmallest(top_n) if is_fewest else report_counts.nlargest(top_n)
                    header = f"Top {len(top_series)} managers supervising the {dir_word} employees:\n"
                    entries = []
                    for rank, (mgr_id, count) in enumerate(top_series.items(), 1):
                        mgr_rows = df[df["employee_id"].str.upper() == mgr_id.upper()]
                        if not mgr_rows.empty:
                            mgr = mgr_rows.iloc[0]
                            entries.append(
                                f"{rank}. {mgr['full_name']}\n"
                                f"   Employee ID: {mgr_id}\n"
                                f"   Role: {mgr.get('role', 'N/A')}\n"
                                f"   Department: {mgr.get('department', 'N/A')}\n"
                                f"   Employees Supervised: {count}"
                            )
                        else:
                            entries.append(f"{rank}. {mgr_id} — Employees Supervised: {count}")
                    answer = header + "\n\n".join(entries)
                else:
                    # Single top/bottom manager
                    best_mgr_id = report_counts.idxmin() if is_fewest else report_counts.idxmax()
                    best_count  = report_counts.min()    if is_fewest else report_counts.max()
                    mgr_rows = df[df["employee_id"].str.upper() == best_mgr_id.upper()]
                    if not mgr_rows.empty:
                        mgr = mgr_rows.iloc[0]
                        answer = (
                            f"The manager supervising the {dir_word} employees is:\n\n"
                            f"  {mgr['full_name']}\n"
                            f"  Employee ID: {best_mgr_id}\n"
                            f"  Role: {mgr.get('role', 'N/A')}\n"
                            f"  Department: {mgr.get('department', 'N/A')}\n"
                            f"  Employees Supervised: {best_count}"
                        )
                    else:
                        answer = (
                            f"The manager with the {dir_word} direct reports is {best_mgr_id} "
                            f"with {best_count} employees supervised."
                        )
            print(f"[DataQuery] Manager supervision query: group_by=manager_id, top_n={top_n}")
        elif group_by_col:
            # ── Generic group-by (dept / role / location) ───────────────────────
            grouped = filtered_df.groupby(group_by_col)
            if is_avg and target_metric:
                series = grouped[target_metric].mean()
                agg_type = f"average {target_metric.replace('_', ' ')}"
            elif is_sum and target_metric:
                series = grouped[target_metric].sum()
                agg_type = f"total {target_metric.replace('_', ' ')}"
            else:
                series = grouped.size()
                agg_type = f"number of {entity_desc}"
                
            is_lowest = bool(re.search(r"\b(lowest|least|bottom)\b", q_lower))
            if is_lowest:
                best_idx = series.idxmin()
                best_val = series.min()
                dir_word = "lowest"
            else:
                best_idx = series.idxmax()
                best_val = series.max()
                dir_word = "highest"
                
            answer = f"According to the HR data, the {group_by_col} with the {dir_word} {agg_type} is {best_idx} ({int(best_val):,})."
            print(f"[DataQuery] Matched compare intent. GroupBy {group_by_col}, Agg {agg_type}: {best_idx} ({best_val})")
        elif target_metric:
            # Row level min/max
            # For dates, 'oldest' or 'earliest' means MIN. For others, 'lowest' means MIN.
            is_min_query = bool(re.search(r"\b(lowest|least|bottom|worst|oldest|earliest|first|senior)\b", q_lower))
            
            # Ensure column exists
            if target_metric not in filtered_df.columns:
                return None
                
            # If it's a date column, convert to datetime for proper comparison
            temp_df = filtered_df.copy()
            if "date_of" in target_metric:
                temp_df[target_metric] = pd.to_datetime(temp_df[target_metric], dayfirst=True, errors='coerce')
                # Drop invalid dates
                temp_df = temp_df.dropna(subset=[target_metric])
            
            if temp_df.empty:
                answer = f"According to the HR data, no valid records found for {target_metric.replace('_', ' ')}."
            else:
                dir_word = "lowest" if is_min_query else "highest"
                if "date_of" in target_metric:
                    dir_word = "earliest" if is_min_query else "latest"
                
                metric_display = target_metric.replace('_', ' ')
                
                def _fmt_metric_val(val, metric: str) -> str:
                    """Format a metric value for display."""
                    if hasattr(val, 'strftime'):
                        return val.strftime('%d-%m-%Y')
                    if metric == "salary" and isinstance(val, (int, float)):
                        return f"₹{val:,.2f}"
                    if isinstance(val, float):
                        return f"{val:,.2f}"
                    return str(val)

                if top_n > 1:
                    if is_min_query:
                        best_rows = temp_df.nsmallest(top_n, target_metric)
                    else:
                        best_rows = temp_df.nlargest(top_n, target_metric)

                    dir_label = "lowest" if is_min_query else "highest"
                    header = (
                        f"Top {len(best_rows)} {dir_label}-{metric_display} employees"
                        + (f" ({entity_desc})" if desc_parts else "")
                        + " according to the HR dataset:\n"
                    )
                    entries = []
                    for i, (_, row) in enumerate(best_rows.iterrows(), 1):
                        val_display = _fmt_metric_val(row[target_metric], target_metric)
                        entry = (
                            f"{i}. {row['full_name']}\n"
                            f"   Employee ID: {row.get('employee_id', 'N/A')}\n"
                            f"   Role: {row.get('role', 'N/A')}\n"
                            f"   Department: {row.get('department', 'N/A')}\n"
                            f"   {metric_display.title()}: {val_display}"
                        )
                        entries.append(entry)
                    answer = header + "\n\n".join(entries)
                else:
                    if is_min_query:
                        best_row = temp_df.loc[temp_df[target_metric].idxmin()]
                    else:
                        best_row = temp_df.loc[temp_df[target_metric].idxmax()]

                    val_display = _fmt_metric_val(best_row[target_metric], target_metric)
                    answer = (
                        f"According to the HR data, the employee with the {dir_word} {metric_display} is:\n\n"
                        f"  {best_row['full_name']}\n"
                        f"  Employee ID: {best_row.get('employee_id', 'N/A')}\n"
                        f"  Role: {best_row.get('role', 'N/A')}\n"
                        f"  Department: {best_row.get('department', 'N/A')}\n"
                        f"  {metric_display.title()}: {val_display}"
                    )
            
            print(f"[DataQuery] Matched row compare intent. {target_metric}")
        else:
            answer = "According to the HR data, I could not determine which metric to compare."
            
    elif is_avg:
        if target_metric and not filtered_df.empty:
            avg_val = filtered_df[target_metric].mean()
            metric_display = target_metric.replace("_", " ")
            answer = f"According to the HR data, the average {metric_display} for the {entity_desc} is {avg_val:,.1f}."
            print(f"[DataQuery] Matched avg intent. Executed pandas mean on {target_metric}: {avg_val}")
        else:
            answer = f"According to the HR data, no specific metric was found to average for the {entity_desc}."
    elif is_sum:
        # Default to salary if metric not found
        metric = target_metric if target_metric else "salary"
        if not filtered_df.empty:
            total_val = filtered_df[metric].sum()
            metric_display = metric.replace("_", " ")
            answer = f"According to the HR data, the total {metric_display} for the {entity_desc} is {total_val:,.2f}."
            print(f"[DataQuery] Matched sum intent. Executed pandas sum on {metric}: {total_val}")
        else:
            answer = f"According to the HR data, there are no {entity_desc} to sum."
    elif is_count:
        count = len(filtered_df)
        if surname_filter and count > 0:
            # For surname queries, include a list of matching employee names
            names_list = "\n".join(f"- {row['full_name']}" for _, row in filtered_df.iterrows())
            answer = (
                f"There are {count} employee{'s' if count != 1 else ''} with the surname \"{surname_filter}\":\n\n"
                f"{names_list}"
            )
        elif surname_filter and count == 0:
            answer = f"According to the HR data, no employees with the surname \"{surname_filter}\" were found."
        else:
            answer = f"According to the HR data, the total number of {entity_desc} is {count}."
        print(f"[DataQuery] Matched count intent. Executed pandas count: {count}")
    elif is_list:
        if len(filtered_df) == 0:
            answer = f"According to the HR data, there are no {entity_desc}."
        else:
            is_unique = "unique" in q_lower
            if "roles" in q_lower and ("names" not in q_lower or is_unique):
                roles = filtered_df['role'].unique().tolist()
                answer = f"According to the HR data, the unique roles of the {entity_desc} are:\n" + "\n".join([f"- {r}" for r in roles])
            else:
                # Determine which columns to include based on what the user asked for
                wants_email = bool(re.search(r"\b(email|emails|email address|email addresses|contact)\b", q_lower))
                wants_dept  = bool(re.search(r"\b(department|dept|team)\b", q_lower))
                wants_role  = not bool(re.search(r"\b(no role|without role)\b", q_lower))  # include role by default

                def _format_row(x):
                    parts = [x['full_name']]
                    meta = []
                    if wants_role:
                        meta.append(x['role'])
                    if wants_dept:
                        meta.append(x['department'])
                    base = f"{x['full_name']} ({', '.join(meta)})" if meta else x['full_name']
                    if wants_email:
                        base += f" — {x['email']}"
                    return base

                if wants_email or wants_dept:
                    # Build a structured table when specific fields are requested
                    header_parts = ["Full Name", "Role"]
                    if wants_dept:
                        header_parts.append("Department")
                    if wants_email:
                        header_parts.append("Email")

                    rows = []
                    for _, x in filtered_df.iterrows():
                        row_parts = [x['full_name'], x['role']]
                        if wants_dept:
                            row_parts.append(x['department'])
                        if wants_email:
                            row_parts.append(x['email'])
                        rows.append(" | ".join(str(v) for v in row_parts))

                    header = " | ".join(header_parts)
                    separator = " | ".join(["-" * len(h) for h in header_parts])
                    table = header + "\n" + separator + "\n" + "\n".join(rows)
                    answer = f"According to the HR data, the {entity_desc} are:\n\n{table}"
                else:
                    names = filtered_df.apply(lambda x: f"{x['full_name']} ({x['role']})", axis=1).tolist()
                    answer = f"According to the HR data, the {entity_desc} are:\n" + "\n".join([f"{i+1}. {n}" for i, n in enumerate(names)])
        print(f"[DataQuery] Matched list intent. Executed pandas listing for {len(filtered_df)} entities.")
        
    return {
        "answer": answer,
        "sources": [{"source": "hr_data.csv"}]
    }
