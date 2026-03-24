import { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { supabase } from '../supabaseClient';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.state?.info) {
      setInfo(location.state.info);
    }
  }, [location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setInfo('');
    setLoading(true);

    try {
      const { data, error: signInError } = await supabase.auth.signInWithPassword({ email, password });

      if (signInError) {
        setPassword(''); // Clear password on failure
        if (signInError.message.toLowerCase().includes('invalid login credentials')) {
          setError('Incorrect email or password. Please try again.');
        } else if (signInError.message.toLowerCase().includes('email not confirmed')) {
          setError('Your email is not verified. Please check your inbox or request a new verification email.');
        } else {
          setError(signInError.message);
        }
        return;
      }

      const emailConfirmed = data.user?.email_confirmed_at || data.user?.user_metadata?.email_confirmed_at;
      if (!emailConfirmed) {
        setPassword('');
        setInfo('Your email address is not verified. Please check your inbox for a verification email.');
        return;
      }

      await supabase
        .from('users')
        .update({ last_login: new Date().toISOString() })
        .eq('user_id', data.user.id);

      navigate('/');
    } catch (err) {
      setError(err.message || 'Unexpected error signing in');
      setPassword('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>Log In</h2>
        <p className="muted">Enter your credentials to access the dashboard.</p>
        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@domain.com" />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="••••••••" />
          </label>
          {error && <div className="form-error">{error}</div>}
          {info && <div className="form-info">{info}</div>}
          <button type="submit" className="cta-button login-btn" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
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