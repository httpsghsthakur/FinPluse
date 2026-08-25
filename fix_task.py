with open(r'C:\Users\gt643\.gemini\antigravity-ide\brain\8cc2dd3f-9805-431d-a773-67966e0a2517\task.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("[ ] 2. Social Sharing Features", "[x] 2. Social Sharing Features")
text = text.replace("[ ] Create ShareInsightModal.tsx", "[x] Create ShareInsightModal.tsx")
text = text.replace("[ ] Add \"Share\" buttons", "[x] Add \"Share\" buttons")

with open(r'C:\Users\gt643\.gemini\antigravity-ide\brain\8cc2dd3f-9805-431d-a773-67966e0a2517\task.md', 'w', encoding='utf-8') as f:
    f.write(text)
