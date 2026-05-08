"""
backend/services/rag_pipeline.py
Central RAG orchestration service.
Moved from services/rag_service.py; imports updated to new structure.
"""
import json
import re
import os

from backend.rag.retrieval.retriever import get_relevant_docs
from backend.rag.llm.groq_client import invoke as llm_invoke, stream as llm_stream
from backend.guardrails.input_guard import validate_input
from backend.guardrails.output_guard import validate_output, mask_pii
from backend.services.data_query import handle_data_query


# ── PII masking (internal context/query) ────────────────────────────
def _mask_pii(text: str) -> str:
    # Use a local map to ensure the same ID gets the same placeholder within one call
    # but different IDs get unique placeholders (e.g. [EMP_ID_1], [EMP_ID_2])
    # This allows the LLM to disambiguate same-named individuals.
    id_map = {}
    
    def repl_id(match):
        val = match.group(0).upper()
        if val not in id_map:
            id_map[val] = f"[EMP_ID_{len(id_map) + 1}]"
        return id_map[val]

    text = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[EMAIL]", text, flags=re.I)
    text = re.sub(r"FINEMP\d+", repl_id, text, flags=re.I)
    return text


def _clean_causal_context(context: str, query: str) -> str:
    """Remove advisory noise and sub-bullets from context for causal queries."""
    if "why" not in query.lower() and "reason" not in query.lower():
        return context
    
    lines = context.split("\n")
    cleaned = []
    for line in lines:
        # Skip INDENTED lines (sub-bullets and sub-analysis)
        if line.startswith("  "):
            continue
        cleaned.append(line)
    
    result = "\n".join(cleaned)
    return result


# ── Deduplication ────────────────────────────────────────────────────
def _deduplicate(docs) -> list:
    seen, cleaned = set(), []
    for d in docs:
        content = d.page_content.strip()
        source = os.path.basename(d.metadata.get("source", ""))
        page = d.metadata.get("page")
        
        # Use content + source + page as a key to avoid removing different segments
        # that might start with similar text (e.g. standard headers)
        key = (re.sub(r"\s+", " ", content)[:200], source, page)
        
        if key not in seen:
            cleaned.append(d)
            seen.add(key)
    print(f"[Dedup] {len(docs)} -> {len(cleaned)} unique")
    return cleaned


def _group_by_source(docs) -> list:
    """Group chunks by source and sort by chunk_id to maintain document order."""
    groups = {}
    for d in docs:
        src = d.metadata.get("source", "unknown")
        if src not in groups:
            groups[src] = []
        groups[src].append(d)
    
    # Sort chunks WITHIN each group by chunk_id if present
    for src in groups:
        groups[src].sort(key=lambda x: x.metadata.get("chunk_id", 0))
    
    sorted_sources = []
    seen = set()
    for d in docs:
        src = d.metadata.get("source", "unknown")
        if src not in seen:
            sorted_sources.append(src)
            seen.add(src)
            
    final_docs = []
    for src in sorted_sources:
        final_docs.extend(groups[src])
    print(f"[Group] Grouped {len(docs)} chunks into {len(groups)} sources (sorted by chunk_id)")
    return final_docs


def _format_context(docs) -> str:
    """Group chunks by source and wrap in clear boundaries."""
    from collections import defaultdict
    groups = defaultdict(list)
    source_order = []
    seen_sources = set()
    
    for d in docs:
        source = os.path.basename(d.metadata.get("source", "unknown"))
        page = d.metadata.get("page")
        # For PDFs, include page in the key to maintain distinction
        key = (source, page if source.lower().endswith('.pdf') else None)
        
        if key not in seen_sources:
            source_order.append(key)
            seen_sources.add(key)
        groups[key].append(d.page_content)
    
    formatted = []
    for key in source_order:
        source, page = key
        contents = groups[key]
        
        if page is not None:
            display_page = page + 1
            source_info = f"[[ AUTHORITATIVE_SOURCE_START: {source} (Page {display_page}) ]]"
        else:
            source_info = f"[[ AUTHORITATIVE_SOURCE_START: {source} ]]"
            
        # Join chunks with a marker to show they are separate snippets from the same file
        merged_content = "\n[...]\n".join(contents)
        formatted.append(f"{source_info}\n{merged_content}\n[[ AUTHORITATIVE_SOURCE_END: {source} ]]")
        
    return "\n\n".join(formatted)


# ── Context limiter ───────────────────────────────────────────────────
def _limit_context(context: str, max_chars: int = 18000) -> str:
    if len(context) > max_chars:
        print("[Warn] Context trimmed")
        return context[:max_chars]
    return context


# ── Aspect vocabulary ─────────────────────────────────────────────────
# Maps a detected query aspect to keywords a sentence must contain
# to be considered directly relevant. Sentences with NONE of these
# keywords are stripped from context before the LLM ever sees them.
_ASPECT_VOCAB: dict[str, set[str]] = {
    "security": {
        "security", "secure", "auth", "authentication", "authorization",
        "authorisation", "rate limit", "rate limiting", "throttl",
        "permission", "access control", "lambda authorizer", "authorizer",
        "protect", "protection", "attack", "threat", "vulnerability",
        "encryption", "tls", "ssl", "firewall", "ddos", "intrusion",
        "credential", "token", "jwt", "oauth", "rbac", "policy",
        "centrali", "entry point", "single entry", "attack surface",
        "microservice",
    },
    "performance": {
        "performance", "latency", "throughput", "speed", "fast", "slow",
        "cache", "caching", "scale", "scaling", "scalab", "load",
        "capacity", "optimiz", "efficient", "response time", "benchmark",
    },
    "cost": {
        "cost", "price", "pricing", "budget", "expense", "spend",
        "billing", "invoice", "fee", "charge", "revenue", "saving",
        "income", "profit", "margin", "compensation", "salary", "benefit",
        "hr costs", "personnel", "talent", "payroll", "commission", "hr", "headcount", "recruit",
    },
    "reliability": {
        "reliab", "availab", "uptime", "failover", "redundan", "resilient",
        "resilien", "fault", "recover", "backup", "disaster", "sla",
        "health check", "circuit breaker",
    },
    "scalability": {
        "scale", "scaling", "scalability", "horizontal", "vertical",
        "hpa", "sharding", "replica", "capacity", "load", "elastic",
        "cache", "caching", "redis", "cdn"
    },
    "fault tolerance": {
        "fault", "tolerance", "tolerant", "resilien", "recover",
        "backup", "disaster", "failover", "redundanc", "redundant",
        "circuit breaker", "availability", "active-active"
    }
}

_ASPECT_QUERY_RE = re.compile(
    r"\b(enhance|improve|ensure|provide|related to|regarding|about|role of|contribution of)\b.*"
    r"\b(security|performance|cost|reliability|availability|scalability|fault tolerance)\b"
    r"|\b(security|performance|cost|reliability|availability|scalability|fault tolerance)\b.*"
    r"\b(feature|benefit|mechanism|aspect|role|function|improve|enhance|protect|contribute)\b"
    r"|how\s+does.*(security|performance|cost|reliability|availability|scalability|fault tolerance)"
    r"|what.*(security|performance|cost|reliability|availability|scalability|fault tolerance).*(feature|mechanism|benefit|aspect|role)",
    re.I,
)


def _detect_aspects(query: str) -> list[str]:
    """Return all focal aspects detected in the query."""
    q = query.lower()
    detected = set()
    for aspect, kws in _ASPECT_VOCAB.items():
        # 1. Direct aspect match
        aspect_term = aspect.replace("_", " ")
        if aspect_term in q:
            detected.add(aspect)
            continue
            
        # 2. Keyword match (e.g. "revenue" triggers "cost")
        if any(f" {kw} " in f" {q} " or q.startswith(f"{kw} ") or q.endswith(f" {kw}") for kw in kws):
            detected.add(aspect)
            continue

        # 3. Pattern match
        if re.search(rf"\b{aspect}\b", q) and _ASPECT_QUERY_RE.search(q):
            detected.add(aspect)
        elif re.search(rf"how does.*\b{aspect}\b", q):
            detected.add(aspect)
        elif re.search(rf"\b{aspect}\b.*(feature|mechanism|benefit|protect|role)", q):
            detected.add(aspect)
            
    return list(detected)


def _filter_context_by_aspect(context: str, query: str) -> str:
    """
    Two-tier aspect filter applied before the LLM sees the context.
    """
    aspects = _detect_aspects(query)
    if not aspects:
        return context

    # Union all keywords and blocklists for detected aspects
    keywords = set()
    for asp in aspects:
        keywords.update(_ASPECT_VOCAB.get(asp, set()))

    # Per-aspect blocklist: patterns that are non-primary for this aspect.
    _BLOCKLIST: dict[str, list[re.Pattern]] = {
        "security": [
            re.compile(r"\bapi\s+version\w*\b", re.I),
            re.compile(r"\bswagger\b", re.I),
            re.compile(r"\bopenapi\b", re.I),
            re.compile(r"\bapi\s+documentation\b", re.I),
            re.compile(r"\bdeveloper\s+documentation\b", re.I),
            re.compile(r"\bdocumentation\s+(via|through|using|with|for)\b", re.I),
            re.compile(r"\bbasic\s+analytics\b", re.I),
            re.compile(r"\brequest\s+logging\b", re.I),
            re.compile(r"\busage\s+analytics\b", re.I),
            re.compile(r"\bapi\s+versioning\b", re.I),
        ]
    }
    
    blocklist = []
    for asp in aspects:
        blocklist.extend(_BLOCKLIST.get(asp, []))

    # Anti-patterns: phrases that CONTAIN an aspect keyword but are NOT
    # mechanisms — they come from unrelated sections (e.g. tech selection)
    _ANTI_PATTERNS: dict[str, list[re.Pattern]] = {
        "security": [
            re.compile(r"\bregular\s+security\s+updates\b", re.I),
            re.compile(r"\btechnology\s+selection\s+criteria\b", re.I),
            re.compile(r"\bselection\s+criteria\b", re.I),
            re.compile(r"\bvendor\s+security\b", re.I),
            re.compile(r"\bsecurity\s+patch\w*\b", re.I),
            re.compile(r"\bsecurity\s+update\w*\b", re.I),
        ]
    }
    anti_patterns = []
    for asp in aspects:
        anti_patterns.extend(_ANTI_PATTERNS.get(asp, []))

    def _has_aspect_keyword(text: str) -> bool:
        t = text.lower()
        return any(kw in t for kw in keywords)

    def _matches_anti_pattern(sentence: str) -> bool:
        """True if the sentence matches a known off-topic anti-pattern,
        regardless of whether it contains a security keyword."""
        return any(pat.search(sentence) for pat in anti_patterns)

    def _is_blocklisted(sentence: str) -> bool:
        """True if the sentence should be stripped from context.
        Anti-patterns are checked first and always win.
        Regular blocklist only fires when no aspect keyword is present.
        """
        if _matches_anti_pattern(sentence):
            return True  # Context leakage — always strip
        if _has_aspect_keyword(sentence):
            return False  # Genuine security content → keep
        return any(pat.search(sentence) for pat in blocklist)

    filtered_paragraphs = []

    for para in context.split("\n\n"):
        lines = para.split("\n")
        header_lines = [l for l in lines if l.startswith("--- SOURCE:")]
        content_lines = [l for l in lines if not l.startswith("--- SOURCE:")]
        content_text_for_check = " ".join(content_lines)

        # Tier 1: skip paragraph entirely if no aspect keyword anywhere in it
        if not _has_aspect_keyword(content_text_for_check):
            continue

        # Tier 2: within the paragraph, drop sentences/lines that are exclusively off-topic
        cleaned_lines = []
        for line in content_lines:
            cleaned_sentences = []
            for sentence in re.split(r"(?<=[.!?])\s+", line):
                if not sentence.strip():
                    continue
                if not _is_blocklisted(sentence):
                    cleaned_sentences.append(sentence)
            
            if cleaned_sentences:
                cleaned_lines.append(" ".join(cleaned_sentences).strip())

        cleaned_content = "\n".join(cleaned_lines).strip()
        if cleaned_content:
            block = "\n".join(header_lines + [cleaned_content])
            filtered_paragraphs.append(block.strip())

    result = "\n\n".join(filtered_paragraphs)
    print(f"[AspectFilter] aspects={aspects} context {len(context)} -> {len(result)} chars")
    return result if result.strip() else context


# ── Lexical filter ────────────────────────────────────────────────────
def _lexical_filter(docs, query: str, threshold: float = 0.05) -> list:
    query_words = set(re.findall(r"\w+", query.lower()))
    strong = []
    for d in docs:
        text_words = set(re.findall(r"\w+", d.page_content.lower()))
        # More lenient overlap check for short queries
        overlap = len(query_words & text_words)
        ratio = overlap / (len(query_words) + 1)
        if ratio >= threshold:
            strong.append(d)
    
    # If no strong matches, fallback to top 5 docs instead of 10
    result = strong if strong else docs[:5]
    print(f"[Filter] {len(docs)} -> {len(result)} strong matches (threshold={threshold})")
    return result


# ── Source builder ────────────────────────────────────────────────────
def _build_sources(docs, max_sources: int = 1) -> list:
    seen, sources = set(), []
    for d in docs:
        source_path = d.metadata.get("source", "unknown")
        page = d.metadata.get("page")
        
        # Deduplicate by source (and page for PDFs)
        is_pdf = source_path.lower().endswith(".pdf")
        key = (source_path, page if is_pdf else None)
            
        if key not in seen:
            seen.add(key)
            entry = {"source": source_path}
            if is_pdf and page is not None:
                # Add 1 because PDF loaders are typically 0-indexed while humans are 1-indexed
                entry["page"] = page + 1
            sources.append(entry)
            
        if len(sources) >= max_sources:
            break
    return sources


# ── Prompt builder ────────────────────────────────────────────────────
def _build_prompt(context: str, user_query: str, role: str = "general", employee_id: str | None = None) -> str:
    id_instruction = (
        f"\nIMPORTANT:\nThe user is asking about Employee ID '{employee_id}'.\n"
        f"ONLY use data belonging to this employee.\n"
        if employee_id else ""
    )

    if role == "admin":
        role_instruction = (
            "You are a Superuser Administrator. You have access to ALL company documents across ALL departments "
            "(Marketing, Finance, HR, Engineering, etc.). You should use any information provided in the context "
            "regardless of the [Access: ...] tags, as you have full clearance."
        )
    else:
        role_instruction = (
            f"You are an enterprise data assistant helping an employee from the '{role}' department.\n"
            f"You have access to:\n"
            f"1. General company documents (Employee Handbook, etc.)\n"
            f"2. Specific documents permitted for the '{role}' role."
        )

    return f"""{role_instruction}

{id_instruction}
⚠ FINANCIAL PERFORMANCE STRICTNESS (CRITICAL):
If the query is about Revenue, Net Income, Gross Margin, Profit growth, Vendor Costs, or Software Subscriptions, and your provided context is only the "Employee Handbook" or "HR Policies", you MUST refuse to answer. State: "The answer to this question is not available in the accessible documents."
Do NOT attempt to use numbers from the handbook (like EPF percentages or leave days) to answer financial performance questions.

⚠ SOURCE ISOLATION AND GROUNDING RULE:
You are strictly prohibited from mixing data (numbers, names, facts) from different documents. 
1. SELECT SOURCE: Choose the single most relevant source for the query.
2. EXCLUSIVE DERIVATION: Derive your entire answer EXCLUSIVELY from that one source. 
3. VERIFICATION STEP: Before finalising, verify that EVERY number, percentage, and fact in your answer is physically present in the text of that specific document.

⚠ INCOMPLETE QUERY RULE:
If the user's question is incomplete, extremely short (like a single letter or punctuation mark), or lacks a clear intent (e.g., ".s"), do NOT attempt to guess what they are asking. Do NOT summarize the context. Simply state: "Please provide a complete and specific question."

⚠ NO DATA AVAILABLE RULE:
If the user's question IS clear and specific, but the provided context does NOT contain the information needed to answer it, do NOT ask for a different question. Instead state: "This information isn't available in the {role} department's documents. You may need to check with the relevant department or request access to the appropriate data."
Do NOT speculate, do NOT partially answer, and do NOT summarize unrelated context.

⚠ ANALYTICAL NARRATIVE RULE:
IF AND ONLY IF the context contains a section titled "Expense Breakdown" or similar financial data:
- You MUST synthesize the primary expense drivers.
- For each category (e.g., Vendor Services), you MUST cite the specific line-item percentage increase.
- If a category is NOT mentioned in the context, do NOT include it.
- If the context does NOT contain an Expense Breakdown section, skip this rule entirely and provide a standard factual response based on available data.

⚠ TOPIC FOCUS RULE:
When a question asks about ONE specific aspect (security, performance, cost, reliability):
1. IDENTIFY TOPIC: Determine if the AUTHORITATIVE_SOURCE is primarily about the asked aspect. 
2. COMPONENT FILTERING: 
   - List every feature/component mentioned in the context that is relevant to the question.
   - For EACH feature, apply this test: "Is the PRIMARY AND DIRECT purpose of this feature to enforce or enhance the asked aspect?" If NO → remove it from your list.
3. ANSWER ONLY PASSING ITEMS: Only the features that pass the filter in Step 2 may appear in your answer.

HARD-BANNED items for security-aspect questions:
  ✗ API versioning / API version management
  ✗ Swagger / OpenAPI documentation
  ✗ Developer documentation / API documentation
  ✗ Request logging / basic analytics / usage analytics

- Answer ONLY from the provided context.
- NO REPETITION: Each mechanism must be stated EXACTLY ONCE.
- ACCURACY AND COMPLETENESS ARE CRITICAL: Ensure numbers are correctly paired with their specific descriptors.
- NO REDUNDANT SOURCE NAMING: Do NOT name the document title or filename in the answer body (e.g., do NOT write "According to marketing_report_q3_2024.md..." or "The Comprehensive Marketing Report states..."). The source is already cited separately at the end. Just state the facts directly.
- CONTEXTUAL ENRICHMENT RULE: After stating the directly requested fact, include 1-2 closely related impact metrics from the SAME topic in the context. "Same topic" means: adjacent bullet points under the same heading, or related objectives about the same feature (e.g., loyalty program enrollment + its impact on repeat purchases + customer satisfaction).
  STRICT REQUIREMENT: Every number you include MUST appear verbatim in the provided context. If a metric does not have an explicit number in the context, do NOT include it and do NOT invent one.
  Example — if context contains "Enrolled 40,000 customers... with 55% redeeming rewards" AND separately "resulting in a 10% increase in repeat purchases" AND "leading to a 5% improvement in customer satisfaction scores":
    GOOD: "In Q3 2024, 40,000 customers enrolled in the loyalty program, with 55% redeeming rewards by quarter-end. This contributed to a 10% increase in repeat purchases compared to Q2 and a 5% improvement in customer satisfaction scores."
  After stating the fact and its grounded impact metrics, STOP. Do NOT continue beyond this.
- SAME-DEPARTMENT CROSS-REFERENCE RULE: If the context contains MULTIPLE sources from the SAME department (e.g., multiple quarterly reports), you MAY briefly reference data from a second source to show trends or comparisons. When doing so, clearly indicate the time period (e.g., "This grew from 40,000 in Q3 to 50,000 in Q4"). You must still list only the PRIMARY source in the [[SOURCES:]] block.
- ANTI-HALLUCINATION RULE (CRITICAL): Before writing ANY number, percentage, or dollar amount in your answer, you MUST be able to point to the EXACT line in the CONTEXT where that number appears. If you cannot, do NOT write it. This applies to enrichment data too — if a number does not appear verbatim in the context, it is fabricated. If the context does not contain enough information to answer the question, use the NO DATA AVAILABLE RULE instead.
- EXPLANATION/REASON RULE: You are an expert analyst.
    * CAUSE-EFFECT CHAIN: For "relationship" questions, you MUST show the full process/chain.
    * APPROVED PHRASING: The ONLY approved way to explain this relationship is: "Issues with delayed vendor payment cycles led to accounts payable delays, which created a temporary strain on cash liquidity during the latter half of 2024."
    * NO ADVISORY: Do NOT include recommendations like "Addressing these delays will be crucial..."
    * FORMAT: Single prose paragraph. No bullet points.
- OVERVIEW/SUMMARY RULE: For "overview", "summary", "report" etc.:
  1. Open with 1 framing sentence.
  2. Enumerate relevant components found WITHIN THE SINGLE cited source.
- SPECIFIC QUERY RULE: For narrow queries, state the requested value and its contextual enrichment. Nothing more.
- NO MARKDOWN BOLD: Do NOT use ** for bold text. Write in plain prose.
- TERMINATION: End with "END_OF_ANSWER". After this, list your EXACTLY ONE source filename in the format "[[SOURCES: filename]]".

CONTEXT:
{context}

QUESTION:
{user_query}

FINAL ANSWER:
"""


# ── Query decomposition ───────────────────────────────────────────────

# Keywords that indicate a question is about a non-HR policy/document
_DOC_SIGNALS = re.compile(
    r"\b(engineering|document|policy|handbook|requirement|coverage|standard|"
    r"sdlc|deployment|security|compliance|architecture|test|testing|sprint|"
    r"according to the|as per|per the|in the)\b",
    re.I,
)

# Keywords that indicate a question is about HR / employee data
_HR_SIGNALS = re.compile(
    r"\b(employee|employees|hr data|hr|salary|manager|role|department|"
    r"location|attendance|performance|leave|joined|hired|based in|who is|profile)\b",
    re.I,
)

# Conjunctions that may join two distinct sub-questions
_CONJUNCTION_SPLIT = re.compile(
    r"\s*,?\s+and\s+according to\s+|\s*,?\s+and\s+|\s*;\s+|\s+as well as\s+",
    re.I,
)


def _split_compound_query(query: str) -> list[str] | None:
    """
    If `query` appears to be two distinct sub-questions (one HR, one doc-based),
    return them as a list of two strings.  Otherwise return None.
    """
    parts = _CONJUNCTION_SPLIT.split(query, maxsplit=1)
    if len(parts) != 2:
        return None
    a, b = parts[0].strip(), parts[1].strip()
    # Both halves must be non-trivial
    if len(a) < 10 or len(b) < 10:
        return None
    # One half should be HR-flavoured, the other doc-flavoured
    a_hr  = bool(_HR_SIGNALS.search(a))
    b_hr  = bool(_HR_SIGNALS.search(b))
    a_doc = bool(_DOC_SIGNALS.search(a))
    b_doc = bool(_DOC_SIGNALS.search(b))
    if (a_hr and b_doc) or (a_doc and b_hr):
        return [a, b]
    return None


def _run_single_rag(sub_query: str, role: str, employee_id: str | None) -> dict:
    """
    Run a focused RAG pass for one sub-query and return
    {answer, sources, usage, latency_ms}.
    """
    docs = get_relevant_docs(sub_query, role, employee_id=employee_id)
    if not docs:
        return {"answer": "No information available.", "sources": []}

    unique_docs = _deduplicate(docs)
    context     = _format_context(unique_docs)
    context     = _limit_context(context)
    context     = _filter_context_by_aspect(context, sub_query)
    print(f"[Debug] Filtered Context (first 500 chars): {context[:500]}...")
    safe_ctx    = _mask_pii(context)
    safe_query  = _mask_pii(sub_query)
    prompt      = _build_prompt(safe_ctx, safe_query, role=role, employee_id=employee_id)

    result      = llm_invoke(prompt, role=role, query=safe_query)
    raw_answer  = result.get("content", "")

    sources_match = re.search(r"\[\[SOURCES:\s*(.*?)\]\]", raw_answer)
    cited_files = []
    if sources_match:
        cited_files = [f.strip() for f in sources_match.group(1).split(",")][:1]

    clean_answer = raw_answer.split("END_OF_ANSWER")[0].strip()
    clean_answer = re.sub(r"\[\[SOURCES:.*?\]\]", "", clean_answer).strip()
    answer = validate_output(clean_answer, context, sub_query)

    sources: list[dict] = []
    seen: set[str] = set()
    if cited_files:
        for fname in cited_files:
            if fname not in seen:
                for d in unique_docs:
                    if os.path.basename(d.metadata.get("source", "")) == fname:
                        entry: dict = {"source": d.metadata.get("source")}
                        if fname.lower().endswith(".pdf") and d.metadata.get("page") is not None:
                            entry["page"] = d.metadata.get("page") + 1
                        sources.append(entry)
                        seen.add(fname)
                        break
                else:
                    sources.append({"source": fname})
                    seen.add(fname)
    if not sources:
        sources = _build_sources(unique_docs, max_sources=1)

    return {
        "answer":     answer,
        "sources":    sources,
        "usage":      result.get("usage", {}),
        "latency_ms": result.get("latency_ms", 0),
    }


def _merge_results(results: list[dict]) -> dict:
    """Merge multiple sub-query results into one combined response."""
    combined_parts = []
    combined_sources: list[dict] = []
    seen_srcs: set[str] = set()
    total_usage: dict = {}
    total_latency = 0

    for i, res in enumerate(results, 1):
        ans = res.get("answer", "").strip()
        if ans and ans.lower() != "no information available":
            combined_parts.append(ans)
        for src in res.get("sources", []):
            key = src.get("source", "") + str(src.get("page", ""))
            if key not in seen_srcs:
                combined_sources.append(src)
                seen_srcs.add(key)
        for k, v in res.get("usage", {}).items():
            total_usage[k] = total_usage.get(k, 0) + v
        total_latency += res.get("latency_ms", 0)

    merged_answer = "\n\n".join(combined_parts) if combined_parts else "No information available."
    return {
        "answer":     merged_answer,
        "sources":    combined_sources,
        "usage":      total_usage,
        "latency_ms": total_latency,
    }


# ── Public API ────────────────────────────────────────────────────────

def process_query(user_query: str, role: str = "general", employee_id: str | None = None) -> dict:
    is_valid, msg = validate_input(user_query)
    if not is_valid:
        return {"answer": msg, "sources": []}

    # ── Step 1: Try deterministic data handler first ─────────────────
    data_res = handle_data_query(user_query, role)
    if data_res:
        return data_res

    # ── Step 2: Query decomposition for compound multi-source queries ─
    sub_queries = _split_compound_query(user_query)
    if sub_queries:
        print(f"[Decompose] Splitting into {len(sub_queries)} sub-queries")
        results = []
        for sq in sub_queries:
            sq = sq.strip()
            # Try deterministic handler first for each sub-query
            dr = handle_data_query(sq, role)
            if dr:
                results.append(dr)
            else:
                results.append(_run_single_rag(sq, role, employee_id))
        return _merge_results(results)

    # ── Step 3: Standard single-pass RAG ─────────────────────────────
    docs = get_relevant_docs(user_query, role, employee_id=employee_id)
    if not docs:
        msg = "This information is not accessible for your role." if role == "general" else "No information available."
        return {"answer": msg, "sources": []}

    unique_docs = _deduplicate(docs)
    grouped_docs = _group_by_source(unique_docs)
    
    # Format context with source metadata
    context    = _format_context(grouped_docs)
    context    = _limit_context(context)
    context    = _filter_context_by_aspect(context, user_query)
    context    = _clean_causal_context(context, user_query)

    safe_ctx   = _mask_pii(context)
    safe_query = _mask_pii(user_query)
    prompt     = _build_prompt(safe_ctx, safe_query, role=role, employee_id=employee_id)

    result = llm_invoke(prompt, role=role, query=safe_query)
    raw_answer = result.get("content", "")
    
    # Extract citations from the dedicated block
    sources_match = re.search(r"\[\[SOURCES:\s*(.*?)\]\]", raw_answer)
    cited_files = []
    if sources_match:
        cited_files = [f.strip() for f in sources_match.group(1).split(",")]
        cited_files = cited_files[:1] # Strictly limit to 1 source
    
    # Clean answer by removing the END_OF_ANSWER and SOURCES block
    clean_answer = raw_answer.split("END_OF_ANSWER")[0].strip()
    clean_answer = re.sub(r"\[\[SOURCES:.*?\]\]", "", clean_answer).strip()
    
    answer = validate_output(clean_answer, context, user_query)
    
    # Build sources based on what the LLM actually cited
    sources = []
    seen_sources = set()
    if cited_files:
        for fname in cited_files:
            if fname not in seen_sources:
                for d in unique_docs:
                    if os.path.basename(d.metadata.get("source", "")) == fname:
                        entry = {"source": d.metadata.get("source")}
                        if fname.lower().endswith(".pdf") and d.metadata.get("page") is not None:
                            entry["page"] = d.metadata.get("page") + 1
                        sources.append(entry)
                        seen_sources.add(fname)
                        break
                else:
                    sources.append({"source": fname})
                    seen_sources.add(fname)
    
    # If no citations found, fallback to the top doc
    if not sources:
        sources = _build_sources(unique_docs, max_sources=1)
    
    # If answer is a refusal, don't show any sources
    refusal_msg = "not available in the accessible documents"
    ans_lower = answer.strip().lower()
    if ans_lower == "no information available" or refusal_msg in ans_lower or "not accessible for your role" in ans_lower or "department's documents" in ans_lower:
        sources = []

    return {
        "answer":      answer,
        "sources":     sources,
        "usage":       result.get("usage", {}),
        "latency_ms":  result.get("latency_ms", 0),
    }


def process_query_stream(user_query: str, role: str = "general", employee_id: str | None = None):
    is_valid, msg = validate_input(user_query)
    if not is_valid:
        yield msg
        return

    # ── Step 1: Try deterministic data handler first ─────────────────
    data_res = handle_data_query(user_query, role)
    if data_res:
        yield data_res["answer"]
        yield f"SOURCES_JSON:{json.dumps(data_res['sources'])}"
        return

    # ── Step 2: Query decomposition for compound multi-source queries ─
    sub_queries = _split_compound_query(user_query)
    if sub_queries:
        print(f"[Decompose/stream] Splitting into {len(sub_queries)} sub-queries")
        merged = _merge_results([
            handle_data_query(sq.strip(), role) or _run_single_rag(sq.strip(), role, employee_id)
            for sq in sub_queries
        ])
        yield merged["answer"]
        yield f"SOURCES_JSON:{json.dumps(merged['sources'])}"
        return

    # ── Step 3: Standard single-pass streaming RAG ───────────────────
    docs = get_relevant_docs(user_query, role, employee_id=employee_id)
    if not docs:
        yield "This information is not accessible for your role." if role == "general" else "No information available in the documents accessible to your role."
        return

    # docs        = _lexical_filter(docs, sub_query)
    unique_docs = _deduplicate(docs)
    grouped_docs = _group_by_source(unique_docs)
    context     = _format_context(grouped_docs)
    context    = _limit_context(context)
    context    = _filter_context_by_aspect(context, user_query)
    context    = _clean_causal_context(context, user_query)
    safe_ctx   = _mask_pii(context)
    safe_query = _mask_pii(user_query)
    prompt     = _build_prompt(safe_ctx, safe_query, role=role, employee_id=employee_id)

    full_answer = ""
    buffer = ""
    terminator = "END_OF_ANSWER"
    stop_streaming = False
    is_refusal = False
    
    for chunk in llm_stream(prompt, role=role, query=safe_query):
        clean_chunk = chunk.replace("**", "")
        full_answer += clean_chunk
        
        # Check for refusal early in the stream
        if not is_refusal and len(full_answer) < 200:
            lower_ans = full_answer.lower()
            if "not available in the accessible documents" in lower_ans or "not accessible for your role" in lower_ans or "department's documents" in lower_ans:
                is_refusal = True

        if not stop_streaming:
            buffer += clean_chunk
            if terminator in buffer:
                stop_streaming = True
                yield buffer.split(terminator)[0]
                buffer = "" 
            else:
                # Yield prefix that is safe
                if len(buffer) > len(terminator):
                    yield buffer[:-len(terminator)]
                    buffer = buffer[-len(terminator):]
    
    if not stop_streaming and buffer:
        yield buffer

    # ── Post-stream grounding validation ─────────────────────────────
    # The streaming path previously bypassed validate_output(), allowing
    # hallucinated numbers through. We now validate the full answer and
    # send a CORRECTION chunk if grounding fails.
    clean_answer = full_answer.split("END_OF_ANSWER")[0].strip()
    clean_answer = re.sub(r"\[\[SOURCES:.*?\]\]", "", clean_answer).strip()
    validated = validate_output(clean_answer, safe_ctx, safe_query)
    
    if validated != clean_answer:
        # Grounding check failed — send correction to replace the streamed answer
        print(f"[StreamGuardrail] Grounding check FAILED — replacing streamed answer")
        yield f"\n\n---CORRECTION---{validated}"
        is_refusal = True

    # Extract citations from the full answer
    sources_match = re.search(r"\[\[SOURCES:\s*(.*?)\]\]", full_answer)
    cited_files = []
    if sources_match:
        cited_files = [f.strip() for f in sources_match.group(1).split(",")]
        cited_files = cited_files[:1] # Strictly limit to 1 source

    # Build sources based on what the LLM actually cited
    sources = []
    seen_sources = set()
    if cited_files:
        for fname in cited_files:
            if fname not in seen_sources:
                for d in unique_docs:
                    if os.path.basename(d.metadata.get("source", "")) == fname:
                        entry = {"source": d.metadata.get("source")}
                        if fname.lower().endswith(".pdf") and d.metadata.get("page") is not None:
                            entry["page"] = d.metadata.get("page") + 1
                        sources.append(entry)
                        seen_sources.add(fname)
                        break
                else:
                    sources.append({"source": fname})
                    seen_sources.add(fname)
    
    # If no citations found, fallback to the top doc
    if not sources:
        sources = _build_sources(unique_docs, max_sources=1)
    
    # If answer is a refusal, don't show any sources
    refusal_msg = "available in the accessible documents"
    fa_lower = full_answer.lower()
    if is_refusal or "no information available" in fa_lower or refusal_msg in fa_lower or "please provide a complete and specific question" in fa_lower or "department's documents" in fa_lower:
        sources = []

    yield f"SOURCES_JSON:{json.dumps(sources)}"
