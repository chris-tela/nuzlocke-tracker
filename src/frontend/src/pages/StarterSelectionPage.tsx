/**
 * Starter Selection Page
 * Allows user to select and configure their starter Pokemon for a new game file
 */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useGameFile } from '../hooks/useGameFile';
import { useVersionStarters } from '../hooks/usePokemon';
import { useAddPokemon } from '../hooks/usePokemon';
import { getGameFile } from '../services/gameFileService';
import { Nature, Status } from '../types/enums';
import { PokemonTypeBadge } from '../components/PokemonTypeBadge';

export const StarterSelectionPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const gameFileId = parseInt(searchParams.get('gameFileId') || '0', 10);
  const { currentGameFile, setCurrentGameFile } = useGameFile();
  const [selectedStarter, setSelectedStarter] = useState<number | null>(null);
  const [nickname, setNickname] = useState('');
  const [gender, setGender] = useState<string>('');
  const [nature, setNature] = useState<string>('');
  const [ability, setAbility] = useState<string>('');
  const [levelInput, setLevelInput] = useState<string>('5');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingGameFile, setIsLoadingGameFile] = useState(true); // Start as true to show loading initially

  // Convert levelInput to number for validation and submission
  const level = parseInt(levelInput, 10) || 0;

  // Helper function to capitalize Pokemon names
  const capitalizePokemonName = (name: string): string => {
    return name
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join('-');
  };

  // Load game file if not already loaded or if it doesn't match the URL param
  useEffect(() => {
    if (!gameFileId || gameFileId === 0) {
      // Invalid gameFileId, redirect back
      navigate('/game-files');
      return;
    }

    // If we don't have a game file, or if the current one doesn't match the URL param
    if (!currentGameFile || currentGameFile.id !== gameFileId) {
      setIsLoadingGameFile(true);
      const loadGameFile = async () => {
        try {
          const gameFile = await getGameFile(gameFileId);
          setCurrentGameFile(gameFile);
        } catch (error) {
          console.error('Failed to load game file:', error);
          setError('Failed to load game file. Please try again.');
          // Don't navigate immediately, let user see the error
        } finally {
          setIsLoadingGameFile(false);
        }
      };
      loadGameFile();
    } else {
      // Game file is already loaded and matches
      setIsLoadingGameFile(false);
    }
  }, [gameFileId, currentGameFile, setCurrentGameFile, navigate]);

  const gameName = currentGameFile?.game_name || '';
  const { data: starters = [], isLoading: isLoadingStarters } = useVersionStarters(gameName || null);
  const addPokemonMutation = useAddPokemon(gameFileId > 0 ? gameFileId : null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!selectedStarter) {
      setError('Please select a starter Pokemon');
      return;
    }

    if (!gameFileId) {
      setError('Game file ID is missing');
      return;
    }

    setIsSubmitting(true);
    try {
      await addPokemonMutation.mutateAsync({
        poke_id: selectedStarter,
        nickname: nickname.trim() || null,
        nature: nature || null,
        ability: ability || null,
        level: level,
        gender: gender || null,
        status: Status.PARTY,
      });

      // Navigate to dashboard after successful starter selection (per Phase 4.3)
      navigate(`/dashboard?gameFileId=${gameFileId}`, { replace: true });
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to add starter Pokemon');
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedStarterData = starters.find((s) => s.poke_id === selectedStarter);

  // Show loading state while game file is being loaded
  if (!gameFileId || gameFileId === 0) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg-light)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}>
        <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
          <p style={{ color: 'var(--color-text-secondary)' }}>Invalid game file</p>
          <button
            onClick={() => navigate('/game-files')}
            className="btn btn-primary"
            style={{ marginTop: '20px' }}
          >
            Back to Game Files
          </button>
        </div>
      </div>
    );
  }

  if (isLoadingGameFile || !currentGameFile || !gameName) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg-light)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}>
        <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            {isLoadingGameFile ? 'Loading game file...' : 'Loading game information...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-bg-light)',
      padding: '40px 20px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '24px',
    }}>
      <div className="card" style={{
        maxWidth: '800px',
        width: '100%',
        padding: '40px',
      }}>
        <h1 style={{
          color: 'var(--color-text-primary)',
          fontSize: '2rem',
          marginBottom: '8px',
          textAlign: 'center',
        }}>
          Choose Your Starter
        </h1>
        <p style={{
          color: 'var(--color-text-secondary)',
          textAlign: 'center',
          marginBottom: '32px',
        }}>
          Select your starter Pokemon to begin your Nuzlocke journey!
        </p>

        {error && (
          <div style={{
            marginBottom: '20px',
            padding: '12px',
            backgroundColor: '#FEE2E2',
            border: '2px solid #F87171',
            borderRadius: '8px',
            color: '#991B1B',
            fontSize: '14px',
            textAlign: 'center',
          }}>
            {error}
            <button
              onClick={() => navigate('/game-files')}
              className="btn btn-primary"
              style={{ marginTop: '12px', display: 'block', margin: '12px auto 0' }}
            >
              Back to Game Files
            </button>
          </div>
        )}

        {isLoadingStarters || !gameName ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              {!gameName ? 'Loading game information...' : 'Loading starters...'}
            </p>
          </div>
        ) : starters.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              No starters available for this game version.
            </p>
            <button
              onClick={() => navigate('/game-files')}
              className="btn btn-primary"
              style={{ marginTop: '20px' }}
            >
              Back to Game Files
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            {/* Starter Selection */}
            <div style={{ marginBottom: '32px' }}>
              <label style={{
                display: 'block',
                marginBottom: '16px',
                fontSize: '16px',
                fontWeight: '600',
                color: 'var(--color-text-primary)',
              }}>
                Select Starter Pokemon
              </label>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '20px',
              }}>
                {starters.map((starter) => (
                  <div
                    key={starter.poke_id}
                    onClick={() => setSelectedStarter(starter.poke_id)}
                    style={{
                      padding: '20px',
                      border: selectedStarter === starter.poke_id
                        ? '3px solid var(--color-pokemon-blue)'
                        : '2px solid var(--color-border)',
                      borderRadius: '12px',
                      backgroundColor: selectedStarter === starter.poke_id
                        ? 'var(--color-bg-light)'
                        : 'var(--color-bg-card)',
                      cursor: 'pointer',
                      transition: 'all 150ms ease',
                      textAlign: 'center',
                    }}
                  >
                    <img
                      src={starter.sprite}
                      alt={starter.name}
                      style={{
                        width: '120px',
                        height: '120px',
                        objectFit: 'contain',
                        marginBottom: '12px',
                        imageRendering: 'pixelated',
                      }}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                    <div style={{
                      fontSize: '18px',
                      fontWeight: '600',
                      color: 'var(--color-text-primary)',
                      marginBottom: '8px',
                    }}>
                      {capitalizePokemonName(starter.name)}
                    </div>
                    {starter.types && starter.types.length > 0 && (
                      <div style={{
                        display: 'flex',
                        gap: '8px',
                        justifyContent: 'center',
                        flexWrap: 'wrap',
                      }}>
                        {starter.types.map((type) => (
                          <PokemonTypeBadge key={type} type={type} />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Starter Configuration Form */}
            {selectedStarterData && (
              <div style={{
                borderTop: '2px solid var(--color-border)',
                paddingTop: '32px',
                marginTop: '32px',
              }}>
                <h2 style={{
                  color: 'var(--color-text-primary)',
                  fontSize: '1.5rem',
                  marginBottom: '24px',
                }}>
                  Configure Your Starter
                </h2>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                  gap: '20px',
                  marginBottom: '24px',
                }}>
                  {/* Nickname */}
                  <div>
                    <label
                      htmlFor="nickname"
                      style={{
                        display: 'block',
                        marginBottom: '8px',
                        fontSize: '14px',
                        fontWeight: '600',
                        color: 'var(--color-text-primary)',
                      }}
                    >
                      Nickname (optional)
                    </label>
                    <input
                      id="nickname"
                      type="text"
                      value={nickname}
                      onChange={(e) => setNickname(e.target.value)}
                      className="input"
                      placeholder="Enter nickname"
                      style={{ width: '100%', boxSizing: 'border-box' }}
                    />
                  </div>

                  {/* Level */}
                  <div>
                    <label
                      htmlFor="level"
                      style={{
                        display: 'block',
                        marginBottom: '8px',
                        fontSize: '14px',
                        fontWeight: '600',
                        color: 'var(--color-text-primary)',
                      }}
                    >
                      Level
                    </label>
                    <input
                      id="level"
                      type="number"
                      value={levelInput}
                      onChange={(e) => {
                        const inputValue = e.target.value;
                        // Allow empty input while typing (for deletion)
                        setLevelInput(inputValue);
                      }}
                      onBlur={(e) => {
                        // Ensure value is within range when input loses focus
                        const inputValue = e.target.value;
                        if (inputValue === '' || inputValue === '0') {
                          setLevelInput('5'); // Default to 5 if empty
                        } else {
                          const numValue = parseInt(inputValue, 10);
                          if (isNaN(numValue) || numValue < 1) {
                            setLevelInput('1');
                          } else if (numValue > 100) {
                            setLevelInput('100');
                          } else {
                            setLevelInput(numValue.toString());
                          }
                        }
                      }}
                      className="input"
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        borderColor: (level < 1 || level > 100) && levelInput !== '' ? '#F87171' : undefined,
                        borderWidth: (level < 1 || level > 100) && levelInput !== '' ? '2px' : undefined,
                      }}
                    />
                    {(level < 1 || level > 100) && levelInput !== '' && (
                      <p style={{
                        marginTop: '4px',
                        fontSize: '12px',
                        color: '#F87171',
                      }}>
                        Level must be between 1 and 100
                      </p>
                    )}
                  </div>

                  {/* Gender */}
                  <div>
                    <label
                      htmlFor="gender"
                      style={{
                        display: 'block',
                        marginBottom: '8px',
                        fontSize: '14px',
                        fontWeight: '600',
                        color: 'var(--color-text-primary)',
                      }}
                    >
                      Gender (optional)
                    </label>
                    <select
                      id="gender"
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                      className="input"
                      style={{ width: '100%', boxSizing: 'border-box' }}
                    >
                      <option value="">None</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                    </select>
                  </div>

                  {/* Nature */}
                  <div>
                    <label
                      htmlFor="nature"
                      style={{
                        display: 'block',
                        marginBottom: '8px',
                        fontSize: '14px',
                        fontWeight: '600',
                        color: 'var(--color-text-primary)',
                      }}
                    >
                      Nature (optional)
                    </label>
                    <select
                      id="nature"
                      value={nature}
                      onChange={(e) => setNature(e.target.value)}
                      className="input"
                      style={{ width: '100%', boxSizing: 'border-box' }}
                    >
                      <option value="">None</option>
                      {Object.values(Nature).map((natureValue) => (
                        <option key={natureValue} value={natureValue}>
                          {natureValue}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Ability */}
                  <div>
                    <label
                      htmlFor="ability"
                      style={{
                        display: 'block',
                        marginBottom: '8px',
                        fontSize: '14px',
                        fontWeight: '600',
                        color: 'var(--color-text-primary)',
                      }}
                    >
                      Ability (optional)
                    </label>
                    <select
                      id="ability"
                      value={ability}
                      onChange={(e) => setAbility(e.target.value)}
                      className="input"
                      style={{ width: '100%', boxSizing: 'border-box' }}
                    >
                      <option value="">Select ability...</option>
                      {selectedStarterData.abilities.map((abil) => (
                        <option key={abil} value={abil}>
                          {abil}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {error && (
                  <div style={{
                    marginBottom: '20px',
                    padding: '12px',
                    backgroundColor: '#FEE2E2',
                    border: '2px solid #F87171',
                    borderRadius: '8px',
                    color: '#991B1B',
                    fontSize: '14px',
                  }}>
                    {error}
                  </div>
                )}

                <div style={{
                  display: 'flex',
                  gap: '12px',
                  justifyContent: 'center',
                }}>
                  <button
                    type="button"
                    onClick={() => navigate('/game-files')}
                    className="btn btn-outline"
                    style={{ flex: 1, maxWidth: '200px' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="btn btn-primary"
                    style={{ flex: 1, maxWidth: '200px' }}
                  >
                    {isSubmitting ? 'Adding Starter...' : 'Start Journey'}
                  </button>
                </div>
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  );
};

