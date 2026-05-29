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
            "Search public-assistance policy sources for relevant content. "
            "Available sources:\n"
            "- olg: the Online Guide (staff procedures and policy)\n"
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


def make_fetch_neighbors_tool(
    sources: list[str], *, name: str = "fetch_neighbors"
) -> dict:
    """Build a tool definition for fetching chunks adjacent to a given
    chunk_id (within the same parent page/chapter).

    Multi-source by enum like make_search_tool; OLG-only variant lives in
    FETCH_OLG_NEIGHBORS_TOOL below.
    """
    return {
        "name": name,
        "description": (
            "Fetch chunks adjacent to a specific chunk_id within the same "
            "parent page or chapter. Use this when a search result looks "
            "promising but the chunk reads as mid-thought — pulling the "
            "neighbors stitches the surrounding context together. Cheaper "
            "than fetching a whole page when you only need a little more "
            "context."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "enum": list(sources),
                    "description": "Which source the chunk belongs to",
                },
                "chunk_id": {
                    "type": "string",
                    "description": (
                        "The exact chunk_id of the anchor chunk, as shown "
                        "in search result headers (e.g., "
                        "sec__SNAP__Eligibility__Stu_Students__035)."
                    ),
                },
                "n": {
                    "type": "integer",
                    "description": "How many neighbors to fetch per side (default 1)",
                    "default": 1,
                },
                "direction": {
                    "type": "string",
                    "enum": ["prev", "next", "both"],
                    "description": (
                        "Which side(s) to fetch (default 'both'). Use "
                        "'next' when the anchor chunk trails off; 'prev' "
                        "when it picks up mid-paragraph."
                    ),
                    "default": "both",
                },
            },
            "required": ["source", "chunk_id"],
        },
    }


def make_fetch_page_tool(
    sources: list[str], *, name: str = "fetch_page"
) -> dict:
    """Build a tool definition for fetching the full text of an OLG page
    by its URL. Heavier than fetch_neighbors — use sparingly.

    Sources list is for symmetry with the other factories; today only OLG
    has URL-addressable pages.
    """
    return {
        "name": name,
        "description": (
            "Fetch all chunks of a single OLG page in reading order, "
            "reassembled into the full page text. Use this only when you "
            "need to read a whole page top-to-bottom — for example when "
            "the seed hits show fragments of a page that clearly covers "
            "the topic and you want to confirm coverage in full. Prefer "
            "fetch_neighbors when you only need a little more context "
            "around a specific hit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "enum": list(sources),
                    "description": "Which source the page belongs to (currently OLG-only)",
                },
                "url": {
                    "type": "string",
                    "description": (
                        "The exact URL of the page, as shown in search "
                        "result headers."
                    ),
                },
            },
            "required": ["source", "url"],
        },
    }


SEARCH_POLICY_TOOL = make_search_tool(["olg", "cmr", "fns", "cfr"])
SEARCH_OLG_TOOL = make_search_tool(["olg"], name="search_olg")
FETCH_OLG_NEIGHBORS_TOOL = make_fetch_neighbors_tool(["olg"], name="fetch_olg_neighbors")
FETCH_OLG_PAGE_TOOL = make_fetch_page_tool(["olg"], name="fetch_olg_page")
