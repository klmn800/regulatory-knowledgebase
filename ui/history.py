"""
Search history persistence via SQLite.

Stores past questions, answers, and evidence for review.
Database created automatically at data/search_history.db.
"""

import json
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "output" / "search_history.db"


def _get_conn() -> sqlite3.Connection:
    """Get a SQLite connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create the searches table if it doesn't exist; add new columns if missing."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            sources TEXT NOT NULL,
            program_filter TEXT,
            deep INTEGER DEFAULT 0,
            answer TEXT NOT NULL,
            evidence TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cost REAL DEFAULT 0,
            duration_seconds REAL DEFAULT 0,
            model TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Per-source filter column added 2026-05-01. Legacy `program_filter` (a
    # preset string like "snap_only") stays around for old rows; new rows
    # write to `programs_by_source` (JSON dict source -> list[str]) instead.
    existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(searches)")}
    if "programs_by_source" not in existing_cols:
        conn.execute("ALTER TABLE searches ADD COLUMN programs_by_source TEXT")

    conn.commit()
    conn.close()


def save_search(
    question: str,
    sources: list[str],
    programs_by_source: dict[str, list[str]],
    deep: bool,
    result,
) -> int:
    """Save a synthesis result to history. Returns the new row ID."""
    # Serialize evidence: keep metadata + score + full text
    evidence_summary = {}
    for source_key, results_list in result.evidence.items():
        evidence_summary[source_key] = [
            {
                "score": r["score"],
                "metadata": r["metadata"],
                "text": r["text"],
                "id": r.get("id", ""),
            }
            for r in results_list
        ]

    conn = _get_conn()
    cursor = conn.execute(
        """INSERT INTO searches
           (question, sources, program_filter, programs_by_source, deep,
            answer, evidence,
            input_tokens, output_tokens, cost, duration_seconds, model)
           VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            question,
            json.dumps(sources),
            json.dumps(programs_by_source, ensure_ascii=False),
            1 if deep else 0,
            result.answer,
            json.dumps(evidence_summary, ensure_ascii=False),
            result.input_tokens,
            result.output_tokens,
            result.cost,
            result.duration_seconds,
            result.model,
        ),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_recent(limit: int = 20) -> list[dict]:
    """Get recent searches, newest first."""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT id, question, sources, program_filter, programs_by_source,
                  deep, duration_seconds, cost, created_at
           FROM searches ORDER BY id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_by_id(search_id: int) -> dict | None:
    """Get a single search by ID, including full answer and evidence."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM searches WHERE id = ?", (search_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    result = _row_to_dict(row)
    result["answer"] = row["answer"]
    result["evidence"] = json.loads(row["evidence"])
    result["input_tokens"] = row["input_tokens"]
    result["output_tokens"] = row["output_tokens"]
    result["model"] = row["model"]
    return result


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a Row to a plain dict with parsed JSON fields."""
    pbs_raw = row["programs_by_source"] if "programs_by_source" in row.keys() else None
    programs_by_source = json.loads(pbs_raw) if pbs_raw else None

    return {
        "id": row["id"],
        "question": row["question"],
        "sources": json.loads(row["sources"]),
        "program_filter": row["program_filter"],
        "programs_by_source": programs_by_source,
        "deep": bool(row["deep"]),
        "duration_seconds": row["duration_seconds"],
        "cost": row["cost"],
        "created_at": row["created_at"],
    }
