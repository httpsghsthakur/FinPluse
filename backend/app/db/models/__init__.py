"""
FinPilot — Database Models Package

Import all models here so Alembic and the session can discover them.
"""
from app.db.models.user import User
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.category import Category
from app.db.models.budget import Budget
from app.db.models.goal import Goal
from app.db.models.insight import Insight
from app.db.models.recurring import RecurringTransaction
from app.db.models.anomaly import Anomaly
from app.db.models.forecast import Forecast
from app.db.models.scenario import Scenario, ScenarioResult as ScenarioResultModel
from app.db.models.chat import ChatSession, ChatMessage
from app.db.models.document import Document, DocumentChunk
from app.db.models.ml_model import ModelVersion, TrainingDataset
from app.db.models.prediction_audit import PredictionAudit
from app.db.models.user_correction import UserCorrection
from app.db.models.market import Instrument, MarketSnapshot, HistoricalCandle
from app.db.models.portfolio import Portfolio, PortfolioPosition

__all__ = [
    "User",
    "Account",
    "Transaction",
    "Category",
    "Budget",
    "Goal",
    "Insight",
    "RecurringTransaction",
    "Anomaly",
    "Forecast",
    "Scenario",
    "ScenarioResultModel",
    "ChatSession",
    "ChatMessage",
    "Document",
    "DocumentChunk",
    "ModelVersion",
    "TrainingDataset",
    "PredictionAudit",
    "UserCorrection",
    "Instrument",
    "MarketSnapshot",
    "HistoricalCandle",
    "Portfolio",
    "PortfolioPosition",
]
