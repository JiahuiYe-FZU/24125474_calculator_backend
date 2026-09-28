"""Calculation history data access layer."""

from __future__ import annotations

from typing import Any, Dict, List

from src.model.database import db_session


def insert_history(expression: str, result: str) -> Dict[str, Any]:
    """Inserts a calculation record and returns the persisted row."""
    with db_session() as conn:
        cursor = conn.execute(
            "INSERT INTO calculation_history (expression, result) VALUES (?, ?)",
            (expression, result),
        )
        row = conn.execute(
            """
            SELECT id, expression, result, created_at
            FROM calculation_history
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def list_history() -> List[Dict[str, Any]]:
    """Queries all calculation history records in descending ID order."""
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT id, expression, result, created_at
            FROM calculation_history
            ORDER BY id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def delete_history(history_id: int) -> bool:
    """Deletes a calculation history record by ID; returns True if deleted."""
    with db_session() as conn:
        cursor = conn.execute(
            "DELETE FROM calculation_history WHERE id = ?",
            (history_id,),
        )
        return cursor.rowcount > 0


def clear_history() -> int:
    """Clears all records in calculation_history and returns deleted count."""
    with db_session() as conn:
        cursor = conn.execute("DELETE FROM calculation_history")
        return cursor.rowcount
