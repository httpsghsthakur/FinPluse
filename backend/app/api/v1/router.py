"""
FinPilot API v1 — Router Aggregator

Combines all v1 route modules into a single router.
"""
from fastapi import APIRouter

from app.api.v1.accounts import router as accounts_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.categories import router as categories_router
from app.api.v1.budgets import router as budgets_router
from app.api.v1.goals import router as goals_router
from app.api.v1.forecast import router as forecast_router
from app.api.v1.insights import router as insights_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.simulator import router as simulator_router
from app.api.v1.copilot import router as copilot_router
from app.api.v1.admin import router as admin_router
from app.api.v1.ml_endpoints import router as ml_router
from app.api.v1.markets import router as markets_router

api_router = APIRouter()

api_router.include_router(markets_router, prefix="/markets", tags=["Markets"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(categories_router, prefix="/categories", tags=["Categories"])
api_router.include_router(budgets_router, prefix="/budgets", tags=["Budgets"])
api_router.include_router(goals_router, prefix="/goals", tags=["Goals"])
api_router.include_router(forecast_router, prefix="/forecast", tags=["Forecast"])
api_router.include_router(insights_router, prefix="/insights", tags=["Insights"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(simulator_router, prefix="/simulator", tags=["Simulator"])
api_router.include_router(copilot_router, prefix="/copilot", tags=["AI Copilot"])
api_router.include_router(ml_router, prefix="/ml", tags=["ML Models"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
