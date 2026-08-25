import re

with open(r'src\pages\CopilotPage.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

# Make it look like a terminal
old_bg = 'className="min-h-[calc(100vh-4rem)] bg-slate-950 p-4 lg:p-6"'
new_bg = 'className="min-h-[calc(100vh-4rem)] bg-[#000000] p-4 lg:p-6 font-mono"'
text = text.replace(old_bg, new_bg)

old_header = '<h1 className="text-2xl font-medium tracking-tight text-white mb-6">AI Copilot</h1>'
new_header = '<h1 className="text-lg font-mono uppercase tracking-widest text-[#a1a1aa] mb-6 border-b border-white/[0.08] pb-4 flex items-center gap-2"><span className="w-2 h-2 bg-blue-500 animate-pulse"></span> Terminal System / Query Interface</h1>'
text = text.replace(old_header, new_header)

old_msg_container = 'className="flex-1 bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-[24px] overflow-hidden flex flex-col"'
new_msg_container = 'className="flex-1 bg-[#050505] border border-white/[0.08] overflow-hidden flex flex-col relative"'
text = text.replace(old_msg_container, new_msg_container)

old_user_msg = 'bg-emerald-500 text-white rounded-2xl rounded-tr-sm'
new_user_msg = 'bg-white text-black border border-white/[0.2] rounded-none'
text = text.replace(old_user_msg, new_user_msg)

old_ai_msg = 'bg-slate-800/80 text-slate-200 border border-slate-700/50 rounded-2xl rounded-tl-sm'
new_ai_msg = 'bg-[#0a0a0a] text-[#ededed] border border-white/[0.08] rounded-none shadow-[inset_4px_0_0_0_rgba(59,130,246,0.5)]'
text = text.replace(old_ai_msg, new_ai_msg)

old_input = 'className="flex-1 bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500/50 transition-colors"'
new_input = 'className="flex-1 bg-[#0a0a0a] border border-white/[0.08] px-4 py-3 text-xs font-mono text-white placeholder-[#52525b] focus:outline-none focus:border-white/[0.3] transition-colors rounded-none"'
text = text.replace(old_input, new_input)

old_submit = 'className="p-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl transition-colors disabled:opacity-50"'
new_submit = 'className="px-6 py-3 bg-white hover:bg-[#e5e5e5] text-black font-mono text-xs uppercase tracking-widest transition-colors disabled:opacity-50 rounded-none"'
text = text.replace(old_submit, new_submit)

with open(r'src\pages\CopilotPage.tsx', 'w', encoding='utf-8') as f:
    f.write(text)
