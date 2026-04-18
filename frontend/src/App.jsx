import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { PatientProvider } from './context/PatientContext';
import LandingPage from './pages/LandingPage';
import StepOne from './pages/StepOne';
import StepTwo from './pages/StepTwo';
import ResultPage from './pages/ResultPage';

function App() {
  return (
    <PatientProvider>
      <Router>
        <div className="min-h-screen">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/step-1" element={<StepOne />} />
            <Route path="/step-2" element={<StepTwo />} />
            <Route path="/results" element={<ResultPage />} />
          </Routes>
        </div>
      </Router>
    </PatientProvider>
  );
}

export default App;
