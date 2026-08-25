import re

with open(r'src\pages\AuthPage.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = '''        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: { full_name: fullName },
          },
        });'''

new_logic = '''        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: { full_name: fullName },
            emailRedirectTo: ${window.location.origin}/app,
          },
        });'''

text = text.replace(old_logic, new_logic)

with open(r'src\pages\AuthPage.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
