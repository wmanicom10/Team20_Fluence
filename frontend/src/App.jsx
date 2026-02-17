import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import DiseaseDataView from './pages/DiseaseDataView';
import './App.css';

/**
 * Main App Component
 * Sets up client-side routing for Fluence application
 * 
 * Routes:
 * - / : Home page
 * - /data : Disease data display view
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
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
