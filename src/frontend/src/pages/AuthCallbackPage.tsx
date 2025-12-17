/**
 * OAuth Callback Page
 * Handles OAuth redirects and token extraction
 */
import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export const AuthCallbackPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { refreshUser, isAuthenticated } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const token = searchParams.get('token');
      const error = searchParams.get('error');

      if (error) {
        // Handle OAuth error - error is already URL encoded
        navigate('/login?error=' + encodeURIComponent(error));
        return;
      }

      if (token) {
        // Token is already handled by AuthContext's useEffect
        // Just refresh user and navigate
        try {
          await refreshUser();
          // Small delay to ensure state is updated
          setTimeout(() => {
            navigate('/game-files');
          }, 100);
        } catch (err) {
          console.error('Failed to refresh user after OAuth:', err);
          navigate('/login?error=authentication_failed');
        }
      } else {
        // No token, redirect to login
        navigate('/login');
      }
    };

    handleCallback();
  }, [searchParams, navigate, refreshUser]);

  // Show loading state while processing
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: 'var(--color-bg-light)',
      flexDirection: 'column',
      gap: '20px',
    }}>
      <div style={{
        fontSize: '18px',
        color: 'var(--color-text-secondary)',
        fontWeight: '600',
      }}>
        Completing authentication...
      </div>
      <div style={{
        width: '40px',
        height: '40px',
        border: '4px solid #E5E7EB',
        borderTop: '4px solid var(--color-pokemon-red)',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
      }} />
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

