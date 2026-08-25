with open(r'C:\Users\gt643\.gemini\antigravity-ide\brain\8cc2dd3f-9805-431d-a773-67966e0a2517\task.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("[ ] 2. Layouts (Command Center Feel)", "[x] 2. Layouts (Command Center Feel)")
text = text.replace("[ ] Redesign Sidebar.tsx and Topbar.tsx", "[x] Redesign Sidebar.tsx and Topbar.tsx")

with open(r'C:\Users\gt643\.gemini\antigravity-ide\brain\8cc2dd3f-9805-431d-a773-67966e0a2517\task.md', 'w', encoding='utf-8') as f:
    f.write(text)
