"""Tests for carbon estimator."""
from app.sustainability.carbon_estimator import CarbonEstimator

def test_estimate_flight():
    est = CarbonEstimator()
    res = est.estimate_transaction(500, "Delta Airlines", "cat-transport")
    assert res["emission_category"] == "flight"
    assert res["kg_co2e"] == 500 * est.FACTORS["flight"]

def test_aggregate():
    est = CarbonEstimator()
    txs = [
        {"amount": -50, "merchant": "Shell", "category_id": "gas"},
        {"amount": -10, "merchant": "Netflix", "category_id": "software"},
        {"amount": 1000, "merchant": "Paycheck", "category_id": "income"} # Should be ignored
    ]
    res = est.aggregate_monthly(txs)
    assert res["total_kg_co2e"] == (50 * est.FACTORS["gas"]) + (10 * est.FACTORS["software"])
