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

    # ── Priority 0: Single-employee record lookup ────────────────────────────
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
    name_match = re.search(r"\b(?:name|full name)\s+(ends with|starts with|contains|is)\s+['\"]?(\w+)['\"]?\b", q_lower)
    if name_match:
        name_filter = (name_match.group(1), name_match.group(2))

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
        if group_by_col:
            # Determine aggregation method
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
                
            answer = f"According to the HR data, the {group_by_col} with the {dir_word} {agg_type} is {best_idx} at {best_val:,.2f}."
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
                
                if top_n > 1:
                    if is_min_query:
                        best_rows = temp_df.nsmallest(top_n, target_metric)
                    else:
                        best_rows = temp_df.nlargest(top_n, target_metric)
                    
                    rows_list = best_rows.apply(lambda x: f"{x['full_name']} ({x['role']}, {x['department']}) on {x[target_metric].strftime('%d-%m-%Y') if hasattr(x[target_metric], 'strftime') else x[target_metric]}", axis=1).tolist()
                    answer = f"According to the HR data, the top {len(rows_list)} employees with the {dir_word} {metric_display} are:\n" + "\n".join([f"{i+1}. {r}" for i, r in enumerate(rows_list)])
                else:
                    if is_min_query:
                        best_row = temp_df.loc[temp_df[target_metric].idxmin()]
                    else:
                        best_row = temp_df.loc[temp_df[target_metric].idxmax()]
                    
                    emp_name = best_row['full_name']
                    emp_role = best_row['role']
                    emp_dept = best_row['department']
                    best_val = best_row[target_metric]
                    if hasattr(best_val, 'strftime'):
                        best_val = best_val.strftime('%d-%m-%Y')
                    
                    answer = f"According to the HR data, the employee with the {dir_word} {metric_display} is {emp_name} ({emp_role}, {emp_dept}) with {metric_display} {best_val}."
            
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
