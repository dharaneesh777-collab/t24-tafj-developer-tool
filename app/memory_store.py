import os
import json
import re
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "learned_patterns.db")

class T24MemoryStore:
    """
    Persistent learning and pattern memory store for Temenos T24/TAFJ.
    Extracts conventions, tables, inserts, and code patterns to improve future generations.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    code TEXT NOT NULL,
                    extracted_routine_name TEXT,
                    extracted_inserts TEXT,
                    extracted_tables TEXT,
                    tags TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def add_sample(self, title: str, category: str, code: str, tags: str = "", notes: str = "") -> Dict[str, Any]:
        """
        Parses and learns from a user-supplied code sample.
        """
        rtn_match = re.search(r"SUBROUTINE\s+([A-Za-z0-9_.]+)", code, re.IGNORECASE)
        routine_name = rtn_match.group(1) if rtn_match else title

        inserts = re.findall(r"\$INSERT\s+([A-Za-z0-9_.]+)", code, re.IGNORECASE)
        inserts_json = json.dumps(list(set(inserts)))

        tables = re.findall(r"(?:FN\.|F\.)([A-Za-z0-9_.]+)", code, re.IGNORECASE)
        tables_json = json.dumps(list(set(tables)))

        created_at = datetime.utcnow().isoformat()

        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO learned_patterns (
                    title, category, code, extracted_routine_name,
                    extracted_inserts, extracted_tables, tags, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, category, code, routine_name,
                inserts_json, tables_json, tags, notes, created_at
            ))
            conn.commit()
            new_id = cursor.lastrowid
        finally:
            conn.close()

        return {
            "id": new_id,
            "title": title,
            "category": category,
            "extracted_routine_name": routine_name,
            "extracted_inserts": list(set(inserts)),
            "extracted_tables": list(set(tables)),
            "created_at": created_at
        }

    def list_samples(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM learned_patterns ORDER BY id DESC")
            rows = cursor.fetchall()
            
            results = []
            for r in rows:
                results.append({
                    "id": r["id"],
                    "title": r["title"],
                    "category": r["category"],
                    "code": r["code"],
                    "extracted_routine_name": r["extracted_routine_name"],
                    "extracted_inserts": json.loads(r["extracted_inserts"]) if r["extracted_inserts"] else [],
                    "extracted_tables": json.loads(r["extracted_tables"]) if r["extracted_tables"] else [],
                    "tags": r["tags"],
                    "notes": r["notes"],
                    "created_at": r["created_at"]
                })
            return results
        finally:
            conn.close()

    def delete_sample(self, sample_id: int) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.execute("DELETE FROM learned_patterns WHERE id = ?", (sample_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_learning_context_for_prompt(self, query: str = "") -> str:
        """
        Retrieves learned patterns to inject into AI reasoning and code generation.
        """
        samples = self.list_samples()
        if not samples:
            return ""

        context_lines = [
            "### LEARNED USER CODING CONVENTIONS & CUSTOM SAMPLES:",
            "The user has provided the following verified reference samples and patterns from their banking environment. "
            "Prioritize these patterns, custom inserts, naming conventions, and table structures when generating code:"
        ]

        for s in samples[:5]:
            context_lines.append(f"\n--- Learned Reference Sample: {s['title']} ({s['category']}) ---")
            if s['notes']:
                context_lines.append(f"User Note: {s['notes']}")
            if s['extracted_inserts']:
                context_lines.append(f"Custom Inserts: {', '.join(s['extracted_inserts'])}")
            if s['extracted_tables']:
                context_lines.append(f"Custom Tables: {', '.join(s['extracted_tables'])}")
            context_lines.append(f"Code Pattern:\n```basic\n{s['code']}\n```")

        return "\n".join(context_lines)
