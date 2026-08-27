import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import SurveyView from './pages/SurveyView';
import { useState } from 'react';

function Nav() {
  return (
    <nav
      className="h-11 flex items-center justify-between px-6 border-b text-xs font-medium z-40 flex-shrink-0"
      style={{ backgroundColor: '#070f1a', borderColor: '#1b3a5e' }}
    >
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 font-bold tracking-wider text-white text-sm">
          <span className="text-blue-400">SONARIS</span>
          <span className="text-slate-400 text-xs font-normal">| Mission Control</span>
        </div>

        <div className="flex items-center gap-2">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-blue-600/30 text-blue-300 border border-blue-500/50 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-slate-800/40'
              }`
            }
          >
            🗺️ GIS Dashboard
          </NavLink>
          <NavLink
            to="/surveys"
            className={({ isActive }) =>
              `px-3 py-1 rounded-md text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-blue-600/30 text-blue-300 border border-blue-500/50 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-slate-800/40'
              }`
            }
          >
            📁 Survey Missions
          </NavLink>
        </div>
      </div>

      <div className="flex items-center gap-3 text-[11px] text-gray-400">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-gray-300 font-mono">EdgeTech SSS Pipeline Online</span>
        </span>
      </div>
    </nav>
  );
}

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <BrowserRouter>
      <div className="h-screen flex flex-col overflow-hidden" style={{ backgroundColor: '#0a1628' }}>
        <Nav />
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<Dashboard key={refreshKey} />} />
            <Route
              path="/surveys"
              element={
                <SurveyView
                  onProcess={() => {
                    setRefreshKey((k) => k + 1);
                  }}
                />
              }
            />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
