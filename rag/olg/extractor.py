"""
HAR TOC URL Extractor (with hierarchy) for DTA Policy Online Guide

Reads a HAR file exported from Chrome DevTools, finds all the TOC
JavaScript responses, reconstructs the full chapter/subchapter tree
structure, and outputs two files:

  1. policy_urls.txt        - flat list of URLs (same as before)
  2. policy_toc.json        - full hierarchical TOC with chapters,
                              subchapters, and pages nested properly

The TOC JSON preserves the book/chapter structure so downstream
tools (like a RAG pipeline) know which chapter and subchapter
each page belongs to.

Usage:
    1. Place your .har file in the same directory as this script
    2. Update HAR_FILENAME below if your file has a different name
    3. Run: python har_url_extractor.py
"""

import json
import re
from pathlib import Path

# ============================================================
# CONFIGURATION - Update these if needed
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = PROJECT_ROOT / "index" / "olg"

HAR_FILENAME = str(PROJECT_ROOT / "raw" / "eohhs.ehs.state.ma.us.har")

BASE_URL = (
    "https://eohhs.ehs.state.ma.us"
    "/DTA/PolicyOnline/BEACON5/!SSL!/WebHelp/"
)

# The root TOC key. This is the top-level file that contains
# the main sections (Welcome, Forms, EAEDC, SNAP, TAFDC, etc.)
# We found this by inspecting the HAR data — toc0 holds all
# 16 top-level categories.
ROOT_TOC_KEY = "toc"

FLAT_OUTPUT = str(INDEX_DIR / "policy_urls.txt")
TOC_OUTPUT = str(INDEX_DIR / "policy_toc.json")

# ============================================================
# MAIN LOGIC
# ============================================================

def load_har_file(filepath):
    """
    Opens the HAR file and returns the parsed JSON content.
    """
    print(f"Loading HAR file: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        har_data = json.load(f)
    print(f"  Found {len(har_data['log']['entries'])} total entries in HAR file.")
    return har_data


def extract_toc_responses(har_data):
    """
    Looks through every entry in the HAR file and pulls out the
    response body text from each TOC JS file request. Returns a
    dictionary mapping the toc key (like 'toc142') to the parsed
    list of entries from that TOC file.

    For example, a request to 'whxdata/toc142.new.js' gets stored
    under the key 'toc142'. It also handles variations like
    'toc0.new.js' or just 'toc0.js'.
    """
    toc_dict = {}

    for entry in har_data["log"]["entries"]:
        url = entry.get("request", {}).get("url", "")

        # We only care about the TOC JavaScript files
        if "whxdata/toc" not in url or not url.endswith(".js"):
            continue

        content = entry.get("response", {}).get("content", {})
        text = content.get("text", "")
        if not text:
            continue

        # Extract the toc key from the URL
        # Handles: toc.new.js (root), toc0.new.js, toc142.new.js, etc.
        key_match = re.search(r"whxdata/(toc\d*)", url)
        if not key_match:
            continue

        toc_key = key_match.group(1)
        # If it matched just "toc" with no number, that's our root
        if toc_key == "toc":
            toc_key = "toc"  # keep it as-is

        # Extract the JSON array from the JavaScript function
        json_match = re.search(
            r"var toc\s*=\s*(\[.*?\])\s*;", text, re.DOTALL
        )
        if not json_match:
            continue

        try:
            entries = json.loads(json_match.group(1))
            # If we encounter the same key twice (e.g. cached vs fresh),
            # keep the one with more entries
            if toc_key not in toc_dict or len(entries) > len(toc_dict[toc_key]):
                toc_dict[toc_key] = entries
        except json.JSONDecodeError:
            print(f"  Warning: Could not parse JSON from {toc_key}")

    print(f"  Found {len(toc_dict)} unique TOC files with parseable content.")
    return toc_dict


def build_tree(toc_dict, toc_key):
    """
    Recursively builds the hierarchical tree starting from a given
    toc key. Each 'book' entry becomes a chapter/subchapter node
    with a 'children' list. Each 'item' entry becomes a leaf node
    with a full URL.

    Returns a list of tree nodes.
    """
    entries = toc_dict.get(toc_key, [])
    nodes = []

    for entry in entries:
        node = {"name": entry.get("name", "Unnamed")}

        if entry.get("type") == "book":
            # This is a chapter or subchapter folder
            node["type"] = "section"

            # Some books also have a URL (the section overview page)
            if entry.get("url"):
                node["url"] = BASE_URL + entry["url"]

            # Recursively build children if this book has a child key
            child_key = entry.get("key")
            if child_key and child_key in toc_dict:
                node["children"] = build_tree(toc_dict, child_key)
            else:
                node["children"] = []
                if child_key:
                    print(f"  Warning: TOC key '{child_key}' referenced "
                          f"by '{entry.get('name')}' not found in HAR data")
        else:
            # This is a leaf page
            node["type"] = "page"
            if entry.get("url"):
                node["url"] = BASE_URL + entry["url"]

        nodes.append(node)

    return nodes


def collect_all_urls(tree, breadcrumb=None):
    """
    Walks the tree and collects every URL along with its breadcrumb
    path (the chain of chapter/subchapter names leading to it).

    Returns a list of dicts like:
    {
        "url": "https://...",
        "title": "Page Name",
        "breadcrumb": ["SNAP", "Expenses and Deductions", "Child Support"]
    }
    """
    if breadcrumb is None:
        breadcrumb = []

    results = []

    for node in tree:
        current_crumb = breadcrumb.copy()

        if node["type"] == "section":
            current_crumb.append(node["name"])

            # If the section itself has an overview URL, include it
            if node.get("url"):
                results.append({
                    "url": node["url"],
                    "title": node["name"],
                    "breadcrumb": current_crumb
                })

            # Recurse into children
            results.extend(
                collect_all_urls(node.get("children", []), current_crumb)
            )
        else:
            # Leaf page
            if node.get("url"):
                results.append({
                    "url": node["url"],
                    "title": node["name"],
                    "breadcrumb": current_crumb
                })

    return results


def save_outputs(tree, all_pages):
    """
    Saves three output files:
      1. The full hierarchical TOC as JSON
      2. A flat text file of URLs
      3. A detailed page manifest with breadcrumbs (for the RAG pipeline)
    """
    # Save the hierarchical TOC
    with open(TOC_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)
    print(f"  Saved hierarchical TOC to {TOC_OUTPUT}")

    # Save flat URL list
    unique_urls = sorted(set(p["url"] for p in all_pages))
    with open(FLAT_OUTPUT, "w", encoding="utf-8") as f:
        for url in unique_urls:
            f.write(url + "\n")
    print(f"  Saved {len(unique_urls)} unique URLs to {FLAT_OUTPUT}")

    # Save the page manifest with breadcrumbs
    manifest_file = str(INDEX_DIR / "policy_manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(all_pages, f, indent=2, ensure_ascii=False)
    print(f"  Saved page manifest with breadcrumbs to {manifest_file}")

    return unique_urls


def print_tree_preview(tree, depth=0, max_depth=3, count=None):
    """
    Prints a preview of the TOC tree structure to the console,
    limited to a certain depth so it doesn't flood the screen.
    """
    if count is None:
        count = [0]

    for node in tree:
        if count[0] >= 60:
            print("  ... (truncated preview)")
            return

        indent = "  " + "    " * depth
        if node["type"] == "section":
            child_count = len(node.get("children", []))
            print(f"{indent}📁 {node['name']} ({child_count} children)")
            count[0] += 1
            if depth < max_depth:
                print_tree_preview(
                    node.get("children", []), depth + 1, max_depth, count
                )
        else:
            print(f"{indent}📄 {node['name']}")
            count[0] += 1


def report_missing_keys(toc_dict):
    """
    Checks if any 'book' entries reference a child toc key that
    we don't have in our HAR data. This helps us know if the
    HAR capture missed any sections.
    """
    all_referenced_keys = set()
    for entries in toc_dict.values():
        for entry in entries:
            if entry.get("type") == "book" and entry.get("key"):
                all_referenced_keys.add(entry["key"])

    missing = all_referenced_keys - set(toc_dict.keys())
    if missing:
        print(f"\n  ⚠️  {len(missing)} referenced TOC keys not found in HAR data:")
        for key in sorted(missing, key=lambda x: int(x[3:])):
            # Find which parent references this missing key
            for parent_key, entries in toc_dict.items():
                for entry in entries:
                    if entry.get("key") == key:
                        print(f"      {key} (referenced by '{entry.get('name')}' in {parent_key})")
                        break
        print("     These sections may have missing pages. You may need to")
        print("     expand those sections in the browser and re-export the HAR.")
    else:
        print("\n  ✅ All referenced TOC keys found — no missing sections!")


def main():
    """
    Main workflow:
    Load HAR -> parse all TOC files -> check for gaps ->
    reconstruct the tree -> save hierarchical TOC and flat URL list.
    """
    # Step 1: Load the HAR file
    har_data = load_har_file(HAR_FILENAME)

    # Step 2: Parse all TOC JS responses into a lookup dictionary
    toc_dict = extract_toc_responses(har_data)

    # Step 3: Verify the root key exists
    if ROOT_TOC_KEY not in toc_dict:
        print(f"\n  ❌ Root key '{ROOT_TOC_KEY}' not found in HAR data!")
        print(f"     Available keys: {sorted(toc_dict.keys(), key=lambda x: int(x[3:]))[:20]}...")
        print("     Update ROOT_TOC_KEY in the script configuration.")
        return

    # Step 4: Check for any missing child keys
    report_missing_keys(toc_dict)

    # Step 5: Recursively build the full tree from the root
    tree = build_tree(toc_dict, ROOT_TOC_KEY)

    # Step 6: Flatten the tree to collect all pages with breadcrumbs
    all_pages = collect_all_urls(tree)
    print(f"\n  Total pages with breadcrumbs: {len(all_pages)}")

    # Step 7: Save outputs
    unique_urls = save_outputs(tree, all_pages)

    # Step 8: Print a preview of the tree structure
    print("\nTOC structure preview:")
    print_tree_preview(tree)

    print(f"\nDone! {len(unique_urls)} unique pages mapped.")
    print(f"  Hierarchical TOC:  {TOC_OUTPUT}")
    print(f"  Page manifest:     policy_manifest.json")
    print(f"  Flat URL list:     {FLAT_OUTPUT}")


if __name__ == "__main__":
    main()