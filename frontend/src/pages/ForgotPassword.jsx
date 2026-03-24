import { useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../supabaseClient';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setInfo('');

    try {
      // Request a password reset email via Supabase
      await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/reset-password'
      });
      setInfo('If an account with that email exists, a password reset link has been sent.');
    } catch (err) {
      setError(err.message || 'Could not request password reset');
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>Reset Password</h2>
        <p className="muted">Enter your email and we'll send a password reset link.</p>
        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@domain.com" />
          </label>
          {error && <div className="form-error">{error}</div>}
          {info && <div className="form-info">{info}</div>}
          <button type="submit" className="cta-button login-btn">Send reset email</button>
        </form>
        <p style={{ marginTop: '1rem', fontSize: '0.95rem' }}>
          Remembered your password? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

export default ForgotPassword;
