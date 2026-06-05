import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';

function ResetPassword() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'PASSWORD_RECOVERY') {
        setInfo('Link accepted. Please enter a new password below.');
        setLoading(false);
      } else if (event === 'SIGNED_IN' && session) {
        setInfo('Link accepted. Please enter a new password below.');
        setLoading(false);
      }
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setInfo('Link accepted. Please enter a new password below.');
        setLoading(false);
      }
    });

    const timer = setTimeout(() => {
      setLoading((prev) => {
        if (prev) {
          setError('No valid recovery tokens found. The link may be invalid or expired.');
          return false;
        }
        return prev;
      });
    }, 6000);

    return () => {
      subscription.unsubscribe();
      clearTimeout(timer);
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setInfo('');
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const { error: updateError } = await supabase.auth.updateUser({ password });
      if (updateError) {
        setError(updateError.message || 'Could not update password');
        setLoading(false);
        return;
      }
      setInfo('Password updated. You are now signed in. Redirecting...');
      setTimeout(() => navigate('/'), 1500);
    } catch (err) {
      setError(err.message || 'Unexpected error updating password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>Set New Password</h2>
        {loading && <p className="muted">Processing reset link...</p>}
        {!loading && (
          <>
            {error && <div className="form-error">{error}</div>}
            {info && <div className="form-info">{info}</div>}
            <form onSubmit={handleSubmit} className="login-form">
              <label>
                New password
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="New password" />
              </label>
              <label>
                Confirm password
                <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required placeholder="Repeat password" />
              </label>
              <button type="submit" className="cta-button login-btn">Set password</button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

export default ResetPassword;