"""
Finpluse v2 -- Carbon Footprint Calculator
"""
from typing import List, Dict, Any
from app.sustainability.emission_db import get_emission_factor

def calculate_transaction_footprint(amount: float, category_id: str, merchant_name: str | None = None) -> float:
    """Calculate carbon footprint (kg CO2e) for a single transaction."""
    # Amounts are typically negative for expenses, so we take absolute value
    abs_amount = abs(amount)
    factor = get_emission_factor(category_id, merchant_name)
    return abs_amount * factor

def aggregate_monthly_footprint(transactions: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate footprint by category for a set of transactions."""
    totals = {}
    for tx in transactions:
        amt = tx.get("amount", 0.0)
        if amt >= 0:
            continue # Skip income
            
        cat = tx.get("category_id", "default")
        merch = tx.get("merchant", None)
        
        co2 = calculate_transaction_footprint(amt, cat, merch)
        totals[cat] = totals.get(cat, 0.0) + co2
        
    return totals
