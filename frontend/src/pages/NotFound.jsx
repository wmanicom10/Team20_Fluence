import { Link } from 'react-router-dom';

/**
 * NotFound (404) Page Component
 * TM20-90: Catch-all route for undefined paths.
 *
 * Displayed when the user navigates to a route that does not exist.
 * Provides clear messaging and navigation options back to valid pages.
 */
function NotFound() {
  return (
    <div className="auth-page">
      <div className="auth-card" style={{ textAlign: 'center' }}>
        <div className="auth-header">
          <span className="auth-icon" style={{ fontSize: '3rem' }}>🔍</span>
          <h2>Page Not Found</h2>
          <p className="muted">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          marginTop: '1.5rem',
          alignItems: 'center',
        }}>
          <Link to="/" className="cta-button" style={{ textDecoration: 'none', display: 'inline-block' }}>
            Go to Home
          </Link>
          <Link to="/data" style={{ color: '#6ec1e4', textDecoration: 'none' }}>
            Browse Disease Data →
          </Link>
        </div>
      </div>
    </div>
  );
}

export default NotFound;
