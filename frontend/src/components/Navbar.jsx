import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Navbar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const isResettingPassword = location.pathname === '/reset-password' || 
                              location.pathname === '/forgot-password' || 
                              location.pathname === '/verify-email';

  const isActive = (path) => {
    return location.pathname === path ? 'nav-link active' : 'nav-link';
  };

  const handleLogout = async () => {
    closeMenu();
    await logout();
    navigate('/login');
  };

  const toggleMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);
  const closeMenu = () => setIsMobileMenuOpen(false);

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/" onClick={closeMenu}>
          <h1>Fluence</h1>
        </Link>
      </div>
      
      <button className="mobile-menu-btn" onClick={toggleMenu} aria-label="Toggle navigation">
        {isMobileMenuOpen ? '✕' : '☰'}
      </button>

      <ul className={`nav-links ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
        <li>
          <Link to="/" className={isActive('/')} onClick={closeMenu}>Home</Link>
        </li>
        <li>
          <Link to="/data" className={isActive('/data')} onClick={closeMenu}>Disease Data</Link>
        </li>
        <li>
          <Link to="/map" className={isActive('/map')} onClick={closeMenu}>Map</Link>
        </li>
        <li>
          <Link to="/submit" className={isActive('/submit')} onClick={closeMenu}>Submit Case</Link>
        </li>
        <li>
          <Link to="/verify" className={isActive('/verify')} onClick={closeMenu}>Verify Official</Link>
        </li>
        {user && !isResettingPassword ? (
          <>
            <li className="nav-email nav-link">{user.email}</li>
            <li>
              <button onClick={handleLogout} className="nav-link nav-logout">
                Log Out
              </button>
            </li>
          </>
        ) : !isResettingPassword && (
          <>
            <li>
              <Link to="/login" className={isActive('/login')} onClick={closeMenu}>Login</Link>
            </li>
            <li>
              <Link to="/signup" className={isActive('/signup')} onClick={closeMenu}>Sign Up</Link>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
}

export default Navbar;