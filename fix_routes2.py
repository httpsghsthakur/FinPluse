import os
import re

directory = 'backend/app/api/v1'
files_to_fix = [
    'accounts.py',
    'categories.py',
    'goals.py',
    'insights.py',
    'ml_endpoints.py'
]

for filename in files_to_fix:
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the missing comma issue
    content = content.replace('Depends(get_db)\n    current_user', 'Depends(get_db),\n    current_user')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done")
