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
    
    # Remove it from the very top if it exists there
    content = re.sub(r'^from app\.api\.deps import get_current_user\nfrom app\.db\.models\.user import User\n', '', content)
    
    # Insert it correctly after __future__ if present, else at the beginning
    if 'from __future__ import annotations' in content:
        if 'from app.api.deps import get_current_user' not in content:
            content = content.replace('from __future__ import annotations', 'from __future__ import annotations\nfrom app.api.deps import get_current_user\nfrom app.db.models.user import User')
    else:
        if 'from app.api.deps import get_current_user' not in content:
            content = 'from app.api.deps import get_current_user\nfrom app.db.models.user import User\n' + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done")
