import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';

function VerifyEmail() {
  const [message, setMessage] = useState('Verifying your email...');
  const [error, setError] = useState('');
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
        }
    });

    return () => subscription.unsubscribe();
    }, []);

  return (
    <div className="login-page">
      <div className="login-card">
        <h2>Email Verification</h2>
        {error ? (
          <div className="form-error">{error}</div>
        ) : (
          <p className="muted">{message}</p>
        )}
      </div>
    </div>
  );
}

export default VerifyEmail;