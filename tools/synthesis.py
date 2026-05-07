"""
Policy synthesis agent — answers policy questions using multi-source RAG.

Standard mode: pre-fetches results, single Claude call to synthesize.
Deep mode: agentic loop with search tools for iterative retrieval.

Usage:
    python agents/synthesis.py "What are the income limits for SNAP?"
    python agents/synthesis.py "expedited benefits process" --sources olg cmr
    python agents/synthesis.py "shelter deduction" --deep
"""

import argparse
import configparser
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = PROJECT_ROOT / "prompts"
CONFIG_FILE = PROJECT_ROOT / "config.ini"

sys.path.insert(0, str(PROJECT_ROOT))
from rag.query import create_client, search_with_client
from tools.cost_tracker import MODEL_PRICING, calculate_cost
from tools.policy_tools import SEARCH_POLICY_TOOL, make_search_tool
from tools.result_formatters import SOURCE_LABELS, format_results_for_prompt
from tools.retry import with_rate_limit_retry


# ============================================================
# CONFIGURATION
# ============================================================


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    return config


def load_prompt(name: str, with_preamble: bool = False) -> str:
    filepath = PROMPTS_DIR / f"{name}.md"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if with_preamble:
        preamble_path = PROMPTS_DIR / "domain_preamble.md"
        if preamble_path.exists():
            with open(preamble_path, "r", encoding="utf-8") as f:
                preamble = f.read()
            content = preamble + "\n\n---\n\n" + content
    return content


# ============================================================
# RESULT TYPES
# ============================================================

@dataclass
class SynthesisResult:
    answer: str
    evidence: dict = field(default_factory=dict)  # source -> list of results
    search_queries: list = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    duration_seconds: float = 0.0
    model: str = ""
    # On API failure: human-readable message. On success: None.
    # `answer` still carries the same "Synthesis failed due to ..." text for
    # backwards compat, but new callers should branch on `error` first.
    error: str | None = None


# ============================================================
# SEARCH CLIENTS
# ============================================================

_search_clients = {}


def get_search_clients(source: str) -> dict:
    """Get or create search clients for a source."""
    if source not in _search_clients:
        _search_clients[source] = create_client(source=source)
    return _search_clients[source]


def do_search(source: str, query: str, top_n: int = 5,
              programs: list[str] | None = None,
              program: str | None = None,
              exclude_programs: list[str] | None = None) -> dict:
    """Execute a search against a source. Returns query.py response dict."""
    clients = get_search_clients(source)
    return search_with_client(
        query=query,
        clients=clients,
        collection="sections",
        programs=programs,
        program=program,
        exclude_programs=exclude_programs,
        top_n=top_n,
        threshold=0.0,
    )


# ============================================================
# STANDARD MODE (single Claude call)
# ============================================================

def run_standard(
    question: str,
    sources: list[str],
    programs_by_source: dict[str, list[str]] | None,
    program: str | None,
    exclude_programs: list[str] | None,
    config: configparser.ConfigParser,
    prompt_name: str = "synthesis",
) -> SynthesisResult:
    """Pre-fetch results from all sources, single Claude call to synthesize."""
    start = time.time()

    model = config.get("synthesis", "model", fallback="claude-sonnet-4-5-20250929")
    max_tokens = config.getint("synthesis", "max_tokens", fallback=1500)
    results_per_search = config.getint("synthesis", "results_per_search", fallback=5)

    system_prompt = load_prompt(prompt_name, with_preamble=True)
    api_key = config.get("api", "anthropic_api_key")
    client = anthropic.Anthropic(api_key=api_key)

    # Pre-fetch results from all requested sources
    all_evidence = {}
    context_parts = []
    search_queries = []

    for source in sources:
        src_programs = (programs_by_source or {}).get(source)
        print(f"  Searching {SOURCE_LABELS.get(source, source)}...", end="", flush=True)
        response = do_search(source, question, top_n=results_per_search,
                             programs=src_programs,
                             program=program, exclude_programs=exclude_programs)
        all_evidence[source] = response["results"]
        search_queries.append(f"{source}: {question}")

        formatted = format_results_for_prompt(response["results"], source)
        context_parts.append(f"=== {SOURCE_LABELS.get(source, source)} Results ===\n{formatted}")
        print(f" {len(response['results'])} results")

    context = "\n\n".join(context_parts)

    user_message = (
        f"## Question\n{question}\n\n"
        f"## Search Results\n{context}\n\n"
        f"Answer the question based on the search results above."
    )

    print("  Synthesizing...", end="", flush=True)

    @with_rate_limit_retry()
    def _do_synthesis_call():
        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

    try:
        response = _do_synthesis_call()
    except anthropic.APIError as e:
        print(f" [API error: {e}]")
        return SynthesisResult(
            answer=f"Synthesis failed due to API error: {e}",
            evidence=all_evidence,
            search_queries=search_queries,
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            duration_seconds=time.time() - start,
            model=model,
            error=str(e),
        )
    print(" done")

    answer = response.content[0].text.strip()
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = calculate_cost(model, input_tokens, output_tokens)

    return SynthesisResult(
        answer=answer,
        evidence=all_evidence,
        search_queries=search_queries,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost,
        duration_seconds=time.time() - start,
        model=model,
    )


# ============================================================
# DEEP MODE (agentic loop with search tools)
# ============================================================

def run_deep(
    question: str,
    sources: list[str],
    programs_by_source: dict[str, list[str]] | None,
    program: str | None,
    exclude_programs: list[str] | None,
    config: configparser.ConfigParser,
    prompt_name: str = "synthesis",
) -> SynthesisResult:
    """Agentic loop — Claude can search iteratively across sources."""
    start = time.time()

    model = config.get("synthesis", "model", fallback="claude-sonnet-4-5-20250929")
    max_tokens = config.getint("synthesis", "max_tokens", fallback=1500)
    max_searches = config.getint("synthesis", "max_searches", fallback=8)
    results_per_search = config.getint("synthesis", "results_per_search", fallback=5)
    max_turns = 15

    system_prompt = load_prompt(prompt_name, with_preamble=True)
    api_key = config.get("api", "anthropic_api_key")
    client = anthropic.Anthropic(api_key=api_key)

    # Pre-fetch initial results (same as standard)
    all_evidence = {}
    context_parts = []
    search_queries = []

    for source in sources:
        src_programs = (programs_by_source or {}).get(source)
        print(f"  Searching {SOURCE_LABELS.get(source, source)}...", end="", flush=True)
        response = do_search(source, question, top_n=results_per_search,
                             programs=src_programs,
                             program=program, exclude_programs=exclude_programs)
        all_evidence[source] = response["results"]
        search_queries.append(f"{source}: {question}")

        formatted = format_results_for_prompt(response["results"], source)
        context_parts.append(f"=== {SOURCE_LABELS.get(source, source)} Results ===\n{formatted}")
        print(f" {len(response['results'])} results")

    context = "\n\n".join(context_parts)

    # Restrict the tool's source enum to only the requested sources
    tool = make_search_tool(sources)

    user_message = (
        f"## Question\n{question}\n\n"
        f"## Initial Search Results\n{context}\n\n"
        f"Answer the question. You have a search tool available to look for "
        f"additional information if the initial results are insufficient. "
        f"You have a budget of {max_searches} additional searches."
    )

    messages = [{"role": "user", "content": user_message}]
    total_input = 0
    total_output = 0
    searches_performed = 0

    print("  Deep analysis", end="", flush=True)

    @with_rate_limit_retry()
    def _do_turn_call():
        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
            tools=[tool],
        )

    for turn in range(max_turns):
        try:
            resp = _do_turn_call()
        except anthropic.APIError as e:
            print(f" [API error: {e}]")
            return SynthesisResult(
                answer=f"Synthesis failed due to API error: {e}",
                evidence=all_evidence,
                search_queries=search_queries,
                input_tokens=total_input,
                output_tokens=total_output,
                cost=calculate_cost(model, total_input, total_output),
                duration_seconds=time.time() - start,
                model=model,
                error=str(e),
            )
        total_input += resp.usage.input_tokens
        total_output += resp.usage.output_tokens

        # Extract any text from the response
        answer_text = ""
        for block in resp.content:
            if hasattr(block, "text") and block.text.strip():
                answer_text = block.text.strip()

        if resp.stop_reason == "tool_use":
            tool_results = []

            for block in resp.content:
                if block.type == "tool_use" and block.name == "search_policy":
                    source = block.input.get("source", "olg")
                    query = block.input.get("query", "")

                    if searches_performed >= max_searches:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": (
                                f"Search budget exhausted ({searches_performed} "
                                f"searches used). Please provide your final "
                                f"answer now based on all results seen."
                            ),
                        })
                        continue

                    searches_performed += 1
                    search_queries.append(f"{source}: {query}")
                    print(".", end="", flush=True)

                    search_response = do_search(
                        source, query,
                        top_n=results_per_search,
                        programs=(programs_by_source or {}).get(source),
                        program=program,
                        exclude_programs=exclude_programs,
                    )

                    # Accumulate evidence
                    if source not in all_evidence:
                        all_evidence[source] = []
                    all_evidence[source].extend(search_response["results"])

                    formatted = format_results_for_prompt(
                        search_response["results"], source
                    )
                    remaining = max_searches - searches_performed
                    formatted += f"\n\n[{remaining} searches remaining]"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": formatted,
                    })

            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": tool_results})
            continue

        # Not tool_use — Claude is done
        print(" done")
        cost = calculate_cost(model, total_input, total_output)

        return SynthesisResult(
            answer=answer_text,
            evidence=all_evidence,
            search_queries=search_queries,
            input_tokens=total_input,
            output_tokens=total_output,
            cost=cost,
            duration_seconds=time.time() - start,
            model=model,
        )

    # Max turns exhausted
    print(" (max turns reached)")
    return SynthesisResult(
        answer=answer_text or "Analysis incomplete — maximum turns reached.",
        evidence=all_evidence,
        search_queries=search_queries,
        input_tokens=total_input,
        output_tokens=total_output,
        cost=calculate_cost(model, total_input, total_output),
        duration_seconds=time.time() - start,
        model=model,
    )


# ============================================================
# PUBLIC API
# ============================================================

def run_synthesis(
    question: str,
    sources: list[str] | None = None,
    programs_by_source: dict[str, list[str]] | None = None,
    program: str | None = None,
    exclude_programs: list[str] | None = None,
    deep: bool = False,
    max_searches: int | None = None,
    prompt_name: str = "synthesis",
    config_overrides: dict | None = None,
) -> SynthesisResult:
    """
    Answer a policy question by searching and synthesizing across sources.

    Args:
        question: Natural language policy question.
        sources: Which sources to search (default: ["olg"]).
        programs_by_source: Per-source program filter, e.g.
            {"olg": ["SNAP", "TAFDC"], "cmr": ["SNAP"]}. Each source uses
            its own list. Sources without an entry are unfiltered.
        program: Single-program shorthand applied to ALL sources (legacy).
        exclude_programs: Exclude these programs from ALL sources (legacy).
        deep: If True, use agentic loop with iterative search.
        max_searches: Override max search budget for deep mode.
        prompt_name: Which prompt file to use (default: "synthesis").
        config_overrides: Dict of synthesis config overrides (e.g. max_tokens).
    """
    if sources is None:
        sources = ["olg"]

    config = load_config()

    if max_searches is not None:
        config.set("synthesis", "max_searches", str(max_searches))

    if config_overrides:
        for key, value in config_overrides.items():
            config.set("synthesis", key, str(value))

    if deep:
        return run_deep(question, sources, programs_by_source,
                        program, exclude_programs, config,
                        prompt_name=prompt_name)
    else:
        return run_standard(question, sources, programs_by_source,
                            program, exclude_programs, config,
                            prompt_name=prompt_name)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Policy synthesis agent — answer policy questions using multi-source RAG"
    )
    parser.add_argument("question", help="Policy question to answer")
    parser.add_argument(
        "--sources", nargs="+", default=["olg"],
        choices=["olg", "cmr", "fns", "cfr"],
        help="Sources to search (default: olg)"
    )
    parser.add_argument(
        "--program", "-p", default=None,
        help="Filter by program (SNAP, TAFDC, EAEDC)"
    )
    parser.add_argument(
        "--deep", action="store_true",
        help="Use agentic deep analysis with iterative search"
    )
    parser.add_argument(
        "--max-searches", type=int, default=None,
        help="Max additional searches in deep mode"
    )
    args = parser.parse_args()

    print(f"\nQuestion: {args.question}")
    print(f"Sources: {', '.join(args.sources)}")
    print(f"Mode: {'deep' if args.deep else 'standard'}")
    if args.program:
        print(f"Program: {args.program}")
    print()

    result = run_synthesis(
        question=args.question,
        sources=args.sources,
        program=args.program,
        deep=args.deep,
        max_searches=args.max_searches,
    )

    print("\n" + "=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(result.answer)
    print("\n" + "-" * 60)
    print(f"Model: {result.model}")
    print(f"Tokens: {result.input_tokens:,} in / {result.output_tokens:,} out")
    print(f"Cost: ${result.cost:.4f}")
    print(f"Duration: {result.duration_seconds:.1f}s")
    print(f"Searches: {len(result.search_queries)}")
    for q in result.search_queries:
        print(f"  - {q}")


if __name__ == "__main__":
    main()
