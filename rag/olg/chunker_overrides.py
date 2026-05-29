"""
Manual chunking overrides for specific OLG pages where the automatic
splitter doesn't produce optimal groupings.

Currently overrides:
- Verification Chart (Vers_Types_VerifChart) — converted from a 32-chunk
  alphabetical split to 12 topical chunks in prose form. See
  `docs/olg_cleanup/plan.md` Phase 2.3.
"""

from __future__ import annotations

import configparser
import re
from pathlib import Path


# ============================================================
# VERIFICATION CHART OVERRIDE
# ============================================================

# Source site base URL lives in config.ini (gitignored), not in code.
_config = configparser.ConfigParser()
_config.read(Path(__file__).resolve().parents[2] / "config.ini")
_BASE_URL = _config.get("olg", "base_url", fallback="")

VERIFICATION_CHART_URL = (
    _BASE_URL + "CrossProg/Verifications/Vers_Types_VerifChart.htm"
)

VERIFICATION_CHART_GROUPS = [
    {
        "label": "Identity, Citizenship & Demographics",
        "items": [
            "Date of Birth",
            "Date of Death",
            "Identity",
            "Massachusetts Residency",
            "Noncitizen Status",
            "Social Security Number or Proof of Application",
            "Clarification of Social Security Number",
            "U.S. Citizenship",
            "Effort to Become a US Citizen",
            "Disability of Elder Noncitizen",
            "Pregnancy",
            "Foster Care",
        ],
    },
    {
        "label": "Household Composition & Relationships",
        "items": [
            "Who you live with",
            "Your Relationship to:",
            "Tax Dependents",
            "People who Joined Your Household",
            "People who Moved Out of Your Household",
            "Temporary Absence",
            "Care and Control",
            "Caring for a Disabled Person in Your Home",
        ],
    },
    {
        "label": "Earned Income & Self-Employment",
        "items": [
            "Earnings and Number of Hours Worked",
            "Earnings from a Job That Ended",
            "Information About a New Job",
            "Self-Employment Income and Number of Hours Worked",
            "Business Expenses",
            "Potential Earnings - DOR",
            "Refunds",
        ],
    },
    {
        "label": "Unearned Income",
        "items": [
            "Unearned Income",
            "Unearned Income that has ended",
            "Pension and Retirement Accounts",
            "Lump Sum Payment",
            "Social Security Disability",
            "Veterans Vendor Payments",
            "Income You Get From Someone Who Rooms",
            "Rental Income",
            "Termination of Benefits in Another State",
            "Living Above Means",
        ],
    },
    {
        "label": "Assets & Resources",
        "items": [
            "Bank Account",
            "Cash on Hand",
            "Stocks and Bonds",
            "Trust Fund",
            "Burial Insurance or Prepaid Funeral Agreement",
            "Life Insurance",
            "Property value",
            "Other Assets",
            "Transferred Asset",
        ],
    },
    {
        "label": "Housing, Utilities & Expenses",
        "items": [
            "Housing Costs",
            "Housing Type",
            "Past Due Housing Costs",
            "Past Due Utility Costs",
            "Utility Costs",
            "Information so DTA can pay your rent",
            "Dependent Care Expenses Costs",
            "Medical Costs",
            "Garnishment Amount and Reason",
        ],
    },
    {
        "label": "Disability & Health",
        "items": [
            "Federally Certified Disability",
            "Proof of Disability, Physical or Mental Health Problem for EAEDC",
            "Proof of Disability, Physical or Mental Health Problem for TAFDC",
            "Proof of Disability, Physical or Mental Health Problem From Medical Provider",
            "Proof of Health Insurance",
            "Immunization",
        ],
    },
    {
        "label": "Work Rules & Pathways",
        "items": [
            "SNAP ABAWD Work Rules Participation",
            "Exemption from SNAP ABAWD Work Rules",
            "Past Exemption",
            "Good Cause for Not Meeting the SNAP ABAWD Work Rules",
            "SNAP General",
            "TAFDC Work Program",
            "Pre-Benefit",
            "Pre-Benefit Job Search Form (Work Ready Client)",
            "Pathways to Self-Sufficiency",
            "Request for an Extension of Time Limited Benefits",
        ],
    },
    {
        "label": "Education & Training",
        "items": [
            "Community College Enrollment",
            "Financial Aid and School Enrollment",
            "School Attendance in",
            "School Attendance from",
            "School/Training Enrollment",
            "Request for School Employee",
        ],
    },
    {
        "label": "Custody, Cooperation & Caretaker Programs",
        "items": [
            "Child Support Cooperation",
            "Child Support Legal Obligation",
            "Payment of Child Support",
            "Good Cause for Not Cooperating with Child Support",
            "Guardianship or Custody",
            "Good Cause for Not Pursuing Custody or Guardianship",
            "EAEDC Caretaker Family",
            "EAEDC Caring for Disabled",
            "Participation in a Mass Rehabilitation Commission Program",
        ],
    },
    {
        "label": "Forms, Replacements & Administrative",
        "items": [
            "Application for Other Benefits",
            "Reevaluation form",
            "Direct Deposit Form",
            "Release of Information",
            "Request for Deduction from EBT Account",
            "Request for a Replacement Check",
            "Request for Replacement SNAP Benefits",
            "Removal of Heightened Level of Security",
            "Request for Heightened Level of Security",
            "Agreement to Reimburse DTA",
            "Assisting Person",
            "Additional Verification",
        ],
    },
]


_CODE_TO_WORD = {
    "M": "Mandatory",
    "O": "Optional",
    "n/a": "Not Applicable",
    "N/A": "Not Applicable",
}


def _expand_code(code: str) -> str:
    """Expand M/O/N/A codes to full words; preserve trailing * markers."""
    if not code or not code.strip():
        return "Not specified"
    code = code.strip()
    suffix = ""
    while code.endswith("*"):
        suffix = "*" + suffix
        code = code[:-1]
    return _CODE_TO_WORD.get(code, code) + suffix


def _clean_item(s: str) -> str:
    """Normalize an item name for matching."""
    base = s.split(";")[0].strip()
    base = re.sub(r"\s+", " ", base)
    return base.lower()


def _row_to_prose(row: list[str]) -> str:
    """Render a verification chart row as a prose block."""
    padded = list(row) + [""] * (6 - len(row))
    item, examples, snap, tafdc, eaedc, notes = padded[:6]

    lines = [
        f"**{item.strip()}** — SNAP: {_expand_code(snap)}, "
        f"TAFDC: {_expand_code(tafdc)}, EAEDC: {_expand_code(eaedc)}."
    ]
    if examples and examples.strip():
        lines.append(f"Examples: {examples.strip()}")
    if notes and notes.strip():
        lines.append(f"Notes: {notes.strip()}")
    return "\n".join(lines)


def chunk_verification_chart(page_data: dict) -> list[dict]:
    """
    Produce manual topical chunks for the Verification Chart.

    Returns a list of section dicts compatible with `create_section_chunks`'s
    chunk-building loop (heading, text, level, parent_heading, chunk_n,
    chunk_total, links).
    """
    # Collect all rows across all source tables (they're alphabetically
    # split in the source HTML, not topically).
    all_rows = []
    for t in page_data.get("tables", []):
        all_rows.extend(t.get("rows", []))

    row_by_item = {}
    for r in all_rows:
        if r and r[0]:
            row_by_item[_clean_item(r[0])] = r

    used = set()

    def find_row(query: str) -> list[str] | None:
        qc = _clean_item(query)
        if qc in row_by_item and qc not in used:
            used.add(qc)
            return row_by_item[qc]
        for k, v in row_by_item.items():
            if k.startswith(qc) and k not in used:
                used.add(k)
                return v
        for k, v in row_by_item.items():
            if qc in k and k not in used:
                used.add(k)
                return v
        return None

    # Total chunks = 1 preamble + N topical groups
    chunk_total = 1 + len(VERIFICATION_CHART_GROUPS)
    sections = []

    vc1_note = (
        "Note: The Examples shown for each item are the proofs listed on "
        "the Verification Checklist (VC-1) notice issued to clients. They "
        "are not an exhaustive list of allowable verifications — the agency "
        "may accept other proofs."
    )

    # Chunk 1: Overview/preamble — use the existing prose section text,
    # stripping the [Table] placeholders (they're rendered separately).
    intro = page_data.get("sections", [{}])[0].get("text", "")
    intro = re.sub(r"\n*\[Table\]\n*", "\n", intro).strip()
    overview_text = f"{intro}\n\n{vc1_note}"
    sections.append({
        "heading": "Verification Chart — Overview",
        "text": overview_text,
        "level": 2,
        "parent_heading": None,
        "chunk_n": 1,
        "chunk_total": chunk_total,
        "links": [],
    })

    # Chunks 2..N: topical groups
    for i, group in enumerate(VERIFICATION_CHART_GROUPS, start=2):
        rows = []
        missing = []
        for item in group["items"]:
            r = find_row(item)
            if r is None:
                missing.append(item)
            else:
                rows.append(r)

        body_parts = [
            f"This portion of the Verification Chart covers "
            f"{group['label']}: the proofs SNAP, TAFDC, and EAEDC clients "
            f"may need to provide for these items.",
            "",
            vc1_note,
            "",
        ]
        body_parts.extend(_row_to_prose(r) + "\n" for r in rows)
        body = "\n".join(body_parts).strip()

        if missing:
            print(
                f"  [verification-chart override] Group "
                f"{group['label']!r} could not match: {missing}"
            )

        sections.append({
            "heading": f"Verification Chart — {group['label']}",
            "text": body,
            "level": 2,
            "parent_heading": None,
            "chunk_n": i,
            "chunk_total": chunk_total,
            "links": [],
        })

    # Diagnostic: report any rows that weren't placed in any group
    leftover = [
        row_by_item[k][0] for k in row_by_item if k not in used
    ]
    if leftover:
        print(
            f"  [verification-chart override] {len(leftover)} unplaced rows: "
            f"{leftover}"
        )

    return sections


# ============================================================
# REGISTRY
# ============================================================

URL_OVERRIDES: dict[str, callable] = {
    VERIFICATION_CHART_URL: chunk_verification_chart,
}
