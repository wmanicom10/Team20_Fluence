import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '../supabaseClient';

function Signup() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirm) {
      setError('Passwords do not match');
      return;
    }

    // 1. Create auth user
    const { data, error: signUpError } = await supabase.auth.signUp({ email, password });
    if (signUpError) {
      setError(signUpError.message);
      return;
    }

    // 2. Insert into your users table
    const { error: insertError } = await supabase.from('users').insert({
      user_id: data.user.id,
      email: email,
      role: 'public',
      verified: false,
      created_at: new Date().toISOString(),
      last_login: new Date().toISOString(),
    });

    // Only block if it's NOT an RLS read-back error
    if (insertError && insertError.code !== '42501') {
      setError(insertError.message);
      return;
    }

    navigate('/');

  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>Sign Up</h2>
        <p className="muted">Start tracking disease data with a Fluence account.</p>
        <form onSubmit={handleSubmit} className="login-form">
          <label>
            Full name
            <input type="text" value={name} onChange={(e) => setName(e.target.value)}
              required placeholder="Jane Doe" />
          </label>
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              required placeholder="you@domain.com" />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              required placeholder="Create a password" />
          </label>
          <label>
            Confirm password
            <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
              required placeholder="Repeat password" />
          </label>
          {error && <div className="form-error">{error}</div>}
          <button type="submit" className="cta-button login-btn">Create account</button>
        </form>
        <p style={{ marginTop: '1rem', fontSize: '0.95rem' }}>
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}

export default Signup;