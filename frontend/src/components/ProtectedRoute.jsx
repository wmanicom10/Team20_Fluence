import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * ProtectedRoute Component
 * TM20-90: Enhanced route guard with loading state and redirect handling.
 *
 * Wraps child components to enforce authentication. If the user is not
 * logged in, they are redirected to /login. While the auth state is loading
 * (e.g. on initial page load while Supabase checks the session), a loading
 * indicator is shown to prevent flash-of-content.
 *
 * Usage:
 *   <Route path="/submit" element={<ProtectedRoute><CaseSubmission /></ProtectedRoute>} />
 *
 * Props:
 *   children — the component(s) to render when authenticated
 *   redirectTo — optional override for redirect target (defaults to "/login")
 */
function ProtectedRoute({ children, redirectTo = '/login' }) {
  const { user, loading } = useAuth();

  // While auth state is being determined, show a loading indicator
  // to prevent unauthenticated flash-of-content
  if (loading) {
    return (
      <div className="route-loading" style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '40vh',
        color: '#888',
        fontSize: '1.1rem',
      }}>
        <p>Checking authentication...</p>
      </div>
    );
  }

  // Unauthenticated users are redirected to the login page
  if (!user) {
    return <Navigate to={redirectTo} replace />;
  }

  // Authenticated — render the protected content
  return children;
}

export default ProtectedRoute;