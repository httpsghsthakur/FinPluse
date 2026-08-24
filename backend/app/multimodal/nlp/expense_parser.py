"""
Finpluse v2 -- Natural Language Expense Parser

Parses free-text expenses like "Lunch at Chipotle $12.50"
"""
import re
from datetime import datetime, timedelta
from typing import Any


class NLExpenseParser:
    """Regex and heuristics based parser for natural language expenses."""

    # Common categories
    CATEGORIES = {
        "food": ["lunch", "dinner", "breakfast", "groceries", "coffee", "snack"],
        "transport": ["gas", "uber", "lyft", "taxi", "train", "bus", "parking"],
        "utilities": ["electric", "water", "internet", "phone", "bill"],
        "shopping": ["amazon", "clothes", "shoes", "target", "walmart"],
    }

    def parse(self, text: str) -> dict[str, Any]:
        """Parse natural language text into a structured expense.

        Args:
            text: e.g. "Gas $45 Shell yesterday"
        """
        text = text.lower().strip()
        result: dict[str, Any] = {
            "amount": 0.0,
            "merchant": "Unknown",
            "category_id": "cat-general",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "is_recurring": False,
        }

        # 1. Extract Amount ($45, 45.50, 12 bucks)
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)\s*(?:bucks|dollars)?', text)
        if amount_match:
            result["amount"] = float(amount_match.group(1))
            # Remove amount from text to help merchant extraction
            text = text.replace(amount_match.group(0), "").strip()

        # 2. Extract Date (yesterday, today, monday)
        if "yesterday" in text:
            result["date"] = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            text = text.replace("yesterday", "")
        
        # 3. Detect Recurring
        if "recurring" in text or "monthly" in text or "subscription" in text:
            result["is_recurring"] = True
            text = re.sub(r'(recurring|monthly|subscription)', '', text)

        # 4. Infer Category
        found_cat = False
        for cat, keywords in self.CATEGORIES.items():
            for kw in keywords:
                if kw in text:
                    result["category_id"] = f"cat-{cat}"
                    found_cat = True
                    # If merchant is unknown, use the keyword as a hint
                    if result["merchant"] == "Unknown":
                        result["merchant"] = kw.capitalize()
                    break
            if found_cat:
                break

        # 5. Fallback Merchant Extraction (whatever is left that's not a stopword)
        stopwords = {"at", "for", "on", "in", "bought", "spent", "paid"}
        words = [w for w in text.split() if w not in stopwords and len(w) > 2]
        if words and result["merchant"] == "Unknown":
            result["merchant"] = " ".join(words).title()
        elif words:
            # Overwrite the hint with actual remaining words
            result["merchant"] = " ".join(words).title()

        # Ensure expense is negative
        if result["amount"] > 0:
            result["amount"] = -result["amount"]

        return result
