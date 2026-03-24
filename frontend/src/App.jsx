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
import NotFound from './pages/NotFound';
import './App.css';

/**
 * Main App Component
 * Sets up client-side routing for Fluence application
 *
 * TM20-90: Route protection and conflict resolution
 *
 * Public routes (no auth required):
 * - /           : Home page
 * - /data        : Disease data display view
 * - /map         : Disease map view
 * - /login       : Login page
 * - /signup      : Sign up page
 * - /forgot-password : Password reset request
 * - /reset-password  : Password reset form
 * - /verify-email    : Email verification guidance
 *
 * Protected routes (auth required — redirects to /login):
 * - /verify      : Health official verification page
 * - /submit      : Case submission page (also requires official verification)
 *
 * Catch-all:
 * - *            : 404 Not Found page
 */
function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<Home />} />
            <Route path="/data" element={<DiseaseDataView />} />
            <Route path="/map" element={<MapView />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/verify-email" element={<VerifyEmail />} />

            {/* Protected routes — require authentication */}
            <Route
              path="/verify"
              element={
                <ProtectedRoute>
                  <HealthOfficialAuth />
                </ProtectedRoute>
              }
            />
            <Route
              path="/submit"
              element={
                <ProtectedRoute>
                  <CaseSubmission />
                </ProtectedRoute>
              }
            />

            {/* Catch-all 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
