import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const isActive = (path) => {
    return location.pathname === path ? 'nav-link active' : 'nav-link';
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/">
          <h1>Fluence</h1>
        </Link>
      </div>
      <ul className="nav-links">
        <li>
          <Link to="/" className={isActive('/')}>Home</Link>
        </li>
        <li>
          <Link to="/data" className={isActive('/data')}>Disease Data</Link>
        </li>
        <li>
          <Link to="/map" className={isActive('/map')}>Map</Link>
        </li>
        <li>
          <Link to="/submit" className={isActive('/submit')}>Submit Case</Link>
        </li>
        <li>
          <Link to="/verify" className={isActive('/verify')}>Verify Official</Link>
        </li>

        {user ? (
          <>
            <li className="nav-email nav-link">{user.email}</li>
            <li>
              <button onClick={handleLogout} className="nav-link nav-logout">
                Log Out
              </button>
            </li>
          </>
        ) : (
          <>
            <li>
              <Link to="/login" className={isActive('/login')}>Login</Link>
            </li>
            <li>
              <Link to="/signup" className={isActive('/signup')}>Sign Up</Link>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
}

export default Navbar;