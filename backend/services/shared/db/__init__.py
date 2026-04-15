"""Shared persistence infrastructure for backend services.

Provides:
  - resolve_db_path(service_name)  — canonical per-service SQLite file path
  - connect(db_path)               — sqlite3 connection with WAL + foreign keys
  - BaseRepository                 — mixin enforcing ARCH_04 and ARCH_07 contracts

No external dependencies — stdlib sqlite3 only.
"""
from .engine import BaseRepository, connect, resolve_db_path

__all__ = ["BaseRepository", "connect", "resolve_db_path"]
