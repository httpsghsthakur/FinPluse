"""
Finpluse v2 -- Federated Learning API
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.db.models.user import User
from app.ml.federated.fl_server import FLServer

router = APIRouter()
fl_server = FLServer(global_model_dim=5)
fl_server.min_clients = 2

@router.post("/submit_deltas")
async def submit_deltas(
    deltas: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Submit locally trained weight deltas to the aggregation server."""
    fl_server.submit_update("api_client", list(deltas.values()), n_samples=100)
    
    # Try aggregating (using min_clients=2 for testing)
    aggregated = fl_server.aggregate()
    
    return {
        "status": "success",
        "aggregated": aggregated
    }
    
@router.get("/global_weights")
async def get_global_weights(
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Get the latest global weights for local training."""
    return fl_server.get_global_model()


