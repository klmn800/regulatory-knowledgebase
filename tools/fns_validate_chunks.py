"""
Quick validation of FNS chunks against the four chunker refinements.

Checks:
  1. §1170.5 — chunks land at "Example of X:" boundaries; no mid-example breaks.
  2. §1065.2 — no chunk ends with `:`. Corpus-wide also: 0 chunks ending with `:`.
  3. §726.7  — Step bodies intact; no chunk ends with bare "Step N. <one sentence>".
  4. §812.2  — chunk prefix includes "812 School Enrollment".

Plus general health:
  - mid-word break check (last token + first token concatenation reads as 1 word)
  - whitespace runs (>= 6 spaces in a row)
  - chunks ending with bare colon (Fix #2 corpus-wide test)
"""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = json.loads((ROOT / "index" / "fns" / "section_chunks.json").read_text(encoding="utf-8"))


def for_section(num: str):
    return [c for c in CHUNKS if c["metadata"]["section_number"] == num]


def show_chunks(num: str, label: str):
    print(f"\n=== §{num} ({label}) ===")
    cs = for_section(num)
    print(f"  {len(cs)} chunks")
    for c in cs:
        prefix_line = c["text"].split("\n", 1)[0]
        body = c["text"].split("\n\n", 1)[1] if "\n\n" in c["text"] else ""
        first_120 = body[:120].replace("\n", " ⏎ ")
        last_120 = body[-120:].replace("\n", " ⏎ ")
        print(f"  --- chunk {c['metadata']['chunk_n']}/{c['metadata']['chunk_total']} ({len(c['text'])} chars) ---")
        print(f"  PREFIX: {prefix_line}")
        print(f"  HEAD:   {first_120}")
        print(f"  TAIL:   ...{last_120}")


# Per-section verifications
show_chunks("1170.5", "Fix #1 — example boundaries")
show_chunks("1065.2", "Fix #2 — colon-orphan")
show_chunks("726.7",  "Fix #3 — step bodies")
show_chunks("812.2",  "Fix #4 — parent title in prefix")


# Corpus-wide checks
print("\n=== Corpus-wide validation ===")

ending_with_colon = []
for c in CHUNKS:
    body = c["text"].split("\n\n", 1)[1] if "\n\n" in c["text"] else c["text"]
    body = body.rstrip()
    if body.endswith(":"):
        ending_with_colon.append((c["chunk_id"], body[-80:]))
print(f"\nChunks ending with ':' (Fix #2 target=0): {len(ending_with_colon)}")
for cid, tail in ending_with_colon[:10]:
    print(f"  {cid}: ...{tail!r}")

# Whitespace runs
ws_runs = []
for c in CHUNKS:
    if re.search(r" {6,}", c["text"]):
        ws_runs.append(c["chunk_id"])
print(f"\nChunks with whitespace runs (>=6 spaces): {len(ws_runs)}")
for cid in ws_runs[:5]:
    print(f"  {cid}")

# Mid-word breaks across consecutive chunks of same section
mid_word = []
by_sec = defaultdict(list)
for c in CHUNKS:
    by_sec[c["metadata"]["section_number"]].append(c)
for sec, cs in by_sec.items():
    cs_sorted = sorted(cs, key=lambda c: c["metadata"]["chunk_n"])
    for a, b in zip(cs_sorted, cs_sorted[1:]):
        a_body = a["text"].split("\n\n", 1)[1] if "\n\n" in a["text"] else a["text"]
        b_body = b["text"].split("\n\n", 1)[1] if "\n\n" in b["text"] else b["text"]
        a_last = re.findall(r"\S+", a_body)[-1] if re.findall(r"\S+", a_body) else ""
        b_first = re.findall(r"\S+", b_body)[0] if re.findall(r"\S+", b_body) else ""
        # Mid-word: prev ends without sentence terminator/punctuation AND first token is lowercase
        if a_last and b_first and a_last[-1].isalpha() and b_first[0].islower():
            mid_word.append((sec, a["metadata"]["chunk_n"], a_last, b_first))
print(f"\nPossible mid-word breaks: {len(mid_word)}")
for sec, n, a, b in mid_word[:10]:
    print(f"  §{sec} chunk {n}: ...{a!r} | {b!r}...")

# Oversize
oversize = [c for c in CHUNKS if len(c["text"]) > 1500]
print(f"\nOversize chunks (>1500): {len(oversize)}")
for c in oversize:
    print(f"  {c['chunk_id']}: {len(c['text'])} chars (§{c['metadata']['section_number']})")

# Sub-MIN
submin = [c for c in CHUNKS if len(c["text"]) < 200]
print(f"\nSub-MIN chunks (<200): {len(submin)}")

# Metadata coverage
no_hp = [c for c in CHUNKS if not c["metadata"].get("hierarchy_path")]
print(f"\nChunks missing hierarchy_path: {len(no_hp)}")
no_chunk_n = [c for c in CHUNKS if c["metadata"].get("chunk_n") is None]
print(f"Chunks missing chunk_n: {len(no_chunk_n)}")

# Mid-example break check (within a single chunk's body, count Example: starts;
# if a chunk has >1 with example bodies in between, that's the unit-as-chunk
# pattern — fine. The pathological case is a chunk whose FIRST line is
# inside an example body but doesn't itself look like an example-start.)
ex_starts_re = re.compile(r"^\s*Example(\s+of\s+[^:]{0,80})?:", re.MULTILINE)
print("\nExample-start-line counts in §1170.5 chunks:")
for c in for_section("1170.5"):
    body = c["text"].split("\n\n", 1)[1] if "\n\n" in c["text"] else c["text"]
    n = len(ex_starts_re.findall(body))
    first_body_line = body.split("\n", 1)[0]
    is_ex = bool(re.match(r"^\s*Example(\s+of\s+[^:]{0,80})?:", first_body_line))
    print(f"  chunk {c['metadata']['chunk_n']}: {n} example-starts, "
          f"first-line-is-example-start={is_ex}, len={len(c['text'])}")
