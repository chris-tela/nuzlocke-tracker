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
  const [level, setLevel] = useState<number>(5);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load game file if not already loaded
  useEffect(() => {
    if (gameFileId && !currentGameFile) {
      const loadGameFile = async () => {
        try {
          const gameFile = await getGameFile(gameFileId);
          setCurrentGameFile(gameFile);
        } catch (error) {
          console.error('Failed to load game file:', error);
          navigate('/game-files');
        }
      };
      loadGameFile();
    }
  }, [gameFileId, currentGameFile, setCurrentGameFile, navigate]);

  const gameName = currentGameFile?.game_name || '';
  const { data: starters = [], isLoading: isLoadingStarters } = useVersionStarters(gameName);
  const addPokemonMutation = useAddPokemon(gameFileId || null);

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
        status: 'PARTY',
      });

      // Navigate to game files page after successful starter selection
      navigate('/game-files');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to add starter Pokemon');
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedStarterData = starters.find((s) => s.poke_id === selectedStarter);

  if (!gameFileId) {
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

        {isLoadingStarters ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <p style={{ color: 'var(--color-text-secondary)' }}>Loading starters...</p>
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
                      {starter.name}
                    </div>
                    <div style={{
                      display: 'flex',
                      gap: '8px',
                      justifyContent: 'center',
                      flexWrap: 'wrap',
                    }}>
                      {starter.types.map((type) => (
                        <span
                          key={type}
                          style={{
                            padding: '4px 8px',
                            backgroundColor: 'var(--color-pokemon-blue)',
                            color: 'var(--color-text-white)',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: '600',
                          }}
                        >
                          {type}
                        </span>
                      ))}
                    </div>
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
                      value={level}
                      onChange={(e) => setLevel(parseInt(e.target.value, 10) || 5)}
                      min={1}
                      max={100}
                      className="input"
                      style={{ width: '100%', boxSizing: 'border-box' }}
                    />
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
                    <input
                      id="nature"
                      type="text"
                      value={nature}
                      onChange={(e) => setNature(e.target.value)}
                      className="input"
                      placeholder="e.g., Adamant"
                      style={{ width: '100%', boxSizing: 'border-box' }}
                    />
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

