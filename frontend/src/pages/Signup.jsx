import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Signup() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { simulateOfflineDemoLogin } = useAuth();
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';

  const passwordRequirements = [
    { label: 'At least 8 characters', met: password.length >= 8 },
    { label: 'Contains a number', met: /\d/.test(password) },
    { label: 'Contains an uppercase letter', met: /[A-Z]/.test(password) },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }
    if (!passwordRequirements.every((r) => r.met)) {
      setError('Password does not meet all requirements');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          email,
          password,
          emailRedirectTo: `${window.location.origin}/verify-email`,
        }),
      });
      const payload = await response.json().catch(() => ({}));

      if (!response.ok || payload?.status === 'error') {
        const message = payload?.error?.details || payload?.error?.message || 'Unexpected error creating account';
        if (message.toLowerCase().includes('fetch')) {
          simulateOfflineDemoLogin();
          navigate('/', { state: { info: 'Demo Mode: Offline Signup Successful! You are browsing locally as a simulated Verified Health Official.' } });
          return;
        } else if (message.toLowerCase().includes('rate limit')) {
          setError('Email rate limit exceeded. Wait a bit, then use the verification email already sent or try resending once the cooldown passes.');
        } else if (message.toLowerCase().includes('email rate limit exceeded')) {
          setError('Email rate limit exceeded. Wait a bit, then use the verification email already sent or try resending once the cooldown passes.');
        } else if (message.toLowerCase().includes('already registered')) {
          setError('An account with this email already exists. Try logging in instead.');
        } else {
          setError(message);
        }
        return;
      }

      navigate('/login', { state: { info: 'A verification email has been sent to your address. Please verify before signing in.' } });
    } catch (err) {
      setError(err.message || 'Unexpected error creating account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>Sign Up</h2>
        <p className="muted">Start tracking disease data with a Fluence account.</p>
        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Full name
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} required placeholder="Jane Doe" />
          </label>
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@domain.com" />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="Create a password" />
          </label>
          {password.length > 0 && (
            <ul className="password-requirements">
              {passwordRequirements.map((r) => (
                <li key={r.label} className={r.met ? 'req-met' : 'req-unmet'}>
                  {r.met ? '✓' : '✗'} {r.label}
                </li>
              ))}
            </ul>
          )}
          <label>
            Confirm password
            <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required placeholder="Repeat password" />
          </label>
          {error && <div className="form-error">{error}</div>}
          <button type="submit" className="cta-button login-btn" disabled={loading}>
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>
        <p style={{ marginTop: '1rem', fontSize: '0.95rem' }}>
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}

export default Signup;
