"""
Hand-curated exclusion lists for the OLG chunker.

Two sets:
- PAGE_EXCLUDES: scraped-page basenames to skip entirely (no chunks emitted)
- CHUNK_EXCLUDES: chunk_ids to drop after chunking

Hand-curation chosen over programmatic detection because the volume is small
(~30 pages) and the cost of misclassifying a real policy page is much higher
than the cost of human review. See docs/olg_cleanup/plan.md Phase 3.
"""

# ============================================================
# PAGE EXCLUDES — basenames in index/olg/scraped_pages/
# ============================================================

PAGE_EXCLUDES: set[str] = {
    # Phase 3.1 — Transmittal logs (13 pages)
    # Chronological tables of policy changes; not useful as RAG retrieval surface.
    "Transmittals__TU_2014.json",
    "Transmittals__TU_2015.json",
    "Transmittals__TU_2016.json",
    "Transmittals__TU_2017.json",
    "Transmittals__TU_2018.json",
    "Transmittals__TU_2019.json",
    "Transmittals__TU_2020.json",
    "Transmittals__TU_2021.json",
    "Transmittals__TU_2022.json",
    "Transmittals__TU_2023.json",
    "Transmittals__TU_2024.json",
    "Transmittals__TU_2025.json",
    "Transmittals__TU_2026.json",

    # Phase 3.2 — Online Forms book catalog pages (8 of 9)
    # Pure form catalogs (Brochures, Flyers, per-program form lists).
    # `Forms__locate_view_and_print_online_forms.json` is kept — it has real guidance.
    "Forms__Brochures.json",
    "Forms__Cross_Programs.json",
    "Forms__EAEDC.json",
    "Forms__FLYERS.json",
    "Forms__Non-Program.json",
    "Forms__SNAP.json",
    "Forms__TAFDC.json",
    "Forms__Voter_Registration.json",
}


# ============================================================
# CHUNK EXCLUDES — chunk_ids dropped after chunking
# ============================================================

CHUNK_EXCLUDES: set[str] = {
    # Phase 3.4 — pure-acronym chunks
    # Section bodies that are only short capitalized tokens with no prose.
    # BPov_NG_Overview "Acceptable Abbreviations" — list of 30+ acronyms (ABAWD, ADA, ...).
    "sec__BP__Overview__BPov_NG_Overview__003",
}
