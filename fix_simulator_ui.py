import re

with open(r'src\pages\SimulatorPage.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Make it look like a tactical control panel
old_bg = 'className="min-h-[calc(100vh-4rem)] bg-slate-950 p-4 lg:p-6"'
new_bg = 'className="min-h-[calc(100vh-4rem)] bg-[#000000] p-4 lg:p-6"'
text = text.replace(old_bg, new_bg)

old_header = '<h1 className="text-2xl font-medium tracking-tight text-white mb-6">'
new_header = '<h1 className="text-xl font-mono uppercase tracking-widest text-[#a1a1aa] mb-6 flex items-center gap-2 border-b border-white/[0.08] pb-4"><span className="w-2 h-2 bg-indigo-500"></span> '
text = text.replace(old_header, new_header)

old_panel = 'className="bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-[24px] p-6 lg:col-span-1"'
new_panel = 'className="bg-[#050505] border border-white/[0.08] p-6 lg:col-span-1 relative"'
text = text.replace(old_panel, new_panel)

old_sub_h2 = '<h2 className="text-lg font-medium text-white mb-6">'
new_sub_h2 = ' {/* Corner accent */}<div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-white/[0.3]" /><h2 className="text-xs font-mono uppercase tracking-widest text-[#a1a1aa] mb-6">'
text = text.replace(old_sub_h2, new_sub_h2)

old_chart = 'className="bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-[24px] p-6 lg:col-span-2"'
new_chart = 'className="bg-[#050505] border border-white/[0.08] p-6 lg:col-span-2 relative"'
text = text.replace(old_chart, new_chart)

with open(r'src\pages\SimulatorPage.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
