import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '../supabaseClient';

function VerifyEmail() {
  const [message, setMessage] = useState('Verifying your email...');
  const [error, setError] = useState('');
  const [email, setEmail] = useState('');
  const [resendLoading, setResendLoading] = useState(false);
  const [resendInfo, setResendInfo] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') {
        supabase.auth.signOut();
        setMessage('Email verified! Redirecting to login...');
        setTimeout(() => navigate('/login', {
          state: { info: 'Email verified! You can now sign in.' }
        }), 1500);
      }
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        supabase.auth.signOut();
        setMessage('Email verified! Redirecting to login...');
        setTimeout(() => navigate('/login', {
          state: { info: 'Email verified! You can now sign in.' }
        }), 1500);
      } else {
        // No session means they navigated here directly or link expired
        setError('This verification link is invalid or has expired.');
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleResend = async (e) => {
    e.preventDefault();
    setResendInfo('');
    setResendLoading(true);
    try {
      await supabase.auth.resend({ type: 'signup', email });
      setResendInfo('Verification email resent. Check your spam folder if you don\'t see it.');
    } catch (err) {
      setResendInfo(err.message || 'Could not resend verification email');
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>Email Verification</h2>
        {error ? (
          <>
            <div className="form-error">{error}</div>
            <p className="muted" style={{ marginTop: '1rem' }}>Enter your email to resend the verification link.</p>
            <form onSubmit={handleResend} className="login-form">
              <label>
                Email
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@domain.com" />
              </label>
              {resendInfo && <div className="form-info">{resendInfo}</div>}
              <button type="submit" className="cta-button login-btn" disabled={resendLoading}>
                {resendLoading ? 'Sending...' : 'Resend verification email'}
              </button>
            </form>
            <p style={{ marginTop: '1rem', fontSize: '0.95rem' }}>
              <Link to="/login">Back to login</Link>
            </p>
          </>
        ) : (
          <p className="muted">{message}</p>
        )}
      </div>
    </div>
  );
}

export default VerifyEmail;