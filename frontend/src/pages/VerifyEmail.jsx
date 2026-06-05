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
    let isActive = true;

    const finishSuccess = async () => {
      await supabase.auth.signOut();
      if (!isActive) {
        return;
      }
      setError('');
      setMessage('Email verified! Redirecting to login...');
      setTimeout(
        () =>
          navigate('/login', {
            state: { info: 'Email verified! You can now sign in.' },
          }),
        1500
      );
    };

    const verifyEmailLink = async () => {
      const url = new URL(window.location.href);
      const query = url.searchParams;
      const hash = new URLSearchParams(url.hash.startsWith('#') ? url.hash.slice(1) : url.hash);

      const code = query.get('code');
      const tokenHash = query.get('token_hash') || hash.get('token_hash');
      const type = query.get('type') || hash.get('type');
      const accessToken = hash.get('access_token');
      const refreshToken = hash.get('refresh_token');

      try {
        if (code) {
          const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
          if (exchangeError) {
            throw exchangeError;
          }
          await finishSuccess();
          return;
        }

        if (tokenHash && type) {
          const { error: verifyError } = await supabase.auth.verifyOtp({
            token_hash: tokenHash,
            type,
          });
          if (verifyError) {
            throw verifyError;
          }
          await finishSuccess();
          return;
        }

        if (accessToken && refreshToken) {
          const { error: sessionError } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken,
          });
          if (sessionError) {
            throw sessionError;
          }
          await finishSuccess();
          return;
        }

        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (session) {
          await finishSuccess();
          return;
        }

        if (isActive) {
          setError('This verification link is invalid or has expired.');
          setMessage('');
        }
      } catch (err) {
        if (isActive) {
          setError(err.message || 'This verification link is invalid or has expired.');
          setMessage('');
        }
      }
    };

    verifyEmailLink();

    return () => {
      isActive = false;
    };
  }, [navigate]);

  const handleResend = async (e) => {
    e.preventDefault();
    setResendInfo('');
    setResendLoading(true);
    try {
      const { error: resendError } = await supabase.auth.resend({
        type: 'signup',
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/verify-email`,
        },
      });
      if (resendError) {
        throw resendError;
      }
      setResendInfo(
        'Verification email resent. It can take a few minutes to arrive, and Supabase may delay repeated sends.'
      );
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
            <p className="muted" style={{ marginTop: '1rem' }}>
              Enter your email to resend the verification link.
            </p>
            <form onSubmit={handleResend} className="login-form">
              <label>
                Email
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="you@domain.com"
                />
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
