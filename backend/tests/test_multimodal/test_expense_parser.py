"""Tests for NL expense parser."""
from app.multimodal.nlp.expense_parser import NLExpenseParser

def test_parse_simple_expense():
    parser = NLExpenseParser()
    result = parser.parse("Lunch at Chipotle $12.50")
    assert result["amount"] == -12.50
    assert result["category_id"] == "cat-food"
    assert "Chipotle" in result["merchant"]

def test_parse_recurring():
    parser = NLExpenseParser()
    result = parser.parse("Netflix monthly $15.99")
    assert result["amount"] == -15.99
    assert result["is_recurring"] is True
