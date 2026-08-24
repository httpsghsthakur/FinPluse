import re

with open(r'backend\app\api\v1\transactions.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace account_id resolution
old_str = '''    csv_text = data.get("csvText", "")
    lines = csv_text.strip().split("\\n")
    imported = 0'''

new_str = '''    csv_text = data.get("csvText", "")
    lines = csv_text.strip().split("\\n")
    imported = 0
    
    # Ensure user has an account
    acc_res = await db.execute(select(Account).where(Account.user_id == current_user.id).limit(1))
    account = acc_res.scalars().first()
    if not account:
        from app.db.models.account import Account
        account = Account(id=f"acc-{current_user.id[:8]}", user_id=current_user.id, name="Default Account", type="checking", balance=0.0, currency="USD")
        db.add(account)
        await db.flush()
    account_id = account.id'''

text = text.replace(old_str, new_str)

with open(r'backend\app\api\v1\transactions.py', 'w', encoding='utf-8') as f:
    f.write(text)
