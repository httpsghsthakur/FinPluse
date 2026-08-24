"""
Finpluse v2 -- Federated Learning API (Server Side)
"""
from typing import Any
from fastapi import APIRouter

from app.ml.federated.fl_server import FLServer

router = APIRouter()
fl_server = FLServer(global_model_dim=20)


@router.get("/global_model")
async def get_global_model() -> dict[str, Any]:
    """Distribute global weights to clients."""
    return {
        "round": fl_server.round,
        "weights": fl_server.get_global_model()
    }


@router.post("/submit_update")
async def submit_update(client_id: str, weights: list[float], n_samples: int) -> dict[str, Any]:
    """Receive local model updates from clients."""
    success = fl_server.submit_update(client_id, weights, n_samples)
    if not success:
        return {"status": "error", "message": "Invalid update"}
    
    # Try aggregating if enough clients
    agg_result = fl_server.aggregate()
    return agg_result
