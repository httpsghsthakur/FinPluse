"""
Finpluse v2 -- Carbon Footprint Emission Database
"""
from typing import Dict

# Mock emission factors database (kg CO2e per dollar spent)
# In production, this would be backed by USEEIO or similar data
EMISSION_FACTORS: Dict[str, float] = {
    "cat-transport": 0.50, # High emission (e.g. gas)
    "cat-food": 0.35,      # Medium emission
    "cat-utilities": 0.40,
    "cat-shopping": 0.20,
    "cat-health": 0.15,
    "cat-housing": 0.25,
    "default": 0.20
}

MERCHANT_MODIFIERS: Dict[str, float] = {
    "Uber": 1.1,      # Slightly worse than average transport
    "Tesla": 0.3,     # EV charging is much cleaner
    "Whole Foods": 0.9, # Local/organic focus reduces footprint slightly
    "Amazon": 1.05    # High shipping footprint
}

def get_emission_factor(category_id: str, merchant_name: str | None = None) -> float:
    base = EMISSION_FACTORS.get(category_id, EMISSION_FACTORS["default"])
    if merchant_name:
        modifier = MERCHANT_MODIFIERS.get(merchant_name, 1.0)
        return base * modifier
    return base
