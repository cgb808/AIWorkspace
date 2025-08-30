import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import GemmaPhi from './pages/GemmaPhi';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<GemmaPhi />} />
        <Route path="/chat" element={<GemmaPhi />} />
        <Route path="/gemma-phi" element={<GemmaPhi />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
