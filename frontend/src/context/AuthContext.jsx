import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';

/**
 * AuthContext
 * TM20-89: Added role and isVerifiedOfficial state for health-official feature gating.
 * After login, checks the official_verifications table to determine if the user
 * has been verified as a health official. This status is used by ProtectedRoute
 * and CaseSubmission to gate access to health-official features.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const AuthContext = createContext({});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [role, setRole] = useState('user');
  const [isVerifiedOfficial, setIsVerifiedOfficial] = useState(false);

  /**
   * Check verification status for a given user email.
   * Queries the backend to see if this user has a verified official record.
   */
  const checkVerificationStatus = async (email) => {
    if (!email) {
      setRole('user');
      setIsVerifiedOfficial(false);
      return;
    }

    try {
      const res = await fetch(
        `${API_BASE}/api/auth/verify-official/status?email=${encodeURIComponent(email)}`
      );
      if (res.ok) {
        const data = await res.json();
        const status = data?.data?.verification_status;
        if (status === 'verified') {
          setRole('health_official');
          setIsVerifiedOfficial(true);
        } else if (status === 'pending') {
          setRole('pending_official');
          setIsVerifiedOfficial(false);
        } else {
          setRole('user');
          setIsVerifiedOfficial(false);
        }
      } else {
        // Endpoint may not exist yet or user has no verification record
        setRole('user');
        setIsVerifiedOfficial(false);
      }
    } catch {
      // Network error — default to basic user role
      setRole('user');
      setIsVerifiedOfficial(false);
    }
  };

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      const currentUser = session?.user ?? null;
      setUser(currentUser);
      setLoading(false);
      if (currentUser?.email) {
        checkVerificationStatus(currentUser.email);
      }
    });

    // Listen for login/logout events
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      const currentUser = session?.user ?? null;
      setUser(currentUser);
      if (currentUser?.email) {
        checkVerificationStatus(currentUser.email);
      } else {
        setRole('user');
        setIsVerifiedOfficial(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const logout = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setRole('user');
    setIsVerifiedOfficial(false);
  };

  return (
    <AuthContext.Provider value={{ user, loading, logout, role, isVerifiedOfficial }}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

// Custom hook for easy access anywhere
export const useAuth = () => useContext(AuthContext);