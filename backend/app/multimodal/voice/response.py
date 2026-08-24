"""
Finpluse v2 -- Voice Response Generation
"""

def generate_response(intent: str, entities: dict, data: dict = None) -> str:
    """Generate natural language response based on intent and data."""
    if intent == "spending_query":
        metric = entities.get("metric", "balance")
        if metric == "balance":
            balance = data.get("balance", 0) if data else 0
            return f"Your current balance is ${balance:,.2f}."
        elif metric == "spending":
            amount = data.get("amount", 0) if data else 0
            cat = entities.get("category", "General")
            return f"You have spent ${amount:,.2f} on {cat} recently."
            
    elif intent == "anomaly_query":
        count = data.get("anomaly_count", 0) if data else 0
        if count == 0:
            return "I haven't noticed any unusual spending patterns lately."
        return f"I found {count} unusual transactions in your recent history."
        
    elif intent == "forecast_query":
        runway = data.get("runway_days", 30) if data else 30
        return f"Based on your current trends, you have about {runway} days of runway left."
        
    return "I'm sorry, I didn't understand your request."
