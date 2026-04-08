"""Mirrors portfolio.controller.ts — FastAPI routes for portfolio endpoints.

In the original Ghostfolio this is a NestJS @Controller('portfolio') that
injects PortfolioService. Here we use a FastAPI APIRouter and receive the
user state from a dependency.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from .portfolio_service import PortfolioService

router = APIRouter()


def _service_from_user(user) -> PortfolioService:
    return PortfolioService(user.activities, user.market_data, user.base_currency)


def create_portfolio_router(get_user) -> APIRouter:
    """Build and return the portfolio router with the given auth dependency."""

    @router.get("/api/v2/portfolio/performance")
    def get_performance(range: str = "max", user=Depends(get_user)) -> dict:
        return _service_from_user(user).get_performance()

    @router.get("/api/v1/portfolio/investments")
    def get_investments(
        range: str = "max", groupBy: str | None = None, user=Depends(get_user),
    ) -> dict:
        return _service_from_user(user).get_investments(group_by=groupBy)

    @router.get("/api/v1/portfolio/holdings")
    def get_holdings(range: str = "max", user=Depends(get_user)) -> dict:
        return _service_from_user(user).get_holdings()

    @router.get("/api/v1/portfolio/details")
    def get_details(range: str = "max", user=Depends(get_user)) -> dict:
        return _service_from_user(user).get_details()

    @router.get("/api/v1/portfolio/dividends")
    def get_dividends(
        range: str = "max", groupBy: str | None = None, user=Depends(get_user),
    ) -> dict:
        return _service_from_user(user).get_dividends(group_by=groupBy)

    @router.get("/api/v1/portfolio/report")
    def get_report(user=Depends(get_user)) -> dict:
        return _service_from_user(user).get_report()

    return router
