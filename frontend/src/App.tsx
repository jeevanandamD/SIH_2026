import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import SurveyView from './pages/SurveyView';
import { useState } from 'react';

function Nav() {
  return (
    <nav
      className="h-10 flex items-center px-4 border-b text-xs font-medium gap-4"
      style={{ backgroundColor: '#0a1628', borderColor: '#1b3a5e' }}
    >
      <NavLink
        to="/"
        className={({ isActive }) =>
          `transition-colors ${isActive ? 'text-blue-400' : 'text-gray-500 hover:text-gray-300'}`
        }
      >
        Dashboard
      </NavLink>
      <NavLink
        to="/surveys"
        className={({ isActive }) =>
          `transition-colors ${isActive ? 'text-blue-400' : 'text-gray-500 hover:text-gray-300'}`
        }
      >
        Surveys
      </NavLink>
    </nav>
  );
}

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <BrowserRouter>
      <div className="h-screen flex flex-col" style={{ backgroundColor: '#0a1628' }}>
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
    </BrowserRouter>
  );
}
