"""Tests for rag/build_record.py. All records are written to a temp index root."""

import json
from datetime import datetime, timedelta, timezone

from rag import build_record as br

TZ = timezone(timedelta(hours=-5))


def test_round_trip_one_stage(tmp_path):
    when = datetime(2026, 4, 30, 17, 4, 33, tzinfo=TZ)
    assert br.record_stage("olg", "scrape", counts={"pages": 3},
                           index_root=tmp_path, when=when)
    info = br.read_index_info("olg", index_root=tmp_path)
    assert info["record_status"] == "present"
    scrape = info["stages"]["scrape"]
    assert scrape["date"] == "2026-04-30"
    assert scrape["completed_at"] == "2026-04-30T17:04:33-05:00"
    assert scrape["counts"] == {"pages": 3}
    # Unrecorded stages are present and unknown
    for name in ("chunk", "embed", "sparse"):
        assert info["stages"][name]["date"] == "unknown"
    assert list(info["stages"]) == ["scrape", "chunk", "embed", "sparse"]


def test_second_stage_merges_without_losing_first(tmp_path):
    br.record_stage("fns", "parse", counts={"sections": 2}, index_root=tmp_path,
                    date="2026-05-02")
    br.record_stage("fns", "chunk", counts={"chunks": 5}, index_root=tmp_path,
                    date="2026-05-03")
    raw = json.loads(br.record_path("fns", tmp_path).read_text(encoding="utf-8"))
    assert raw["schema_version"] == 1 and raw["source"] == "fns"
    assert set(raw["stages"]) == {"parse", "chunk"}
    # date without `when` → completed_at is null
    assert raw["stages"]["parse"]["completed_at"] is None


def test_embed_stage_date_is_oldest_collection(tmp_path):
    br.record_embed_collection("cmr", "chapters", "cmr_chapters", "m-broad", 18,
                               index_root=tmp_path, date="2026-05-04")
    br.record_embed_collection("cmr", "sections", "cmr_sections", "m-sec", 1415,
                               index_root=tmp_path, date="2026-06-01")
    embed = br.read_index_info("cmr", index_root=tmp_path)["stages"]["embed"]
    assert embed["date"] == "2026-05-04"
    assert embed["counts"] == {"chapters": 18, "sections": 1415}
    colls = embed["details"]["collections"]
    assert colls["sections"]["model"] == "m-sec"
    # Re-embedding the stale tier moves the stage date forward
    br.record_embed_collection("cmr", "chapters", "cmr_chapters", "m-broad", 18,
                               index_root=tmp_path, date="2026-06-02")
    embed = br.read_index_info("cmr", index_root=tmp_path)["stages"]["embed"]
    assert embed["date"] == "2026-06-01"


def test_missing_record_reads_as_unknown(tmp_path):
    info = br.read_index_info("cfr", index_root=tmp_path)
    assert info["record_status"] == "missing"
    assert all(s["date"] == "unknown" for s in info["stages"].values())
    assert list(info["stages"]) == ["parse", "chunk", "embed", "sparse"]


def test_unreadable_record_reads_as_unknown(tmp_path):
    path = br.record_path("olg", tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    info = br.read_index_info("olg", index_root=tmp_path)
    assert info["record_status"] == "unreadable"
    assert info["stages"]["scrape"]["date"] == "unknown"


def test_write_over_unreadable_record_recovers(tmp_path, capsys):
    path = br.record_path("olg", tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    assert br.record_stage("olg", "chunk", index_root=tmp_path, date="2026-05-01")
    assert br.read_index_info("olg", index_root=tmp_path)["record_status"] == "present"
    assert "unreadable" in capsys.readouterr().err


def test_write_failure_returns_false_and_does_not_raise(tmp_path, capsys):
    # index_root is a file, so the source directory can't be created
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    assert br.record_stage("olg", "scrape", index_root=blocker) is False
    assert "Warning: build record" in capsys.readouterr().err


def test_invalid_stage_for_source_is_rejected_without_raising(tmp_path):
    assert br.record_stage("olg", "parse", index_root=tmp_path) is False
    assert not br.record_path("olg", tmp_path).exists()


def test_format_text_summary(tmp_path):
    br.record_stage("olg", "scrape", index_root=tmp_path, date="2026-04-30")
    line = br.format_index_info_text(br.read_index_info("olg", index_root=tmp_path))
    assert line.startswith("Index build (olg): scraped 2026-04-30 | chunked unknown")
    missing = br.format_index_info_text(br.read_index_info("fns", index_root=tmp_path))
    assert "[build record missing]" in missing
