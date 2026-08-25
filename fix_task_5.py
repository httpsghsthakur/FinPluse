with open(r'C:\Users\gt643\.gemini\antigravity-ide\brain\8cc2dd3f-9805-431d-a773-67966e0a2517\task.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("[ ] 4. Application Pages", "[x] 4. Application Pages")
text = text.replace("[ ] Update DashboardPage.tsx layout", "[x] Update DashboardPage.tsx layout")
text = text.replace("[ ] Reskin CopilotPage.tsx", "[x] Reskin CopilotPage.tsx")
text = text.replace("[ ] Reskin SimulatorPage.tsx", "[x] Reskin SimulatorPage.tsx")

with open(r'C:\Users\gt643\.gemini\antigravity-ide\brain\8cc2dd3f-9805-431d-a773-67966e0a2517\task.md', 'w', encoding='utf-8') as f:
    f.write(text)
