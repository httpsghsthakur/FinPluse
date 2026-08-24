import re

with open(r'backend\app\api\v1\transactions.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = '''          if len(parts) >= 3:
              date_str, merchant_str, amount_str = parts[0], parts[1], parts[2]
              cat_str = parts[3] if len(parts) > 3 else "cat-other"
              try:
                  amount = float(amount_str)
              except ValueError:
                  continue'''

new_logic = '''          if len(parts) >= 3:
              date_str, merchant_str, amount_str = parts[0], parts[1], parts[2]
              cat_str = parts[3] if len(parts) > 3 else "cat-other"
              
              # ML Auto-Categorization (TF-IDF + Logistic Regression)
              if not cat_str or cat_str == "cat-other":
                  try:
                      import pandas as pd
                      from app.ml.classifiers.logistic_baseline import LogisticBaselineClassifier
                      # Dummy training data for real-time demo inference
                      train_df = pd.DataFrame({
                          "merchant": ["whole foods", "safeway", "uber", "lyft", "netflix", "hbo", "chevron", "shell"],
                          "category": ["cat-groceries", "cat-groceries", "cat-transport", "cat-transport", "cat-entertainment", "cat-entertainment", "cat-auto", "cat-auto"]
                      })
                      clf = LogisticBaselineClassifier()
                      clf.fit(train_df, train_df["category"])
                      # Predict
                      pred_cat = clf.predict([merchant_str])
                      if pred_cat and len(pred_cat) > 0:
                          cat_str = pred_cat[0]
                  except Exception as e:
                      import logging
                      logging.getLogger(__name__).error(f"Categorization failed: {e}")
              
              try:
                  amount = float(amount_str)
              except ValueError:
                  continue'''

text = text.replace(old_logic, new_logic)

with open(r'backend\app\api\v1\transactions.py', 'w', encoding='utf-8') as f:
    f.write(text)
