import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HealthDashboard from './pages/HealthDashboard';

function App() {
  const [health, setHealth] = useState(null);

  return (
    <BrowserRouter>
      <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-600 selection:text-white">
        <Navbar health={health} />
        
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<HealthDashboard health={health} setHealth={setHealth} />} />
            <Route path="/health" element={<HealthDashboard health={health} setHealth={setHealth} />} />
          </Routes>
        </main>

        <Footer />
      </div>
    </BrowserRouter>
  );
}

export default App;
