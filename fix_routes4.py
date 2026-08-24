import os
import re

directory = 'backend/app/api/v1'
files_to_fix = [
    'accounts.py',
    'categories.py',
    'goals.py',
    'insights.py',
    'ml_endpoints.py',
    'dashboard.py'
]

for filename in files_to_fix:
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace (db: AsyncSession = Depends(get_db)): with (db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    content = content.replace('db: AsyncSession = Depends(get_db)):', 'db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done")
