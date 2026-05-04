"""One-off: rename variant collections into production names.

Idempotent — safe to re-run. Skips swaps already completed.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import chromadb

CHROMA_PATH = PROJECT_ROOT / "index" / "chroma_db"

SWAPS = [
    ("cmr_sections", "cmr_sections_vctx3", "voyage-context-3"),
    ("cmr_chapters", "cmr_chapters_voyage4large", "voyage-4-large"),
    ("sections", "sections_vctx3", "voyage-context-3"),
    ("pages", "pages_v4l", "voyage-4-large"),
]


def main() -> None:
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    existing = {c.name for c in client.list_collections()}

    for prod_name, variant_name, model in SWAPS:
        prod_exists = prod_name in existing
        variant_exists = variant_name in existing

        if not prod_exists and not variant_exists:
            print(f"[SKIP] {prod_name}: neither prod nor variant present")
            continue

        if not variant_exists and prod_exists:
            print(f"[SKIP] {prod_name}: already swapped (variant {variant_name} not found)")
            continue

        variant = client.get_collection(variant_name)
        variant_count = variant.count()

        if prod_exists:
            prod = client.get_collection(prod_name)
            prod_count = prod.count()
            print(f"[SWAP] {prod_name}: prod has {prod_count} (v3), variant {variant_name} has {variant_count} ({model})")
            if variant_count == 0:
                print(f"  ABORT: variant {variant_name} is empty — refusing to swap")
                continue
            client.delete_collection(prod_name)
            print(f"  deleted prod {prod_name}")
            existing.discard(prod_name)
        else:
            print(f"[SWAP] {prod_name}: no prod collection, renaming {variant_name} ({model}, {variant_count} chunks)")

        variant.modify(name=prod_name)
        existing.discard(variant_name)
        existing.add(prod_name)
        print(f"  renamed {variant_name} -> {prod_name}")

    print()
    print("Final collection state:")
    for c in sorted(client.list_collections(), key=lambda c: c.name):
        print(f"  {c.name:40} {c.count():>6} chunks")


if __name__ == "__main__":
    main()
