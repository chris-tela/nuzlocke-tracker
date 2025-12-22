/**
 * Routes Page
 * Track route progression and log encounters
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameFile } from '../hooks/useGameFile';
import { useUpcomingRoutes, useRouteProgress, useRouteEncounters, useAddRouteProgress, useAddPokemonFromRoute } from '../hooks/useRoutes';
import { usePokemonInfoByName } from '../hooks/usePokemon';
import { Nature, Status, type NatureValue, type StatusValue } from '../types/enums';
import { PokemonTypeBadge } from '../components/PokemonTypeBadge';

// Helper function to get encounter method icon path
const getEncounterMethodIcon = (method: string): string | null => {
  const methodLower = method.toLowerCase();
  
  // Handle special mappings (multiple methods map to one icon)
  if (methodLower === 'gift' || methodLower === 'gift-egg') {
    return '/images/encounters/gift.png';
  }
  if (methodLower === 'surf' || methodLower === 'surf-spots') {
    return '/images/encounters/surf.png';
  }
  if (methodLower === 'super-rod' || methodLower === 'super-rod-spots') {
    return '/images/encounters/super-rod.png';
  }
  
  // 1-to-1 mappings
  const methodIcons: Record<string, string> = {
    'walk': '/images/encounters/walk.png',
    'dark-grass': '/images/encounters/dark-grass.png',
    'good-rod': '/images/encounters/good-rod.png',
    'grass-spots': '/images/encounters/grass-spots.png',
    'old-rod': '/images/encounters/old-rod.png',
    'rock-smash': '/images/encounters/rock-smash.png',
  };
  
  return methodIcons[methodLower] || null;
};

// Component to display Pokemon sprite with loading state
const PokemonSprite = ({ pokemonName }: { pokemonName: string }) => {
  const { data: pokemonInfo, isLoading } = usePokemonInfoByName(pokemonName.toLowerCase());

  if (isLoading) {
    return (
      <div
        style={{
          width: '96px',
          height: '96px',
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

  if (!pokemonInfo?.sprite) {
    return (
      <div
        style={{
          width: '96px',
          height: '96px',
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
        width: '96px',
        height: '96px',
        borderRadius: '8px',
        backgroundColor: 'var(--color-bg-light)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      <img
        src={pokemonInfo.sprite}
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

// Component for individual encounter card with types
const EncounterCard = ({
  encounter,
  isClickable,
  onLogEncounterWithPokemon,
}: {
  encounter: { pokemon: string; minLevel: number; maxLevel: number; methods?: string[]; chance?: number };
  isClickable: boolean;
  onLogEncounterWithPokemon: (pokemonName: string) => void;
}) => {
  const { data: pokemonInfo } = usePokemonInfoByName(encounter.pokemon.toLowerCase());

  return (
    <div
      onClick={() => {
        if (isClickable) {
          onLogEncounterWithPokemon(encounter.pokemon);
        }
      }}
      style={{
        padding: '16px',
        borderRadius: '12px',
        border: '1px solid var(--color-border)',
        backgroundColor: 'var(--color-bg-card)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px',
        cursor: isClickable ? 'pointer' : 'default',
        transition: isClickable ? 'all 150ms ease' : 'none',
      }}
      onMouseEnter={(e) => {
        if (isClickable) {
          e.currentTarget.style.borderColor = 'var(--color-pokemon-primary)';
          e.currentTarget.style.backgroundColor = 'var(--color-bg-light)';
        }
      }}
      onMouseLeave={(e) => {
        if (isClickable) {
          e.currentTarget.style.borderColor = 'var(--color-border)';
          e.currentTarget.style.backgroundColor = 'var(--color-bg-card)';
        }
      }}
    >
      <PokemonSprite pokemonName={encounter.pokemon} />
      <div
        style={{
          textAlign: 'center',
          width: '100%',
        }}
      >
        <div
          style={{
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            textTransform: 'capitalize',
            marginBottom: '4px',
          }}
        >
          {encounter.pokemon}
        </div>
        {pokemonInfo?.types && pokemonInfo.types.length > 0 && (
          <div
            style={{
              display: 'flex',
              gap: '6px',
              justifyContent: 'center',
              flexWrap: 'wrap',
              marginBottom: '6px',
            }}
          >
            {pokemonInfo.types.map((type) => (
              <PokemonTypeBadge key={type} type={type} />
            ))}
          </div>
        )}
        <div
          style={{
            fontSize: '0.85rem',
            color: 'var(--color-text-primary)',
            fontWeight: 500,
          }}
        >
          Lv. {encounter.minLevel}
          {encounter.maxLevel !== encounter.minLevel
            ? `-${encounter.maxLevel}`
            : ''}
          {encounter.chance !== undefined && (
            <>, {encounter.chance}%</>
          )}
        </div>
        {encounter.methods && Array.isArray(encounter.methods) && encounter.methods.length > 0 && (
          <div
            style={{
              display: 'flex',
              gap: '6px',
              justifyContent: 'center',
              alignItems: 'center',
              flexWrap: 'wrap',
              marginTop: '4px',
            }}
          >
            {encounter.methods.map((method, index) => {
              const iconPath = getEncounterMethodIcon(method);
              return (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  {iconPath ? (
                    <img
                      src={iconPath}
                      alt={method}
                      title={method}
                      style={{
                        width: '35px',
                        height: '35px',
                        objectFit: 'contain',
                      }}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : null}
                  {!iconPath && (
                    <span
                      style={{
                        fontSize: '0.75rem',
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      {method}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

// Component to render a single route with its encounters
const RouteCard = ({
  routeName,
  isEncountered,
  onMarkAsSeen,
  onLogEncounter,
  onLogEncounterWithPokemon,
  gameName,
}: {
  routeName: string;
  isEncountered: boolean;
  onMarkAsSeen: () => void;
  onLogEncounter: () => void;
  onLogEncounterWithPokemon: (pokemonName: string) => void;
  gameName: string | null;
}) => {
  const { data: routeEncounters, isLoading: isLoadingEncounters } = useRouteEncounters(routeName, gameName);

  // Parse encounter data - format: [pokemonName, minLevel, maxLevel, version_name, region_name, methods, chance]
  const parseEncounters = () => {
    if (!routeEncounters?.data || !Array.isArray(routeEncounters.data)) {
      return [];
    }
    return routeEncounters.data.map((enc: any) => ({
      pokemon: enc[0] || '',
      minLevel: enc[1] || 0,
      maxLevel: enc[2] || 0,
      version_name: enc[3] || '',
      region: enc[4] || '',
      methods: enc[5] || [],
      chance: enc[6] !== undefined ? enc[6] : undefined,
    }));
  };

  const encounters = parseEncounters();

  return (
    <div
      className="card"
      style={{
        padding: '24px',
        marginBottom: '16px',
      }}
    >
      <h3
        style={{
          color: 'var(--color-text-primary)',
          fontSize: '1.2rem',
          marginTop: 0,
          marginBottom: '20px',
          fontWeight: 600,
        }}
      >
        {routeName}
      </h3>

      {isLoadingEncounters ? (
        <p style={{ color: 'var(--color-text-secondary)' }}>Loading encounters...</p>
      ) : encounters.length === 0 ? (
        <p style={{ color: 'var(--color-text-secondary)' }}>No encounters found.</p>
      ) : (
        <>
          {/* Encounter Grid with Sprites */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: '16px',
              marginBottom: '20px',
            }}
          >
            {encounters.map((encounter, index) => {
              const isClickable = !isEncountered && encounters.length > 0;
              return (
                <EncounterCard
                  key={index}
                  encounter={encounter}
                  isClickable={isClickable}
                  onLogEncounterWithPokemon={onLogEncounterWithPokemon}
                />
              );
            })}
          </div>
        </>
      )}

      {/* Actions - only show for upcoming routes (not encountered) */}
      {!isEncountered && (
        <div
          style={{
            display: 'flex',
            gap: '12px',
            flexWrap: 'wrap',
          }}
        >
          {/* Log Encounter button - only show if there are encounters */}
          {encounters.length > 0 && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={onLogEncounter}
            >
              Log Encounter
            </button>
          )}
          {/* Mark as Seen button - always show for upcoming routes */}
          <button
            type="button"
            className="btn btn-outline"
            onClick={onMarkAsSeen}
          >
            Mark as Seen
          </button>
        </div>
      )}
    </div>
  );
};

export const RoutesPage = () => {
  const navigate = useNavigate();
  const { currentGameFile } = useGameFile();
  const gameFileId = currentGameFile?.id ?? null;
  const gameName = currentGameFile?.game_name ?? null;

  const { data: upcomingRoutes = [], isLoading: isLoadingUpcoming } = useUpcomingRoutes(gameFileId);
  const { data: encounteredRoutes = [], isLoading: isLoadingEncountered } = useRouteProgress(gameFileId);
  
  const addRouteProgressMutation = useAddRouteProgress(gameFileId);
  const addPokemonFromRouteMutation = useAddPokemonFromRoute(gameFileId);

  // Visibility toggles
  const [showEncounteredRoutes, setShowEncounteredRoutes] = useState(true);
  const [showUpcomingRoutes, setShowUpcomingRoutes] = useState(true);

  // Log Encounter Modal State
  const [showCatchModal, setShowCatchModal] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState<string | null>(null);
  const [selectedPokemonName, setSelectedPokemonName] = useState<string>('');
  const [nickname, setNickname] = useState('');
  const [levelInput, setLevelInput] = useState('5');
  const [nature, setNature] = useState<NatureValue | ''>('');
  const [ability, setAbility] = useState('');
  const [gender, setGender] = useState<string>('');
  const [status, setStatus] = useState<StatusValue | ''>(Status.PARTY);
  const [error, setError] = useState<string | null>(null);

  const level = parseInt(levelInput, 10) || 0;

  // Fetch Pokemon info for ability dropdown when a Pokemon is selected
  const { data: pokemonInfo } = usePokemonInfoByName(selectedPokemonName || null);

  // Fetch encounters for the selected route (for the modal)
  const { data: routeEncounters } = useRouteEncounters(selectedRoute, gameName);

  useEffect(() => {
    if (!currentGameFile) {
      navigate('/game-files');
    }
  }, [currentGameFile, navigate]);

  if (!currentGameFile || !gameFileId) {
    return null;
  }

  const handleMarkAsSeen = async (routeName: string) => {
    try {
      setError(null);
      await addRouteProgressMutation.mutateAsync(routeName);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to confirm route');
    }
  };

  const handleOpenCatchModal = (routeName: string, pokemonName?: string) => {
    setSelectedRoute(routeName);
    setShowCatchModal(true);
    setError(null);
    setSelectedPokemonName(pokemonName || '');
    setNickname('');
    setLevelInput('5'); // Will be updated when routeEncounters loads or when Pokemon is selected
    setNature('');
    setAbility('');
    setGender('');
    setStatus(Status.PARTY);
  };

  // Helper function to get min level for a Pokemon
  const getMinLevelForPokemon = (pokemonName: string): number | null => {
    if (!routeEncounters?.data || !Array.isArray(routeEncounters.data)) {
      return null;
    }
    const encounter = routeEncounters.data.find(
      (enc: any) => enc[0]?.toLowerCase() === pokemonName.toLowerCase()
    ) as any;
    return encounter && encounter[1] ? encounter[1] : null;
  };

  // Update level when Pokemon is selected from dropdown or when routeEncounters loads
  useEffect(() => {
    if (showCatchModal && selectedPokemonName && routeEncounters?.data) {
      const minLevel = getMinLevelForPokemon(selectedPokemonName);
      if (minLevel !== null) {
        setLevelInput(String(minLevel));
      }
    }
  }, [showCatchModal, selectedPokemonName, routeEncounters]);

  const handleCloseCatchModal = () => {
    setShowCatchModal(false);
    setError(null);
    setSelectedRoute(null);
    setSelectedPokemonName('');
    setNickname('');
    setLevelInput('5');
    setNature('');
    setAbility('');
    setGender('');
    setStatus(Status.PARTY);
  };

  const handleSubmitCatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRoute || !selectedPokemonName) {
      setError('Please select a Pokemon');
      return;
    }

    if (level < 1 || level > 100) {
      setError('Level must be between 1 and 100');
      return;
    }

    // Parse encounters for validation
    const parseEncounters = () => {
      if (!routeEncounters?.data || !Array.isArray(routeEncounters.data)) {
        return [];
      }
      return routeEncounters.data.map((enc: any) => ({
        pokemon: enc[0] || '',
        minLevel: enc[1] || 0,
        maxLevel: enc[2] || 0,
        version_name: enc[3] || '',
        region: enc[4] || '',
        methods: enc[5] || [],
        chance: enc[6] !== undefined ? enc[6] : undefined,
      }));
    };

    const encounters = parseEncounters();
    const encounter = encounters.find(
      (enc) => enc.pokemon.toLowerCase() === selectedPokemonName.toLowerCase()
    );

    if (!encounter) {
      setError('Pokemon not found in route encounters');
      return;
    }

    if (!pokemonInfo?.poke_id) {
      setError('Loading Pokemon information... Please wait a moment and try again.');
      return;
    }

    try {
      setError(null);
      // Add the Pokemon
      await addPokemonFromRouteMutation.mutateAsync({
        routeName: selectedRoute,
        pokemon: {
          poke_id: pokemonInfo.poke_id,
          nickname: nickname.trim() || null,
          nature: nature || null,
          ability: ability.trim() || null,
          level: level,
          gender: gender || null,
          status: status || Status.PARTY,
        },
      });
      
      // Also mark the route as seen (moves it to encountered routes)
      // Only do this if the route is not already encountered
      if (!encounteredRoutes.includes(selectedRoute)) {
        try {
          await addRouteProgressMutation.mutateAsync(selectedRoute);
        } catch (routeErr: any) {
          // If marking as seen fails, log but don't block the Pokemon addition
          console.warn('Failed to mark route as seen:', routeErr);
        }
      }
      
      handleCloseCatchModal();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to add Pokemon');
    }
  };

  // Parse encounters for the modal
  const parseEncounters = () => {
    if (!routeEncounters?.data || !Array.isArray(routeEncounters.data)) {
      return [];
    }
    return routeEncounters.data.map((enc: any) => ({
      pokemon: enc[0] || '',
      minLevel: enc[1] || 0,
      maxLevel: enc[2] || 0,
      version_name: enc[3] || '',
      region: enc[4] || '',
      methods: enc[5] || [],
      chance: enc[6] !== undefined ? enc[6] : undefined,
    }));
  };

  const encounters = parseEncounters();

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
            position: 'sticky',
            top: '20px',
            zIndex: 10,
            backgroundColor: 'var(--color-bg-light)',
            padding: '12px 0',
            marginBottom: '8px',
          }}
        >
          <h1
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '1.8rem',
              margin: 0,
            }}
          >
            Routes
          </h1>
          <button
            className="btn btn-outline"
            onClick={() => navigate('/dashboard')}
            style={{ fontSize: '0.9rem', padding: '8px 16px' }}
          >
            {'<-'} Back to Dashboard
          </button>
        </div>

        {/* Encountered Routes Section */}
        <div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '16px',
            }}
          >
            <h2
              style={{
                color: 'var(--color-text-primary)',
                fontSize: '1.5rem',
                margin: 0,
                fontWeight: 600,
              }}
            >
              Encountered Routes
            </h2>
            <button
              type="button"
              onClick={() => setShowEncounteredRoutes(!showEncounteredRoutes)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-text-primary)',
                cursor: 'pointer',
                fontSize: '1.2rem',
                padding: '4px 8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'transform 150ms ease',
              }}
              title={showEncounteredRoutes ? 'Hide section' : 'Show section'}
            >
              {showEncounteredRoutes ? '▼' : '▲'}
            </button>
          </div>
          {showEncounteredRoutes && (
            isLoadingEncountered ? (
              <p style={{ color: 'var(--color-text-secondary)' }}>Loading routes...</p>
            ) : encounteredRoutes.length === 0 ? (
              <p style={{ color: 'var(--color-text-secondary)' }}>
                No routes encountered yet.
              </p>
            ) : (
              <div>
                {encounteredRoutes.map((routeName) => (
                  <RouteCard
                    key={routeName}
                    routeName={routeName}
                    isEncountered={true}
                    onMarkAsSeen={() => handleMarkAsSeen(routeName)}
                    onLogEncounter={() => handleOpenCatchModal(routeName)}
                    onLogEncounterWithPokemon={(pokemonName) => handleOpenCatchModal(routeName, pokemonName)}
                    gameName={gameName}
                  />
                ))}
              </div>
            )
          )}
        </div>

        {/* Upcoming Routes Section */}
        <div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '16px',
            }}
          >
            <h2
              style={{
                color: 'var(--color-text-primary)',
                fontSize: '1.5rem',
                margin: 0,
                fontWeight: 600,
              }}
            >
              Upcoming Routes
            </h2>
            <button
              type="button"
              onClick={() => setShowUpcomingRoutes(!showUpcomingRoutes)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-text-primary)',
                cursor: 'pointer',
                fontSize: '1.2rem',
                padding: '4px 8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'transform 150ms ease',
              }}
              title={showUpcomingRoutes ? 'Hide section' : 'Show section'}
            >
              {showUpcomingRoutes ? '▼' : '▲'}
            </button>
          </div>
          {showUpcomingRoutes && (
            isLoadingUpcoming ? (
              <p style={{ color: 'var(--color-text-secondary)' }}>Loading routes...</p>
            ) : upcomingRoutes.length === 0 ? (
              <p style={{ color: 'var(--color-text-secondary)' }}>
                No upcoming routes. All routes have been completed!
              </p>
            ) : (
              <div>
                {upcomingRoutes.map((routeName) => (
                  <RouteCard
                    key={routeName}
                    routeName={routeName}
                    isEncountered={false}
                    onMarkAsSeen={() => handleMarkAsSeen(routeName)}
                    onLogEncounter={() => handleOpenCatchModal(routeName)}
                    onLogEncounterWithPokemon={(pokemonName) => handleOpenCatchModal(routeName, pokemonName)}
                    gameName={gameName}
                  />
                ))}
              </div>
            )
          )}
        </div>
      </div>

      {/* Log Encounter Modal */}
      {showCatchModal && selectedRoute && (
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
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: '520px',
              padding: '24px',
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: '16px',
                color: 'var(--color-text-primary)',
              }}
            >
              Log Encounter - {selectedRoute}
            </h2>
            <form onSubmit={handleSubmitCatch}>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                  marginBottom: '16px',
                }}
              >
                {/* Pokemon Selection */}
                <div>
                  <label
                    htmlFor="pokemon"
                    style={{
                      display: 'block',
                      marginBottom: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                    }}
                  >
                    Pokemon *
                  </label>
                  <select
                    id="pokemon"
                    className="input"
                    value={selectedPokemonName}
                    onChange={(e) => {
                      const pokemonName = e.target.value;
                      setSelectedPokemonName(pokemonName);
                      setError(null);
                      
                      // Set level to min level when Pokemon is selected
                      if (pokemonName && routeEncounters?.data) {
                        const minLevel = getMinLevelForPokemon(pokemonName);
                        if (minLevel !== null) {
                          setLevelInput(String(minLevel));
                        }
                      }
                    }}
                    style={{ width: '100%' }}
                    required
                  >
                    <option value="">Select a Pokemon</option>
                    {encounters.map((encounter, index) => (
                      <option key={index} value={encounter.pokemon}>
                        {encounter.pokemon.charAt(0).toUpperCase() + encounter.pokemon.slice(1)} (Lv.{' '}
                        {encounter.minLevel}
                        {encounter.maxLevel !== encounter.minLevel ? `-${encounter.maxLevel}` : ''})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Nickname */}
                <div>
                  <label
                    htmlFor="nickname"
                    style={{
                      display: 'block',
                      marginBottom: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                    }}
                  >
                    Nickname
                  </label>
                  <input
                    id="nickname"
                    className="input"
                    type="text"
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    style={{ width: '100%' }}
                    placeholder="Optional"
                  />
                </div>

                {/* Level */}
                <div>
                  <label
                    htmlFor="level"
                    style={{
                      display: 'block',
                      marginBottom: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                    }}
                  >
                    Level *
                  </label>
                  <input
                    id="level"
                    className="input"
                    type="number"
                    value={levelInput}
                    onChange={(e) => setLevelInput(e.target.value)}
                    style={{
                      width: '100%',
                      borderColor:
                        (level < 1 || level > 100) && levelInput !== '' ? '#F87171' : undefined,
                      borderWidth:
                        (level < 1 || level > 100) && levelInput !== '' ? '2px' : undefined,
                    }}
                    min="1"
                    max="100"
                    required
                  />
                  {(level < 1 || level > 100) && levelInput !== '' && (
                    <p style={{ marginTop: '4px', fontSize: '0.75rem', color: '#F87171' }}>
                      Level must be between 1 and 100
                    </p>
                  )}
                </div>

                {/* Nature */}
                <div>
                  <label
                    htmlFor="nature"
                    style={{
                      display: 'block',
                      marginBottom: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                    }}
                  >
                    Nature
                  </label>
                  <select
                    id="nature"
                    className="input"
                    value={nature}
                    onChange={(e) => setNature(e.target.value as NatureValue | '')}
                    style={{ width: '100%' }}
                  >
                    <option value="">None</option>
                    {Object.values(Nature).map((n) => (
                      <option key={n} value={n}>
                        {n}
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
                      marginBottom: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                    }}
                  >
                    Ability
                  </label>
                  {pokemonInfo?.abilities && pokemonInfo.abilities.length > 0 ? (
                    <select
                      id="ability"
                      className="input"
                      value={ability}
                      onChange={(e) => setAbility(e.target.value)}
                      style={{ width: '100%' }}
                    >
                      <option value="">None</option>
                      {pokemonInfo.abilities.map((abil) => (
                        <option key={abil} value={abil}>
                          {abil}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      id="ability"
                      className="input"
                      type="text"
                      value={ability}
                      onChange={(e) => setAbility(e.target.value)}
                      placeholder="Enter ability"
                      style={{ width: '100%' }}
                    />
                  )}
                </div>

                {/* Gender */}
                <div>
                  <label
                    htmlFor="gender"
                    style={{
                      display: 'block',
                      marginBottom: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                    }}
                  >
                    Gender
                  </label>
                  <select
                    id="gender"
                    className="input"
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="">None</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>

                {/* Status */}
                <div>
                  <label
                    htmlFor="status"
                    style={{
                      display: 'block',
                      marginBottom: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                    }}
                  >
                    Status
                  </label>
                  <select
                    id="status"
                    className="input"
                    value={status}
                    onChange={(e) => setStatus(e.target.value as StatusValue | '')}
                    style={{ width: '100%' }}
                  >
                    <option value={Status.PARTY}>Party</option>
                    <option value={Status.STORED}>Stored</option>
                    <option value={Status.FAINTED}>Fainted</option>
                  </select>
                </div>
              </div>

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
                  marginTop: '8px',
                }}
              >
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={handleCloseCatchModal}
                  style={{ fontSize: '0.85rem', padding: '8px 14px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ fontSize: '0.85rem', padding: '8px 14px' }}
                >
                  Add Pokemon
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
