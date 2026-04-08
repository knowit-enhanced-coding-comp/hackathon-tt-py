"""Thin routing layer for table operations.

Maps HTTP endpoints to TableService methods via FastAPI APIRouter.
Part of the immutable wrapper layer.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from .table_service import TableService
from app.implementation.table.processor.default.table_processor import (
    DefaultTableProcessor,
)

router = APIRouter()


def _service() -> TableService:
    processor = DefaultTableProcessor()
    return TableService(processor)


def create_table_router() -> APIRouter:
    """Build and return the table router with all endpoints."""

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------

    @router.post("/from-json")
    def from_json(body: dict[str, Any]) -> dict:
        return _service().from_json(body)

    @router.post("/from-csv")
    def from_csv_endpoint(body: dict[str, Any]) -> dict:
        return _service().from_csv(body)

    # ------------------------------------------------------------------
    # Column operations
    # ------------------------------------------------------------------

    @router.post("/select")
    def select(body: dict[str, Any]) -> dict:
        return _service().select(body)

    @router.post("/rename")
    def rename(body: dict[str, Any]) -> dict:
        return _service().rename(body)

    @router.post("/relocate")
    def relocate(body: dict[str, Any]) -> dict:
        return _service().relocate(body)

    @router.post("/derive")
    def derive(body: dict[str, Any]) -> dict:
        return _service().derive(body)

    @router.post("/assign")
    def assign(body: dict[str, Any]) -> dict:
        return _service().assign(body)

    # ------------------------------------------------------------------
    # Row operations
    # ------------------------------------------------------------------

    @router.post("/filter")
    def filter_rows(body: dict[str, Any]) -> dict:
        return _service().filter_rows(body)

    @router.post("/orderby")
    def orderby(body: dict[str, Any]) -> dict:
        return _service().orderby(body)

    @router.post("/slice")
    def slice_rows(body: dict[str, Any]) -> dict:
        return _service().slice_rows(body)

    @router.post("/sample")
    def sample(body: dict[str, Any]) -> dict:
        return _service().sample(body)

    @router.post("/dedupe")
    def dedupe(body: dict[str, Any]) -> dict:
        return _service().dedupe(body)

    @router.post("/impute")
    def impute(body: dict[str, Any]) -> dict:
        return _service().impute(body)

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    @router.post("/rollup")
    def rollup(body: dict[str, Any]) -> dict:
        return _service().rollup(body)

    @router.post("/groupby-rollup")
    def groupby_rollup(body: dict[str, Any]) -> dict:
        return _service().groupby_rollup(body)

    # ------------------------------------------------------------------
    # Reshaping
    # ------------------------------------------------------------------

    @router.post("/fold")
    def fold(body: dict[str, Any]) -> dict:
        return _service().fold(body)

    @router.post("/pivot")
    def pivot(body: dict[str, Any]) -> dict:
        return _service().pivot(body)

    @router.post("/spread")
    def spread(body: dict[str, Any]) -> dict:
        return _service().spread(body)

    @router.post("/unroll")
    def unroll(body: dict[str, Any]) -> dict:
        return _service().unroll(body)

    # ------------------------------------------------------------------
    # Joins
    # ------------------------------------------------------------------

    @router.post("/join")
    def join(body: dict[str, Any]) -> dict:
        return _service().join(body)

    @router.post("/semijoin")
    def semijoin(body: dict[str, Any]) -> dict:
        return _service().semijoin(body)

    @router.post("/antijoin")
    def antijoin(body: dict[str, Any]) -> dict:
        return _service().antijoin(body)

    @router.post("/cross")
    def cross(body: dict[str, Any]) -> dict:
        return _service().cross(body)

    # ------------------------------------------------------------------
    # Set operations
    # ------------------------------------------------------------------

    @router.post("/union")
    def union(body: dict[str, Any]) -> dict:
        return _service().union(body)

    @router.post("/intersect")
    def intersect(body: dict[str, Any]) -> dict:
        return _service().intersect(body)

    @router.post("/except")
    def except_op(body: dict[str, Any]) -> dict:
        return _service().except_op(body)

    @router.post("/concat")
    def concat(body: dict[str, Any]) -> dict:
        return _service().concat(body)

    # ------------------------------------------------------------------
    # Format output
    # ------------------------------------------------------------------

    @router.post("/to-csv")
    def to_csv(body: dict[str, Any]) -> dict:
        return _service().to_csv(body)

    @router.post("/to-markdown")
    def to_markdown(body: dict[str, Any]) -> dict:
        return _service().to_markdown(body)

    @router.post("/to-json")
    def to_json_endpoint(body: dict[str, Any]) -> dict:
        return _service().to_json(body)

    return router
