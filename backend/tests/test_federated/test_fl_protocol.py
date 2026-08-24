"""Tests for federated learning protocol."""
import numpy as np
from app.ml.federated.fl_server import FLServer
from app.ml.federated.fl_client import FLClient

def test_fl_round():
    server = FLServer(global_model_dim=5)
    server.min_clients = 2
    
    w1 = [1.0, 1.0, 1.0, 1.0, 1.0]
    w2 = [3.0, 3.0, 3.0, 3.0, 3.0]
    
    server.submit_update("client_A", w1, n_samples=100)
    res = server.aggregate()
    assert res["status"] == "waiting"
    
    server.submit_update("client_B", w2, n_samples=100)
    res = server.aggregate()
    assert res["status"] == "success"
    
    new_global = server.get_global_model()
    assert np.allclose(new_global, [2.0, 2.0, 2.0, 2.0, 2.0]) # FedAvg
