"""
Finpluse v2 -- Voice Natural Language Understanding
"""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

def extract_intent_and_entities(text: str) -> dict[str, Any]:
    """
    Mock intent classification and entity extraction.
    """
    text_lower = text.lower()
    
    if "balance" in text_lower:
        return {"intent": "spending_query", "entities": {"metric": "balance"}}
    elif "spend" in text_lower or "spent" in text_lower:
        # Simple extraction for demo
        category = "General"
        if "food" in text_lower or "eat" in text_lower or "restaurant" in text_lower:
            category = "Dining"
        return {"intent": "spending_query", "entities": {"metric": "spending", "category": category}}
    elif "anomaly" in text_lower or "weird" in text_lower:
        return {"intent": "anomaly_query", "entities": {}}
    elif "forecast" in text_lower or "future" in text_lower or "predict" in text_lower:
        return {"intent": "forecast_query", "entities": {}}
        
    return {"intent": "unknown", "entities": {}}

