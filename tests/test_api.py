"""Backend API and expression evaluation tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

# Forced (not setdefault): a real CALCULATOR_DB must never be cleared
# by the fresh_db fixture below.
os.environ["CALCULATOR_DB"] = str(BASE / "tests" / "test_calculation.db")

from src.main import app  # noqa: E402
from src.model.database import db_session, init_db  # noqa: E402
from src.service.expression_service import (  # noqa: E402
    DivisionByZeroError,
    ExpressionError,
    calculate,
)


@pytest.fixture(autouse=True)
def fresh_db():
    init_db()
    with db_session() as conn:
        conn.execute("DELETE FROM calculation_history")
    yield


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestCalculateFunction:
    def test_basic_ops(self):
        assert calculate("12+8") == 20
        assert calculate("12-8") == 4
        assert calculate("12*8") == 96
        assert calculate("12/4") == 3

    def test_precedence(self):
        assert calculate("1+2*3") == 7
        assert calculate("8-3*2") == 2
        assert calculate("10/2+7") == 12

    def test_parentheses(self):
        assert calculate("(1+2)*3") == 9
        assert calculate("((1+2)*3)") == 9

    def test_unary(self):
        assert calculate("-5+8") == 3
        assert calculate("3*-2") == -6
        assert calculate("+5+3") == 8

    def test_decimal(self):
        assert calculate("1.5+2.5") == 4
        assert abs(calculate("0.1+0.2") - 0.3) < 1e-9

    def test_display_symbols(self):
        assert calculate("12×8") == 96
        assert calculate("12÷4") == 3

    def test_division_by_zero(self):
        with pytest.raises(DivisionByZeroError):
            calculate("1/0")

    def test_invalid(self):
        for bad in ["", "   ", "(1+2", "1++", "1.2.3", "a+1", "1 2", "()", "1/"]:
            with pytest.raises(ExpressionError):
                calculate(bad)

    def test_required_cases(self):
        """Tests for standard calculation cases."""
        assert calculate("15+7") == 22
        assert calculate("15-7") == 8
        assert calculate("6*8") == 48
        assert calculate("21/3") == 7
        assert calculate("2+4*5") == 22
        assert calculate("(2+4)*5") == 30
        assert calculate("18/3/2") == 3
        assert calculate("10-3-2") == 5
        assert calculate("-6+9") == 3
        assert calculate("+6-9") == -3
        assert calculate("5*-2") == -10
        assert calculate("-(2+3)*4") == -20
        assert calculate("1.25+2.5") == 3.75
        assert calculate("0*7") == 0

    def test_zero_is_valid_result(self):
        assert calculate("5-5") == 0
        assert calculate("0*7") == 0

    def test_float_display_strategy(self):
        # Floating-point calculation and precision tests
        assert calculate("0.1+0.2") == 0.3
        assert calculate("1.5+2.5") == 4

    def test_whitespace_between_numbers_rejected(self):
        with pytest.raises(ExpressionError):
            calculate("1 2")
        with pytest.raises(ExpressionError):
            calculate("1\t2")
        # Tests for spaces surrounding operators
        assert calculate("1  +  2") == 3

    def test_no_code_execution_surface(self):
        for bad in [
            "__import__('os')",
            "1+open('x')",
            "lambda:1",
            "1 if 1 else 2",
            "print(1)",
        ]:
            with pytest.raises(ExpressionError):
                calculate(bad)

    def test_nested_parentheses(self):
        assert calculate("(((1+2)*3)+4)*2") == 26
        assert calculate("((2+3)*(4-1))/5") == 3

    def test_scientific_notation_input(self):
        # Results may be displayed in scientific notation and fed back in.
        assert calculate("1e-7") == pytest.approx(1e-7)
        assert calculate("1e-7+1") == pytest.approx(1.0000001)
        assert calculate("2.5E+2") == 250
        assert calculate("1e3") == 1000
        assert calculate("1.5e-3") == pytest.approx(0.0015)

    def test_large_integer_stays_exact(self):
        exact = 9007199254740993  # 2**53 + 1, not representable as float
        assert calculate(str(exact)) == exact
        assert calculate("9999999999999999999999+1") == 10000000000000000000000
        assert calculate("12345678901234567890*2") == 24691357802469135780

    def test_api_rejects_overlong_expression(self, client: TestClient):
        resp = client.post("/api/calculate", json={"expression": "1" * 300})
        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert "expression" in body["message"]

    def test_api_missing_field_unified_error(self, client: TestClient):
        resp = client.post("/api/calculate", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert isinstance(body["message"], str) and body["message"]


class TestApi:
    def test_calculate_and_history(self, client: TestClient):
        resp = client.post("/api/calculate", json={"expression": "(1+2)*3"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["result"] == 9
        assert body["expression"] == "(1+2)*3"

        history = client.get("/api/history").json()["history"]
        assert len(history) == 1
        assert history[0]["expression"] == "(1+2)*3"
        assert history[0]["result"] == "9"
        assert history[0]["id"] == body["id"]
        assert history[0]["created_at"]

    def test_calculate_invalid(self, client: TestClient):
        resp = client.post("/api/calculate", json={"expression": "1/0"})
        assert resp.status_code == 400
        body = resp.json()
        assert body["success"] is False
        assert body["message"] == "Division by zero"

        resp = client.post("/api/calculate", json={"expression": "1+"})
        assert resp.status_code == 400

    def test_failed_calculate_not_saved(self, client: TestClient):
        client.post("/api/calculate", json={"expression": "1/0"})
        history = client.get("/api/history").json()["history"]
        assert history == []

    def test_delete_one(self, client: TestClient):
        created = client.post("/api/calculate", json={"expression": "1+1"}).json()
        other = client.post("/api/calculate", json={"expression": "2+2"}).json()

        resp = client.delete(f"/api/history/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        history = client.get("/api/history").json()["history"]
        assert [item["id"] for item in history] == [other["id"]]

        missing = client.delete(f"/api/history/{created['id']}")
        assert missing.status_code == 404
        assert missing.json()["success"] is False

    def test_invalid_history_id(self, client: TestClient):
        resp = client.delete("/api/history/0")
        assert resp.status_code == 422
        resp = client.delete("/api/history/-1")
        assert resp.status_code == 422

    def test_scientific_notation_via_api(self, client: TestClient):
        resp = client.post("/api/calculate", json={"expression": "1e-7+1"})
        assert resp.status_code == 200
        assert resp.json()["result"] == pytest.approx(1.0000001)

    def test_history_persisted_content(self, client: TestClient):
        """Validates persisted history fields."""
        a = client.post("/api/calculate", json={"expression": "(6-2)*3"}).json()
        b = client.post("/api/calculate", json={"expression": "1.25+2.5"}).json()
        assert a["result"] == 12
        assert b["result"] == 3.75

        history = client.get("/api/history").json()["history"]
        by_id = {item["id"]: item for item in history}
        assert by_id[a["id"]]["expression"] == "(6-2)*3"
        assert by_id[a["id"]]["result"] == "12"
        assert by_id[a["id"]]["created_at"]
        assert by_id[b["id"]]["expression"] == "1.25+2.5"
        assert by_id[b["id"]]["result"] == "3.75"

        # Tests single item deletion isolation
        client.delete(f"/api/history/{a['id']}")
        left = client.get("/api/history").json()["history"]
        assert [item["id"] for item in left] == [b["id"]]

    def test_clear_all(self, client: TestClient):
        client.post("/api/calculate", json={"expression": "1+1"})
        client.post("/api/calculate", json={"expression": "2+2"})
        resp = client.delete("/api/history")
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 2
        assert client.get("/api/history").json()["history"] == []

    def test_health(self, client: TestClient):
        body = client.get("/health").json()
        assert body["status"] == "ok"
        assert body["service"] == "calculator-backend"
