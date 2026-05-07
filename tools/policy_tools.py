"""
Anthropic tool definitions for policy search and lookup.

Single source of truth for the tools every agentic-loop callsite uses.
Synthesis imports `SEARCH_POLICY_TOOL` and `make_search_tool`; comparator
and QC migrate next.

Per decision #7 (cross-cutting), tool descriptions stay neutral — they
describe what the tool DOES, not what each caller wants from it. Caller
intent (e.g., "focus on procedures gaps") lives in the caller's prompt.
"""


def make_search_tool(sources: list[str], *, name: str = "search_policy") -> dict:
    """Build a fresh Anthropic tool definition with the source enum
    restricted to `sources`.

    The factory returns a fresh dict each call — no shared mutable state,
    so callers can't accidentally mutate a shared definition.
    """
    return {
        "name": name,
        "description": (
            "Search Massachusetts DTA policy sources for relevant content. "
            "Available sources:\n"
            "- olg: DTA Online Guide (staff procedures and policy)\n"
            "- cmr: Code of Massachusetts Regulations, Title 106 (state law)\n"
            "- fns: FNS Handbook 310 (federal SNAP QC standard)\n"
            "- cfr: 7 CFR Parts 271-275, 280, 292 (federal SNAP regulations)\n\n"
            "Try different query angles: specific policy terms, BEACON procedures, "
            "broader topic areas, synonyms, related topics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "enum": list(sources),
                    "description": "Which source to search",
                },
                "query": {
                    "type": "string",
                    "description": "Natural language search query",
                },
            },
            "required": ["source", "query"],
        },
    }


def make_lookup_fns_section_tool() -> dict:
    """Build a fresh Anthropic tool definition for the FNS section lookup
    used by comparator L2 to follow cross-references."""
    return {
        "name": "lookup_fns_section",
        "description": (
            "Look up a specific FNS Handbook 310 section by its number. "
            "Use this when the section you're analyzing cross-references "
            "another FNS section (e.g., 'See Section 512'). Returns the "
            "full text of that section."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "section_number": {
                    "type": "string",
                    "description": "The FNS section number to look up (e.g., '512', '1021.1')",
                },
            },
            "required": ["section_number"],
        },
    }


SEARCH_POLICY_TOOL = make_search_tool(["olg", "cmr", "fns", "cfr"])
SEARCH_OLG_TOOL = make_search_tool(["olg"], name="search_olg")
