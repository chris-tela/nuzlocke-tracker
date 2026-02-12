/**
 * Trainers Page
 * Shows all trainers for the current game grouped by location,
 * with important trainers pinned at the top as "Key Battles".
 */
import { useState, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useGameFile } from '../hooks/useGameFile';
import { useTrainersByGame, useImportantTrainers } from '../hooks/useTrainers';
import { TrainerCard } from '../components/TrainerCard';
import type { Trainer } from '../types/trainer';

const SECTIONS_PER_PAGE = 15;

export const TrainersPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { currentGameFile } = useGameFile();

  const gameName = currentGameFile?.game_name ?? searchParams.get('gameName') ?? null;
  const starter: string | undefined = undefined; // TODO: currentGameFile?.starter_selected

  const { data: allTrainers = [], isLoading: isLoadingAll } = useTrainersByGame(gameName, starter);
  const { data: importantTrainers = [], isLoading: isLoadingImportant } = useImportantTrainers(gameName, starter);

  // Accordion state: which locations are expanded
  const [expandedLocations, setExpandedLocations] = useState<Set<string>>(new Set());

  // Load-more pagination state
  const [displayedSectionCount, setDisplayedSectionCount] = useState(SECTIONS_PER_PAGE);

  // Build a Set of important trainer IDs for quick lookup
  const importantTrainerIds = useMemo(() => {
    return new Set(importantTrainers.map((t) => t.id));
  }, [importantTrainers]);

  // Group trainers by location, preserving insertion order (battle_order)
  const locationGroups = useMemo(() => {
    const groups = new Map<string, Trainer[]>();
    for (const trainer of allTrainers) {
      const loc = trainer.location || 'Unknown';
      if (!groups.has(loc)) {
        groups.set(loc, []);
      }
      groups.get(loc)!.push(trainer);
    }
    return groups;
  }, [allTrainers]);

  // Count important trainers per location
  const importantCountByLocation = useMemo(() => {
    const counts = new Map<string, number>();
    for (const [loc, trainers] of locationGroups) {
      const count = trainers.filter((t) => importantTrainerIds.has(t.id)).length;
      if (count > 0) {
        counts.set(loc, count);
      }
    }
    return counts;
  }, [locationGroups, importantTrainerIds]);

  const allLocationKeys = useMemo(() => Array.from(locationGroups.keys()), [locationGroups]);
  const displayedLocationKeys = allLocationKeys.slice(0, displayedSectionCount);
  const hasMore = displayedSectionCount < allLocationKeys.length;

  const toggleLocation = (location: string) => {
    setExpandedLocations((prev) => {
      const next = new Set(prev);
      if (next.has(location)) {
        next.delete(location);
      } else {
        next.add(location);
      }
      return next;
    });
  };

  const handleLoadMore = () => {
    setDisplayedSectionCount((prev) =>
      Math.min(prev + SECTIONS_PER_PAGE, allLocationKeys.length)
    );
  };

  const isLoading = isLoadingAll || isLoadingImportant;

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
            gap: '12px',
            position: 'sticky',
            top: '20px',
            zIndex: 10,
            backgroundColor: 'var(--color-bg-light)',
            padding: '12px 0',
            marginBottom: '8px',
            paddingRight: '60px',
          }}
        >
          <h1
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '1.8rem',
              margin: 0,
              flex: 1,
              minWidth: 0,
            }}
          >
            Trainers
          </h1>
          <div
            style={{
              display: 'flex',
              gap: '12px',
              alignItems: 'center',
              flexShrink: 0,
            }}
          >
            <button
              className="btn btn-outline"
              onClick={() => navigate('/dashboard')}
              style={{
                fontSize: '0.9rem',
                padding: '8px 16px',
                whiteSpace: 'nowrap',
                zIndex: 11,
              }}
            >
              {'<-'} Back to Dashboard
            </button>
          </div>
        </div>

        {isLoading ? (
          <p style={{ color: 'var(--color-text-secondary)' }}>Loading trainers...</p>
        ) : allTrainers.length === 0 ? (
          <p style={{ color: 'var(--color-text-secondary)' }}>
            No trainers found for this game.
          </p>
        ) : (
          <>
            {/* Key Battles Section */}
            {importantTrainers.length > 0 && (
              <div>
                <h2
                  style={{
                    color: 'var(--color-text-primary)',
                    fontSize: '1.5rem',
                    margin: 0,
                    marginBottom: '16px',
                    fontWeight: 600,
                  }}
                >
                  Key Battles
                </h2>
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '16px',
                  }}
                >
                  {importantTrainers.map((trainer) => (
                    <TrainerCard
                      key={trainer.id}
                      trainer={trainer}
                      highlight={true}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Route-grouped Accordion */}
            <div>
              <h2
                style={{
                  color: 'var(--color-text-primary)',
                  fontSize: '1.5rem',
                  margin: 0,
                  marginBottom: '16px',
                  fontWeight: 600,
                }}
              >
                All Trainers by Location
              </h2>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                {displayedLocationKeys.map((location) => {
                  const trainers = locationGroups.get(location)!;
                  const isExpanded = expandedLocations.has(location);
                  const importantCount = importantCountByLocation.get(location) || 0;

                  return (
                    <div key={location} className="card" style={{ padding: 0, overflow: 'hidden' }}>
                      {/* Accordion Header */}
                      <button
                        type="button"
                        onClick={() => toggleLocation(location)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          width: '100%',
                          padding: '16px 20px',
                          border: 'none',
                          background: 'none',
                          cursor: 'pointer',
                          fontFamily: 'inherit',
                          textAlign: 'left',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            flex: 1,
                            minWidth: 0,
                          }}
                        >
                          <span
                            style={{
                              fontWeight: 600,
                              fontSize: '1rem',
                              color: 'var(--color-text-primary)',
                            }}
                          >
                            {location}
                          </span>
                          <span
                            style={{
                              fontSize: '0.8rem',
                              color: 'var(--color-text-secondary)',
                              flexShrink: 0,
                            }}
                          >
                            ({trainers.length} trainer{trainers.length !== 1 ? 's' : ''})
                          </span>
                          {importantCount > 0 && (
                            <span
                              style={{
                                display: 'inline-block',
                                padding: '2px 8px',
                                borderRadius: 'var(--radius-sm, 4px)',
                                fontSize: '0.7rem',
                                fontWeight: 600,
                                color: '#FFFFFF',
                                backgroundColor: 'var(--color-pokemon-primary, #E74C3C)',
                                flexShrink: 0,
                              }}
                            >
                              {importantCount} key
                            </span>
                          )}
                        </div>
                        <span
                          style={{
                            fontSize: '1rem',
                            color: 'var(--color-text-primary)',
                            flexShrink: 0,
                            marginLeft: '8px',
                          }}
                        >
                          {isExpanded ? '\u25B2' : '\u25BC'}
                        </span>
                      </button>

                      {/* Expanded Content */}
                      {isExpanded && (
                        <div
                          style={{
                            padding: '0 20px 20px 20px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '12px',
                          }}
                        >
                          {trainers.map((trainer) => (
                            <TrainerCard
                              key={trainer.id}
                              trainer={trainer}
                              highlight={importantTrainerIds.has(trainer.id)}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Load More Button */}
              {hasMore && (
                <div
                  style={{
                    textAlign: 'center',
                    padding: '20px',
                  }}
                >
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={handleLoadMore}
                    style={{
                      fontSize: '0.9rem',
                      padding: '10px 24px',
                    }}
                  >
                    Load more ({allLocationKeys.length - displayedSectionCount} remaining)
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
