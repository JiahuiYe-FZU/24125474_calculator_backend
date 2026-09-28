"""Calculation and history API controller."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from src.model import history as history_model
from src.service.expression_service import ExpressionError, calculate

router = APIRouter(prefix="/api", tags=["calculator"])

HistoryId = Annotated[int, Path(ge=1, description="History record ID")]


def _error(message: str, status_code: int) -> HTTPException:
    """Builds a unified error response."""
    return HTTPException(status_code=status_code, detail={"success": False, "message": message})


class CalculateRequest(BaseModel):
    expression: str = Field(..., min_length=1, max_length=256)


class HistoryItem(BaseModel):
    id: int
    expression: str
    result: str
    created_at: str


@router.post("/calculate")
def calculate_expression(payload: CalculateRequest) -> dict:
    """Receives an expression request, calculates the result, and persists history."""
    expression = payload.expression.strip()
    try:
        value = calculate(expression)
    except ExpressionError as exc:
        raise _error(exc.message, 400) from exc

    record = history_model.insert_history(expression, str(value))
    return {
        "success": True,
        "expression": expression,
        "result": value,
        "id": record["id"],
        "created_at": record["created_at"],
    }


@router.get("/history")
def get_history() -> dict:
    """Retrieves all calculation history records in descending order."""
    items = history_model.list_history()
    return {"success": True, "history": items}


@router.delete("/history/{history_id}")
def delete_history(history_id: HistoryId) -> dict:
    """Deletes a single calculation history record by ID."""
    deleted = history_model.delete_history(history_id)
    if not deleted:
        raise _error("History record not found", 404)
    return {"success": True, "id": history_id}


@router.delete("/history")
def clear_history() -> dict:
    """Clears all calculation history records."""
    count = history_model.clear_history()
    return {"success": True, "deleted": count}
