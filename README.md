# Calculator Backend

The **backend service** of the client-server calculator system: responsible for expression parsing and evaluation, data validation, exception handling, and database persistence of calculation history.

## Project Overview

- Receives expression strings from the frontend and evaluates them on the backend.
- Persists successful calculation records into a SQLite database.
- Provides endpoints for history retrieval, deletion by ID, and clearing all history.
- **Strictly prohibits** arbitrary code execution such as `eval` or `exec`.

## Tech Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.10+ |
| Web Framework | FastAPI |
| Server | Uvicorn |
| Database | SQLite |
| Testing | pytest + TestClient |

## Environment

- Python >= 3.10
- Dependencies listed in `requirements.txt`

## Installation

```powershell
cd 24125474_calculator_backend
pip install -r requirements.txt
```

## Running the Service

```powershell
python -m src.run
```

Or:

```powershell
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Default listening address: `http://127.0.0.1:8000`.

## Configuration

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `CALCULATOR_DB` | SQLite database file path | `calculation.db` under project root |
| `CALCULATOR_RELOAD` | Enables Uvicorn hot-reload when set to `1` | Disabled |

## Calculation Notes

- Integer arithmetic (`+`, `-`, `*`) stays exact: integer literals are parsed as Python integers, with no 53-bit float truncation.
- Division and scientific-notation literals use double precision; float results are rounded to 12 significant digits to hide binary floating-point noise.
- Scientific notation is accepted on input (`1e-7`, `2.5E+2`), so a result displayed as `1e-07` can be fed straight back into a new expression.
- Because JavaScript `Number` cannot represent integers beyond 2**53 exactly, very large integer results may lose precision once rendered or re-submitted by the frontend; the backend response itself is exact.

## Database Initialization

Table creation runs automatically on first launch (or can be triggered via `src.model.database.init_db`):

```text
calculation_history
-------------------
id          INTEGER PRIMARY KEY AUTOINCREMENT
expression  TEXT NOT NULL
result      TEXT NOT NULL
created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
```

Deleting `calculation.db` resets all data.

## API Documentation

| Method | Path | Description | Success | Failure |
|--------|------|-------------|---------|---------|
| POST | `/api/calculate` | Calculates expression and saves history | 200 | 400 invalid expression / division by zero; 422 validation; 500 database failure |
| GET | `/api/history` | Retrieves all history (newest to oldest) | 200 | 500 database failure |
| DELETE | `/api/history/{id}` | Deletes a single history record | 200 | 404 not found; 422 invalid ID; 500 database failure |
| DELETE | `/api/history` | Clears all history | 200 | 500 database failure |
| GET | `/health` | Health check endpoint | 200 | — |

Every error response uses the same JSON shape, including validation errors and unexpected server failures:

```json
{
  "success": false,
  "message": "Division by zero"
}
```

FastAPI validation errors and domain errors are converted into a unified JSON format with a readable `message` string.

### Calculation Request Example

```http
POST /api/calculate
Content-Type: application/json
```

```json
{ "expression": "(1+2)*3" }
```

Successful response (HTTP 200):

```json
{
  "success": true,
  "expression": "(1+2)*3",
  "result": 9,
  "id": 1,
  "created_at": "2026-10-01 10:20:00"
}
```

Note: `/api/calculate` returns `result` as a JSON **number**, while `GET /api/history` returns the persisted `result` as a **string** (the database stores it as text). The difference is intentional; clients that compare values should convert explicitly.

Error response (HTTP 400):

```json
{
  "success": false,
  "message": "Division by zero"
}
```

### History Response Example

```json
{
  "success": true,
  "history": [
    {
      "id": 1,
      "expression": "(1+2)*3",
      "result": "9",
      "created_at": "2026-10-01 10:20:00"
    }
  ]
}
```

### Health Response Example

```json
{
  "status": "ok",
  "service": "calculator-backend"
}
```

## Client-Server Connection

1. Start the backend service (default `http://127.0.0.1:8000`).
2. The frontend resolves the backend address in this order: `window.CALCULATOR_API_BASE` (deployment override), the page host with port 8000, then `http://127.0.0.1:8000` for pages opened from the file system.
3. The frontend communicates via HTTP + JSON to `/api/*` with **no local calculation logic**.
4. Stopping the backend service stops the calculation flow, confirming all core computations rely on the backend.

CORS is enabled for all origins to facilitate local testing.

## Project Structure

```text
24125474_calculator_backend/
├── src/
│   ├── controller/
│   │   └── calc_controller.py     # API routes and request validation
│   ├── service/
│   │   └── expression_service.py  # Lexical analysis and recursive descent parser
│   ├── model/
│   │   ├── database.py            # SQLite connection and schema
│   │   └── history.py             # History database operations
│   ├── main.py                    # FastAPI application instance
│   └── run.py                     # Server entry point
├── tests/
│   └── test_api.py                # API and expression test suite
├── requirements.txt
├── pytest.ini
├── codestyle.md
└── README.md
```

## Testing

Run all unit and API tests with pytest:

```powershell
pytest
```

The test suite runs against an isolated test database and covers basic arithmetic, operator precedence, parentheses, decimals, unary signs, division by zero, invalid input handling, history persistence, and deletion.

## Code Style

See [codestyle.md](./codestyle.md) (based on PEP 8).
