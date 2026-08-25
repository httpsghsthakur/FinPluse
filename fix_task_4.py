with open(r'C:\Users\gt643\.gemini\antigravity-ide\brain\8cc2dd3f-9805-431d-a773-67966e0a2517\task.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("[ ] 3. Data Visualizations & Cards", "[x] 3. Data Visualizations & Cards")
text = text.replace("[ ] Restyle KpiCard.tsx and ChartCard.tsx", "[x] Restyle KpiCard.tsx and ChartCard.tsx")

with open(r'C:\Users\gt643\.gemini\antigravity-ide\brain\8cc2dd3f-9805-431d-a773-67966e0a2517\task.md', 'w', encoding='utf-8') as f:
    f.write(text)
