"""
Finpluse v2 -- Green Alternatives Suggestion Engine
"""
from typing import List, Dict, Any

def suggest_alternatives(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Suggest greener alternatives based on transaction history."""
    suggestions = []
    
    # Simple rule-based mock engine
    transport_spend = sum(abs(tx["amount"]) for tx in transactions if tx.get("category_id") == "cat-transport" and tx.get("amount", 0) < 0)
    
    if transport_spend > 200:
        suggestions.append({
            "type": "transport",
            "title": "Switch to Public Transit",
            "description": f"You spent  on transport. Switching to a monthly transit pass could save you ~150kg CO2e.",
            "potential_co2_savings": 150.0,
            "difficulty": "medium"
        })
        
    shopping_spend = sum(abs(tx["amount"]) for tx in transactions if tx.get("merchant") == "Amazon" and tx.get("amount", 0) < 0)
    if shopping_spend > 100:
        suggestions.append({
            "type": "shopping",
            "title": "Shop Local",
            "description": "Consolidating online orders or shopping locally can reduce packaging and shipping emissions by up to 40%.",
            "potential_co2_savings": 25.0,
            "difficulty": "easy"
        })
        
    return suggestions
