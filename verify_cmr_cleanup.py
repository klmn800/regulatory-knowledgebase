"""
Pre-embedding verification checklist for CMR cleanup.
Checks parser output, chunker output, and regression items.
"""
import json
import re
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent
PARSED_DIR = PROJECT_ROOT / "index" / "cmr" / "parsed_sections"
SECTION_CHUNKS_FILE = PROJECT_ROOT / "index" / "cmr" / "section_chunks.json"
CHAPTER_CHUNKS_FILE = PROJECT_ROOT / "index" / "cmr" / "chapter_chunks.json"

MIN_CHUNK_SIZE = 200

results = []  # list of (section, check_name, pass_bool, detail)

def record(section, name, passed, detail=""):
    results.append((section, name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}")
    if detail:
        for line in detail.strip().split("\n"):
            print(f"         {line}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 5a. PARSER OUTPUT VERIFICATION
# ============================================================
print("=" * 70)
print("5a. PARSER OUTPUT VERIFICATION")
print("=" * 70)

# 1. Check 4 previously broken titles
print("\n--- Check 1: Previously broken titles ---")
broken_title_checks = [
    ("cmr703_703_192.json", "EAEDC Medical Standards"),
    ("cmr703_703_720.json", "EAEDC Exemptions"),
    ("cmr366_366_115.json", "Unclear Information"),
    ("cmr367_367_825.json", "Results of an ADH - Notification"),
]
for filename, expected_title in broken_title_checks:
    path = PARSED_DIR / filename
    if not path.exists():
        record("5a.1", f"{filename} exists", False, f"File not found: {path}")
        continue
    data = load_json(path)
    actual_title = data.get("section_title", "")
    passed = actual_title == expected_title
    detail = "" if passed else f"Expected: '{expected_title}'\n  Actual: '{actual_title}'"
    record("5a.1", f"{filename} title = '{expected_title}'", passed, detail)

# 2. Check 3 no-colon headings still present
print("\n--- Check 2: No-colon headings still present ---")
no_colon_checks = [
    ("cmr364_364_360.json", "Child Support Income Counted in the Month after Receipt"),
    ("cmr703_703_300.json", "TAFDC Relationship and Living Arrangement"),
    ("cmr706_706_110.json", "Inquiries"),
]
for filename, expected_title in no_colon_checks:
    path = PARSED_DIR / filename
    if not path.exists():
        record("5a.2", f"{filename} exists", False, f"File not found: {path}")
        continue
    data = load_json(path)
    actual_title = data.get("section_title", "")
    passed = actual_title == expected_title
    detail = "" if passed else f"Expected: '{expected_title}'\n  Actual: '{actual_title}'"
    record("5a.2", f"{filename} title = '{expected_title}'", passed, detail)

# 3. Total section count
print("\n--- Check 3: Total section count ---")
json_files = list(PARSED_DIR.glob("*.json"))
section_count = len(json_files)
passed = section_count == 592
detail = f"Found {section_count} JSON files (expected 592)"
record("5a.3", "Total section count = 592", passed, detail)

# 4. Titles starting with lowercase suspect words
print("\n--- Check 4: Titles starting with lowercase suspect words ---")
suspect_prefixes = ["or ", "and ", "are ", "the ", "in ", "to ", "for ", "of ", "is ", "has ", "was ", "were ", "that ", "which ", "if "]
suspect_titles = []
for jf in sorted(json_files):
    data = load_json(jf)
    title = data.get("section_title", "")
    for prefix in suspect_prefixes:
        if title.lower().startswith(prefix) and title[0].islower():
            suspect_titles.append((jf.name, title))
            break

passed = len(suspect_titles) == 0
detail = f"Found {len(suspect_titles)} suspect titles"
if suspect_titles:
    for fname, title in suspect_titles[:20]:
        detail += f"\n  {fname}: '{title}'"
    if len(suspect_titles) > 20:
        detail += f"\n  ... and {len(suspect_titles) - 20} more"
record("5a.4", "No titles starting with lowercase conjunctions/prepositions", passed, detail)

# 5. Titles > 80 chars
print("\n--- Check 5: Titles > 80 chars ---")
long_titles = []
for jf in sorted(json_files):
    data = load_json(jf)
    title = data.get("section_title", "")
    if len(title) > 80:
        long_titles.append((jf.name, data.get("section_number", ""), title, len(title)))

detail = f"Found {len(long_titles)} titles > 80 chars"
if long_titles:
    for fname, secnum, title, length in long_titles:
        detail += f"\n  {secnum} ({length} chars): '{title}'"
# This is informational — not a hard pass/fail, but flag if many
passed = len(long_titles) <= 5  # allow a few
record("5a.5", f"Titles > 80 chars: {len(long_titles)} (threshold <= 5)", passed, detail)


# ============================================================
# 5b. CHUNKER OUTPUT VERIFICATION
# ============================================================
print("\n" + "=" * 70)
print("5b. CHUNKER OUTPUT VERIFICATION")
print("=" * 70)

chunks = load_json(SECTION_CHUNKS_FILE)
print(f"\nLoaded {len(chunks)} chunks from section_chunks.json")

# 1. Zero chunks under MIN_CHUNK_SIZE
print("\n--- Check 1: No chunks under MIN_CHUNK_SIZE (200 chars) ---")
short_chunks = []
for c in chunks:
    text = c.get("text", "")
    if len(text) < MIN_CHUNK_SIZE:
        short_chunks.append((c["chunk_id"], len(text), text[:100]))

passed = len(short_chunks) == 0
detail = f"Found {len(short_chunks)} chunks < {MIN_CHUNK_SIZE} chars"
if short_chunks:
    for cid, length, preview in short_chunks[:10]:
        detail += f"\n  {cid}: {length} chars — '{preview}...'"
    if len(short_chunks) > 10:
        detail += f"\n  ... and {len(short_chunks) - 10} more"
record("5b.1", f"Zero chunks under {MIN_CHUNK_SIZE} chars", passed, detail)

# 2. Zero chunks with "(continued)" in section_title
print("\n--- Check 2: No '(continued)' in section_title metadata ---")
continued_chunks = []
for c in chunks:
    st = c.get("metadata", {}).get("section_title", "")
    if "(continued)" in st.lower():
        continued_chunks.append((c["chunk_id"], st))

passed = len(continued_chunks) == 0
detail = f"Found {len(continued_chunks)} chunks with '(continued)' in section_title"
if continued_chunks:
    for cid, st in continued_chunks[:10]:
        detail += f"\n  {cid}: '{st}'"
record("5b.2", "Zero chunks with '(continued)' in section_title", passed, detail)

# 3. Multi-chunk sections: chunks 2+ have non-empty hierarchy_path
print("\n--- Check 3: Multi-chunk sections have hierarchy_path on chunks 2+ ---")
missing_hierarchy = []
for c in chunks:
    meta = c.get("metadata", {})
    chunk_n = meta.get("chunk_n", 1)
    chunk_total = meta.get("chunk_total", 1)
    hierarchy_path = meta.get("hierarchy_path", "")
    if chunk_total > 1 and chunk_n > 1 and not hierarchy_path:
        missing_hierarchy.append((c["chunk_id"], chunk_n, chunk_total))

passed = len(missing_hierarchy) == 0
detail = f"Found {len(missing_hierarchy)} multi-chunk secondary chunks missing hierarchy_path"
if missing_hierarchy:
    for cid, cn, ct in missing_hierarchy[:10]:
        detail += f"\n  {cid}: chunk {cn}/{ct}"
    if len(missing_hierarchy) > 10:
        detail += f"\n  ... and {len(missing_hierarchy) - 10} more"
record("5b.3", "All multi-chunk secondary chunks have hierarchy_path", passed, detail)

# 4. chunk_n and chunk_total consistency
print("\n--- Check 4: chunk_n/chunk_total consistency ---")
sections_chunks = defaultdict(list)
for c in chunks:
    meta = c.get("metadata", {})
    sec_num = meta.get("section_number", "unknown")
    chunk_n = meta.get("chunk_n", 0)
    chunk_total = meta.get("chunk_total", 0)
    sections_chunks[sec_num].append((chunk_n, chunk_total, c["chunk_id"]))

inconsistent = []
for sec_num, chunk_list in sorted(sections_chunks.items()):
    chunk_list.sort(key=lambda x: x[0])
    # All should have same chunk_total
    totals = set(ct for _, ct, _ in chunk_list)
    if len(totals) > 1:
        inconsistent.append((sec_num, f"Mixed chunk_totals: {totals}"))
        continue
    expected_total = totals.pop()
    # chunk_n should be 1..chunk_total consecutively
    actual_ns = [cn for cn, _, _ in chunk_list]
    expected_ns = list(range(1, expected_total + 1))
    if actual_ns != expected_ns:
        inconsistent.append((sec_num, f"Expected chunk_ns {expected_ns}, got {actual_ns}"))
    # Count should match chunk_total
    if len(chunk_list) != expected_total:
        inconsistent.append((sec_num, f"Expected {expected_total} chunks, found {len(chunk_list)}"))

passed = len(inconsistent) == 0
detail = f"Checked {len(sections_chunks)} sections"
if inconsistent:
    detail += f"\n  Found {len(inconsistent)} inconsistencies:"
    for sec_num, msg in inconsistent[:15]:
        detail += f"\n  {sec_num}: {msg}"
    if len(inconsistent) > 15:
        detail += f"\n  ... and {len(inconsistent) - 15} more"
record("5b.4", "chunk_n/chunk_total are consecutive and consistent", passed, detail)

# 5. Chunk IDs are per-section (not globally numbered)
print("\n--- Check 5: Chunk IDs are per-section ---")
# Chunk IDs should follow pattern cmr_sec_XXX_YYY__NNN
bad_ids = []
id_pattern = re.compile(r"^cmr_sec_\d+_\d+[a-zA-Z]?__\d{3}$")
for c in chunks:
    cid = c["chunk_id"]
    if not id_pattern.match(cid):
        bad_ids.append(cid)

# Also check that the suffix __NNN restarts per section
section_id_bases = defaultdict(list)
for c in chunks:
    cid = c["chunk_id"]
    parts = cid.rsplit("__", 1)
    if len(parts) == 2:
        base, suffix = parts
        section_id_bases[base].append(int(suffix))

non_zero_start = []
for base, suffixes in section_id_bases.items():
    suffixes.sort()
    if suffixes[0] != 0:
        non_zero_start.append((base, suffixes))

passed_pattern = len(bad_ids) == 0
passed_restart = len(non_zero_start) == 0
passed = passed_pattern and passed_restart

detail = ""
if bad_ids:
    detail += f"Bad ID patterns: {bad_ids[:5]}"
if non_zero_start:
    detail += f"\nIDs not starting at __000: {[(b, s) for b, s in non_zero_start[:5]]}"
if not detail:
    detail = f"All {len(chunks)} chunk IDs follow per-section pattern cmr_sec_XXX_YYY__NNN"
record("5b.5", "Chunk IDs are per-section (cmr_sec_XXX_YYY__NNN)", passed, detail)

# 6. Total chunk count
print("\n--- Check 6: Total chunk count ---")
record("5b.6", f"Total chunk count: {len(chunks)}", True, f"{len(chunks)} section-level chunks")

# 7. Spot-checks
print("\n--- Check 7: Spot-checks ---")

# 7a. 703.192: should have top-level labels (A) through (O) and correct title
print("  7a. Section 703.192")
sec_703_192_chunks = [c for c in chunks if c["metadata"].get("section_number") == "703.192"]
if sec_703_192_chunks:
    # Check title in prefix
    all_text = " ".join(c["text"] for c in sec_703_192_chunks)
    has_correct_title = "EAEDC Medical Standards" in sec_703_192_chunks[0]["text"]

    # Check for (A) through (O) labels
    expected_labels = [f"({chr(65 + i)})" for i in range(15)]  # (A) through (O)
    found_labels = [label for label in expected_labels if label in all_text]
    has_all_labels = len(found_labels) == 15

    detail = f"{len(sec_703_192_chunks)} chunks, title in prefix: {has_correct_title}"
    detail += f"\n  Labels found: {len(found_labels)}/15 — {found_labels}"
    if not has_all_labels:
        missing = [l for l in expected_labels if l not in found_labels]
        detail += f"\n  Missing: {missing}"
    passed = has_correct_title and has_all_labels
    record("5b.7a", "703.192: correct title + labels (A)-(O)", passed, detail)
else:
    record("5b.7a", "703.192: found in chunks", False, "No chunks found for 703.192")

# 7b. 363.140: should have (A) through (I) labels
print("  7b. Section 363.140")
sec_363_140_chunks = [c for c in chunks if c["metadata"].get("section_number") == "363.140"]
if sec_363_140_chunks:
    all_text = " ".join(c["text"] for c in sec_363_140_chunks)
    expected_labels = [f"({chr(65 + i)})" for i in range(9)]  # (A) through (I)
    found_labels = [label for label in expected_labels if label in all_text]
    has_all_labels = len(found_labels) == 9
    detail = f"{len(sec_363_140_chunks)} chunks, labels found: {len(found_labels)}/9 — {found_labels}"
    if not has_all_labels:
        missing = [l for l in expected_labels if l not in found_labels]
        detail += f"\n  Missing: {missing}"
    passed = has_all_labels
    record("5b.7b", "363.140: labels (A)-(I)", passed, detail)
else:
    record("5b.7b", "363.140: found in chunks", False, "No chunks found for 363.140")

# 7c. Find a small 2-chunk section
print("  7c. Small 2-chunk section")
two_chunk_sections = [(sec, clist) for sec, clist in sections_chunks.items() if len(clist) == 2]
if two_chunk_sections:
    example_sec = two_chunk_sections[0][0]
    example_chunks = [c for c in chunks if c["metadata"].get("section_number") == example_sec]
    detail = f"Example: {example_sec} — {len(example_chunks)} chunks"
    for ec in example_chunks:
        detail += f"\n  {ec['chunk_id']}: {len(ec['text'])} chars, hierarchy='{ec['metadata'].get('hierarchy_path', '')}'"
    record("5b.7c", f"2-chunk section found: {example_sec}", True, detail)
else:
    record("5b.7c", "2-chunk section found", False, "No 2-chunk sections found")

# 7d. Find a no-split (1-chunk) section
print("  7d. No-split (1-chunk) section")
one_chunk_sections = [(sec, clist) for sec, clist in sections_chunks.items() if len(clist) == 1]
if one_chunk_sections:
    example_sec = one_chunk_sections[0][0]
    example_chunks = [c for c in chunks if c["metadata"].get("section_number") == example_sec]
    ec = example_chunks[0]
    detail = f"Example: {example_sec} — {ec['chunk_id']}: {len(ec['text'])} chars"
    detail += f"\n  hierarchy_path='{ec['metadata'].get('hierarchy_path', '')}'"
    record("5b.7d", f"1-chunk section found: {example_sec}", True, detail)
else:
    record("5b.7d", "1-chunk section found", False, "No 1-chunk sections found")

# 7e. Section with no Level 1 markers (only Level 2)
print("  7e. Section with no Level 1 markers")
# Level 1 markers are (A), (B), etc. Level 2 are (1), (2), etc.
level1_pattern = re.compile(r"\n\([A-Z]\)")
level2_pattern = re.compile(r"\n\(\d+\)")
no_level1_sections = []
for sec_num, chunk_list in sections_chunks.items():
    sec_chunks = [c for c in chunks if c["metadata"].get("section_number") == sec_num]
    all_text = "\n".join(c["text"] for c in sec_chunks)
    has_l1 = bool(level1_pattern.search(all_text))
    has_l2 = bool(level2_pattern.search(all_text))
    if not has_l1 and has_l2 and len(chunk_list) > 1:
        no_level1_sections.append(sec_num)

if no_level1_sections:
    example_sec = no_level1_sections[0]
    example_chunks = [c for c in chunks if c["metadata"].get("section_number") == example_sec]
    detail = f"Example: {example_sec} — {len(example_chunks)} chunks (no Level 1 markers, has Level 2)"
    for ec in example_chunks[:3]:
        hp = ec["metadata"].get("hierarchy_path", "")
        detail += f"\n  {ec['chunk_id']}: hierarchy='{hp}'"
    record("5b.7e", f"Section with only Level 2 markers found: {example_sec}", True, detail)
else:
    # Try to find any section that has (1), (2) but no (A), (B) even if single chunk
    for sec_num, chunk_list in sections_chunks.items():
        sec_chunks = [c for c in chunks if c["metadata"].get("section_number") == sec_num]
        all_text = "\n".join(c["text"] for c in sec_chunks)
        has_l1 = bool(level1_pattern.search(all_text))
        has_l2 = bool(level2_pattern.search(all_text))
        if not has_l1 and has_l2:
            no_level1_sections.append(sec_num)
    if no_level1_sections:
        example_sec = no_level1_sections[0]
        detail = f"Example: {example_sec} (single chunk, no Level 1, has Level 2)"
        record("5b.7e", f"Section with only Level 2 markers: {example_sec}", True, detail)
    else:
        record("5b.7e", "Section with only Level 2 markers", False, "None found")


# ============================================================
# 5c. REGRESSION CHECK
# ============================================================
print("\n" + "=" * 70)
print("5c. REGRESSION CHECK")
print("=" * 70)

# 1. Single-chunk sections should have no hierarchy_path in prefix
print("\n--- Check 1: Single-chunk sections have no hierarchy_path ---")
single_with_hierarchy = []
for c in chunks:
    meta = c.get("metadata", {})
    if meta.get("chunk_total", 1) == 1:
        hp = meta.get("hierarchy_path", "")
        if hp:
            single_with_hierarchy.append((c["chunk_id"], hp))

passed = len(single_with_hierarchy) == 0
detail = f"Found {len(single_with_hierarchy)} single-chunk sections with non-empty hierarchy_path"
if single_with_hierarchy:
    for cid, hp in single_with_hierarchy[:10]:
        detail += f"\n  {cid}: '{hp}'"
record("5c.1", "Single-chunk sections have empty hierarchy_path", passed, detail)

# 2. Chapter-level documents present (18 in chapter_chunks.json)
print("\n--- Check 2: Chapter-level documents ---")
chapter_chunks = load_json(CHAPTER_CHUNKS_FILE)
passed = len(chapter_chunks) == 18
detail = f"Found {len(chapter_chunks)} chapter-level documents (expected 18)"
if chapter_chunks:
    chapter_ids = [c["chunk_id"] for c in chapter_chunks]
    detail += f"\n  IDs: {', '.join(sorted(chapter_ids))}"
record("5c.2", "18 chapter-level documents in chapter_chunks.json", passed, detail)

# 3. Metadata fields are ChromaDB-compatible (no None values)
print("\n--- Check 3: ChromaDB-compatible metadata ---")
none_metadata = []
invalid_types = []
for c in chunks:
    meta = c.get("metadata", {})
    for key, value in meta.items():
        if value is None:
            none_metadata.append((c["chunk_id"], key))
        elif not isinstance(value, (str, int, float, bool)):
            invalid_types.append((c["chunk_id"], key, type(value).__name__, repr(value)[:50]))

# Also check chapter chunks
for c in chapter_chunks:
    meta = c.get("metadata", {})
    for key, value in meta.items():
        if value is None:
            none_metadata.append((c["chunk_id"], key))
        elif not isinstance(value, (str, int, float, bool)):
            invalid_types.append((c["chunk_id"], key, type(value).__name__, repr(value)[:50]))

passed_none = len(none_metadata) == 0
passed_types = len(invalid_types) == 0
passed = passed_none and passed_types

detail = ""
if none_metadata:
    detail += f"None values found in {len(none_metadata)} metadata fields:"
    for cid, key in none_metadata[:10]:
        detail += f"\n  {cid}.{key} = None"
    if len(none_metadata) > 10:
        detail += f"\n  ... and {len(none_metadata) - 10} more"
if invalid_types:
    detail += f"\nInvalid types in {len(invalid_types)} metadata fields:"
    for cid, key, tname, val in invalid_types[:10]:
        detail += f"\n  {cid}.{key} = {tname}: {val}"
if not detail:
    detail = f"All metadata fields are ChromaDB-compatible (str/int/float/bool) across {len(chunks)} section + {len(chapter_chunks)} chapter chunks"
record("5c.3", "Metadata ChromaDB-compatible (no None, valid types)", passed, detail)


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

total = len(results)
passed_count = sum(1 for _, _, p, _ in results if p)
failed_count = total - passed_count

print(f"\nTotal checks: {total}")
print(f"  PASSED: {passed_count}")
print(f"  FAILED: {failed_count}")

if failed_count > 0:
    print("\nFailed checks:")
    for section, name, passed, detail in results:
        if not passed:
            print(f"  [{section}] {name}")
            if detail:
                for line in detail.strip().split("\n"):
                    print(f"           {line}")

print(f"\nVerdict: {'ALL CHECKS PASSED - safe to re-embed' if failed_count == 0 else 'FIX ISSUES BEFORE RE-EMBEDDING'}")
