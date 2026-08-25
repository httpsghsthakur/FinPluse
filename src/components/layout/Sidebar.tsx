import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  Receipt,
  PieChart,
  Target,
  TrendingUp,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  Activity,
} from 'lucide-react';
import { useUIStore } from '../../lib/store/useUIStore';
import { cn } from '../../lib/utils/cn';

const NAV_ITEMS = [
  { name: 'Overview', path: '/app', icon: LayoutDashboard },
  { name: 'Terminal (AI)', path: '/app/copilot', icon: Bot, highlight: true },
  { name: 'Ledger', path: '/app/transactions', icon: Receipt },
  { name: 'Allocations', path: '/app/budgets', icon: PieChart },
  { name: 'Targets', path: '/app/goals', icon: Target },
  { name: 'Projections', path: '/app/forecast', icon: TrendingUp },
  { name: 'Simulation', path: '/app/simulator', icon: SlidersHorizontal },
];

export const Sidebar: React.FC = () => {
  const { isSidebarOpen, toggleSidebar } = useUIStore();
  const location = useLocation();

  return (
    <aside
      className={cn(
        'relative h-screen bg-[#000000] border-r border-white/[0.08] transition-all duration-300 flex flex-col',
        isSidebarOpen ? 'w-64' : 'w-20'
      )}
    >
      {/* Brand */}
      <div className="h-16 flex items-center px-6 border-b border-white/[0.08]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white flex items-center justify-center">
            <Activity className="w-5 h-5 text-black" strokeWidth={2.5} />
          </div>
          {isSidebarOpen && (
            <span className="font-mono text-sm font-bold tracking-widest text-white uppercase">
              Finpluse
            </span>
          )}
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 transition-all group relative',
                  isActive
                    ? 'text-white bg-white/[0.04]'
                    : 'text-[#a1a1aa] hover:text-white hover:bg-white/[0.02]',
                  item.highlight && !isActive && 'text-blue-400 hover:text-blue-300'
                )
              }
            >
              {isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-white shadow-[0_0_8px_rgba(255,255,255,0.8)]" />
              )}
              <item.icon
                className={cn(
                  'w-5 h-5 flex-shrink-0',
                  isActive ? 'opacity-100' : 'opacity-50 group-hover:opacity-100'
                )}
              />
              {isSidebarOpen && (
                <span className="font-mono text-xs tracking-wider uppercase">
                  {item.name}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-4 border-t border-white/[0.08]">
        <button
          onClick={toggleSidebar}
          className="w-full flex items-center justify-center p-2 text-[#a1a1aa] hover:text-white hover:bg-white/[0.04] transition-colors"
        >
          {isSidebarOpen ? (
            <ChevronLeft className="w-5 h-5" />
          ) : (
            <ChevronRight className="w-5 h-5" />
          )}
        </button>
      </div>
    </aside>
  );
};
