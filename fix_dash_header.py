import re

with open(r'src\pages\DashboardPage.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace header styles
old_header = '<h1 className="text-2xl font-medium tracking-tight text-white">'
new_header = '<h1 className="text-xl font-mono uppercase tracking-widest text-white flex items-center gap-2"><span className="w-2 h-2 bg-white"></span> Overview</h1>'
text = text.replace(old_header, new_header)

old_btn = 'className="flex items-center gap-2 bg-[#141414] hover:bg-[#1a1a1a] border border-white/[0.08] px-4 py-2 rounded-lg text-sm text-white transition-colors"'
new_btn = 'className="flex items-center gap-2 bg-[#0a0a0a] hover:bg-white hover:text-black border border-white/[0.2] px-4 py-1.5 text-xs font-mono uppercase tracking-wider text-white transition-colors"'
text = text.replace(old_btn, new_btn)

with open(r'src\pages\DashboardPage.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
