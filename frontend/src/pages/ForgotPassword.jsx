import { useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../supabaseClient';

function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setInfo('');
    setLoading(true);

    try {
      await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/reset-password'
      });
      setInfo('If an account with that email exists, a password reset link has been sent. Check your spam folder if you don\'t see it.');
      setSent(true);
    } catch (err) {
      setError(err.message || 'Could not request password reset');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setInfo('');
    setLoading(true);
    try {
      await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/reset-password'
      });
      setInfo('Reset email resent. Check your spam folder if you don\'t see it.');
    } catch (err) {
      setError(err.message || 'Could not resend reset email');
    } finally {
      setLoading(false);
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
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@domain.com" disabled={sent} />
          </label>
          {error && <div className="form-error">{error}</div>}
          {info && <div className="form-info">{info}</div>}
          {!sent && (
            <button type="submit" className="cta-button login-btn" disabled={loading}>
              {loading ? 'Sending...' : 'Send reset email'}
            </button>
          )}
        </form>
        {sent && (
          <button onClick={handleResend} className="cta-button login-btn" disabled={loading} style={{ marginTop: '0.75rem' }}>
            {loading ? 'Resending...' : 'Resend email'}
          </button>
        )}
        <p style={{ marginTop: '1rem', fontSize: '0.95rem' }}>
          Remembered your password? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

export default ForgotPassword;