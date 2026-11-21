"""Pipeline stages write their build record (task 2.0). Temp index roots only."""

from datetime import datetime, timezone

from rag import build_record as br
from rag.sparse_index import build_sparse_index, save_index


def _chunks():
    return [
        {"chunk_id": "sec__A__000", "text": "Synthetic alpha text about income."},
        {"chunk_id": "sec__A__001", "text": "Synthetic beta text about resources."},
    ]


def test_save_index_records_sparse_stage(tmp_path):
    idx = build_sparse_index("olg", _chunks())
    save_index(idx, tmp_path / "sparse" / "olg.pkl")
    info = br.read_index_info("olg", index_root=tmp_path)
    sparse = info["stages"]["sparse"]
    assert sparse["counts"] == {"chunks": 2}
    assert sparse["date"] == datetime.fromtimestamp(idx.built_at).date().isoformat()
    assert sparse["completed_at"] is not None


def test_save_index_outside_sparse_dir_does_not_record(tmp_path):
    idx = build_sparse_index("olg", _chunks())
    save_index(idx, tmp_path / "eval" / "olg.pkl")
    assert not br.record_path("olg", tmp_path).exists()
    assert not br.record_path("olg", tmp_path / "eval").exists()


def test_save_index_record_false_does_not_record(tmp_path):
    idx = build_sparse_index("fns", _chunks())
    save_index(idx, tmp_path / "sparse" / "fns.pkl", record=False)
    assert not br.record_path("fns", tmp_path).exists()


def test_embedder_skips_record_for_evaluation_runs():
    from rag.embedder import should_record_build
    assert should_record_build(None, None) is True
    assert should_record_build("voyage4large", None) is False
    assert should_record_build(None, "index/cfr/section_chunks_fullpath.json") is False


def test_scrape_stage_dated_by_oldest_page(tmp_path):
    progress = {
        "u1": {"status": "success", "scraped_at": "2026-04-28T10:00:00+00:00"},
        "u2": {"status": "success", "scraped_at": "2026-04-30T21:00:00+00:00"},
        "u3": {"status": "404"},
        "u4": {"status": "failed"},
    }
    when = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    assert br.record_scrape_from_progress(progress, index_root=tmp_path, when=when)
    scrape = br.read_index_info("olg", index_root=tmp_path)["stages"]["scrape"]
    oldest_local = datetime(2026, 4, 28, 10, 0, tzinfo=timezone.utc).astimezone()
    assert scrape["date"] == oldest_local.date().isoformat()
    assert scrape["counts"] == {"pages_scraped": 2, "not_found_404": 1, "failed": 1}
    assert "oldest_page_fetched_at" in scrape["details"]


def test_scrape_stage_not_recorded_without_successes(tmp_path):
    assert br.record_scrape_from_progress({"u": {"status": "404"}},
                                          index_root=tmp_path) is False
    assert not br.record_path("olg", tmp_path).exists()
