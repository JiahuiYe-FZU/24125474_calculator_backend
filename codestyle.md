# Backend Code Style Guide (codestyle)

## Specification Sources

The Python code conventions for this project are based on official community standards:

- **PEP 8 — Style Guide for Python Code**  
  <https://peps.python.org/pep-0008/>
- Supplementary reference: **Google Python Style Guide**  
  <https://google.github.io/styleguide/pyguide.html>

Items not explicitly enforced in PEP 8 are standardized by this project.

---

## 1. Naming Conventions

| Type | Style | Example |
|------|-------|---------|
| Module / Package | lower_case_with_underscores | `expression_service.py` |
| Function / Variable | snake_case | `calculate`, `history_id` |
| Class | PascalCase | `ExpressionError`, `CalculateRequest` |
| Constant | UPPER_SNAKE_CASE | `DB_PATH`, `SCHEMA` |
| Private / Internal | Leading underscore | `_tokenize`, `_Parser` |

## 2. Indentation and Line Width

- Use **4 spaces** for indentation; tabs are forbidden.
- Keep line width within **88 characters** where possible (aligned with Black and PEP 8 recommendations).
- Maintain visual alignment or hanging indentation when breaking multi-line function parameters.

## 3. Imports

- Group imports into standard library, third-party libraries, and local packages, separated by blank lines.
- Prefer absolute imports: `from src.model import history`.
- Avoid wildcard imports: `import *`.
- Test-only dependencies should reside in test files.

## 4. Strings and Documentation

- Write clear, concise docstrings for modules, public classes, and functions.
- Use English for error messages to ensure standardized API responses.
- Use UTF-8 encoding universally.

## 5. Type Annotations

- Add type annotations to parameters and return values of public functions (PEP 484).
- Use `typing` primitives or built-in generics (`list`, `dict`).

## 6. Error Handling

- Use custom exceptions for anticipated domain errors (e.g. `ExpressionError`).
- Bare `except:` clauses are prohibited; always catch specific exception types.
- The API layer maps exceptions to appropriate HTTP status codes and JSON payloads without leaking internal stack traces.

## 7. Security Standards

- Execution of user input via `eval`, `exec`, or `compile` is **strictly prohibited**.
- Mathematical expressions must be parsed via lexical scanning + recursive descent (see `expression_service.py`).
- SQL queries must use parameterized placeholders; raw string concatenation is forbidden.

## 8. Layered Architecture

| Directory | Responsibility | Must Not Contain |
|-----------|----------------|------------------|
| `controller/` | HTTP handling, request validation, status codes | Complex algorithms, SQL queries |
| `service/` | Expression parsing and calculation | HTTP objects, direct database access |
| `model/` | Database connections and CRUD operations | Business logic, HTTP objects |

## 9. Formatting Recommendations

Compatible tools:

```bash
ruff check .
ruff format .
```

Or:

```bash
black .
```

## 10. Testing

- Test files reside under `tests/` named `test_*.py`.
- Each public endpoint and function must have test assertions for normal cases, invalid inputs, division by zero, and non-existent record deletions.
