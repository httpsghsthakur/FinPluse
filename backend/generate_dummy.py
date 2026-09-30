import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "ml", "pipeline", "data", "raw")
os.makedirs(DATA_DIR, exist_ok=True)
output_path = os.path.join(DATA_DIR, "master_market_dataset.parquet")

instruments = ["NSE_EQ|INE002A01018", "NSE_EQ|INE040A01034"]
rows = []
base_date = datetime.now() - timedelta(days=2000)

for instrument in instruments:
    price = 1000.0
    for i in range(2000):
        date = base_date + timedelta(days=i)
        if date.weekday() >= 5: continue # Skip weekends
        
        change = np.random.normal(0, 0.02)
        price = price * (1 + change)
        
        rows.append({
            "timestamp": date,
            "instrument_key": instrument,
            "open": price * 0.99,
            "high": price * 1.02,
            "low": price * 0.98,
            "close": price,
            "volume": int(np.random.normal(100000, 20000))
        })

df = pd.DataFrame(rows)
df.set_index('timestamp', inplace=True)
df.to_parquet(output_path, engine="pyarrow")
print(f"Dummy data generated: {output_path}")
