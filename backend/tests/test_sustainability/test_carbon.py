import pytest
from app.sustainability.emission_db import get_emission_factor
from app.sustainability.calculator import calculate_transaction_footprint, aggregate_monthly_footprint
from app.sustainability.green_alternatives import suggest_alternatives

def test_emission_factor():
    assert get_emission_factor("cat-transport") == 0.50
    assert get_emission_factor("cat-transport", "Uber") == 0.50 * 1.1
    assert get_emission_factor("cat-transport", "Tesla") == 0.50 * 0.3

def test_calculator():
    co2 = calculate_transaction_footprint(-100.0, "cat-transport", "Uber")
    assert co2 == 100.0 * 0.50 * 1.1

def test_aggregate_footprint():
    txs = [
        {"amount": -100.0, "category_id": "cat-transport", "merchant": "Uber"},
        {"amount": -50.0, "category_id": "cat-food"},
        {"amount": 1000.0, "category_id": "cat-income"} # should be ignored
    ]
    totals = aggregate_monthly_footprint(txs)
    assert totals["cat-transport"] == pytest.approx(55.0)
    assert totals["cat-food"] == pytest.approx(50.0 * 0.35)
    assert "cat-income" not in totals

def test_green_alternatives():
    txs = [
        {"amount": -250.0, "category_id": "cat-transport", "merchant": "Uber"},
        {"amount": -150.0, "category_id": "cat-shopping", "merchant": "Amazon"}
    ]
    suggestions = suggest_alternatives(txs)
    assert len(suggestions) == 2
    types = [s["type"] for s in suggestions]
    assert "transport" in types
    assert "shopping" in types

