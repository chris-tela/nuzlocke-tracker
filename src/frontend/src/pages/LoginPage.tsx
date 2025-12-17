/**
 * Login Page
 * Pokemon-style login page with OAuth and JWT login options
 */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { OAuthLogin } from '../components/OAuthLogin';
import { getErrorMessage } from '../utils/errorHandler';

export const LoginPage = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { login, register, isAuthenticated, isLoading } = useAuth();
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Check for error query parameter (from OAuth callback)
  useEffect(() => {
    const errorParam = searchParams.get('error');
    if (errorParam) {
      const errorMessage = decodeURIComponent(errorParam);
      setError(errorMessage);
      
      // If error is about account not found, switch to register mode
      if (errorMessage.includes('Account not found') || errorMessage.includes('Please use Register')) {
        setIsRegisterMode(true);
      }
      
      // Clear the error from URL
      setSearchParams((prev) => {
        prev.delete('error');
        return prev;
      }, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  // Redirect if already authenticated (but only if not coming from logout)
  useEffect(() => {
    if (!isLoading && isAuthenticated && !window.location.search.includes('logout')) {
      navigate('/game-files', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (isRegisterMode) {
        await register(username, password);
      } else {
        await login(username, password);
      }
      // Navigation will happen via useEffect when isAuthenticated changes
      navigate('/game-files');
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg-light)'
      }}>
        <div style={{ fontSize: '18px', color: 'var(--color-text-secondary)' }}>
          Loading...
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-bg-light)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
    }}>
      <div className="card" style={{
        maxWidth: '450px',
        width: '100%',
        minWidth: '320px',
        padding: '40px',
        textAlign: 'center',
        boxSizing: 'border-box',
      }}>
        {/* Pokemon Logo/Title */}
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: '700',
            color: 'var(--color-pokemon-red)',
            marginBottom: '8px',
            textShadow: '2px 2px 4px rgba(0,0,0,0.1)',
          }}>
            Nuzlocke Tracker
          </h1>
          <p style={{
            color: 'var(--color-text-secondary)',
            fontSize: '16px',
            margin: 0,
          }}>
            Track your Pokemon journey
          </p>
        </div>

        {/* Mode Toggle */}
        <div style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '32px',
          backgroundColor: 'var(--color-bg-light)',
          padding: '4px',
          borderRadius: '8px',
        }}>
          <button
            type="button"
            onClick={() => {
              setIsRegisterMode(false);
              setError(null);
            }}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              borderRadius: '6px',
              backgroundColor: isRegisterMode ? 'transparent' : 'var(--color-bg-card)',
              color: isRegisterMode ? 'var(--color-text-secondary)' : 'var(--color-pokemon-red)',
              fontWeight: isRegisterMode ? '400' : '600',
              cursor: 'pointer',
              transition: 'all 150ms ease',
              boxShadow: isRegisterMode ? 'none' : 'var(--shadow-sm)',
            }}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => {
              setIsRegisterMode(true);
              setError(null);
            }}
            style={{
              flex: 1,
              padding: '10px',
              border: 'none',
              borderRadius: '6px',
              backgroundColor: isRegisterMode ? 'var(--color-bg-card)' : 'transparent',
              color: isRegisterMode ? 'var(--color-pokemon-red)' : 'var(--color-text-secondary)',
              fontWeight: isRegisterMode ? '600' : '400',
              cursor: 'pointer',
              transition: 'all 150ms ease',
              boxShadow: isRegisterMode ? 'var(--shadow-sm)' : 'none',
            }}
          >
            Register
          </button>
        </div>

        {/* OAuth Login Section */}
        <OAuthLogin mode={isRegisterMode ? 'register' : 'login'} />

        {/* Divider */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          margin: '32px 0',
          color: 'var(--color-text-secondary)',
        }}>
          <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--color-border)' }} />
          <span style={{ padding: '0 16px', fontSize: '14px' }}>OR</span>
          <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--color-border)' }} />
        </div>

        {/* JWT Login Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px', textAlign: 'left' }}>
            <label
              htmlFor="username"
              style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '600',
                color: 'var(--color-text-primary)',
              }}
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="input"
              placeholder="Enter your username"
              style={{ 
                width: '100%',
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ marginBottom: '24px', textAlign: 'left' }}>
            <label
              htmlFor="password"
              style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '600',
                color: 'var(--color-text-primary)',
              }}
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="input"
              placeholder="Enter your password"
              style={{ 
                width: '100%',
                boxSizing: 'border-box',
              }}
              minLength={6}
            />
          </div>

          {error && (
            <div
              style={{
                marginBottom: '20px',
                padding: '12px',
                backgroundColor: '#FEE2E2',
                border: '2px solid #F87171',
                borderRadius: '8px',
                color: '#991B1B',
                fontSize: '14px',
                textAlign: 'left',
                wordWrap: 'break-word',
                overflowWrap: 'break-word',
                maxWidth: '100%',
                boxSizing: 'border-box',
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn btn-primary"
            style={{
              width: '100%',
              fontSize: '16px',
              padding: '14px 24px',
            }}
          >
            {isSubmitting
              ? 'Loading...'
              : isRegisterMode
              ? 'Create Account'
              : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

