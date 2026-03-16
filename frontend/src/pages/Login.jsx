import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '../supabaseClient';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

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
          <button type="submit" className="cta-button login-btn">Sign In</button>
        </form>
        <p style={{ marginTop: '1rem', fontSize: '0.95rem' }}>
          Don't have an account? <Link to="/signup">Create one</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;