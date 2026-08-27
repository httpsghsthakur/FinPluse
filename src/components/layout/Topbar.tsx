import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Search,
  RefreshCw,
  Plus,
  Menu,
  X,
  Activity,
  Terminal,
  Command,
} from 'lucide-react';
import { useUserStore } from '../../lib/store/useUserStore';
import { useUIStore } from '../../lib/store/useUIStore';
import { CurrencyCode } from '../../types';
import { cn } from '../../lib/utils/cn';

export const Topbar: React.FC = () => {
  const navigate = useNavigate();
  const profile = useUserStore((s) => s.profile);
  const currency = useUserStore((s) => s.profile.currency);
  const setCurrency = useUserStore((s) => s.setCurrency);

  const {
    isMobileNavOpen,
    toggleMobileNav,
    openAddTxModal,
    showToast,
  } = useUIStore();
  const [isSyncing, setIsSyncing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  const handleSyncAll = () => {
    setIsSyncing(true);
    setTimeout(() => {
      setIsSyncing(false);
      showToast({
        type: 'success',
        title: 'System Synced',
        description: 'Ledger data imported and verified.',
      });
    }, 800);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/app/transactions?q=` + encodeURIComponent(searchQuery));
    }
  };

  return (
    <header className="h-16 bg-[#000000]/80 backdrop-blur-xl border-b border-white/[0.06] px-4 lg:px-6 flex items-center justify-between gap-4 sticky top-0 z-20">
      {/* Mobile brand & hamburger */}
      <div className="flex items-center gap-3 md:hidden">
        <button
          onClick={toggleMobileNav}
          className="p-1.5 text-[#a1a1aa] hover:text-white hover:bg-white/[0.06] transition-all duration-200 rounded-lg"
        >
          {isMobileNavOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
        <NavLink to="/app" className="font-mono text-sm font-bold tracking-widest text-white uppercase flex items-center gap-2">
          <Activity className="w-4 h-4" />
          Finpluse
        </NavLink>
      </div>

      {/* System Status / Search */}
      <div className="hidden md:flex items-center gap-4 flex-1">
        {/* Animated status badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 glass-card-static rounded-lg">
          <span className="relative w-1.5 h-1.5">
            <span className="absolute inset-0 bg-emerald-400 rounded-full" />
            <span className="absolute inset-[-3px] border border-emerald-400/40 rounded-full animate-ring-pulse" />
          </span>
          <span className="font-mono text-[10px] uppercase text-[#a1a1aa] tracking-wider">
            Engine: Online
          </span>
        </div>
        
        {/* Search with glow focus */}
        <form onSubmit={handleSearchSubmit} className={cn(
          "flex-1 max-w-md relative transition-all duration-300",
          isSearchFocused && "max-w-lg"
        )}>
          <Search className={cn(
            "w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none transition-colors duration-200",
            isSearchFocused ? "text-emerald-400" : "text-[#a1a1aa]"
          )} />
          <input
            type="text"
            placeholder="Query ledger..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setIsSearchFocused(true)}
            onBlur={() => setIsSearchFocused(false)}
            className="w-full pl-9 pr-4 py-1.5 bg-[#0a0a0a] border border-white/[0.06] text-xs font-mono text-white placeholder-[#52525b] input-glow rounded-lg transition-all duration-300"
          />
          {/* Keyboard shortcut hint */}
          <div className="absolute right-3 top-1/2 -translate-y-1/2 hidden lg:flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 text-[9px] font-mono text-[#52525b] bg-white/[0.03] border border-white/[0.06] rounded">
              ⌘K
            </kbd>
          </div>
        </form>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 lg:gap-3">
        <button
          onClick={openAddTxModal}
          className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-[#0a0a0a] hover:bg-[#141414] text-white text-xs font-mono border border-white/[0.06] hover:border-white/[0.12] transition-all duration-200 rounded-lg btn-glow"
        >
          <Plus className="w-3.5 h-3.5" />
          Log Entry
        </button>

        <div className="relative">
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value as CurrencyCode)}
            className="bg-[#0a0a0a] border border-white/[0.06] text-white text-xs font-mono px-3 py-1.5 appearance-none pr-8 focus:outline-none hover:border-white/[0.12] cursor-pointer rounded-lg transition-all duration-200"
          >
            <option value="INR">INR</option>
            <option value="USD">USD</option>
            <option value="GBP">GBP</option>
          </select>
        </div>

        <button
          onClick={handleSyncAll}
          disabled={isSyncing}
          className="p-1.5 border border-white/[0.06] bg-[#0a0a0a] text-[#a1a1aa] hover:text-white hover:border-white/[0.12] transition-all duration-200 rounded-lg"
        >
          <RefreshCw className={cn('w-4 h-4 transition-transform duration-700', isSyncing && 'animate-spin text-emerald-400')} />
        </button>

        {/* Copilot Link — Animated gradient */}
        <NavLink
          to="/app/copilot"
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono transition-all duration-300 rounded-lg relative overflow-hidden group"
          style={{
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(6, 182, 212, 0.08))',
            border: '1px solid rgba(16, 185, 129, 0.2)',
          }}
        >
          {/* Shimmer overlay on hover */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.05] to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
          <Terminal className="w-3.5 h-3.5 text-emerald-400 relative z-10" />
          <span className="hidden md:inline text-emerald-400 font-semibold relative z-10">Command Line</span>
        </NavLink>

        <NavLink to="/app/settings" className="pl-2 border-l border-white/[0.06]">
          <div className="relative group">
            <img
              src={profile.avatarUrl}
              alt={profile.name}
              className="w-7 h-7 rounded-lg object-cover border border-white/[0.08] group-hover:border-emerald-500/40 transition-all duration-300 group-hover:shadow-[0_0_15px_rgba(16,185,129,0.2)]"
            />
            {/* Online status dot */}
            <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 bg-emerald-400 rounded-full border border-[#030303]" />
          </div>
        </NavLink>
      </div>
    </header>
  );
};
