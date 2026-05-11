"""
Format search results for inclusion in Claude prompts.

Single per-source dispatcher used by every app that injects RAG hits into a
prompt. Synthesis imports this directly; QC and comparator migrate next.
The Jinja template layer also dispatches per-source (CA-3 template part) but
that's deferred to the next coordinated UI change.

Keyword options preserve current synthesis behavior by default; comparator
calls some sources without URLs, and a future caller may want percent-format
scores — both are absorbed by kwargs without restructuring the dispatch.
"""

SOURCE_LABELS = {
    "olg": "OLG",
    "cmr": "CMR",
    "fns": "FNS",
    "cfr": "CFR",
}


def _format_score(score: float, score_format: str) -> str:
    if score_format == "percent":
        return f"{score * 100:.0f}%"
    return f"{score:.2f}"


def format_results_for_prompt(
    results: list[dict],
    source: str,
    *,
    include_url: bool = True,
    include_breadcrumb: bool = True,
    score_format: str = "decimal",
) -> str:
    """Format search results for inclusion in a Claude prompt.

    Defaults match synthesis's prior behavior. Comparator's leaner formatters
    pass `include_url=False`; UI-template-style callers can pass
    `score_format="percent"`.
    """
    label = SOURCE_LABELS.get(source, source.upper())
    if not results:
        return f"No {label} matches found."

    parts = []
    for i, result in enumerate(results):
        meta = result["metadata"]
        score = result["score"]
        text = result["text"][:1000]
        score_str = _format_score(score, score_format)

        if source == "olg":
            page_title = meta.get("page_title", meta.get("title", ""))
            heading = meta.get("section_heading", "")
            parent_heading = meta.get("parent_heading", "")
            breadcrumb = meta.get("breadcrumb", "")
            url = meta.get("url", "")
            chunk_n = meta.get("chunk_n")
            chunk_total = meta.get("chunk_total")
            chunk_id = result.get("id", "")
            header = f"[{label} Match {i+1}] Score: {score_str}"
            if chunk_id:
                header += f" | id: {chunk_id}"
            if page_title:
                header += f" | Page: {page_title}"
            if heading:
                header += f" | Section: {heading}"
            if chunk_total is not None and chunk_total > 1:
                header += f" (part {chunk_n} of {chunk_total})"
            if parent_heading:
                header += f"\n  Within: {parent_heading}"
            if include_breadcrumb and breadcrumb:
                header += f"\n  Path: {breadcrumb}"
            if include_url and url:
                header += f"\n  URL: {url}"

        elif source == "fns":
            chapter = meta.get("chapter", "")
            chapter_title = meta.get("chapter_title", "")
            sec_num = meta.get("section_number", "")
            sec_title = meta.get("section_title", "")
            chunk_n = meta.get("chunk_n")
            chunk_total = meta.get("chunk_total")
            header = f"[{label} Match {i+1}] Score: {score_str}"
            header += f" | Chapter {chapter}: {chapter_title}"
            if sec_num:
                header += f" | Section: {sec_num} {sec_title}"
            if chunk_total is not None and chunk_total > 1:
                header += f" (part {chunk_n} of {chunk_total})"

        elif source == "cmr":
            chapter = meta.get("chapter", "")
            program = meta.get("program", "")
            sec_num = meta.get("section_number", "")
            sec_title = meta.get("section_title", "")
            hierarchy_path = meta.get("hierarchy_path", "")
            chunk_n = meta.get("chunk_n")
            chunk_total = meta.get("chunk_total")
            header = f"[{label} Match {i+1}] Score: {score_str}"
            header += f" | 106 CMR {chapter} ({program})"
            if sec_num:
                header += f" | Section: {sec_num} {sec_title}"
            if hierarchy_path:
                header += f"\n  Subsection: {hierarchy_path}"
            if chunk_total is not None and chunk_total > 1:
                header += f" (part {chunk_n} of {chunk_total})"

        elif source == "cfr":
            part = meta.get("part", "")
            program = meta.get("program", "")
            sec_num = meta.get("section_number", "")
            sec_title = meta.get("section_title", "")
            hierarchy_path = meta.get("hierarchy_full_path") or meta.get("hierarchy_path", "")
            chunk_n = meta.get("chunk_n")
            chunk_total = meta.get("chunk_total")
            header = f"[{label} Match {i+1}] Score: {score_str}"
            header += f" | 7 CFR {part} ({program})"
            if sec_num:
                header += f" | Section: § {sec_num} {sec_title}"
            if hierarchy_path:
                header += f"\n  Subsection: {hierarchy_path}"
            if chunk_total is not None and chunk_total > 1:
                header += f" (part {chunk_n} of {chunk_total})"

        else:
            header = f"[{label} Match {i+1}] Score: {score_str}"

        parts.append(f"{header}\n{text}")
        if len(result["text"]) > 1000:
            parts.append("... (truncated)")
        parts.append("")

    return "\n".join(parts)
