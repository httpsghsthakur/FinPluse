import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Receipt,
  Bot,
  Target,
  TrendingUp,
} from "lucide-react";
import { cn } from "../../lib/utils/cn";

const MOBILE_TABS = [
  { name: "Dashboard", path: "/app", icon: LayoutDashboard },
  { name: "Transactions", path: "/app/transactions", icon: Receipt },
  { name: "Copilot", path: "/app/copilot", icon: Bot, isCenter: true },
  { name: "Goals", path: "/app/goals", icon: Target },
  { name: "Forecast", path: "/app/forecast", icon: TrendingUp },
];

export const BottomNav: React.FC = () => {
  const location = useLocation();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 h-[72px] bg-[#030303]/95 backdrop-blur-2xl border-t border-white/[0.06] z-40 px-3 flex items-center justify-around">
      {MOBILE_TABS.map((tab) => {
        const Icon = tab.icon;
        const isActive =
          tab.path === "/app"
            ? location.pathname === "/app"
            : location.pathname.startsWith(tab.path);

        if (tab.isCenter) {
          return (
            <NavLink
              key={tab.path}
              to={tab.path}
              className="flex flex-col items-center -mt-6 group"
            >
              <div
                className={cn(
                  "w-13 h-13 rounded-2xl flex items-center justify-center shadow-lg transition-all duration-300 active:scale-95 relative",
                  isActive
                    ? "bg-emerald-400 text-slate-950"
                    : "bg-emerald-500 text-slate-950 hover:bg-emerald-400",
                )}
              >
                <Icon className="w-6 h-6 relative z-10" />
                {/* Glow ring */}
                <div className={cn(
                  "absolute inset-[-4px] rounded-2xl border transition-all duration-300",
                  isActive
                    ? "border-emerald-400/30 shadow-[0_0_25px_rgba(16,185,129,0.3)]"
                    : "border-transparent"
                )} />
                {/* Floating animation dot */}
                {isActive && (
                  <div className="absolute -bottom-2 w-1 h-1 rounded-full bg-emerald-400 animate-breathing" />
                )}
              </div>
              <span
                className={cn(
                  "text-[10px] font-semibold mt-1.5 transition-colors",
                  isActive ? "text-emerald-400" : "text-slate-500",
                )}
              >
                {tab.name}
              </span>
            </NavLink>
          );
        }

        return (
          <NavLink
            key={tab.path}
            to={tab.path}
            className={cn(
              "flex flex-col items-center py-1 px-2 rounded-xl transition-all duration-200 relative",
              isActive
                ? "text-emerald-400 font-semibold"
                : "text-slate-500 hover:text-slate-300",
            )}
          >
            <Icon className={cn(
              "w-5 h-5 transition-transform duration-200",
              isActive && "scale-110"
            )} />
            <span className="text-[10px] mt-0.5">{tab.name}</span>
            {/* Active indicator dot */}
            {isActive && (
              <div className="absolute -top-0.5 w-1 h-1 rounded-full bg-emerald-400" />
            )}
          </NavLink>
        );
      })}
    </nav>
  );
};
