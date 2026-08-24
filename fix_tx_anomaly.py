import re

with open(r'backend\app\api\v1\transactions.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace import section to include EnhancedIsolationForest
old_import = '''from app.db.session import get_db
from app.db.models.transaction import Transaction'''
new_import = '''from app.db.session import get_db
from app.db.models.transaction import Transaction
from app.ml.anomaly.ml_detectors import EnhancedIsolationForest'''
text = text.replace(old_import, new_import)

# Replace anomaly logic in import_csv
old_logic = '''              tx = Transaction(
                  id=f"tx-import-{int(datetime.utcnow().timestamp() * 1000)}-{i}",
                  user_id=current_user.id,
                  date=date.fromisoformat(date_str) if date_str else date.today(),
                  merchant=merchant_str or "Imported Merchant",
                  amount=amount,
                  category_id=cat_str,
                  account_id=account_id,
                  status="settled",
                  is_recurring=False,
              )
              db.add(tx)'''

new_logic = '''              
              # Simple inline anomaly scoring using Isolation Forest
              # (For production, this would be batched or asynchronous)
              import pandas as pd
              import numpy as np
              df_score = pd.DataFrame([{
                  "amount": amount,
                  "date": date_str or str(date.today()),
              }])
              detector = EnhancedIsolationForest(contamination=0.03, n_estimators=50)
              # Hack for demo: fit on dummy data + current point so it can predict
              dummy_data = pd.DataFrame({
                  "amount": np.random.normal(50, 15, 20).tolist() + [amount],
                  "date": [str(date.today())] * 21
              })
              detector.fit(dummy_data)
              X = detector._extract_features(df_score)
              if detector._scaler.mean_ is not None:
                  X_scaled = detector._scaler.transform(X)
                  pred = detector._model.predict(X_scaled)[0]
                  is_anomaly = bool(pred == -1)
                  anomaly_score = float(detector._model.decision_function(X_scaled)[0])
              else:
                  is_anomaly = False
                  anomaly_score = 0.0

              tx = Transaction(
                  id=f"tx-import-{int(datetime.utcnow().timestamp() * 1000)}-{i}",
                  user_id=current_user.id,
                  date=date.fromisoformat(date_str) if date_str else date.today(),
                  merchant=merchant_str or "Imported Merchant",
                  amount=amount,
                  category_id=cat_str,
                  account_id=account_id,
                  status="settled",
                  is_recurring=False,
                  is_anomaly=is_anomaly,
                  anomaly_reason="Isolation Forest detected unusual pattern" if is_anomaly else None,
                  anomaly_score=anomaly_score,
              )
              db.add(tx)'''

text = text.replace(old_logic, new_logic)

with open(r'backend\app\api\v1\transactions.py', 'w', encoding='utf-8') as f:
    f.write(text)
