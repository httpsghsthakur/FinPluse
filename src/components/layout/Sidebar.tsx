import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  Receipt,
  PieChart,
  Target,
  ChevronLeft,
  ChevronRight,
  Activity,
  LineChart,
  BrainCircuit,
  Briefcase,
  MonitorPlay,
  Filter,
  BellRing,
  Settings
} from 'lucide-react';
import { useUIStore } from '../../lib/store/useUIStore';
import { cn } from '../../lib/utils/cn';

const FINPULSE_ITEMS = [
  { name: 'Dashboard', path: '/app', icon: LayoutDashboard },
  { name: 'Markets', path: '/app/markets', icon: LineChart },
  { name: 'Stock Research', path: '/app/research', icon: Activity },
  { name: 'AI Predictions', path: '/app/predictions', icon: BrainCircuit },
  { name: 'Portfolio', path: '/app/portfolio', icon: Briefcase },
  { name: 'Paper Trading', path: '/app/paper-trading', icon: MonitorPlay },
  { name: 'Screener', path: '/app/screener', icon: Filter },
  { name: 'Alerts', path: '/app/alerts', icon: BellRing },
  { name: 'AI Assistant', path: '/app/copilot', icon: Bot, highlight: true },
];

const FINANCE_ITEMS = [
  { name: 'Bank Statements', path: '/app/statements', icon: Receipt },
  { name: 'Income & Exp', path: '/app/transactions', icon: PieChart },
  { name: 'Goals', path: '/app/goals', icon: Target },
];

export const Sidebar: React.FC = () => {
  const { isSidebarCollapsed, toggleSidebar } = useUIStore();
  const location = useLocation();

  const renderNavGroup = (title: string, items: typeof FINPULSE_ITEMS) => (
    <div className="mb-6">
      {!isSidebarCollapsed && (
        <div className="px-4 mb-2 text-[10px] font-bold tracking-widest text-slate-500 uppercase">
          {title}
        </div>
      )}
      <div className="space-y-1">
        {items.map((item, index) => {
          const isActive = item.path === '/app'
            ? location.pathname === '/app'
            : location.pathname.startsWith(item.path);
          return (
            <NavLink
              key={item.path}
              to={item.path}
              title={isSidebarCollapsed ? item.name : undefined}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 transition-all duration-300 group relative rounded-lg',
                isActive
                  ? 'text-white bg-emerald-500/10 nav-active-glow border border-emerald-500/20'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.04]',
                item.highlight && !isActive && 'text-emerald-400 hover:text-emerald-300'
              )}
            >
              <item.icon
                className={cn(
                  'w-4 h-4 flex-shrink-0 transition-all duration-300 relative z-10',
                  isActive ? 'opacity-100 text-emerald-400' : 'opacity-70 group-hover:opacity-100'
                )}
              />
              {!isSidebarCollapsed && (
                <span className="font-medium text-xs relative z-10">
                  {item.name}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>
    </div>
  );

  return (
    <aside
      className={cn(
        'relative h-screen bg-[#020202] border-r border-slate-800/50 transition-all duration-500 ease-out flex flex-col hidden md:flex',
        !isSidebarCollapsed ? 'w-64' : 'w-20'
      )}
    >
      {/* ═══ Brand ═══ */}
      <div className="h-16 flex items-center px-5 border-b border-slate-800/50 relative z-10">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-8 h-8 rounded bg-emerald-500/10 flex items-center justify-center relative z-10 border border-emerald-500/20">
              <Activity className="w-4 h-4 text-emerald-400" strokeWidth={2.5} />
            </div>
          </div>
          {!isSidebarCollapsed && (
            <span className="font-bold text-sm text-white tracking-wide uppercase">
              FinPulse AI
            </span>
          )}
        </div>
      </div>

      {/* ═══ Nav Items ═══ */}
      <nav className="flex-1 py-6 px-3 overflow-y-auto custom-scrollbar relative z-10">
        {renderNavGroup("Market Intelligence", FINPULSE_ITEMS)}
        {renderNavGroup("Personal Finance", FINANCE_ITEMS)}
        
        {!isSidebarCollapsed && <div className="h-px bg-slate-800/50 mx-4 my-4" />}
        
        <NavLink
          to="/app/settings"
          title={isSidebarCollapsed ? "Settings" : undefined}
          className={cn(
            'flex items-center gap-3 px-3 py-2.5 transition-all duration-300 group relative rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.04]',
            location.pathname.startsWith('/app/settings') && 'text-white bg-white/10'
          )}
        >
          <Settings className="w-4 h-4 opacity-70 group-hover:opacity-100" />
          {!isSidebarCollapsed && <span className="font-medium text-xs">Settings</span>}
        </NavLink>
      </nav>

      {/* ═══ Collapse Toggle ═══ */}
      <div className="p-4 border-t border-slate-800/50 relative z-10">
        <button
          onClick={toggleSidebar}
          className="w-full flex items-center justify-center p-2 text-slate-500 hover:text-white hover:bg-white/5 transition-all duration-300 rounded-lg group"
        >
          {!isSidebarCollapsed ? (
            <ChevronLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
          ) : (
            <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          )}
        </button>
      </div>
    </aside>
  );
};

