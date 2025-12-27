import { NavLink } from 'react-router-dom';
import { LayoutGrid, Box, Palette, Info, GitFork, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';

// Moved NavItem outside to avoid re-creation during render
const NavItem = ({
  to,
  icon: Icon,
  label,
  className,
}: {
  to: string;
  icon: any;
  label: string;
  className?: string;
}) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      clsx(
        'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
        isActive
          ? 'bg-blue-50 text-blue-600'
          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900',
        className
      )
    }
  >
    <Icon size={18} />
    <span>{label}</span>
  </NavLink>
);

export default function AppSidebar() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(true);

  return (
    <aside className="w-64 h-full bg-white border-r border-slate-200 flex flex-col flex-shrink-0">
      <div className="p-4 border-b border-slate-100 mb-2">
        <div className="flex items-center gap-2 font-bold text-slate-800 text-lg">
          <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center">
            <span className="text-sm">AA</span>
          </div>
          AgentArchitect
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Flows Section */}
        <div className="space-y-1">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2">
            Workspace
          </div>
          <NavItem to="/flows" icon={GitFork} label="Flows" />
          <NavItem to="/agents" icon={Box} label="Agents & Nodes" />
        </div>

        {/* Settings Section */}
        <div className="space-y-1">
          <button
            onClick={() => setIsSettingsOpen(!isSettingsOpen)}
            className="w-full flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider px-3 mb-2 hover:text-slate-600 focus:outline-none"
          >
            Settings
            {isSettingsOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          </button>

          {isSettingsOpen && (
            <div className="space-y-1 animate-in slide-in-from-top-1 duration-200">
              {/* Redirect /settings to /settings/models usually, but links connect directly */}
              <NavItem to="/settings/general" icon={Box} label="General" />
              <NavItem to="/settings/models" icon={LayoutGrid} label="Models & Keys" />
              <NavItem to="/settings/appearance" icon={Palette} label="Appearance" />
              <NavItem to="/settings/help" icon={Info} label="Help" />
              <NavItem to="/settings/about" icon={Info} label="About" />
            </div>
          )}
        </div>
      </div>

      <div className="p-4 border-t border-slate-100 text-xs text-slate-400 text-center">
        v0.1.0 Alpha
      </div>
    </aside>
  );
}
