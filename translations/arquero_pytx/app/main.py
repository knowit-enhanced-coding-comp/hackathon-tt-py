"""
Arquero pytx — FastAPI entry point.

Bootstraps the app and wires modules. All table processing logic lives
under app/implementation/, with HTTP wiring in app/wrapper/. This file
is part of the immutable wrapper layer.
"""
from __future__ import annotations

from fastapi import FastAPI

from .wrapper.table.table_controller import create_table_router

app = FastAPI(title="Arquero pytx skeleton")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Table module
# ---------------------------------------------------------------------------

app.include_router(create_table_router())
