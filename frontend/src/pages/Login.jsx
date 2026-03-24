import { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { supabase } from '../supabaseClient';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.state && location.state.info) {
      setError('');
      setInfo(location.state.info);
    }
  }, [location]);

  const [info, setInfo] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // 1. Authenticate against Supabase Auth
    const { data, error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    if (signInError) {
      setError(signInError.message);
      return;
    }

    // 2. Update last_login in your users table
    const { error: updateError } = await supabase
      .from('users')
      .update({ last_login: new Date().toISOString() })
      .eq('user_id', data.user.id);

    if (updateError) {
      console.error('Could not update last_login:', updateError.message);
      // Non-fatal, don't block navigation
    }

    // If email is not verified, show clear guidance instead of navigating silently
    const emailConfirmed = data.user?.email_confirmed_at || data.user?.user_metadata?.email_confirmed_at;
    if (!emailConfirmed) {
      setInfo('Your email address is not verified. Please check your inbox for a verification email.');
      return;
    }

    navigate('/');
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>Log In</h2>
        <p className="muted">Enter your credentials to access the dashboard.</p>
        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              required placeholder="you@domain.com" />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              required placeholder="••••••••" />
          </label>
            {error && <div className="form-error">{error}</div>}
            {info && <div className="form-info">{info}</div>}
          <button type="submit" className="cta-button login-btn">Sign In</button>
        </form>
          <p style={{ marginTop: '1rem', fontSize: '0.95rem' }}>
            Don't have an account? <Link to="/signup">Create one</Link>
          </p>
          <p style={{ marginTop: '0.25rem', fontSize: '0.95rem' }}>
            <Link to="/forgot-password">Forgot password?</Link>
          </p>
      </div>
    </div>
  );
}

export default Login;