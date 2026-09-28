"""Server startup entry point."""

from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.environ.get("CALCULATOR_RELOAD") == "1",
    )
