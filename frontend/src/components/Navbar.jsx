import { Link, useLocation } from 'react-router-dom';

/**
 * Navbar Component
 * Provides navigation between pages in the Fluence application
 * Reusable across all pages
 */
function Navbar() {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? 'nav-link active' : 'nav-link';
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
          <Link to="/" className={isActive('/')}>
            Home
          </Link>
        </li>
        <li>
          <Link to="/data" className={isActive('/data')}>
            Disease Data
          </Link>
        </li>
        <li>
          <Link to="/map" className={isActive('/map')}>
            Map
          </Link>
        </li>
        <li>
          <Link to="/submit" className={isActive('/submit')}>
            Submit Case
          </Link>
        </li>
        <li>
          <Link to="/login" className={isActive('/login')}>
            Login
          </Link>
        </li>
        <li>
          <Link to="/signup" className={isActive('/signup')}>
            Sign Up
          </Link>
        </li>
      </ul>
    </nav>
  );
}

export default Navbar;
