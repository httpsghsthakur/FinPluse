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
  Lightbulb,
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
  { name: 'Insights', path: '/app/insights', icon: Lightbulb },
];

export const Sidebar: React.FC = () => {
  const { isSidebarCollapsed, toggleSidebar } = useUIStore();
  const location = useLocation();

  return (
    <aside
      className={cn(
        'relative h-screen bg-[#000000]/90 backdrop-blur-xl border-r border-white/[0.06] transition-all duration-500 ease-out flex flex-col hidden md:flex',
        !isSidebarCollapsed ? 'w-64' : 'w-20'
      )}
    >
      {/* Subtle gradient overlay on sidebar */}
      <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/[0.02] to-transparent pointer-events-none" />

      {/* ═══ Brand ═══ */}
      <div className="h-16 flex items-center px-6 border-b border-white/[0.06] relative z-10">
        <div className="flex items-center gap-3">
          {/* Animated logo with pulse ring */}
          <div className="relative">
            <div className="w-8 h-8 bg-white flex items-center justify-center relative z-10">
              <Activity className="w-5 h-5 text-black" strokeWidth={2.5} />
            </div>
            <div className="absolute inset-0 bg-white/20 animate-ring-pulse rounded-sm" />
          </div>
          {!isSidebarCollapsed && (
            <span className="font-mono text-sm font-bold tracking-widest text-white uppercase animate-fadeIn">
              Finpluse
            </span>
          )}
        </div>
      </div>

      {/* ═══ Nav Items ═══ */}
      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto relative z-10">
        {NAV_ITEMS.map((item, index) => {
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
                  ? 'text-white bg-white/[0.06] nav-active-glow'
                  : 'text-[#a1a1aa] hover:text-white hover:bg-white/[0.04]',
                item.highlight && !isActive && 'text-blue-400 hover:text-blue-300'
              )}
              style={{
                animationDelay: `${index * 0.05}s`,
              }}
            >
              {/* Active glow background */}
              {isActive && (
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/[0.08] to-transparent rounded-lg pointer-events-none" />
              )}
              <item.icon
                className={cn(
                  'w-5 h-5 flex-shrink-0 transition-all duration-300 relative z-10',
                  isActive
                    ? 'opacity-100 scale-110'
                    : 'opacity-50 group-hover:opacity-100 group-hover:scale-105'
                )}
              />
              {!isSidebarCollapsed && (
                <span className="font-mono text-xs tracking-wider uppercase relative z-10">
                  {item.name}
                </span>
              )}
              {/* Hover indicator dot */}
              {!isActive && !isSidebarCollapsed && (
                <div className="absolute right-3 w-1 h-1 rounded-full bg-white/0 group-hover:bg-white/30 transition-all duration-300" />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* ═══ Collapse Toggle ═══ */}
      <div className="p-4 border-t border-white/[0.06] relative z-10">
        <button
          onClick={toggleSidebar}
          className="w-full flex items-center justify-center p-2 text-[#a1a1aa] hover:text-white hover:bg-white/[0.06] transition-all duration-300 rounded-lg group"
        >
          <div className="transition-transform duration-500 ease-out" style={{
            transform: isSidebarCollapsed ? 'rotate(0deg)' : 'rotate(0deg)'
          }}>
            {!isSidebarCollapsed ? (
              <ChevronLeft className="w-5 h-5 group-hover:-translate-x-0.5 transition-transform" />
            ) : (
              <ChevronRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
            )}
          </div>
        </button>
      </div>
    </aside>
  );
};
