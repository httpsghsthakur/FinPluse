import re

with open(r'src\components\ui\ChartCard.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace background and styling class
old_container = '"bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-[24px] p-5.5 flex flex-col"'
new_container = '"bg-[#050505] border border-white/[0.08] p-5 flex flex-col relative"'
text = text.replace(old_container, new_container)

# Add corner accent inside the div if possible, or just replace the header
old_header = '<h3 className="text-sm font-semibold text-slate-200">{title}</h3>'
new_header = '''{/* Corner accent */}
      <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-white/[0.3]" />
      <h3 className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-[#a1a1aa]">{title}</h3>'''
text = text.replace(old_header, new_header)

old_subtitle = '<p className="text-xs text-slate-400 mt-1">{subtitle}</p>'
new_subtitle = '<p className="font-mono text-[9px] uppercase tracking-wider text-[#a1a1aa] mt-1">{subtitle}</p>'
text = text.replace(old_subtitle, new_subtitle)

with open(r'src\components\ui\ChartCard.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
