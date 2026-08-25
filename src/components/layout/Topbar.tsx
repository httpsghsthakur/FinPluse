import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Search,
  RefreshCw,
  Sun,
  Moon,
  Plus,
  Bot,
  Menu,
  X,
  Activity,
  Terminal,
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
  const theme = useUserStore((s) => s.profile.theme);
  const toggleTheme = useUserStore((s) => s.toggleTheme);

  const {
    isMobileNavOpen,
    toggleMobileNav,
    openAddTxModal,
    showToast,
  } = useUIStore();
  const [isSyncing, setIsSyncing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

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
      navigate(/app/transactions?q= + encodeURIComponent(searchQuery));
    }
  };

  return (
    <header className="h-16 bg-[#000000] border-b border-white/[0.08] px-4 lg:px-6 flex items-center justify-between gap-4 sticky top-0 z-20">
      {/* Mobile brand & hamburger */}
      <div className="flex items-center gap-3 md:hidden">
        <button
          onClick={toggleMobileNav}
          className="p-1.5 rounded-none text-[#a1a1aa] hover:text-white hover:bg-white/[0.04] transition-colors"
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
        <div className="flex items-center gap-2 px-3 py-1 bg-white/[0.03] border border-white/[0.08]">
          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
          <span className="font-mono text-[10px] uppercase text-[#a1a1aa] tracking-wider">
            Engine: Online
          </span>
        </div>
        
        <form onSubmit={handleSearchSubmit} className="flex-1 max-w-md relative">
          <Search className="w-4 h-4 text-[#a1a1aa] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Query ledger..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 bg-[#0a0a0a] border border-white/[0.08] text-xs font-mono text-white placeholder-[#52525b] focus:outline-none focus:border-white/[0.2] transition-colors"
          />
        </form>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 lg:gap-3">
        <button
          onClick={openAddTxModal}
          className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-[#141414] hover:bg-[#1a1a1a] text-white text-xs font-mono border border-white/[0.08] transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Log Entry
        </button>

        <div className="relative">
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value as CurrencyCode)}
            className="bg-[#141414] border border-white/[0.08] text-white text-xs font-mono px-3 py-1.5 appearance-none pr-8 focus:outline-none focus:border-white/[0.2] cursor-pointer"
          >
            <option value="INR">INR</option>
            <option value="USD">USD</option>
            <option value="GBP">GBP</option>
          </select>
        </div>

        <button
          onClick={handleSyncAll}
          disabled={isSyncing}
          className="p-1.5 border border-white/[0.08] bg-[#141414] text-[#a1a1aa] hover:text-white transition-colors"
        >
          <RefreshCw className={cn('w-4 h-4', isSyncing && 'animate-spin text-white')} />
        </button>

        <NavLink
          to="/app/copilot"
          className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 text-xs font-mono transition-colors"
        >
          <Terminal className="w-3.5 h-3.5" />
          <span className="hidden md:inline">Command Line</span>
        </NavLink>

        <NavLink to="/app/settings" className="pl-2 border-l border-white/[0.08]">
          <img
            src={profile.avatarUrl}
            alt={profile.name}
            className="w-7 h-7 object-cover grayscale hover:grayscale-0 transition-all border border-white/[0.08]"
          />
        </NavLink>
      </div>
    </header>
  );
};
