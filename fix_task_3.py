with open(r'C:\Users\gt643\.gemini\antigravity-ide\brain\8cc2dd3f-9805-431d-a773-67966e0a2517\task.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("[ ] 3. Landing Page Polish", "[x] 3. Landing Page Polish")
text = text.replace("[ ] Update LandingPage.tsx copy", "[x] Update LandingPage.tsx copy")
text = text.replace("[ ] Refine UI/UX with premium", "[x] Refine UI/UX with premium")

with open(r'C:\Users\gt643\.gemini\antigravity-ide\brain\8cc2dd3f-9805-431d-a773-67966e0a2517\task.md', 'w', encoding='utf-8') as f:
    f.write(text)
