"""Exact phrase search, pure functions (PRD 0002 task 4.0). Synthetic text only."""

import random

import pytest

from rag.exact_search import (
    EmptyPhraseError,
    attribute,
    build_stream,
    exact_search,
    find_matches,
    normalize,
    normalize_with_map,
    order_chunks,
)


# ---------------------------------------------------------------- normalization

@pytest.mark.parametrize("raw, expected", [
    ("Income LIMITS", "income limits"),                       # case-fold
    ("Straße", "strasse"),                                    # full case-fold
    ("the ‘client’s’ “form”", "the 'client's' \"form\""),  # quotes
    ("a‐b‑c‒d–e—f−g－h", "a-b-c-d-e-f-g-h"),   # dashes
    ("a b c d", "a b c d"),                    # unicode spaces
    ("in­come ve​rifi‍cation﻿", "income verification"),  # removed chars
    ("## Heading\nbody", "heading body"),                     # heading marker
    ("  ### Deep heading", "deep heading"),                   # indented marker
    ("#hashtag stays", "#hashtag stays"),                     # not a heading
    ("Step 1 # not at line start", "step 1 # not at line start"),
    ("a \t\n\n  b", "a b"),                                   # whitespace run
    ("   padded   ", "padded"),                               # trim
])
def test_normalize_rules(raw, expected):
    assert normalize(raw) == expected


def test_normalize_with_map_matches_normalize_and_maps_back():
    raw = "## Title\n\nThe  “SNAP”—rule"
    norm, omap = normalize_with_map(raw)
    assert norm == normalize(raw) == 'title the "snap"-rule'
    assert len(omap) == len(norm)
    start = norm.index("snap")
    assert raw[omap[start]:omap[start + 3] + 1] == "SNAP"


def test_normalize_with_map_agrees_on_random_text():
    alphabet = list("ab #\n\t ​­—’“Xß-")
    rng = random.Random(7)
    for _ in range(3000):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
        assert normalize_with_map(s)[0] == normalize(s), repr(s)


def test_find_matches_non_overlapping_and_substring():
    assert find_matches("aa", "aaaa") == [0, 2]
    assert find_matches("snap", "snap and snapshot") == [0, 9]


# ---------------------------------------------------------------- attribution

def _chunk(cid, body, prefix="P > Q", program="SNAP"):
    return {"id": cid, "text": f"{prefix}\n\n{body}", "metadata": {"program": program}}


def _doc(did, text, program="SNAP", title=None):
    meta = {"program": program}
    if title:
        meta["title"] = title
    return {"id": did, "text": text, "metadata": meta}


def test_phrase_straddling_chunk_boundary():
    chunks = [_chunk("c__000", "alpha beta"), _chunk("c__001", "gamma delta")]
    doc = _doc("p1", "alpha beta\n\ngamma delta")
    res = exact_search("beta gamma", [doc], lambda pid: chunks)
    (r,) = res["results"]
    assert r["id"] == "c__000"
    assert r["chunk_ids"] == ["c__000", "c__001"]
    assert r["match_count"] == 1


def test_heading_crossing_phrase_aligns_to_chunk_under_heading():
    chunks = [_chunk("c__000", "intro text", prefix="Page > Overview"),
              _chunk("c__001", "alpha beta", prefix="Page > Rules"),
              _chunk("c__002", "more alpha", prefix="Page > Rules")]
    doc = _doc("p1", "## Overview\nintro text\n\n## Rules\nalpha beta\n\nmore alpha")
    res = exact_search("rules alpha", [doc], lambda pid: chunks)
    (r,) = res["results"]
    assert r["id"] == "c__001" and r["chunk_ids"] == ["c__001"]
    # A heading on its own lands on the first chunk under it, not on the
    # split-off chunk that repeats the same prefix.
    res = exact_search("rules", [doc], lambda pid: chunks)
    assert [r["id"] for r in res["results"]] == ["c__001"]
    # A phrase crossing from one section's body into the next heading.
    res = exact_search("intro text rules", [doc], lambda pid: chunks)
    assert res["results"][0]["chunk_ids"] == ["c__000", "c__001"]


def test_body_alignment_unchanged_by_heading_pass():
    chunks = [_chunk("c__000", "rules apply here", prefix="Page > Rules")]
    doc = _doc("p1", "## Rules\nrules apply here")
    res = exact_search("rules", [doc], lambda pid: chunks)
    (r,) = res["results"]
    assert r["id"] == "c__000" and r["match_count"] == 2


def test_text_missing_from_chunks_is_reported_unaligned():
    chunks = [_chunk("c__000", "alpha beta", prefix="Page > Rules")]
    doc = _doc("p1", "## Rules\nalpha beta\n\nomitted history text", title="Rules page")
    res = exact_search("omitted history", [doc], lambda pid: chunks)
    (r,) = res["results"]
    assert r["id"] is None and r["chunk_ids"] == []
    assert r["parent_id"] == "p1"
    assert r["text"] == doc["text"]
    assert r["metadata"]["page_title"] == "Rules page"


def test_heading_occurrence_does_not_shift_later_attribution():
    chunks = [_chunk("c__000", "Income is counted monthly for every household member.")]
    doc = _doc("p1", "## Income\n\nIncome is counted monthly for every household member.")
    stream, spans = build_stream(chunks)
    parent = normalize(doc["text"])
    offsets = find_matches("income", parent)
    assert attribute("income", parent, offsets, stream, spans) == [None, [0]]


def test_order_chunks_follows_parent_text():
    chunks = [_chunk("b__000", "second part here"), _chunk("a__000", "first part here")]
    parent = normalize("first part here\n\nsecond part here")
    assert [c["id"] for c in order_chunks(parent, chunks)] == ["a__000", "b__000"]


# ---------------------------------------------------------------- ranking and totals

def _corpus():
    docs = [
        _doc("p_b", "x rule one\n\nx rule two", program="SNAP"),
        _doc("p_a", "x rule three\n\nx rule four", program="TAFDC"),
        _doc("p_c", "x rule five\n\nx rule left out of the chunks", program="SNAP",
             title="C"),
    ]
    chunks = {
        "p_b": [_chunk("b__000", "x rule one"), _chunk("b__001", "x rule two")],
        "p_a": [_chunk("a__000", "x rule three", program="TAFDC"),
                _chunk("a__001", "x rule four", program="TAFDC")],
        "p_c": [_chunk("c__000", "x rule five", prefix="C > X rule heading")],
    }
    return docs, chunks


def test_ordering_by_parent_count_then_id_unaligned_last():
    docs, chunks = _corpus()
    res = exact_search("x rule", docs, chunks.get)
    order = [(r["parent_id"], r["id"]) for r in res["results"]]
    # Every parent has 2 matches, so ties break by parent id; p_c's second
    # match isn't in any chunk, so it can't be aligned and comes last.
    assert order == [("p_a", "a__000"), ("p_a", "a__001"),
                     ("p_b", "b__000"), ("p_b", "b__001"),
                     ("p_c", "c__000"), ("p_c", None)]
    assert [r["rank"] for r in res["results"]] == [1, 2, 3, 4, 5, 6]
    assert res["total_matches"] == 6


def test_parent_with_more_matches_ranks_first():
    docs = [_doc("p_a", "tick"), _doc("p_z", "tick tick tick")]
    chunks = {"p_a": [_chunk("a__000", "tick")], "p_z": [_chunk("z__000", "tick tick tick")]}
    res = exact_search("tick", docs, chunks.get)
    assert [r["parent_id"] for r in res["results"]] == ["p_z", "p_a"]
    assert res["results"][0]["match_count"] == 3


def test_top_caps_results_and_reports_totals():
    docs, chunks = _corpus()
    res = exact_search("x rule", docs, chunks.get, top=2)
    assert res["result_count"] == 2
    assert res["total_results"] == 6
    assert res["total_matches"] == 6
    assert res["truncated"] is True
    full = exact_search("x rule", docs, chunks.get)
    assert full["truncated"] is False and full["result_count"] == 6


def test_program_filter_applies_to_chunks_and_unaligned_parent():
    docs, chunks = _corpus()
    res = exact_search("x rule", docs, chunks.get,
                       filter_fn=lambda m: m.get("program") == "SNAP")
    assert {r["parent_id"] for r in res["results"]} == {"p_b", "p_c"}
    assert res["total_matches"] == 4
    res = exact_search("x rule", docs, chunks.get,
                       filter_fn=lambda m: m.get("program") == "TAFDC")
    assert [r["id"] for r in res["results"]] == ["a__000", "a__001"]


def test_snippets_capped_at_three():
    body = " ".join(["word"] * 10)
    res = exact_search("word", [_doc("p", body)], lambda pid: [_chunk("c__000", body)])
    (r,) = res["results"]
    assert r["match_count"] == 10 and len(r["snippets"]) == 3


def test_context_attaches_parent_document():
    docs, chunks = _corpus()
    res = exact_search("x rule one", docs, chunks.get, include_context=True)
    assert res["results"][0]["parent_context"]["text"] == docs[0]["text"]
    res = exact_search("x rule one", docs, chunks.get)
    assert res["results"][0]["parent_context"] is None


def test_no_match_returns_empty():
    docs, chunks = _corpus()
    res = exact_search("nothing like this", docs, chunks.get)
    assert res["result_count"] == 0 and res["results"] == []
    assert res["truncated"] is False


@pytest.mark.parametrize("phrase", ["", "   ", "​", "##"])
def test_empty_phrase_raises(phrase):
    with pytest.raises(EmptyPhraseError):
        exact_search(phrase, [], lambda pid: [])


def test_reordered_duplicate_examples_all_align():
    # Parent text lists two repeated examples as A B A B; the chunks hold A A B B.
    a = "Example of a restored benefit: an allotment was authorized for the month."
    b = "Example of a retroactive benefit: an allotment was authorized for the month."
    chunks = [_chunk("s1__000", a), _chunk("s1__001", a),
              _chunk("s2__000", b), _chunk("s2__001", b)]
    parent = normalize("\n\n".join([a, b, a, b]))
    stream, spans = build_stream(chunks)
    offsets = find_matches("an allotment was authorized", parent)
    got = attribute("an allotment was authorized", parent, offsets, stream, spans)
    assert None not in got
    assert sorted(g[0] for g in got) == [0, 1, 2, 3]
    assert {got[0][0], got[2][0]} == {0, 1} and {got[1][0], got[3][0]} == {2, 3}
