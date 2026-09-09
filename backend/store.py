import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from models import Fact, Entity, Reconciliation, DocumentMetadata

DB_PATH = "veritas.db"

class StorageEngine:
    """
    SQLite-based bi-temporal storage engine for facts, entities, and reconciliations.
    Preserves audit history and closes validity windows on contradiction rather than deleting.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    total_pages INTEGER NOT NULL,
                    ingested_at TEXT NOT NULL
                )
            """)

            # Entities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    canonical_name TEXT NOT NULL UNIQUE,
                    entity_type TEXT NOT NULL,
                    aliases TEXT NOT NULL
                )
            """)

            # Facts table with bi-temporal fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    normalized_value REAL,
                    unit TEXT,
                    currency TEXT,
                    period_start TEXT,
                    period_end TEXT,
                    fiscal_period TEXT,
                    scope TEXT,
                    doc_id TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    quote TEXT NOT NULL,
                    bbox TEXT,
                    is_verified INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    fact_type TEXT,
                    valid_from TEXT,
                    valid_to TEXT,
                    is_superseded INTEGER DEFAULT 0,
                    superseded_by TEXT,
                    FOREIGN KEY(doc_id) REFERENCES documents(doc_id)
                )
            """)

            # Reconciliations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reconciliations (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    fact_a_id TEXT NOT NULL,
                    fact_b_id TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    axis_of_difference TEXT,
                    confidence REAL NOT NULL,
                    FOREIGN KEY(fact_a_id) REFERENCES facts(id),
                    FOREIGN KEY(fact_b_id) REFERENCES facts(id)
                )
            """)
            conn.commit()

    def save_document(self, doc_id: str, filename: str, total_pages: int):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO documents (doc_id, filename, total_pages, ingested_at) VALUES (?, ?, ?, ?)",
                (doc_id, filename, total_pages, datetime.utcnow().isoformat())
            )
            conn.commit()

    def save_facts(self, facts: List[Fact]):
        with self._get_conn() as conn:
            for f in facts:
                now_str = datetime.utcnow().isoformat()
                conn.execute("""
                    INSERT OR REPLACE INTO facts (
                        id, subject, predicate, object, normalized_value, unit, currency,
                        period_start, period_end, fiscal_period, scope, doc_id, page,
                        quote, bbox, is_verified, confidence, fact_type,
                        valid_from, valid_to, is_superseded, superseded_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f.id, f.subject, f.predicate, f.object, f.normalized_value, f.unit, f.currency,
                    f.period_start, f.period_end, f.fiscal_period, f.scope, f.doc_id, f.page,
                    f.quote, json.dumps(f.bbox) if f.bbox else None, 1 if f.is_verified else 0,
                    f.confidence, f.fact_type, f.valid_from or now_str, f.valid_to,
                    1 if f.is_superseded else 0, f.superseded_by
                ))
            conn.commit()

    def save_reconciliations(self, recs: List[Reconciliation]):
        with self._get_conn() as conn:
            for r in recs:
                conn.execute("""
                    INSERT OR REPLACE INTO reconciliations (
                        id, type, fact_a_id, fact_b_id, reasoning, axis_of_difference, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.id, r.type, r.factA.id, r.factB.id, r.reasoning, r.axis_of_difference, r.confidence
                ))

                # If genuine contradiction, apply bi-temporal invalidation
                if r.type == "contradiction":
                    now_str = datetime.utcnow().isoformat()
                    # Invalidate the older fact (factA if earlier, or whichever was prior)
                    conn.execute("""
                        UPDATE facts SET is_superseded = 1, valid_to = ?, superseded_by = ?
                        WHERE id = ?
                    """, (now_str, r.factB.id, r.factA.id))

            conn.commit()

    def get_all_facts(self) -> List[Fact]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM facts").fetchall()
            return [self._row_to_fact(r) for r in rows]

    def get_fact_by_id(self, fact_id: str) -> Optional[Fact]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM facts WHERE id = ?", (fact_id,)).fetchone()
            if row:
                return self._row_to_fact(row)
        return None

    def get_reconciliations(self, rec_type: Optional[str] = None) -> List[Reconciliation]:
        facts_map = {f.id: f for f in self.get_all_facts()}
        results = []
        with self._get_conn() as conn:
            query = "SELECT * FROM reconciliations"
            params = []
            if rec_type and rec_type != "all":
                query += " WHERE type = ?"
                params.append(rec_type)

            rows = conn.execute(query, params).fetchall()
            for r in rows:
                fa = facts_map.get(r["fact_a_id"])
                fb = facts_map.get(r["fact_b_id"])
                if fa and fb:
                    results.append(Reconciliation(
                        id=r["id"],
                        type=r["type"],
                        factA=fa,
                        factB=fb,
                        reasoning=r["reasoning"],
                        axis_of_difference=r["axis_of_difference"],
                        confidence=r["confidence"]
                    ))
        return results

    def _row_to_fact(self, row: sqlite3.Row) -> Fact:
        bbox = json.loads(row["bbox"]) if row["bbox"] else None
        return Fact(
            id=row["id"],
            subject=row["subject"],
            predicate=row["predicate"],
            object=row["object"],
            normalized_value=row["normalized_value"],
            unit=row["unit"],
            currency=row["currency"],
            period_start=row["period_start"],
            period_end=row["period_end"],
            fiscal_period=row["fiscal_period"],
            scope=row["scope"],
            doc_id=row["doc_id"],
            page=row["page"],
            quote=row["quote"],
            bbox=bbox,
            is_verified=bool(row["is_verified"]),
            confidence=row["confidence"],
            fact_type=row["fact_type"],
            valid_from=row["valid_from"],
            valid_to=row["valid_to"],
            is_superseded=bool(row["is_superseded"]),
            superseded_by=row["superseded_by"]
        )

    def clear_database(self):
        """Clears all stored documents, facts, and reconciliations for a clean demo state."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM reconciliations")
            conn.execute("DELETE FROM facts")
            conn.execute("DELETE FROM documents")
            conn.execute("DELETE FROM entities")
            conn.commit()
