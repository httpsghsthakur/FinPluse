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
    
    if 'get_current_user' not in content:
        # add imports after future
        if 'from __future__ import annotations' in content:
            content = content.replace('from __future__ import annotations', 'from __future__ import annotations\nfrom app.api.deps import get_current_user\nfrom app.db.models.user import User')
        else:
            content = 'from app.api.deps import get_current_user\nfrom app.db.models.user import User\n' + content
            
    # Add current_user to any async def that has Depends(get_db) but not current_user
    # Using regex
    content = re.sub(r'(async def [a-zA-Z0-9_]+\(.*?\s+db: AsyncSession = Depends\(get_db\),?)(\s*\):)', r'\1\n    current_user: User = Depends(get_current_user),\2', content, flags=re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
print("Done")
