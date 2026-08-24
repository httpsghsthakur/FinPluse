import pytest
from app.multimodal.voice.nlu import extract_intent_and_entities
from app.multimodal.voice.response import generate_response

def test_extract_intent_spending():
    res = extract_intent_and_entities("How much did I spend on food?")
    assert res["intent"] == "spending_query"
    assert res["entities"]["category"] == "Dining"

def test_generate_response_forecast():
    resp = generate_response("forecast_query", {}, {"runway_days": 120})
    assert "120 days" in resp
