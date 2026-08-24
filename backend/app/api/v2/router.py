"""Finpluse API v2 -- Router Aggregator."""
from fastapi import APIRouter
from app.api.v2.forecast import router as forecast_router
from app.api.v2.anomalies import router as anomalies_router
from app.api.v2.explain import router as explain_router
from app.api.v2.multimodal import router as multimodal_router
from app.api.v2.agents import router as agents_router
from app.api.v2.multimodal import router as multimodal_router
from app.api.v2.security import router as security_router
from app.api.v2.banking import router as banking_router
from app.api.v2.sustainability import router as sustainability_router
from app.api.v2.federated import router as federated_router

v2_router = APIRouter()
v2_router.include_router(forecast_router, prefix="/forecast", tags=["Forecast v2"])
v2_router.include_router(anomalies_router, prefix="/anomalies", tags=["Anomalies v2"])
v2_router.include_router(explain_router, prefix="/explain", tags=["Explainability v2"])
v2_router.include_router(multimodal_router, prefix="/multimodal", tags=["Multimodal v2"])
v2_router.include_router(agents_router, prefix="/agents", tags=["Agents v2"])
v2_router.include_router(security_router, prefix="/security", tags=["Security v2"])
v2_router.include_router(banking_router, prefix="/banking", tags=["Banking v2"])
v2_router.include_router(sustainability_router, prefix="/sustainability", tags=["Sustainability v2"])
v2_router.include_router(federated_router, prefix="/federated", tags=["Federated v2"])

