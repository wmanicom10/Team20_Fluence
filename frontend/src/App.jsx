import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import DiseaseDataView from './pages/DiseaseDataView';
import MapView from './pages/MapView';
import Login from './pages/Login';
import Signup from './pages/Signup';
import CaseSubmission from './pages/CaseSubmission';
import './App.css';

/**
 * Main App Component
 * Sets up client-side routing for Fluence application
 * 
 * Routes:
 * - / : Home page
 * - /data : Disease data display view
 * - /map : Disease map view
 */
function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/data" element={<DiseaseDataView />} />
            <Route path="/map" element={<MapView />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/submit" element={<CaseSubmission />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
