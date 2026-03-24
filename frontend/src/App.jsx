import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import DiseaseDataView from './pages/DiseaseDataView';
import MapView from './pages/MapView';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import CaseSubmission from './pages/CaseSubmission';
import HealthOfficialAuth from './pages/HealthOfficialAuth';
import ProtectedRoute from './components/ProtectedRoute';
import VerifyEmail from './pages/VerifyEmail';
import './App.css';

/**
 * Main App Component
 * Sets up client-side routing for Fluence application
 * 
 * Routes:
 * - / : Home page
 * - /data : Disease data display view
 * - /map : Disease map view
 * - /login, /signup : Authentication pages
 * - /verify : Health official verification page
 * - /submit : Protected case submission page
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
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/verify" element={<HealthOfficialAuth />} />
            <Route
              path="/submit"
              element={
                <ProtectedRoute>
                  <CaseSubmission />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
