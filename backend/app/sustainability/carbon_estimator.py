"""
Finpluse v2 -- Carbon Footprint Tracking

Estimates kgCO2e per transaction using merchant MCC codes and NLP.
"""
from typing import Any
import re

class CarbonEstimator:
    """Estimates CO2 emissions from transaction data.
    
    Uses standard emissions factors (kg CO2 per $ spend).
    """

    # Emissions factors (kg CO2e per $1) - approximate values
    FACTORS = {
        "flight": 1.5,
        "gas": 1.2,
        "electricity": 0.9,
        "meat": 0.8,
        "fast_food": 0.4,
        "clothing": 0.3,
        "electronics": 0.25,
        "general_retail": 0.15,
        "software": 0.05,
        "healthcare": 0.1,
    }

    # Keyword matching to categories
    KEYWORDS = {
        "flight": ["airline", "airways", "delta", "united", "american airlines", "flight"],
        "gas": ["shell", "chevron", "exxon", "mobil", "bp", "gas"],
        "electricity": ["electric", "pg&e", "coned", "power"],
        "meat": ["butcher", "steakhouse"],
        "fast_food": ["mcdonalds", "burger king", "wendys", "taco bell", "chipotle"],
        "clothing": ["zara", "h&m", "nordstrom", "macys", "apparel"],
        "electronics": ["apple", "best buy", "electronics"],
        "software": ["netflix", "spotify", "adobe", "aws", "software"],
    }

    def estimate_transaction(self, amount: float, merchant: str, category_id: str) -> dict[str, Any]:
        """Estimate carbon footprint for a single transaction."""
        amount = abs(amount)
        if amount == 0:
            return {"kg_co2e": 0.0, "category": "unknown", "confidence": 1.0}

        merchant_lower = merchant.lower()
        matched_cat = "general_retail"
        confidence = 0.5

        # Rule-based matching
        for cat, keywords in self.KEYWORDS.items():
            if any(kw in merchant_lower for kw in keywords):
                matched_cat = cat
                confidence = 0.9
                break

        # Fallback to general category mappings
        if confidence == 0.5:
            if "transport" in category_id:
                matched_cat = "gas"
                confidence = 0.7
            elif "food" in category_id:
                matched_cat = "fast_food"
                confidence = 0.6
            elif "utilities" in category_id:
                matched_cat = "electricity"
                confidence = 0.7

        factor = self.FACTORS.get(matched_cat, self.FACTORS["general_retail"])
        kg_co2e = amount * factor

        return {
            "kg_co2e": round(kg_co2e, 2),
            "emission_category": matched_cat,
            "factor_used": factor,
            "confidence": confidence,
            "offsets_cost_usd": round(kg_co2e * 0.02, 2)  # Assuming $20 per ton
        }

    def aggregate_monthly(self, transactions: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate footprint over a list of transactions (e.g. a month)."""
        total_co2 = 0.0
        by_category = {}

        for tx in transactions:
            if tx.get("amount", 0) > 0:  # Skip income
                continue
            
            est = self.estimate_transaction(tx.get("amount", 0), tx.get("merchant", ""), tx.get("category_id", ""))
            total_co2 += est["kg_co2e"]
            
            cat = est["emission_category"]
            by_category[cat] = by_category.get(cat, 0.0) + est["kg_co2e"]

        # Sort categories by emission
        by_category = {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda item: item[1], reverse=True)}

        return {
            "total_kg_co2e": round(total_co2, 2),
            "equivalent_trees_yearly": round(total_co2 / 20.0, 1), # 1 tree absorbs ~20kg/yr
            "equivalent_miles_driven": round(total_co2 / 0.4, 1),  # avg car 0.4kg/mile
            "by_category": by_category,
            "suggested_offset_cost": round(total_co2 * 0.02, 2)
        }
