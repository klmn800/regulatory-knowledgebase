"""
Scraper for DTA Online Policy Guide pages.

Reads the page manifest (produced by extractor.py), fetches each URL,
parses the HTML with parser.py, and saves structured JSON output to
the scraped_pages/ directory.

Features:
  - Respectful rate limiting (1.5s delay between requests)
  - Retry with exponential backoff on transient failures
  - Progress tracking — can be interrupted and resumed
  - Batch mode for testing (--batch N scrapes only N pages)
  - 404 tracking with summary report at the end
  - Program area derived from URL path structure

Output:
  - scraped_pages/*.json   — one structured JSON file per page
  - scrape_progress.json   — tracks status of every URL
  - scrape_report.txt      — summary after each run (totals, 404s, errors)

Usage:
    # Test with 10 pages first
    python scraper.py --batch 10

    # Resume a previous run (picks up where it left off)
    python scraper.py

    # Force re-scrape of failed pages
    python scraper.py --retry-failed

    # Scrape specific program only
    python scraper.py --program SNAP

    # Full scrape (all ~1,204 pages)
    python scraper.py --batch 0
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from parser import parse_page


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = PROJECT_ROOT / "index" / "olg"
MANIFEST_FILE = INDEX_DIR / "policy_manifest.json"
OUTPUT_DIR = INDEX_DIR / "scraped_pages"
PROGRESS_FILE = INDEX_DIR / "scrape_progress.json"
REPORT_FILE = INDEX_DIR / "scrape_report.txt"

BASE_URL = (
    "https://eohhs.ehs.state.ma.us"
    "/DTA/PolicyOnline/BEACON5/!SSL!/WebHelp/"
)

REQUEST_DELAY = 1.5       # seconds between requests
MAX_RETRIES = 3           # retry count for transient errors
BACKOFF_BASE = 2.0        # exponential backoff multiplier
REQUEST_TIMEOUT = 15      # seconds per HTTP request
USER_AGENT = "DTAPolicyScraper/1.0 (RAG pipeline; respectful crawling)"


# ============================================================
# MANIFEST LOADING
# ============================================================

def load_manifest() -> list[dict]:
    """
    Load the page manifest and deduplicate by URL.

    The manifest can have the same URL listed multiple times (when a
    page appears in multiple TOC locations). We keep the first
    occurrence's breadcrumb since the manifest is ordered by the TOC
    hierarchy.

    Returns a list of dicts with keys: url, title, breadcrumb, program.
    """
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    seen_urls = set()
    pages = []

    for entry in raw:
        url = entry["url"]

        # Skip malformed URLs (ones with embedded full URLs)
        if "WebHelp/https:" in url or "WebHelp/http:" in url:
            continue

        if url in seen_urls:
            continue
        seen_urls.add(url)

        program = _detect_program(url)

        pages.append({
            "url": url,
            "title": entry.get("title", ""),
            "breadcrumb": entry.get("breadcrumb", []),
            "program": program,
        })

    return pages


def _detect_program(url: str) -> str:
    """
    Derive the program area from the URL path structure.

    URLs look like:
        .../WebHelp/SNAP/Eligibility/SNAPelig_Overview.htm
        .../WebHelp/CrossProg/Income/CPinc_Budgeting.htm
        .../WebHelp/Welcome.htm  (root level)

    We grab the first path segment after WebHelp/.
    """
    after_webhelp = url.split("WebHelp/")[-1]
    parts = after_webhelp.split("/")

    if len(parts) <= 1:
        # Root-level file like Welcome.htm
        return "General"

    program = parts[0]

    # Normalize some folder names to cleaner labels
    program_map = {
        "CrossProg": "Cross-Program",
        "DomViolence": "Domestic Violence",
        "NoticeForms": "Notices/Forms",
        "SelfServ": "Self-Service",
        "PandP": "Policies & Procedures",
        "SUN_Bucks": "SUN Bucks",
        "ScheduledMailings": "Scheduled Mailings",
    }
    return program_map.get(program, program)


# ============================================================
# PROGRESS TRACKING
# ============================================================

def load_progress() -> dict:
    """
    Load the progress file. Returns a dict mapping URL to status info:
    {
        "https://...": {
            "status": "success" | "failed" | "404",
            "file": "filename.json",
            "scraped_at": "2026-03-02T...",
            "error": "..." (only for failed)
        }
    }
    """
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(progress: dict) -> None:
    """Write the progress dict to disk."""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


# ============================================================
# FILENAME GENERATION
# ============================================================

def url_to_filename(url: str) -> str:
    """
    Convert a URL to a safe filename for the JSON output.

    Takes the path after WebHelp/ and replaces / with __ to create
    a flat but readable filename.

    Example:
        .../WebHelp/SNAP/Eligibility/SNAPelig_HH.htm
        -> SNAP__Eligibility__SNAPelig_HH.json
    """
    after_webhelp = url.split("WebHelp/")[-1]
    # Remove .htm extension
    after_webhelp = re.sub(r"\.htm[l]?$", "", after_webhelp, flags=re.IGNORECASE)
    # Replace path separators with double underscore
    safe_name = after_webhelp.replace("/", "__")
    # Remove any other unsafe characters
    safe_name = re.sub(r"[^\w\-.]", "_", safe_name)
    return safe_name + ".json"


# ============================================================
# HTTP FETCHING
# ============================================================

def fetch_page(url: str) -> tuple[str | None, int, str | None]:
    """
    Fetch a single URL and return (html, status_code, error_message).

    Returns:
        (html_string, 200, None) on success
        (None, 404, "Not Found") on 404
        (None, status_code, error_message) on other failures
    """
    # Percent-encode any non-ASCII characters in the URL (e.g., en-dashes)
    from urllib.parse import quote
    safe_url = quote(url, safe=":/?#[]@!$&'()*+,;=-._~")

    req = urllib.request.Request(safe_url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html",
    })

    try:
        resp = urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT)
        html = resp.read().decode("utf-8", errors="replace")
        return html, resp.status, None
    except urllib.error.HTTPError as e:
        return None, e.code, str(e)
    except urllib.error.URLError as e:
        return None, 0, f"URLError: {e.reason}"
    except Exception as e:
        return None, 0, f"{type(e).__name__}: {e}"


def fetch_with_retry(url: str) -> tuple[str | None, int, str | None]:
    """
    Fetch a URL with retries and exponential backoff.

    404s are NOT retried (they're permanent). Only transient errors
    (timeouts, 5xx, connection errors) are retried.
    """
    for attempt in range(MAX_RETRIES):
        html, status, error = fetch_page(url)

        # Success
        if html is not None:
            return html, status, None

        # 404 — don't retry, it's a permanent failure
        if status == 404:
            return None, 404, error

        # 403 — don't retry, might be blocked
        if status == 403:
            return None, 403, error

        # Transient error — retry with backoff
        if attempt < MAX_RETRIES - 1:
            wait = BACKOFF_BASE ** attempt
            print(f"    Retry {attempt + 1}/{MAX_RETRIES - 1} "
                  f"after {wait:.0f}s (status={status}, error={error})")
            time.sleep(wait)

    return None, status, error


# ============================================================
# SCRAPING PIPELINE
# ============================================================

def scrape_page(page: dict) -> dict:
    """
    Scrape a single page: fetch HTML, parse it, assemble the full
    output record with metadata.

    Args:
        page: dict with url, title, breadcrumb, program

    Returns:
        dict with all parsed content + metadata, or a minimal dict
        with status="error" or status="404" on failure.
    """
    url = page["url"]

    html, status, error = fetch_with_retry(url)

    if html is None:
        return {
            "url": url,
            "status": "404" if status == 404 else "error",
            "error": error,
            "http_status": status,
        }

    # Parse the HTML content
    parsed = parse_page(html, page_url=url)

    # Assemble the full output record
    return {
        "url": url,
        "title": parsed["title"] or page.get("title", ""),
        "program": page["program"],
        "breadcrumb": page["breadcrumb"],
        "last_updated": parsed["last_updated"],
        "sections": parsed["sections"],
        "tables": parsed["tables"],
        "internal_links": parsed["internal_links"],
        "related_pages": parsed.get("related_pages", []),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# REPORT GENERATION
# ============================================================

def generate_report(progress: dict, pages: list[dict], elapsed: float) -> str:
    """
    Generate a human-readable summary of the scrape run.
    """
    total = len(pages)
    success = sum(1 for v in progress.values() if v["status"] == "success")
    not_found = sum(1 for v in progress.values() if v["status"] == "404")
    failed = sum(1 for v in progress.values() if v["status"] == "failed")
    pending = total - len(progress)

    lines = [
        "=" * 60,
        "DTA Online Guide Scrape Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
        f"Total pages in manifest:  {total}",
        f"Successfully scraped:     {success}",
        f"404 Not Found:            {not_found}",
        f"Failed (other errors):    {failed}",
        f"Remaining (not yet run):  {pending}",
        f"Elapsed time:             {elapsed:.1f}s",
        "",
    ]

    if not_found > 0:
        lines.append("-" * 60)
        lines.append("Pages returning 404 (may be removed or renamed):")
        lines.append("-" * 60)
        for url, info in sorted(progress.items()):
            if info["status"] == "404":
                filename = url.split("WebHelp/")[-1]
                lines.append(f"  {filename}")
        lines.append("")

    if failed > 0:
        lines.append("-" * 60)
        lines.append("Pages that failed (non-404 errors):")
        lines.append("-" * 60)
        for url, info in sorted(progress.items()):
            if info["status"] == "failed":
                filename = url.split("WebHelp/")[-1]
                lines.append(f"  {filename}: {info.get('error', 'unknown')}")
        lines.append("")

    return "\n".join(lines)


# ============================================================
# MAIN ORCHESTRATION
# ============================================================

def run_scraper(
    batch_size: int = 0,
    retry_failed: bool = False,
    program_filter: str | None = None,
    force: bool = False,
) -> None:
    """
    Main scraping loop.

    Args:
        batch_size: Number of pages to scrape. 0 means all.
        retry_failed: If True, re-scrape pages that previously failed
                      (but not 404s, since those are permanent).
        program_filter: If set, only scrape pages from this program.
        force: If True, re-scrape every page in the manifest, ignoring
               existing progress. 404s are still skipped (they don't come
               back from --force). Use this to refresh content after
               parser changes.
    """
    # Load manifest and progress
    pages = load_manifest()
    progress = load_progress()

    print(f"Loaded {len(pages)} unique pages from manifest")
    print(f"Progress: {len(progress)} pages already processed")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Filter to pages that need scraping
    to_scrape = []
    for page in pages:
        url = page["url"]

        # Apply program filter
        if program_filter and page["program"].lower() != program_filter.lower():
            continue

        # 404s are always skipped — they don't become valid pages on retry
        if url in progress and progress[url]["status"] == "404":
            continue

        # In force mode, scrape every non-404 page regardless of prior status
        if force:
            to_scrape.append(page)
            continue

        # Skip already-successful pages
        if url in progress and progress[url]["status"] == "success":
            continue

        # Skip failed pages unless --retry-failed
        if url in progress and progress[url]["status"] == "failed":
            if not retry_failed:
                continue

        to_scrape.append(page)

    if not to_scrape:
        print("Nothing to scrape — all pages already processed.")
        print(f"  (Use --retry-failed to re-attempt failed pages)")
        return

    # Apply batch size limit
    if batch_size > 0:
        to_scrape = to_scrape[:batch_size]

    print(f"Scraping {len(to_scrape)} pages "
          f"(delay: {REQUEST_DELAY}s between requests)")
    if program_filter:
        print(f"  Filtered to program: {program_filter}")
    print()

    # Scrape loop
    start_time = time.time()
    success_count = 0
    error_count = 0

    for i, page in enumerate(to_scrape, start=1):
        url = page["url"]
        short_name = url.split("WebHelp/")[-1]

        print(f"[{i}/{len(to_scrape)}] {short_name}", end=" ", flush=True)

        result = scrape_page(page)

        if "status" in result and result["status"] in ("404", "error"):
            # Failed — record in progress
            status = result["status"]
            progress[url] = {
                "status": "404" if status == "404" else "failed",
                "error": result.get("error", ""),
                "http_status": result.get("http_status", 0),
                "attempted_at": datetime.now(timezone.utc).isoformat(),
            }
            error_count += 1
            print(f"  [{status.upper()}]" +
                  (f" {result.get('error', '')}" if status != "404" else ""))
        else:
            # Success — save the JSON file
            filename = url_to_filename(url)
            output_path = OUTPUT_DIR / filename

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            progress[url] = {
                "status": "success",
                "file": filename,
                "scraped_at": result["scraped_at"],
            }
            success_count += 1

            section_count = len(result["sections"])
            table_count = len(result["tables"])
            print(f"  OK ({section_count} sections, {table_count} tables)")

        # Save progress after every page (so we can resume)
        save_progress(progress)

        # Rate limiting — don't hit the server too fast
        if i < len(to_scrape):
            time.sleep(REQUEST_DELAY)

    elapsed = time.time() - start_time

    # Generate and save report
    report = generate_report(progress, pages, elapsed)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print()
    print(report)
    print(f"Report saved to: {REPORT_FILE}")
    print(f"Progress saved to: {PROGRESS_FILE}")
    print(f"Page data saved to: {OUTPUT_DIR}/")


# ============================================================
# CLI
# ============================================================

def main():
    """Parse command-line arguments and run the scraper."""
    arg_parser = argparse.ArgumentParser(
        description="Scrape DTA Online Policy Guide pages for RAG pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scraper.py --batch 10        # Test with 10 pages
  python scraper.py                   # Resume / scrape all remaining
  python scraper.py --retry-failed    # Re-attempt previously failed pages
  python scraper.py --program SNAP    # Scrape only SNAP pages
        """,
    )

    arg_parser.add_argument(
        "--batch", type=int, default=0,
        help="Number of pages to scrape (0 = all remaining). Default: 0",
    )
    arg_parser.add_argument(
        "--retry-failed", action="store_true",
        help="Re-scrape pages that previously failed (not 404s)",
    )
    arg_parser.add_argument(
        "--program", type=str, default=None,
        help="Only scrape pages from this program (e.g., SNAP, TAFDC, EAEDC)",
    )
    arg_parser.add_argument(
        "--force", action="store_true",
        help="Re-scrape every non-404 page in the manifest, ignoring prior "
             "progress. Use after parser changes to refresh extracted content.",
    )

    args = arg_parser.parse_args()

    run_scraper(
        batch_size=args.batch,
        retry_failed=args.retry_failed,
        program_filter=args.program,
        force=args.force,
    )


if __name__ == "__main__":
    main()
