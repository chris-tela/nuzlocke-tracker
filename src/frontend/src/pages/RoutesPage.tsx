/**
 * Routes Page
 * Track route progression and log encounters
 */
import { useState, useEffect, useRef, useMemo, useCallback, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameFile } from '../hooks/useGameFile';
import { useUpcomingRoutes, useRouteProgress, useRouteEncounters, useAddRouteProgress, useAddPokemonFromRoute } from '../hooks/useRoutes';
import { usePokemonInfoByName, usePokemon } from '../hooks/usePokemon';
import { Nature, Status, type NatureValue, type StatusValue } from '../types/enums';
import { PokemonTypeBadge } from '../components/PokemonTypeBadge';
import { getPokemonSpritePath } from '../utils/pokemonSprites';

// Lazy loading image component using Intersection Observer
const LazyImage = ({ 
  src, 
  alt, 
  style,
  onError 
}: { 
  src: string; 
  alt: string; 
  style?: React.CSSProperties;
  onError?: (e: React.SyntheticEvent<HTMLImageElement, Event>) => void;
}) => {
  const [isInView, setIsInView] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const imgRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px', // Start loading 50px before entering viewport
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <div ref={imgRef} style={{ ...style, position: 'relative' }}>
        {isInView && (
          <img
            src={src}
            alt={alt}
            style={{
              ...style,
              opacity: isLoaded ? 1 : 0,
              transition: 'opacity 0.2s ease-in-out',
              position: 'relative',
            }}
            onLoad={() => setIsLoaded(true)}
            onError={onError}
            loading="lazy"
          />
        )}
        {!isLoaded && isInView && (
          <div
            style={{
              ...style,
              backgroundColor: 'var(--color-bg-light)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'absolute',
              top: 0,
              left: 0,
            }}
          >
            <div
              style={{
                width: '20px',
                height: '20px',
                border: '2px solid var(--color-border)',
                borderTopColor: 'var(--color-pokemon-primary)',
                borderRadius: '50%',
                animation: 'spin 0.6s linear infinite',
              }}
            />
          </div>
        )}
      </div>
  );
};

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
const PokemonSprite = memo(({ pokemonName }: { pokemonName: string }) => {
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

  if (!pokemonInfo?.name) {
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
        position: 'relative',
      }}
    >
      <LazyImage
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
});

PokemonSprite.displayName = 'PokemonSprite';

// Component for individual encounter card with types
const EncounterCard = memo(({
  encounter,
  isClickable,
  onLogEncounterWithPokemon,
  isCaught,
  isCaughtOnThisRoute,
  isAlreadyOwned,
  isEncounteredRoute,
}: {
  encounter: { pokemon: string; minLevel: number; maxLevel: number; encounterMethods?: Record<string, number> };
  isClickable: boolean;
  onLogEncounterWithPokemon: (pokemonName: string) => void;
  isCaught?: boolean;
  isCaughtOnThisRoute?: boolean;
  isAlreadyOwned?: boolean;
  isEncounteredRoute?: boolean;
}) => {
  const { data: pokemonInfo } = usePokemonInfoByName(encounter.pokemon.toLowerCase());

  // Only disable/grey out if owned but NOT caught on this route AND it's an upcoming route
  // In encountered routes, show owned Pokemon normally (not greyed out)
  const isDisabled = isAlreadyOwned && !isCaught && !isEncounteredRoute;
  
  return (
    <div
      onClick={() => {
        if (isClickable && !isDisabled) {
          onLogEncounterWithPokemon(encounter.pokemon);
        }
      }}
      style={{
        padding: '16px',
        borderRadius: '12px',
        border: isCaught 
          ? `3px solid ${isCaughtOnThisRoute ? '#9333ea' : 'var(--color-pokemon-primary)'}` 
          : '1px solid var(--color-border)',
        backgroundColor: isDisabled ? 'var(--color-bg-light)' : 'var(--color-bg-card)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '8px',
        cursor: (isClickable && !isDisabled) ? 'pointer' : (isCaught ? 'default' : 'not-allowed'),
        transition: isClickable ? 'all 150ms ease' : 'none',
        boxShadow: isCaught 
          ? `0 0 0 2px ${isCaughtOnThisRoute ? '#9333ea' : 'var(--color-pokemon-primary)'}, 0 4px 6px rgba(0, 0, 0, 0.1)` 
          : 'none',
        position: 'relative',
        opacity: isDisabled ? 0.5 : 1,
        filter: isDisabled ? 'grayscale(100%)' : 'none',
      }}
      onMouseEnter={(e) => {
        if (isClickable && !isDisabled && !isCaughtOnThisRoute) {
          e.currentTarget.style.borderColor = 'var(--color-pokemon-primary)';
          e.currentTarget.style.backgroundColor = 'var(--color-bg-light)';
        }
      }}
      onMouseLeave={(e) => {
        if (isClickable && !isDisabled && !isCaughtOnThisRoute) {
          e.currentTarget.style.borderColor = isCaught 
            ? (isCaughtOnThisRoute ? '#9333ea' : 'var(--color-pokemon-primary)')
            : 'var(--color-border)';
          e.currentTarget.style.backgroundColor = 'var(--color-bg-card)';
        }
      }}
    >
      {isCaught && (
        <div
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            backgroundColor: isCaughtOnThisRoute ? '#9333ea' : 'var(--color-pokemon-primary)',
            color: 'white',
            fontSize: '0.7rem',
            fontWeight: 600,
            padding: '2px 6px',
            borderRadius: '4px',
            zIndex: 1,
          }}
        >
          ✓ Caught
        </div>
      )}
      {isAlreadyOwned && !isCaught && (
        <div
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            backgroundColor: '#9333ea',
            color: 'white',
            fontSize: '0.7rem',
            fontWeight: 600,
            padding: '2px 6px',
            borderRadius: '4px',
            zIndex: 1,
          }}
        >
          Owned
        </div>
      )}
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
            marginBottom: '4px',
          }}
        >
          Lv. {encounter.minLevel}
          {encounter.maxLevel !== encounter.minLevel
            ? `-${encounter.maxLevel}`
            : ''}
        </div>
        {encounter.encounterMethods && Object.keys(encounter.encounterMethods).length > 0 && (() => {
          const methodEntries = Object.entries(encounter.encounterMethods);
          const methodCount = methodEntries.length;
          const useTwoColumns = methodCount > 2;
          const midPoint = Math.ceil(methodCount / 2);
          const firstColumn = methodEntries.slice(0, midPoint);
          const secondColumn = methodEntries.slice(midPoint);

          const renderMethod = ([method, chance]: [string, number]) => {
            const iconPath = getEncounterMethodIcon(method);
            return (
              <div
                key={method}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.75rem',
                }}
              >
                {iconPath ? (
                  <img
                    src={iconPath}
                    alt={method}
                    title={method}
                    style={{
                      width: '24px',
                      height: '24px',
                      objectFit: 'contain',
                    }}
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                ) : null}
                <span
                  style={{
                    color: 'var(--color-text-secondary)',
                    textTransform: 'capitalize',
                  }}
                >
                  {method.replace(/-/g, ' ')}
                </span>
                <span
                  style={{
                    color: 'var(--color-text-primary)',
                    fontWeight: 600,
                  }}
                >
                  {chance}%
                </span>
              </div>
            );
          };

          return (
            <div
              style={{
                display: useTwoColumns ? 'grid' : 'flex',
                gridTemplateColumns: useTwoColumns ? '1fr 1fr' : undefined,
                flexDirection: useTwoColumns ? undefined : 'column',
                gap: '4px',
                alignItems: 'center',
                marginTop: '4px',
                width: '100%',
              }}
            >
              {useTwoColumns ? (
                <>
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                      alignItems: 'flex-start',
                    }}
                  >
                    {firstColumn.map(renderMethod)}
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                      alignItems: 'flex-start',
                    }}
                  >
                    {secondColumn.map(renderMethod)}
                  </div>
                </>
              ) : (
                methodEntries.map(renderMethod)
              )}
            </div>
          );
        })()}
      </div>
    </div>
  );
});

EncounterCard.displayName = 'EncounterCard';

// Component to render a single route with its encounters
const RouteCard = memo(({
  routeName,
  isEncountered,
  onMarkAsSeen,
  onLogEncounter,
  onLogEncounterWithPokemon,
  gameName,
  caughtPokemon,
  ownedPokemonNames,
  pokemonCaughtOn,
}: {
  routeName: string;
  isEncountered: boolean;
  onMarkAsSeen: () => void;
  onLogEncounter: () => void;
  onLogEncounterWithPokemon: (pokemonName: string) => void;
  gameName: string | null;
  caughtPokemon?: string | null;
  ownedPokemonNames?: Set<string>;
  pokemonCaughtOn?: Map<string, string | null>;
}) => {
  const { data: routeEncounters, isLoading: isLoadingEncounters } = useRouteEncounters(routeName, gameName);

  // Parse encounter data - format: [pokemonName, minLevel, maxLevel, game_name, region_name, {encounter_method: chance}]
  // Memoize to avoid recalculating on every render
  const encounters = useMemo(() => {
    if (!routeEncounters?.data || !Array.isArray(routeEncounters.data)) {
      return [];
    }
    return routeEncounters.data.map((enc: any) => ({
      pokemon: enc[0] || '',
      minLevel: enc[1] || 0,
      maxLevel: enc[2] || 0,
      game_name: enc[3] || '',
      region: enc[4] || '',
      encounterMethods: enc[5] && typeof enc[5] === 'object' ? enc[5] : {},
    }));
  }, [routeEncounters?.data]);

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
              const pokemonNameLower = encounter.pokemon.toLowerCase();
              const routeNameLower = routeName.toLowerCase();
              
              // Check if caught in this session (temporary state)
              const isCaughtThisSession = Boolean(isEncountered && caughtPokemon && 
                pokemonNameLower === caughtPokemon.toLowerCase());
              
              // Check if permanently caught on this route (from caught_on field)
              const caughtOnRoute = pokemonCaughtOn?.get(pokemonNameLower);
              const isCaughtOnThisRoute = caughtOnRoute?.toLowerCase() === routeNameLower;
              
              // Show purple border if permanently caught on this route
              const isCaught = isCaughtThisSession || isCaughtOnThisRoute;
              const isAlreadyOwned = Boolean(ownedPokemonNames?.has(pokemonNameLower));
              return (
                <EncounterCard
                  key={index}
                  encounter={encounter}
                  isClickable={isClickable}
                  onLogEncounterWithPokemon={onLogEncounterWithPokemon}
                  isCaught={isCaught}
                  isCaughtOnThisRoute={isCaughtOnThisRoute}
                  isAlreadyOwned={isAlreadyOwned}
                  isEncounteredRoute={isEncountered}
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
});

RouteCard.displayName = 'RouteCard';

export const RoutesPage = () => {
  const navigate = useNavigate();
  const { currentGameFile } = useGameFile();
  const gameFileId = currentGameFile?.id ?? null;
  const gameName = currentGameFile?.game_name ?? null;

  const { data: upcomingRoutes = [], isLoading: isLoadingUpcoming } = useUpcomingRoutes(gameFileId);
  const { data: encounteredRoutes = [], isLoading: isLoadingEncountered } = useRouteProgress(gameFileId);
  const { data: allOwnedPokemon = [] } = usePokemon(gameFileId);
  
  const addRouteProgressMutation = useAddRouteProgress(gameFileId);
  const addPokemonFromRouteMutation = useAddPokemonFromRoute(gameFileId);

  // Track which Pokemon was caught from each route
  const [routeCaughtPokemon, setRouteCaughtPokemon] = useState<Record<string, string>>({});

  // Create a set of owned Pokemon names for quick lookup
  const ownedPokemonNames = useMemo(() => {
    return new Set(allOwnedPokemon.map(p => p.name.toLowerCase()));
  }, [allOwnedPokemon]);

  // Create a map of Pokemon names to their caught_on values
  const pokemonCaughtOn = useMemo(() => {
    const map = new Map<string, string | null>();
    allOwnedPokemon.forEach(p => {
      if (p.name && p.caught_on !== undefined) {
        map.set(p.name.toLowerCase(), p.caught_on);
      }
    });
    return map;
  }, [allOwnedPokemon]);

  // Visibility toggles
  const [showEncounteredRoutes, setShowEncounteredRoutes] = useState(true);
  const [showUpcomingRoutes, setShowUpcomingRoutes] = useState(true);

  // Infinite scroll state
  const [displayedEncounteredCount, setDisplayedEncounteredCount] = useState(15);
  const [displayedUpcomingCount, setDisplayedUpcomingCount] = useState(15);

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

  // Reset displayed counts when routes data changes
  useEffect(() => {
    setDisplayedEncounteredCount(15);
  }, [encounteredRoutes.length]);

  useEffect(() => {
    setDisplayedUpcomingCount(15);
  }, [upcomingRoutes.length]);

  // Infinite scroll handler with throttling
  useEffect(() => {
    let ticking = false;
    
    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          // Check if user scrolled near bottom (within 200px)
          if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 200) {
            // Load more encountered routes if there are more to show
            if (showEncounteredRoutes && displayedEncounteredCount < encounteredRoutes.length) {
              setDisplayedEncounteredCount(prev => Math.min(prev + 15, encounteredRoutes.length));
            }
            // Load more upcoming routes if there are more to show
            if (showUpcomingRoutes && displayedUpcomingCount < upcomingRoutes.length) {
              setDisplayedUpcomingCount(prev => Math.min(prev + 15, upcomingRoutes.length));
            }
          }
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [showEncounteredRoutes, showUpcomingRoutes, displayedEncounteredCount, displayedUpcomingCount, encounteredRoutes.length, upcomingRoutes.length]);

  if (!currentGameFile || !gameFileId) {
    return null;
  }

  const handleMarkAsSeen = useCallback(async (routeName: string) => {
    try {
      setError(null);
      await addRouteProgressMutation.mutateAsync(routeName);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to confirm route');
    }
  }, [addRouteProgressMutation]);

  const handleOpenCatchModal = useCallback((routeName: string, pokemonName?: string) => {
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
  }, []);

  // Helper function to get min level for a Pokemon - memoized
  const getMinLevelForPokemon = useCallback((pokemonName: string): number | null => {
    if (!routeEncounters?.data || !Array.isArray(routeEncounters.data)) {
      return null;
    }
    const encounter = routeEncounters.data.find(
      (enc: any) => enc[0]?.toLowerCase() === pokemonName.toLowerCase()
    ) as any;
    return encounter && encounter[1] ? encounter[1] : null;
  }, [routeEncounters?.data]);

  // Update level when Pokemon is selected from dropdown or when routeEncounters loads
  useEffect(() => {
    if (showCatchModal && selectedPokemonName && routeEncounters?.data) {
      const minLevel = getMinLevelForPokemon(selectedPokemonName);
      if (minLevel !== null) {
        setLevelInput(String(minLevel));
      }
    }
  }, [showCatchModal, selectedPokemonName, routeEncounters]);

  const handleCloseCatchModal = useCallback(() => {
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
  }, []);

  const handleSubmitCatch = useCallback(async (e: React.FormEvent) => {
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
        game_name: enc[3] || '',
        region: enc[4] || '',
        encounterMethods: enc[5] && typeof enc[5] === 'object' ? enc[5] : {},
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
      
      // Track which Pokemon was caught from this route
      if (selectedRoute) {
        setRouteCaughtPokemon(prev => ({
          ...prev,
          [selectedRoute]: selectedPokemonName,
        }));
      }

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
  }, [selectedRoute, selectedPokemonName, nickname, nature, ability, level, gender, status, pokemonInfo, routeEncounters, encounteredRoutes, addPokemonFromRouteMutation, addRouteProgressMutation, handleCloseCatchModal]);

  // Parse encounters for the modal - memoized
  const encounters = useMemo(() => {
    if (!routeEncounters?.data || !Array.isArray(routeEncounters.data)) {
      return [];
    }
    return routeEncounters.data.map((enc: any) => ({
      pokemon: enc[0] || '',
      minLevel: enc[1] || 0,
      maxLevel: enc[2] || 0,
      game_name: enc[3] || '',
      region: enc[4] || '',
      encounterMethods: enc[5] && typeof enc[5] === 'object' ? enc[5] : {},
    }));
  }, [routeEncounters?.data]);

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
            flexDirection: 'column',
            gap: '12px',
            position: 'sticky',
            top: '20px',
            zIndex: 10,
            backgroundColor: 'var(--color-bg-light)',
            padding: '12px 0',
            marginBottom: '8px',
            paddingRight: '60px', // Account for theme toggle on mobile
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <h1
              style={{
                color: 'var(--color-text-primary)',
                fontSize: '1.8rem',
                margin: 0,
                flex: 1,
                minWidth: 0, // Allow text to shrink if needed
              }}
            >
              Routes
            </h1>
            <button
              className="btn btn-outline"
              onClick={() => navigate('/dashboard')}
              style={{
                fontSize: '0.9rem',
                padding: '8px 16px',
                whiteSpace: 'nowrap',
                flexShrink: 0,
                zIndex: 11, // Ensure it's above theme toggle
              }}
            >
              {'<-'} Back to Dashboard
            </button>
          </div>
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
                {encounteredRoutes.slice(0, displayedEncounteredCount).map((routeName) => (
                  <RouteCard
                    key={routeName}
                    routeName={routeName}
                    isEncountered={true}
                    onMarkAsSeen={() => handleMarkAsSeen(routeName)}
                    onLogEncounter={() => handleOpenCatchModal(routeName)}
                    onLogEncounterWithPokemon={(pokemonName) => handleOpenCatchModal(routeName, pokemonName)}
                    gameName={gameName}
                    caughtPokemon={routeCaughtPokemon[routeName]}
                    ownedPokemonNames={ownedPokemonNames}
                    pokemonCaughtOn={pokemonCaughtOn}
                  />
                ))}
                {displayedEncounteredCount < encounteredRoutes.length && (
                  <div
                    style={{
                      textAlign: 'center',
                      padding: '20px',
                      color: 'var(--color-text-secondary)',
                    }}
                  >
                    Loading more routes...
                  </div>
                )}
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
                {upcomingRoutes.slice(0, displayedUpcomingCount).map((routeName) => (
                  <RouteCard
                    key={routeName}
                    routeName={routeName}
                    isEncountered={false}
                    onMarkAsSeen={() => handleMarkAsSeen(routeName)}
                    onLogEncounter={() => handleOpenCatchModal(routeName)}
                    onLogEncounterWithPokemon={(pokemonName) => handleOpenCatchModal(routeName, pokemonName)}
                    gameName={gameName}
                    ownedPokemonNames={ownedPokemonNames}
                    pokemonCaughtOn={pokemonCaughtOn}
                  />
                ))}
                {displayedUpcomingCount < upcomingRoutes.length && (
                  <div
                    style={{
                      textAlign: 'center',
                      padding: '20px',
                      color: 'var(--color-text-secondary)',
                    }}
                  >
                    Loading more routes...
                  </div>
                )}
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
                    {encounters.map((encounter, index) => {
                      const isOwned = ownedPokemonNames.has(encounter.pokemon.toLowerCase());
                      return (
                        <option 
                          key={index} 
                          value={encounter.pokemon}
                          disabled={isOwned}
                          style={isOwned ? { color: '#999', fontStyle: 'italic' } : {}}
                        >
                          {encounter.pokemon.charAt(0).toUpperCase() + encounter.pokemon.slice(1)} (Lv.{' '}
                          {encounter.minLevel}
                          {encounter.maxLevel !== encounter.minLevel ? `-${encounter.maxLevel}` : ''})
                          {isOwned ? ' - Already Owned' : ''}
                        </option>
                      );
                    })}
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
