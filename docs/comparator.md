# Comparator — FNS vs OLG Cross-Source Analysis

The comparator is a four-layer pipeline that systematically compares every FNS Handbook 310 section against OLG coverage to find matches, gaps, and conflicts.

## Workflow

```mermaid
flowchart TD
    START([FNS Sections<br/>index/fns/parsed_sections/]) --> L0

    subgraph L0 ["Layer 0: Pre-Classification"]
        L0{classify_sections<br/>Haiku API}
        L0 -->|compare| L0_PASS[Policy sections]
        L0 -->|skip/reference| L0_SKIP[Filtered out]
    end

    L0_PASS --> RAG

    subgraph L1 ["Layer 1: Triage"]
        RAG[multi_query_olg<br/>ChromaDB search<br/>rag/query.py] --> L1_CALL
        L1_CALL{run_layer1<br/>Haiku API}
        L1_CALL -->|"match (HIGH)"| L1_DONE[Accept L1 verdict]
        L1_CALL -->|"not_applicable (HIGH)"| L1_DONE
        L1_CALL -->|"partial_match / no_match<br/>or LOW/MEDIUM confidence"| ESCALATE[Escalate to L2]
    end

    ESCALATE --> ENGINE

    subgraph L2 ["Layer 2: Deep Investigation"]
        ENGINE{engine?}
        ENGINE -->|claude-code| L2_CC[run_layer2_claude_code<br/>Claude Code CLI session<br/>tools/claude_code_runner.py]
        ENGINE -->|api| L2_API[run_layer2<br/>Haiku/Sonnet API<br/>Agentic tool loop]

        L2_CC -->|"Searches OLG via<br/>python rag/query.py"| L2_RESULT
        L2_API -->|"Searches OLG via<br/>search_olg tool_use"| L2_RESULT

        L2_RESULT[Result JSON<br/>output/comparator/results/sec.json]
    end

    L2_RESULT --> L3_CHECK

    subgraph L3 ["Layer 3: CMR Cross-Check"]
        L3_CHECK{Classification?}
        L3_CHECK -->|"confirmed_gap /<br/>different_standard /<br/>procedures_missing"| CMR_SEARCH
        L3_CHECK -->|"match / partial_match /<br/>not_applicable"| SKIP_L3[Skip L3]

        CMR_SEARCH[query_cmr<br/>ChromaDB search] --> L3_CALL
        L3_CALL{run_layer3<br/>Haiku API}
        L3_CALL --> L3_RESULT[CMR context added<br/>to result JSON]
    end

    L1_DONE --> CSV
    SKIP_L3 --> CSV
    L3_RESULT --> CSV

    CSV[build_csv_row / compile_results<br/>comparison_{engine}_{timestamp}.csv]

    style L0 fill:#f0f0f0
    style L1 fill:#e8f4e8
    style L2 fill:#e8e8f4
    style L3 fill:#f4e8e8
```

## Layer Details

### Layer 0: Pre-Classification (`classify_sections`)

Batch-classifies all FNS sections before the main run. Labels each section as:
- **compare** -- Contains policy requirements to check against OLG
- **skip** -- Introductory text, definitions, or chapter headers with no testable requirements
- **reference** -- Cross-references to other sections (e.g., "See Section 512")

Output: Classification stored in memory during the run (used to filter sections for L1)

### Layer 1: Triage (`run_layer1`)

For each section that passes L0:
1. `multi_query_olg()` generates 2-3 search queries from the FNS text and searches ChromaDB (excludes TAFDC/EAEDC programs to focus on SNAP while retaining Cross-Program content)
2. Haiku classifies based on the FNS text + top OLG matches
3. HIGH confidence `match` or `not_applicable` stops here; everything else escalates to L2

Prompt: `prompts/layer1_triage.md`

### Layer 2: Deep Investigation

The most expensive layer. An agentic search loop that autonomously queries the OLG, follows cross-references, and builds a comprehensive assessment.

**Claude Code engine** (`run_layer2_claude_code` > `tools/claude_code_runner.py`):
- Spawns a Claude Code CLI session via `claude -p --output-format json --dangerously-skip-permissions`
- The session uses `python rag/query.py` to search the OLG and `Read` to check FNS cross-references
- Writes its result JSON to `output/comparator/results/{section_number}.json`
- Session ID captured for later conversation resume via `claude --resume {id}`
- Parallel execution: `--parallel N` runs N concurrent L2 sessions
- Cost: $0 marginal (subscription), ~2.5 min per section sequential, ~1 min/section at parallel 5

**API engine** (`run_layer2`):
- Haiku/Sonnet with `search_olg` and `lookup_fns_section` tools
- Agentic loop: Claude calls tools, gets results, decides next search
- Cost: ~$0.25 per section (Haiku), higher for Sonnet

Prompt: `prompts/layer2_investigation.md` (API), `prompts/layer2_claude_code.md` (CLI)

### Layer 3: CMR Cross-Check (`run_layer3`)

Only fires when L2 finds a gap or conflict:
1. `query_cmr()` searches CMR ChromaDB for relevant state regulations
2. Haiku analyzes whether the CMR supports the OLG position, requires something different, or is silent
3. Result written back into the section's result JSON

Prompt: `prompts/layer3_validation.md`

## Classification Taxonomy

| Classification | Meaning |
|---------------|---------|
| `match` | OLG adequately covers the FNS requirement |
| `partial_match` | OLG covers some aspects but has gaps |
| `not_applicable` | FNS section is QC-only, not caseworker policy |
| `confirmed_gap` | No OLG coverage for a real policy requirement |
| `different_standard` | OLG and FNS take conflicting positions |
| `policy_present_procedures_missing` | OLG has the policy but no worker procedures |

## CLI Reference

```bash
# Full comparison run (Claude Code engine)
python programs/comparator/comparator.py --chapter 10 --engine claude-code

# Parallel execution (5 concurrent L2 workers)
python programs/comparator/comparator.py --chapter 10 --engine claude-code --parallel 5

# Full comparison run (API engine)
python programs/comparator/comparator.py --chapter 10 --engine api

# Specific sections only
python programs/comparator/comparator.py --chapter 10 --sections "1013.4,1036,1044" --engine claude-code

# Windowed mode (visible console windows, for debugging)
python programs/comparator/comparator.py --chapter 10 --engine claude-code --windowed

# Pre-classify sections (Layer 0 only)
python programs/comparator/comparator.py --classify --chapter 10

# Dry run (show what would be processed)
python programs/comparator/comparator.py --chapter 10 --dry-run

# Compile result JSONs into CSV
python programs/comparator/comparator.py --compile --chapter 10

# Resume an interrupted run
python programs/comparator/comparator.py --chapter 10 --engine claude-code --resume
```

## Output Files

```
output/comparator/
├── results/                              # Per-section L2 verdicts (JSON)
│   ├── 1013.4.json                       #   Also serves as resume markers
│   ├── 1036.json                         #   L3 results stored as _layer3 key
│   └── ...
├── sessions/                             # Prompt files and batch scripts
│   ├── prompt_L2_1013.4.txt
│   └── ...
└── comparison_{engine}_{timestamp}.csv   # Final compiled report
```

## Resume Agent Conversations

When using the Claude Code engine, each L2 session gets a UUID saved in the result JSON and CSV (`session_id` column). To resume a conversation with an agent that investigated a particular section:

```bash
claude --resume "550e8400-e29b-41d4-a716-446655440000"
```

This restores the full conversation context -- all searches performed, OLG pages read, and reasoning. Useful for auditing findings or asking follow-up questions.

## Key Files

| File | Role |
|------|------|
| `programs/comparator/comparator.py` | Main comparator engine (all layers, CSV output) |
| `tools/claude_code_runner.py` | Claude Code CLI subprocess wrapper |
| `rag/query.py` | Shared search interface (OLG, FNS, CMR) |
| `prompts/domain_preamble.md` | Domain context shared across all prompts |
| `prompts/layer0_classify.md` | L0 classification prompt |
| `prompts/layer1_triage.md` | L1 triage prompt |
| `prompts/layer2_investigation.md` | L2 investigation prompt (API) |
| `prompts/layer2_claude_code.md` | L2 investigation prompt (CLI) |
| `prompts/layer3_validation.md` | L3 CMR cross-check prompt |
