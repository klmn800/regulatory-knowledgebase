"""query.py CLI contract (PRD 0002 task 3.0). Offline: ChromaDB and Voyage are faked,
the project root is a temp directory, and every document is synthetic."""

import json

import pytest
from chromadb.errors import NotFoundError
from voyageai.error import APIConnectionError

from rag import query as q
from rag import build_record as br
from rag.sparse_index import build_sparse_index, save_index


# ---------------------------------------------------------------- fakes

SECTIONS = {
    "sec__SNAP__Alpha__000": ("SNAP > Alpha\n\nSynthetic text about income rules.",
                              {"program": "SNAP", "parent_page_id": "page__alpha",
                               "url": "https://example.test/alpha.htm", "chunk_n": 0}),
    "sec__SNAP__Alpha__001": ("SNAP > Alpha\n\nSynthetic text about form XY-9.",
                              {"program": "SNAP", "parent_page_id": "page__alpha",
                               "url": "https://example.test/alpha.htm", "chunk_n": 1}),
    "sec__TAFDC__Beta__000": ("TAFDC > Beta\n\nSynthetic text about resources.",
                              {"program": "TAFDC", "parent_page_id": "page__beta",
                               "url": "https://example.test/beta.htm", "chunk_n": 0}),
}
PAGES = {
    "page__alpha": ("# Alpha\n\nSynthetic text about income rules.\n\n"
                    "Synthetic text about form XY-9.",
                    {"title": "Alpha", "program": "SNAP"}),
    "page__beta": ("# Beta\n\nSynthetic text about resources.",
                   {"title": "Beta", "program": "TAFDC"}),
}


def _matches(meta, where):
    if not where:
        return True
    (field, cond), = where.items()
    if isinstance(cond, dict):
        if "$in" in cond:
            return meta.get(field) in cond["$in"]
        if "$nin" in cond:
            return meta.get(field) not in cond["$nin"]
    return meta.get(field) == cond


class FakeCollection:
    def __init__(self, docs):
        self.docs = docs

    def get(self, ids=None, where=None, include=None, limit=None):
        keys = [i for i in (ids if ids is not None else self.docs) if i in self.docs]
        keys = [k for k in keys if _matches(self.docs[k][1], where)]
        return {"ids": keys,
                "documents": [self.docs[k][0] for k in keys],
                "metadatas": [self.docs[k][1] for k in keys]}

    def query(self, query_embeddings, n_results, include=None, where=None):
        keys = [k for k in self.docs if _matches(self.docs[k][1], where)][:n_results]
        return {"ids": [keys],
                "documents": [[self.docs[k][0] for k in keys]],
                "metadatas": [[self.docs[k][1] for k in keys]],
                "distances": [[0.2 + 0.1 * i for i in range(len(keys))]]}


class FakeChroma:
    collections = {"sections": SECTIONS, "pages": PAGES}

    def __init__(self, path=None, settings=None):
        pass

    def get_collection(self, name):
        if name not in self.collections:
            raise NotFoundError(f"Collection [{name}] does not exist")
        return FakeCollection(self.collections[name])


class FakeVoyage:
    def __init__(self, api_key=None):
        pass


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A temp project root with config.ini, a ChromaDB dir and fakes installed."""
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    config = tmp_path / "config.ini"
    config.write_text("[api]\nvoyage_api_key = test-key\n\n"
                      f"[chromadb]\npersist_dir = {chroma_dir.as_posix()}\n",
                      encoding="utf-8")
    monkeypatch.setattr(q, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(q, "CONFIG_FILE", config)
    monkeypatch.setattr(q, "OLG_PROGRAMS_WHITELIST", None)
    monkeypatch.setattr(q.chromadb, "PersistentClient", FakeChroma)
    monkeypatch.setattr(q.voyageai, "Client", FakeVoyage)
    monkeypatch.setattr(q, "embed_query", lambda text, client, model: [0.0, 1.0])
    monkeypatch.delenv("QUERY_DEBUG", raising=False)
    monkeypatch.setattr(FakeChroma, "collections",
                        {"sections": SECTIONS, "pages": PAGES})
    return tmp_path


def _sparse_index(root, source="olg"):
    chunks = [{"chunk_id": cid, "text": text} for cid, (text, _) in SECTIONS.items()]
    save_index(build_sparse_index(source, chunks),
               root / "index" / "sparse" / f"{source}.pkl", record=False)


def run(capsys, *argv):
    code = q.main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def run_json(capsys, *argv):
    code, out, err = run(capsys, *argv, "--json")
    return code, json.loads(out), err


# ---------------------------------------------------------------- success JSON

def test_search_json_has_envelope_and_unchanged_fields(env, capsys):
    code, data, err = run_json(capsys, "income")
    assert code == 0 and err == ""
    assert data["contract_version"] == "1.0"
    assert data["command"] == "search"
    assert data["index"]["source"] == "olg"
    assert data["index"]["record_status"] == "missing"
    assert data["index"]["stages"]["embed"]["date"] == "unknown"

    clients = q.create_client("olg")
    direct = json.loads(json.dumps(q.search_with_client("income", clients)))
    assert {k: v for k, v in data.items()
            if k not in ("contract_version", "command", "index")} == direct
    assert data["mode"] == "dense"


def test_index_block_reads_build_record(env, capsys):
    br.record_stage("olg", "chunk", counts={"sections": 3},
                    index_root=env / "index", date="2026-05-01")
    _, data, _ = run_json(capsys, "income")
    assert data["index"]["record_status"] == "present"
    assert data["index"]["stages"]["chunk"]["date"] == "2026-05-01"


def test_chunk_and_url_json_have_envelope(env, capsys):
    code, data, _ = run_json(capsys, "--chunk-id", "sec__SNAP__Alpha__000",
                             "--neighbors", "1")
    assert code == 0
    assert data["command"] == "chunk"
    assert data["target_chunk_id"] == "sec__SNAP__Alpha__000"
    assert data["chunk_count"] == 2 and "index" in data

    code, data, _ = run_json(capsys, "--url", "https://example.test/alpha.htm")
    assert code == 0 and data["command"] == "url" and data["chunk_count"] == 2


def test_list_json_shape_olg(env, capsys):
    code, data, _ = run_json(capsys, "--list-programs")
    assert code == 0 and data["command"] == "list"
    assert data["programs"] == [{"program": "SNAP", "chunk_count": 2},
                                {"program": "TAFDC", "chunk_count": 1}]
    assert data["structure"] is None
    assert data["total_chunks"] == 3


def test_list_does_not_need_api_key(env, capsys):
    (env / "config.ini").write_text(
        f"[chromadb]\npersist_dir = {(env / 'chroma').as_posix()}\n", encoding="utf-8")
    code, _, _ = run_json(capsys, "--list-programs")
    assert code == 0


def test_list_text_ends_with_index_line(env, capsys):
    code, out, _ = run(capsys, "--list-programs")
    assert code == 0
    assert "Total: 3 chunks across 2 programs" in out
    assert "Index build (olg): scraped unknown" in out
    assert "[build record missing]" in out


def test_collect_source_info_structure_for_cmr():
    metas = [{"chapter": "362", "chapter_title": "T1", "program": "SNAP"},
             {"chapter": "362", "chapter_title": "T1", "program": "SNAP"},
             {"chapter": "343", "chapter_title": "T2", "program": "Hearings"}]
    info = q.collect_source_info("cmr", metas)
    assert info["structure"] == [
        {"key": "343", "title": "T2", "chunk_count": 1, "program": "Hearings"},
        {"key": "362", "title": "T1", "chunk_count": 2, "program": "SNAP"},
    ]
    assert info["total_chunks"] == 3


def test_guardrail_empty_response_has_envelope(env, capsys, monkeypatch):
    monkeypatch.setattr(q, "OLG_PROGRAMS_WHITELIST", ["SNAP"])
    code, data, _ = run_json(capsys, "income", "--program", "TAFDC")
    assert code == 0
    assert data["command"] == "search" and data["result_count"] == 0
    assert data["filters"] == {"olg_programs_guardrail": "no_match"}
    assert "index" in data


# ---------------------------------------------------------------- --mode

def test_mode_passes_through(env, capsys):
    _sparse_index(env)
    code, data, _ = run_json(capsys, "form XY-9", "--mode", "sparse")
    assert code == 0 and data["mode"] == "sparse"
    assert data["results"][0]["id"] == "sec__SNAP__Alpha__001"

    code, data, _ = run_json(capsys, "form XY-9", "--mode", "hybrid")
    assert code == 0 and data["mode"] == "hybrid"
    assert all("rrf_score" in r for r in data["results"])


@pytest.mark.parametrize("mode", ["sparse", "hybrid"])
def test_broad_collection_with_sparse_modes_is_usage(env, capsys, mode):
    _sparse_index(env)
    code, data, err = run_json(capsys, "income", "--collection", "pages",
                               "--mode", mode)
    assert code == 2 and data["error"]["kind"] == "usage"


def test_missing_sparse_index_is_unavailable(env, capsys):
    code, data, _ = run_json(capsys, "income", "--mode", "hybrid")
    assert code == 3 and data["error"]["kind"] == "unavailable"
    assert "sparse index" in data["error"]["message"]


def test_api_raises_sparse_index_missing(env):
    clients = q.create_client("olg")
    with pytest.raises(q.SparseIndexMissingError):
        q.search_with_client("income", clients, mode="sparse")
    assert issubclass(q.SparseIndexMissingError, FileNotFoundError)


def test_api_broad_collection_still_downgrades_to_dense(env):
    clients = q.create_client("olg")
    resp = q.search_with_client("income", clients, collection="pages", mode="hybrid")
    assert resp["mode"] == "dense"


# ---------------------------------------------------------------- usage errors (2)

@pytest.mark.parametrize("argv", [
    [],                                              # no command
    ["income", "--chunk-id", "x"],                   # two commands
    ["--url", "https://example.test/a.htm", "--list-programs"],
    ["--url", "https://example.test/a.htm", "--source", "fns"],
    ["income", "--collection", "parts"],             # wrong tier for olg
    ["income", "--top", "abc"],                      # argparse type error
    ["income", "--no-such-flag"],
    ["income", "--program", "NOPE"],                 # unknown program
    ["   "],                                         # empty query
])
def test_usage_errors_exit_2(env, capsys, argv):
    code, out, err = run(capsys, *argv)
    assert code == 2
    assert out == ""
    assert err.startswith("query.py: error [usage]: ")
    assert err.count("\n") == 1


def test_argparse_error_json_object(env, capsys):
    code, out, err = run(capsys, "income", "--top", "abc", "--source", "cfr", "--json")
    data = json.loads(out)
    assert code == 2
    assert data["contract_version"] == "1.0"
    assert data["command"] == "search"
    assert data["error"] == {"kind": "usage", "exit_code": 2,
                             "message": "argument --top/-n: invalid int value: 'abc'"}
    assert data["index"]["source"] == "cfr"


def test_error_json_index_null_when_source_unknown(env, capsys):
    code, out, _ = run(capsys, "income", "--source", "xyz", "--json")
    assert code == 2 and json.loads(out)["index"] is None


# ---------------------------------------------------------------- unavailable (3)

def test_missing_config_is_unavailable(env, capsys):
    (env / "config.ini").unlink()
    code, data, err = run_json(capsys, "income")
    assert code == 3 and data["error"]["kind"] == "unavailable"
    assert "config file not found" in err


def test_missing_api_key_is_unavailable(env, capsys):
    (env / "config.ini").write_text("[api]\n", encoding="utf-8")
    code, _, err = run(capsys, "income")
    assert code == 3 and "voyage_api_key" in err


def test_missing_chroma_dir_is_unavailable(env, capsys):
    (env / "chroma").rmdir()
    code, out, err = run(capsys, "--chunk-id", "x")
    assert code == 3 and out == "" and "ChromaDB directory not found" in err


def test_missing_collection_is_unavailable(env, capsys, monkeypatch):
    monkeypatch.setattr(FakeChroma, "collections", {"sections": SECTIONS})
    code, _, err = run(capsys, "income", "--collection", "pages")
    assert code == 3 and "'pages'" in err


# ---------------------------------------------------------------- api (4), internal (5)

def test_voyage_failure_is_api(env, capsys, monkeypatch):
    def boom(*a, **k):
        raise APIConnectionError("connection refused")
    monkeypatch.setattr(q, "embed_query", boom)
    code, data, err = run_json(capsys, "income")
    assert code == 4 and data["error"]["kind"] == "api"
    assert "APIConnectionError" in err


def test_unexpected_failure_is_internal(env, capsys, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("synthetic failure")
    monkeypatch.setattr(q, "embed_query", boom)
    code, out, err = run(capsys, "income")
    assert code == 5 and out == ""
    assert err == "query.py: error [internal]: RuntimeError: synthetic failure\n"


def test_query_debug_prints_traceback(env, capsys, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("synthetic failure")
    monkeypatch.setattr(q, "embed_query", boom)
    monkeypatch.setenv("QUERY_DEBUG", "1")
    code, _, err = run(capsys, "income")
    assert code == 5
    assert "Traceback" in err
    assert err.rstrip().splitlines()[-1].startswith("query.py: error [internal]")


# ---------------------------------------------------------------- --exact

def test_exact_json(env, capsys):
    code, data, err = run_json(capsys, "--exact", "Synthetic TEXT")
    assert code == 0 and err == ""
    assert data["command"] == "exact" and data["contract_version"] == "1.0"
    assert data["phrase"] == "Synthetic TEXT"
    assert data["normalized_phrase"] == "synthetic text"
    assert data["total_matches"] == 3 and data["total_results"] == 3
    assert data["truncated"] is False
    assert data["results"][0]["parent_id"] == "page__alpha"
    assert data["results"][0]["id"] == "sec__SNAP__Alpha__000"
    assert "index" in data


def test_exact_needs_no_api_key_or_config(env, capsys):
    (env / "config.ini").write_text(
        f"[chromadb]\npersist_dir = {(env / 'chroma').as_posix()}\n", encoding="utf-8")
    assert run_json(capsys, "--exact", "form xy-9")[0] == 0
    (env / "config.ini").unlink()
    (env / "index" / "chroma_db").mkdir(parents=True)   # the default persist_dir
    code, data, _ = run_json(capsys, "--exact", "form xy-9")
    assert code == 0 and data["result_count"] == 1


def test_exact_never_calls_voyage(env, capsys, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("Voyage called")
    monkeypatch.setattr(q, "embed_query", boom)
    monkeypatch.setattr(q.voyageai, "Client", boom)
    assert run_json(capsys, "--exact", "income")[0] == 0


def test_exact_top_and_program_filter(env, capsys):
    _, data, _ = run_json(capsys, "--exact", "synthetic", "--top", "1")
    assert data["result_count"] == 1 and data["total_results"] == 3
    assert data["truncated"] is True
    _, data, _ = run_json(capsys, "--exact", "synthetic", "--program", "tafdc")
    assert data["filters"] == {"program": "TAFDC"}
    assert [r["id"] for r in data["results"]] == ["sec__TAFDC__Beta__000"]


def test_exact_context(env, capsys):
    _, data, _ = run_json(capsys, "--exact", "resources", "--context")
    assert data["results"][0]["parent_context"]["metadata"]["title"] == "Beta"


def test_exact_guardrail(env, capsys, monkeypatch):
    monkeypatch.setattr(q, "OLG_PROGRAMS_WHITELIST", ["SNAP"])
    _, data, _ = run_json(capsys, "--exact", "synthetic")
    assert {r["metadata"]["program"] for r in data["results"]} == {"SNAP"}
    code, data, _ = run_json(capsys, "--exact", "synthetic", "--program", "TAFDC")
    assert code == 0 and data["result_count"] == 0
    assert data["filters"] == {"olg_programs_guardrail": "no_match"}


def test_exact_no_match_is_success(env, capsys):
    code, data, _ = run_json(capsys, "--exact", "nothing like this")
    assert code == 0 and data["result_count"] == 0


@pytest.mark.parametrize("argv", [
    ["--exact", "  "],
    ["--exact", "x", "--mode", "dense"],
    ["--exact", "x", "--threshold", "0.5"],
    ["--exact", "x", "--collection", "sections"],
    ["--exact", "x", "income"],
    ["--exact", "x", "--program", "NOPE"],
])
def test_exact_usage_errors(env, capsys, argv):
    code, data, err = run_json(capsys, *argv)
    assert code == 2 and data["command"] == "exact"
    assert err.startswith("query.py: error [usage]: ")


def test_exact_text_output(env, capsys):
    code, out, _ = run(capsys, "--exact", "form XY-9")
    assert code == 0
    assert 'Found 1 results (1 matches) for exact "form XY-9"' in out
    assert "Chunk:   sec__SNAP__Alpha__001" in out


def test_json_stdout_is_utf8_even_on_a_cp1252_stream(env, monkeypatch):
    import io
    import sys
    buf = io.BytesIO()
    stream = io.TextIOWrapper(buf, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", stream)
    assert q.main(["--exact", "a → b", "--json"]) == 0
    stream.flush()
    assert json.loads(buf.getvalue().decode("utf-8"))["phrase"] == "a → b"


@pytest.mark.parametrize("mode", ["sparse", "hybrid"])
def test_text_output_handles_null_scores(env, capsys, mode, monkeypatch):
    _sparse_index(env)
    # Dense finds nothing, so every hybrid hit is BM25-only (score null).
    monkeypatch.setattr(FakeChroma, "collections",
                        {"sections": SECTIONS, "pages": PAGES})
    monkeypatch.setattr(FakeCollection, "query",
                        lambda self, **k: {"ids": [[]], "documents": [[]],
                                           "metadatas": [[]], "distances": [[]]})
    code, out, err = run(capsys, "form XY-9", "--mode", mode)
    assert code == 0, err
    assert "BM25: " in out
