import asyncio
from datetime import datetime, date
import sys

def test_csv_logic():
    csv_text = "Date,Merchant,Amount,Category\n2026-08-15,Whole Foods Market,92.50,cat-groceries"
    lines = csv_text.strip().split("\n")
    
    for i, line in enumerate(lines):
        if i == 0:
            continue
        parts = [p.strip().strip("\"'") for p in line.split(",")]
        print("Parts:", parts)
        if len(parts) >= 3:
            date_str, merchant_str, amount_str = parts[0], parts[1], parts[2]
            cat_str = parts[3] if len(parts) > 3 else "cat-other"
            
            try:
                amount = float(amount_str)
            except ValueError as e:
                print("ValueError:", e)
                continue
                
            print("Successfully parsed transaction!")
            print(f"Date: {date.fromisoformat(date_str)}")
            print(f"Merchant: {merchant_str}")
            print(f"Amount: {amount}")
            print(f"Category: {cat_str}")
            print(f"ID: tx-import-{int(datetime.utcnow().timestamp() * 1000)}-{i}")

test_csv_logic()
