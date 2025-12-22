/**
 * Gyms Page
 * Track badges earned and preview upcoming gym battles
 */
import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameFile } from '../hooks/useGameFile';
import { useGymProgress, useUpcomingGyms, useAddGym, useVersionGyms } from '../hooks/useGyms';
import { PokemonTypeBadge } from '../components/PokemonTypeBadge';
import { usePokemonInfoByName } from '../hooks/usePokemon';
import { getPokemonSpritePath } from '../utils/pokemonSprites';

// Type for gym data from the API
interface GymData {
  gym_number: string;
  location: string;
  badge_name: string;
  trainer_name?: string;
  trainer_image?: string;
  badge_type?: string;
  pokemon?: any[];
}

// Component to display Pokemon sprite with loading state
const PokemonSprite = ({ pokemonName, size = 64 }: { pokemonName: string; size?: number }) => {
  const { data: pokemonInfo, isLoading } = usePokemonInfoByName(pokemonName.toLowerCase());

  if (isLoading) {
    return (
      <div
        style={{
          width: `${size}px`,
          height: `${size}px`,
          borderRadius: '8px',
          backgroundColor: 'var(--color-bg-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.7rem',
          color: 'var(--color-text-secondary)',
        }}
      >
        ...
      </div>
    );
  }

  if (!pokemonInfo?.name) {
    return (
      <div
        style={{
          width: `${size}px`,
          height: `${size}px`,
          borderRadius: '8px',
          backgroundColor: 'var(--color-bg-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.7rem',
          color: 'var(--color-text-secondary)',
        }}
      >
        ?
      </div>
    );
  }

  return (
    <div
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: '8px',
        backgroundColor: 'var(--color-bg-light)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      <img
        src={getPokemonSpritePath(pokemonInfo.name)}
        alt={pokemonName}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          imageRendering: 'pixelated',
        }}
        onError={(e) => {
          e.currentTarget.style.display = 'none';
        }}
      />
    </div>
  );
};

// Component to display Pokemon types
const PokemonTypes = ({ pokemonName }: { pokemonName: string }) => {
  const { data: pokemonInfo, isLoading } = usePokemonInfoByName(pokemonName.toLowerCase());

  if (isLoading || !pokemonInfo?.types || pokemonInfo.types.length === 0) {
    return null;
  }

  return (
    <>
      {pokemonInfo.types.map((type) => (
        <PokemonTypeBadge key={type} type={type} />
      ))}
    </>
  );
};

// Component for individual gym badge in timeline
const BadgeItem = ({
  gymNumber,
  badgeName,
  location,
  isCompleted,
  isSelected,
  onClick,
}: {
  gymNumber: string;
  badgeName: string;
  location: string;
  isCompleted: boolean;
  isSelected: boolean;
  onClick: () => void;
}) => {
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px',
        cursor: 'pointer',
        padding: '12px',
        borderRadius: '12px',
        border: isSelected 
          ? '2px solid var(--color-pokemon-primary)' 
          : isCompleted 
            ? '2px solid var(--color-pokemon-green)'
            : '1px solid var(--color-border)',
        backgroundColor: isSelected 
          ? 'var(--color-bg-light)' 
          : isCompleted 
            ? 'var(--color-bg-card)' 
            : 'var(--color-bg-light)',
        transition: 'all 150ms ease',
        minWidth: '100px',
        opacity: isCompleted || isSelected ? 1 : 0.6,
        filter: isCompleted ? 'none' : 'grayscale(100%)',
        boxShadow: isSelected ? '0 0 8px rgba(79, 70, 229, 0.5)' : 'none',
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.opacity = '1';
          if (!isCompleted) {
            e.currentTarget.style.borderColor = 'var(--color-pokemon-blue)';
          }
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          if (isCompleted) {
            e.currentTarget.style.borderColor = 'var(--color-pokemon-green)';
          } else {
            e.currentTarget.style.borderColor = 'var(--color-border)';
          }
          e.currentTarget.style.opacity = isCompleted ? '1' : '0.6';
        }
      }}
    >
      {/* Badge Icon Placeholder */}
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: isCompleted 
            ? 'var(--color-pokemon-green)' 
            : 'var(--color-bg-card)',
          border: `3px solid ${isCompleted ? 'var(--color-pokemon-green)' : 'var(--color-border)'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.5rem',
          fontWeight: 'bold',
          color: isCompleted ? 'var(--color-text-white)' : 'var(--color-text-secondary)',
        }}
      >
        {gymNumber}
      </div>
      <div
        style={{
          textAlign: 'center',
          fontSize: '0.75rem',
          color: isCompleted ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
          fontWeight: isSelected ? 600 : 400,
          lineHeight: '1.3',
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: '2px' }}>{badgeName}</div>
        <div style={{ fontSize: '0.7rem', opacity: 0.8 }}>{location}</div>
      </div>
    </div>
  );
};

export const GymsPage = () => {
  const navigate = useNavigate();
  const { currentGameFile } = useGameFile();
  const gameFileId = currentGameFile?.id ?? null;

  const { data: gymProgress = [], isLoading: isLoadingProgress } = useGymProgress(gameFileId);
  const { data: upcomingGymsResponse, isLoading: isLoadingUpcoming } = useUpcomingGyms(gameFileId);
  const gameName = currentGameFile?.game_name || null;
  const { data: versionGyms = [], isLoading: isLoadingVersionGyms } = useVersionGyms(gameName);
  const addGymMutation = useAddGym(gameFileId);

  // Extract upcoming gyms from response and normalize gym_number to string
  const upcomingGyms: GymData[] = (upcomingGymsResponse?.upcoming_gyms || []).map((gym: any) => ({
    ...gym,
    gym_number: String(gym.gym_number), // Normalize to string for consistency
  }));

  // Get all gyms (from version, merged with progress data) for display
  const allGyms: GymData[] = useMemo(() => {
    // Start with all version gyms (1-8) to ensure we have complete data
    const versionGymsData: GymData[] = (versionGyms as any[]).map((gym: any) => ({
      gym_number: String(gym.gym_number),
      location: gym.location || '',
      badge_name: gym.badge_name || '',
      trainer_name: gym.trainer_name,
      trainer_image: gym.trainer_image,
      badge_type: gym.badge_type,
      pokemon: gym.pokemon,
    }));

    // Create a map for quick lookup
    const gymsMap = new Map<string, GymData>();
    
    // Add all version gyms first (these have complete data)
    versionGymsData.forEach(gym => {
      gymsMap.set(gym.gym_number, gym);
    });

    // Override with upcoming gyms data if available (they might have updated info)
    upcomingGyms.forEach(gym => {
      if (gymsMap.has(gym.gym_number)) {
        // Merge data, keeping version gym data as base but updating with upcoming gym data
        const existing = gymsMap.get(gym.gym_number)!;
        gymsMap.set(gym.gym_number, { ...existing, ...gym });
      } else {
        gymsMap.set(gym.gym_number, gym);
      }
    });

    // Sort by gym number and return array
    return Array.from(gymsMap.values()).sort((a, b) => {
      const numA = parseInt(a.gym_number, 10);
      const numB = parseInt(b.gym_number, 10);
      return numA - numB;
    });
  }, [versionGyms, upcomingGyms]);

  // Find the next gym that can be marked as completed
  const nextGymToComplete = useMemo(() => {
    const completedCount = gymProgress.length;
    if (completedCount >= 8) return null;
    const nextGymNum = completedCount + 1;
    return upcomingGyms.find(gym => parseInt(gym.gym_number, 10) === nextGymNum) || null;
  }, [gymProgress, upcomingGyms]);

  const [selectedGymNumber, setSelectedGymNumber] = useState<string | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Select first upcoming gym by default, or first gym if none upcoming
  useEffect(() => {
    if (!selectedGymNumber && allGyms.length > 0) {
      const firstUpcoming = allGyms.find(gym => 
        !gymProgress.some((completed: any) => String(completed.gym_number) === gym.gym_number)
      ) || allGyms[0];
      setSelectedGymNumber(firstUpcoming.gym_number);
    }
  }, [allGyms, gymProgress, selectedGymNumber]);

  useEffect(() => {
    if (!currentGameFile) {
      navigate('/game-files');
    }
  }, [currentGameFile, navigate]);

  if (!currentGameFile || !gameFileId) {
    return null;
  }

  const isLoading = isLoadingProgress || isLoadingUpcoming || isLoadingVersionGyms;

  const selectedGym = allGyms.find(gym => gym.gym_number === selectedGymNumber);
  const isSelectedGymCompleted = selectedGym 
    ? gymProgress.some((gym: any) => String(gym.gym_number) === selectedGym.gym_number)
    : false;

  const handleMarkGymCompleted = async () => {
    if (!nextGymToComplete) {
      setError('No gym available to mark as completed');
      return;
    }

    try {
      setError(null);
      const completedGymNumber = parseInt(nextGymToComplete.gym_number, 10);
      await addGymMutation.mutateAsync(completedGymNumber);
      setShowConfirmModal(false);
      
      // Automatically select the next gym after completion
      // Since we know the gym numbers are sequential (1-8), we can calculate the next one
      const nextGymNum = completedGymNumber + 1;
      if (nextGymNum <= 8) {
        // Set the next gym number directly (it will be found in allGyms once queries refetch)
        setSelectedGymNumber(String(nextGymNum));
      } else {
        // All gyms completed, keep current selection
        setSelectedGymNumber(nextGymToComplete.gym_number);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to mark gym as completed');
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg-light)',
        padding: '40px 20px',
      }}
    >
      <div
        style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h1
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '1.8rem',
              margin: 0,
            }}
          >
            Gyms
          </h1>
          <button
            className="btn btn-outline"
            onClick={() => navigate(`/dashboard?gameFileId=${gameFileId}`)}
            style={{ fontSize: '0.9rem', padding: '8px 16px' }}
          >
            {'<-'} Back to Dashboard
          </button>
        </div>

        {/* Badge Timeline */}
        <div className="card" style={{ padding: '24px' }}>
          <h2
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '1.5rem',
              marginTop: 0,
              marginBottom: '20px',
              fontWeight: 600,
            }}
          >
            Badge Timeline
          </h2>
          {isLoading ? (
            <p style={{ color: 'var(--color-text-secondary)' }}>Loading gyms...</p>
          ) : (
            <div
              style={{
                display: 'flex',
                gap: '12px',
                justifyContent: 'flex-start',
                overflowX: 'auto',
                paddingBottom: '8px',
                WebkitOverflowScrolling: 'touch',
              }}
            >
              {Array.from({ length: 8 }, (_, i) => {
                const gymNumber = String(i + 1);
                const gym = allGyms.find(g => g.gym_number === gymNumber);
                const isCompleted = gymProgress.some((g: any) => String(g.gym_number) === gymNumber);
                
                if (!gym) {
                  // Gym not yet loaded/available
                  return (
                    <BadgeItem
                      key={gymNumber}
                      gymNumber={gymNumber}
                      badgeName="???"
                      location="Unknown"
                      isCompleted={false}
                      isSelected={false}
                      onClick={() => {}}
                    />
                  );
                }

                return (
                  <BadgeItem
                    key={gymNumber}
                    gymNumber={gymNumber}
                    badgeName={gym.badge_name}
                    location={gym.location}
                    isCompleted={isCompleted}
                    isSelected={selectedGymNumber === gymNumber}
                    onClick={() => setSelectedGymNumber(gymNumber)}
                  />
                );
              })}
            </div>
          )}
        </div>

        {/* Gym Detail Panel */}
        {selectedGym && (
          <div className="card" style={{ padding: '24px' }}>
            <h2
              style={{
                color: 'var(--color-text-primary)',
                fontSize: '1.5rem',
                marginTop: 0,
                marginBottom: '16px',
                fontWeight: 600,
              }}
            >
              Gym {selectedGym.gym_number}: {selectedGym.location}
            </h2>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(200px, 1fr) 2fr',
                gap: '24px',
                marginBottom: '24px',
              }}
            >
              {/* Gym Info */}
              <div>
                <div
                  style={{
                    marginBottom: '12px',
                    padding: '12px',
                    backgroundColor: 'var(--color-bg-light)',
                    borderRadius: '8px',
                  }}
                >
                  <div
                    style={{
                      fontSize: '0.85rem',
                      color: 'var(--color-text-secondary)',
                      marginBottom: '4px',
                    }}
                  >
                    Badge
                  </div>
                  <div
                    style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      color: 'var(--color-text-primary)',
                    }}
                  >
                    {selectedGym.badge_name}
                  </div>
                </div>

                {selectedGym.trainer_name && (
                  <div
                    style={{
                      marginBottom: '12px',
                      padding: '12px',
                      backgroundColor: 'var(--color-bg-light)',
                      borderRadius: '8px',
                    }}
                  >
                    <div
                      style={{
                        fontSize: '0.85rem',
                        color: 'var(--color-text-secondary)',
                        marginBottom: '8px',
                      }}
                    >
                      Gym Leader
                    </div>
                    {selectedGym.trainer_image && (
                      <div
                        style={{
                          width: '120px',
                          height: '120px',
                          borderRadius: '8px',
                          backgroundColor: 'var(--color-bg-card)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          overflow: 'hidden',
                          border: '1px solid var(--color-border)',
                          marginBottom: '8px',
                        }}
                      >
                        <img
                          src={selectedGym.trainer_image}
                          alt={selectedGym.trainer_name}
                          style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'contain',
                            imageRendering: 'auto',
                          }}
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                      </div>
                    )}
                    <div
                      style={{
                        fontSize: '1.1rem',
                        fontWeight: 600,
                        color: 'var(--color-text-primary)',
                      }}
                    >
                      {selectedGym.trainer_name}
                    </div>
                  </div>
                )}

                {selectedGym.badge_type && (
                  <div
                    style={{
                      marginBottom: '12px',
                      padding: '12px',
                      backgroundColor: 'var(--color-bg-light)',
                      borderRadius: '8px',
                    }}
                  >
                    <div
                      style={{
                        fontSize: '0.85rem',
                        color: 'var(--color-text-secondary)',
                        marginBottom: '4px',
                      }}
                    >
                      Type Specialty
                    </div>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <PokemonTypeBadge type={selectedGym.badge_type.toLowerCase()} />
                    </div>
                  </div>
                )}

                {isSelectedGymCompleted && (
                  <div
                    style={{
                      padding: '12px',
                      backgroundColor: 'var(--color-pokemon-green)',
                      borderRadius: '8px',
                      color: 'var(--color-text-white)',
                      fontWeight: 600,
                      textAlign: 'center',
                    }}
                  >
                    ✓ Completed
                  </div>
                )}
              </div>

              {/* Gym Leader Team */}
              <div>
                <h3
                  style={{
                    color: 'var(--color-text-primary)',
                    fontSize: '1.1rem',
                    marginTop: 0,
                    marginBottom: '16px',
                    fontWeight: 600,
                  }}
                >
                  Gym Leader Team
                </h3>
                {selectedGym.pokemon && Array.isArray(selectedGym.pokemon) && selectedGym.pokemon.length > 0 ? (
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                      gap: '12px',
                    }}
                  >
                    {selectedGym.pokemon.map((poke: any, index: number) => {
                      const pokemonName = typeof poke === 'string' ? poke : poke.name || poke;
                      const level = typeof poke === 'object' && poke.level ? poke.level : null;
                      
                      return (
                        <div
                          key={index}
                          style={{
                            padding: '14px',
                            borderRadius: '10px',
                            border: '1px solid var(--color-border)',
                            backgroundColor: 'var(--color-bg-card)',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '10px',
                          }}
                        >
                          <PokemonSprite pokemonName={pokemonName} size={72} />
                          <div
                            style={{
                              textAlign: 'center',
                              width: '100%',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '4px',
                            }}
                          >
                            <div
                              style={{
                                fontSize: '0.9rem',
                                fontWeight: 600,
                                color: 'var(--color-text-primary)',
                                textTransform: 'capitalize',
                              }}
                            >
                              {pokemonName}
                            </div>
                            {level !== null && (
                              <div
                                style={{
                                  fontSize: '0.75rem',
                                  color: 'var(--color-text-secondary)',
                                }}
                              >
                                Lv. {level}
                              </div>
                            )}
                            <div
                              style={{
                                display: 'flex',
                                gap: '4px',
                                justifyContent: 'center',
                                flexWrap: 'wrap',
                                marginTop: '2px',
                              }}
                            >
                              <PokemonTypes pokemonName={pokemonName} />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p style={{ color: 'var(--color-text-secondary)' }}>
                    Team information not available.
                  </p>
                )}
              </div>
            </div>

            {/* Mark Next Gym Completed Button */}
            {!isSelectedGymCompleted && 
             nextGymToComplete && 
             selectedGym.gym_number === nextGymToComplete.gym_number && (
              <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--color-border)' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => setShowConfirmModal(true)}
                  style={{ fontSize: '0.9rem', padding: '10px 20px' }}
                >
                  Mark Gym {selectedGym.gym_number} Completed
                </button>
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div
            style={{
              padding: '12px',
              backgroundColor: '#FEE2E2',
              border: '1px solid #F87171',
              borderRadius: '8px',
              color: '#B91C1C',
              fontSize: '0.85rem',
            }}
          >
            {error}
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && nextGymToComplete && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
          }}
          onClick={() => setShowConfirmModal(false)}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: '480px',
              padding: '24px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: '16px',
                color: 'var(--color-text-primary)',
              }}
            >
              Mark Gym {nextGymToComplete.gym_number} as Completed?
            </h2>
            <p
              style={{
                color: 'var(--color-text-secondary)',
                marginBottom: '20px',
              }}
            >
              This will mark the {nextGymToComplete.badge_name} Badge as earned at{' '}
              {nextGymToComplete.location}.
            </p>

            {error && (
              <div
                style={{
                  marginBottom: '12px',
                  padding: '10px',
                  backgroundColor: '#FEE2E2',
                  border: '1px solid #F87171',
                  borderRadius: '8px',
                  color: '#B91C1C',
                  fontSize: '0.85rem',
                }}
              >
                {error}
              </div>
            )}

            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: '8px',
              }}
            >
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => {
                  setShowConfirmModal(false);
                  setError(null);
                }}
                style={{ fontSize: '0.85rem', padding: '8px 14px' }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleMarkGymCompleted}
                disabled={addGymMutation.isPending}
                style={{ fontSize: '0.85rem', padding: '8px 14px' }}
              >
                {addGymMutation.isPending ? 'Saving...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
