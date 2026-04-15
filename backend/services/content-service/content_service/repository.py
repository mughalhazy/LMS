from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContentRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS content_assets (
                    content_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    storage_uri TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    checksum_sha256 TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    tags_json TEXT NOT NULL,
                    language TEXT,
                    duration_seconds INTEGER,
                    license TEXT,
                    accessibility_notes TEXT,
                    access_policy_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        row = {
            **payload,
            "tags_json": json.dumps(payload["tags"]),
            "access_policy_json": json.dumps(payload["access_policy"]),
            "created_at": now,
            "updated_at": now,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO content_assets (
                    content_id, tenant_id, content_type, storage_uri, version, checksum_sha256,
                    title, description, tags_json, language, duration_seconds, license,
                    accessibility_notes, access_policy_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["content_id"],
                    row["tenant_id"],
                    row["content_type"],
                    row["storage_uri"],
                    row["version"],
                    row["checksum_sha256"],
                    row["title"],
                    row.get("description"),
                    row["tags_json"],
                    row.get("language"),
                    row.get("duration_seconds"),
                    row.get("license"),
                    row.get("accessibility_notes"),
                    row["access_policy_json"],
                    row["created_at"],
                    row["updated_at"],
                ),
            )
        return self.get(payload["content_id"], payload["tenant_id"])

    def get(self, content_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM content_assets WHERE content_id = ? AND tenant_id = ?",
                (content_id, tenant_id),
            ).fetchone()
        return self._decode(row) if row else None

    def update(self, content_id: str, tenant_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get(content_id, tenant_id)
        if not existing:
            return None

        merged = {**existing, **updates}
        merged["updated_at"] = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE content_assets
                SET title = ?, description = ?, tags_json = ?, language = ?, duration_seconds = ?,
                    license = ?, accessibility_notes = ?, access_policy_json = ?, updated_at = ?
                WHERE content_id = ? AND tenant_id = ?
                """,
                (
                    merged["title"],
                    merged.get("description"),
                    json.dumps(merged.get("tags", [])),
                    merged.get("language"),
                    merged.get("duration_seconds"),
                    merged.get("license"),
                    merged.get("accessibility_notes"),
                    json.dumps(merged["access_policy"]),
                    merged["updated_at"],
                    content_id,
                    tenant_id,
                ),
            )
        return self.get(content_id, tenant_id)

    def list_for_tenant(self, tenant_id: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        clauses = ["tenant_id = ?"]
        values: List[Any] = [tenant_id]

        if filters.get("content_type"):
            clauses.append("content_type = ?")
            values.append(filters["content_type"])

        if filters.get("language"):
            clauses.append("language = ?")
            values.append(filters["language"])

        query = f"SELECT * FROM content_assets WHERE {' AND '.join(clauses)} ORDER BY updated_at DESC"
        with self._connect() as conn:
            rows = conn.execute(query, tuple(values)).fetchall()

        decoded = [self._decode(row) for row in rows]
        tag_filter = filters.get("tag")
        if tag_filter:
            decoded = [row for row in decoded if tag_filter in row.get("tags", [])]
        return decoded

    @staticmethod
    def _decode(row: sqlite3.Row) -> Dict[str, Any]:
        as_dict = dict(row)
        as_dict["tags"] = json.loads(as_dict.pop("tags_json"))
        as_dict["access_policy"] = json.loads(as_dict.pop("access_policy_json"))
        return as_dict
