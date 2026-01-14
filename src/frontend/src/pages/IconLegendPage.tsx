/**
 * Icon Legend Page
 * Displays all encounter method and condition icons with their meanings
 */
import { useNavigate } from 'react-router-dom';
import { getPokemonSpritePath } from '../utils/pokemonSprites';

// Helper function to get encounter method icon path (same as RoutesPage)
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

// Helper function to get condition icon path (same as RoutesPage)
const getConditionIcon = (condition: string): string | null => {
  const conditionLower = condition.toLowerCase();
  
  // Handle story-progress conditions (anything that starts with "story-progress")
  if (conditionLower.startsWith('story-progress')) {
    return '/images/conditions/story-progress.png';
  }
  
  // Map conditions to their icon paths
  const conditionIcons: Record<string, string> = {
    'time-morning': '/images/conditions/time-morning.png',
    'time-day': '/images/conditions/time-day.png',
    'time-night': '/images/conditions/time-night.png',
    'season-spring': '/images/conditions/season-spring.png',
    'season-summer': '/images/conditions/season-summer.png',
    'season-autumn': '/images/conditions/season-autumn.png',
    'season-winter': '/images/conditions/season-winter.png',
  };
  
  return conditionIcons[conditionLower] || null;
};

// All encounter methods to display
const ENCOUNTER_METHODS = [
  'walk',
  'dark-grass',
  'gift',
  'gift-egg',
  'good-rod',
  'grass-spots',
  'old-rod',
  'rock-smash',
  'surf',
  'surf-spots',
  'super-rod',
  'super-rod-spots',
];

// All conditions to display
const CONDITIONS = [
  'time-morning',
  'time-day',
  'time-night',
  'season-spring',
  'season-summer',
  'season-autumn',
  'season-winter',
  'story-progress',
];

// Descriptions for encounter methods
const ENCOUNTER_METHOD_DESCRIPTIONS: Record<string, string> = {
  'walk': 'Found when walking in tall grass or a cave',
  'dark-grass': 'Walking in dark grass',
  'gift': 'Receiving a gift',
  'gift-egg': 'Receiving a gift egg',
  'surf': 'Found while surfing',
  'surf-spots': 'Found while encountering a surf spot while surfing',
  'rock-smash': 'Found when using rock smash',
  'old-rod': 'Fishing with an old rod',
  'good-rod': 'Fishing with a good rod',
  'super-rod': 'Fishing with a super rod',
  'super-rod-spots': 'Fishing with a super rod in dark spots',
};

// Descriptions for conditions
const CONDITION_DESCRIPTIONS: Record<string, string> = {
  'story-progress': 'Story progress bench mark required',
};

export const IconLegendPage = () => {
  const navigate = useNavigate();

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
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '32px',
          }}
        >
          <h1
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '2rem',
              fontWeight: 700,
              margin: 0,
            }}
          >
            Icon Legend
          </h1>
          <button
            onClick={() => navigate('/routes')}
            className="btn btn-outline"
            style={{
              padding: '8px 16px',
            }}
          >
            Back to Routes
          </button>
        </div>

        {/* Encounter Methods Section */}
        <div
          className="card"
          style={{
            padding: '32px',
            marginBottom: '24px',
          }}
        >
          <h2
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '1.5rem',
              fontWeight: 600,
              marginTop: 0,
              marginBottom: '24px',
            }}
          >
            Encounter Methods
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: '20px',
            }}
          >
            {ENCOUNTER_METHODS.map((method) => {
              const iconPath = getEncounterMethodIcon(method);
              return (
                <div
                  key={method}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '12px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--color-bg-light)',
                  }}
                >
                  {iconPath ? (
                    <img
                      src={iconPath}
                      alt={method}
                      style={{
                        width: '32px',
                        height: '32px',
                        objectFit: 'contain',
                      }}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--color-text-secondary)',
                        fontSize: '0.75rem',
                        textTransform: 'capitalize',
                      }}
                    >
                      {method.replace(/-/g, ' ')}
                    </div>
                  )}
                  <div
                    style={{
                      flex: 1,
                    }}
                  >
                    <div
                      style={{
                        color: 'var(--color-text-primary)',
                        fontWeight: 600,
                        marginBottom: '4px',
                        textTransform: 'capitalize',
                      }}
                    >
                      {method.replace(/-/g, ' ')}
                    </div>
                    {ENCOUNTER_METHOD_DESCRIPTIONS[method] && (
                      <div
                        style={{
                          color: 'var(--color-text-secondary)',
                          fontSize: '0.875rem',
                          fontStyle: 'normal',
                        }}
                      >
                        {ENCOUNTER_METHOD_DESCRIPTIONS[method]}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Conditions Section */}
        <div
          className="card"
          style={{
            padding: '32px',
          }}
        >
          <h2
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '1.5rem',
              fontWeight: 600,
              marginTop: 0,
              marginBottom: '24px',
            }}
          >
            Conditions
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: '20px',
            }}
          >
            {CONDITIONS.map((condition) => {
              const iconPath = getConditionIcon(condition);
              return (
                <div
                  key={condition}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '12px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--color-bg-light)',
                  }}
                >
                  {iconPath ? (
                    <img
                      src={iconPath}
                      alt={condition}
                      style={{
                        width: '32px',
                        height: '32px',
                        objectFit: 'contain',
                      }}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--color-text-secondary)',
                        fontSize: '0.75rem',
                        textTransform: 'capitalize',
                      }}
                    >
                      {condition.replace(/-/g, ' ')}
                    </div>
                  )}
                  <div
                    style={{
                      flex: 1,
                    }}
                  >
                    <div
                      style={{
                        color: 'var(--color-text-primary)',
                        fontWeight: 600,
                        marginBottom: '4px',
                        textTransform: 'capitalize',
                      }}
                    >
                      {condition.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                    {CONDITION_DESCRIPTIONS[condition] && (
                      <div
                        style={{
                          color: 'var(--color-text-secondary)',
                          fontSize: '0.875rem',
                          fontStyle: 'normal',
                        }}
                      >
                        {CONDITION_DESCRIPTIONS[condition]}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Example Section */}
        <div
          className="card"
          style={{
            padding: '32px',
            position: 'relative',
          }}
        >
          {/* Explanations */}
          <div
            style={{
              position: 'absolute',
              top: '24px',
              right: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
              maxWidth: '280px',
            }}
          >
            {/* Level Explanation */}
            <div
              style={{
                padding: '14px 16px',
                backgroundColor: 'var(--color-bg-light)',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                fontSize: '0.9rem',
                lineHeight: '1.5',
                color: 'var(--color-text-secondary)',
              }}
            >
              <strong style={{ color: 'var(--color-text-primary)' }}>Level:</strong> Lowest & highest possible level found in a route
            </div>
            
            {/* Walk + Time Morning Explanation */}
            <div
              style={{
                padding: '14px 16px',
                backgroundColor: 'var(--color-bg-light)',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                fontSize: '0.9rem',
                lineHeight: '1.5',
                color: 'var(--color-text-secondary)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', gap: '6px', flexShrink: 0, marginTop: '2px' }}>
                {getEncounterMethodIcon('walk') && (
                  <img
                    src={getEncounterMethodIcon('walk')!}
                    alt="walk"
                    style={{
                      width: '24px',
                      height: '24px',
                      objectFit: 'contain',
                    }}
                  />
                )}
                {getConditionIcon('time-morning') && (
                  <img
                    src={getConditionIcon('time-morning')!}
                    alt="time-morning"
                    style={{
                      width: '24px',
                      height: '24px',
                      objectFit: 'contain',
                    }}
                  />
                )}
              </div>
              <div>
                Walking in the morning gives a <strong style={{ color: 'var(--color-text-primary)' }}>5%</strong> chance of encountering Pikachu
              </div>
            </div>
            
            {/* Surf + Time Night Explanation */}
            <div
              style={{
                padding: '14px 16px',
                backgroundColor: 'var(--color-bg-light)',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                fontSize: '0.9rem',
                lineHeight: '1.5',
                color: 'var(--color-text-secondary)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', gap: '6px', flexShrink: 0, marginTop: '2px' }}>
                {getEncounterMethodIcon('surf') && (
                  <img
                    src={getEncounterMethodIcon('surf')!}
                    alt="surf"
                    style={{
                      width: '24px',
                      height: '24px',
                      objectFit: 'contain',
                    }}
                  />
                )}
                {getConditionIcon('time-night') && (
                  <img
                    src={getConditionIcon('time-night')!}
                    alt="time-night"
                    style={{
                      width: '24px',
                      height: '24px',
                      objectFit: 'contain',
                    }}
                  />
                )}
              </div>
              <div>
                Surfing in the night gives a <strong style={{ color: 'var(--color-text-primary)' }}>10%</strong> chance of encountering Pikachu
              </div>
            </div>
          </div>
          <h2
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '1.5rem',
              fontWeight: 600,
              marginTop: 0,
              marginBottom: '24px',
            }}
          >
            Example
          </h2>
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
              }}
            >
              <div
                style={{
                  padding: '20px',
                  borderRadius: '12px',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg-card)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '12px',
                  maxWidth: '300px',
                  width: '100%',
                }}
              >
                {/* Pikachu Sprite */}
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
                    src={getPokemonSpritePath('pikachu')}
                    alt="Pikachu"
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

                {/* Pokemon Name */}
                <div
                  style={{
                    fontWeight: 600,
                    color: 'var(--color-text-primary)',
                    textTransform: 'capitalize',
                    fontSize: '1.1rem',
                  }}
                >
                  Pikachu
                </div>

                {/* Level */}
                <div
                  style={{
                    fontSize: '0.9rem',
                    color: 'var(--color-text-primary)',
                    fontWeight: 500,
                  }}
                >
                  Lv. 5-10
                </div>

                {/* Encounter Methods */}
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                    width: '100%',
                    marginTop: '8px',
                  }}
                >
                  {/* Walk + time-morning = 5% */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      fontSize: '0.75rem',
                      justifyContent: 'center',
                    }}
                  >
                    {getEncounterMethodIcon('walk') && (
                      <img
                        src={getEncounterMethodIcon('walk')!}
                        alt="walk"
                        style={{
                          width: '24px',
                          height: '24px',
                          objectFit: 'contain',
                        }}
                      />
                    )}
                    {getConditionIcon('time-morning') && (
                      <img
                        src={getConditionIcon('time-morning')!}
                        alt="time-morning"
                        style={{
                          width: '24px',
                          height: '24px',
                          objectFit: 'contain',
                        }}
                      />
                    )}
                    <span
                      style={{
                        color: 'var(--color-text-primary)',
                        fontWeight: 600,
                      }}
                    >
                      5%
                    </span>
                  </div>

                  {/* Surf + time-night = 10% */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      fontSize: '0.75rem',
                      justifyContent: 'center',
                    }}
                  >
                    {getEncounterMethodIcon('surf') && (
                      <img
                        src={getEncounterMethodIcon('surf')!}
                        alt="surf"
                        style={{
                          width: '24px',
                          height: '24px',
                          objectFit: 'contain',
                        }}
                      />
                    )}
                    {getConditionIcon('time-night') && (
                      <img
                        src={getConditionIcon('time-night')!}
                        alt="time-night"
                        style={{
                          width: '24px',
                          height: '24px',
                          objectFit: 'contain',
                        }}
                      />
                    )}
                    <span
                      style={{
                        color: 'var(--color-text-primary)',
                        fontWeight: 600,
                      }}
                    >
                      10%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
  );
};

