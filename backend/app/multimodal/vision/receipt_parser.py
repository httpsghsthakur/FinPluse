"""
Finpluse v2 -- Receipt OCR Parser

Parses text extracted from images via Tesseract/Cloud Vision.
"""
import re
from typing import Any


class ReceiptParser:
    """Extracts structured data from raw OCR text."""

    def parse_ocr_text(self, text: str) -> dict[str, Any]:
        """Extract merchant, total amount, and date from raw OCR text."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        result = {
            "merchant": "Unknown Merchant",
            "total_amount": 0.0,
            "date": None,
            "items": [],
            "confidence": 0.0
        }

        if not lines:
            return result

        # 1. Merchant is usually the first non-empty line with text
        for line in lines[:3]:
            if len(line) > 3 and not re.search(r'\d', line):
                result["merchant"] = line
                break
        
        if result["merchant"] == "Unknown Merchant":
             result["merchant"] = lines[0] # Fallback

        # 2. Extract Total Amount
        # Look for "Total", "Amount Due", etc followed by a number
        total_pattern = re.compile(r'(?:total|amount due|balance).*?\$?(\d+\.\d{2})', re.IGNORECASE)
        for line in reversed(lines):  # Total is usually at the bottom
            match = total_pattern.search(line)
            if match:
                result["total_amount"] = -float(match.group(1))
                result["confidence"] += 0.4
                break
        
        # Fallback for amount: find the largest number with 2 decimals
        if result["total_amount"] == 0.0:
            amounts = []
            for line in lines:
                matches = re.findall(r'\$?(\d+\.\d{2})', line)
                for m in matches:
                    amounts.append(float(m))
            if amounts:
                result["total_amount"] = -max(amounts)
                result["confidence"] += 0.2

        # 3. Extract Date
        date_pattern = re.compile(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})')
        for line in lines:
            match = date_pattern.search(line)
            if match:
                result["date"] = match.group(1)
                result["confidence"] += 0.3
                break

        # Normalize confidence
        result["confidence"] = min(1.0, result["confidence"] + 0.1)

        return result
