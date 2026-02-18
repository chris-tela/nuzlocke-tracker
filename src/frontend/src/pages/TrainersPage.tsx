import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useGameFile } from '../hooks/useGameFile';
import { useTrainersByGame } from '../hooks/useTrainers';
import { usePartyPokemon } from '../hooks/usePokemon';
import { TrainerCard } from '../components/TrainerCard';
import type { Trainer } from '../types/trainer';

const TRAINERS_PER_PAGE = 20;
type ScopeMode = 'all' | 'important';
const ALL_IMPORTANCE_FILTER = '__all__';

function normalizeImportanceReason(reason: string): string {
  return reason.trim().toLowerCase().replace(/[_\s-]+/g, ' ');
}

function toImportanceLabel(reason: string): string {
  return reason
    .trim()
    .replace(/^reason:\s*/i, '')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export const TrainersPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { currentGameFile } = useGameFile();

  const gameName = currentGameFile?.game_name ?? searchParams.get('gameName') ?? null;
  const gameFileId = currentGameFile?.id ?? null;
  const starter: string | undefined = undefined; // TODO: currentGameFile?.starter_selected

  const { data: allTrainers = [], isLoading: isLoadingAll } = useTrainersByGame(gameName, starter);
  const { data: partyPokemon = [], isLoading: isLoadingParty } = usePartyPokemon(gameFileId);
  const searchTermFromParams = searchParams.get('search')?.trim() ?? '';
  const importanceFromParams = searchParams.get('sortBy');
  const scopeFromParamsRaw = searchParams.get('scope');
  const scopeFromParams: ScopeMode = scopeFromParamsRaw === 'important' ? 'important' : 'all';
  const normalizedImportanceFromParams = importanceFromParams?.trim()
    ? normalizeImportanceReason(importanceFromParams)
    : ALL_IMPORTANCE_FILTER;
  const [searchTerm, setSearchTerm] = useState(searchTermFromParams);
  const [importanceFilter, setImportanceFilter] = useState<string>(normalizedImportanceFromParams);
  const [scopeMode, setScopeMode] = useState<ScopeMode>(scopeFromParams);
  const [displayedTrainerCount, setDisplayedTrainerCount] = useState(TRAINERS_PER_PAGE);

  useEffect(() => {
    setSearchTerm(searchTermFromParams);
    setImportanceFilter(normalizedImportanceFromParams);
    setScopeMode(scopeFromParams);
    setDisplayedTrainerCount(TRAINERS_PER_PAGE);
  }, [searchTermFromParams, normalizedImportanceFromParams, scopeFromParams]);

  const sortedTrainers = useMemo(() => {
    const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
    const trainers = [...allTrainers];
    trainers.sort((a, b) => {
      const orderDiff = a.battle_order - b.battle_order;
      if (orderDiff !== 0) {
        return orderDiff;
      }

      const trainerDiff = collator.compare(a.trainer_name, b.trainer_name);
      if (trainerDiff !== 0) {
        return trainerDiff;
      }

      return collator.compare(a.location || 'Unknown', b.location || 'Unknown');
    });
    return trainers;
  }, [allTrainers]);

  const importanceOptions = useMemo(() => {
    const byReason = new Map<string, string>();
    for (const trainer of sortedTrainers) {
      if (!trainer.is_important || !trainer.importance_reason?.trim()) continue;
      const normalized = normalizeImportanceReason(trainer.importance_reason);
      if (!byReason.has(normalized)) {
        byReason.set(normalized, toImportanceLabel(trainer.importance_reason));
      }
    }

    return Array.from(byReason.entries())
      .map(([value, label]) => ({ value, label }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [sortedTrainers]);

  const visibleTrainers = useMemo(() => {
    const scoped =
      scopeMode === 'important'
        ? sortedTrainers.filter((trainer) => trainer.is_important)
        : sortedTrainers;
    const byImportance =
      importanceFilter === ALL_IMPORTANCE_FILTER
        ? scoped
        : scoped.filter(
            (trainer) =>
              trainer.importance_reason != null &&
              normalizeImportanceReason(trainer.importance_reason) === importanceFilter
          );

    const query = searchTerm.trim().toLowerCase();
    if (!query) {
      return byImportance;
    }

    return byImportance.filter((trainer) => trainer.trainer_name.toLowerCase().includes(query));
  }, [scopeMode, sortedTrainers, searchTerm, importanceFilter]);

  const displayedTrainers = useMemo(
    () => visibleTrainers.slice(0, displayedTrainerCount),
    [visibleTrainers, displayedTrainerCount]
  );
  const hasMore = displayedTrainerCount < visibleTrainers.length;

  const handleLoadMore = () => {
    setDisplayedTrainerCount((prev) =>
      Math.min(prev + TRAINERS_PER_PAGE, visibleTrainers.length)
    );
  };

  const handleScopeChange = (nextScope: ScopeMode) => {
    setScopeMode(nextScope);
    setDisplayedTrainerCount(TRAINERS_PER_PAGE);
  };

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    setDisplayedTrainerCount(TRAINERS_PER_PAGE);
  };

  const handleImportanceFilterChange = (value: string) => {
    setImportanceFilter(value);
    setDisplayedTrainerCount(TRAINERS_PER_PAGE);
  };

  const isLoading = isLoadingAll;
  const canEvaluateMatchup = !isLoadingParty && gameFileId != null && partyPokemon.length > 0;

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

        <div
          className="card"
          style={{
            display: 'flex',
            gap: '24px',
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>Scope</span>
            <div
              style={{
                display: 'inline-flex',
                gap: '6px',
                padding: '4px',
                borderRadius: '999px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-bg-light)',
              }}
            >
              <button
                type="button"
                aria-pressed={scopeMode === 'all'}
                onClick={() => handleScopeChange('all')}
                style={{
                  fontSize: '0.85rem',
                  padding: '6px 14px',
                  borderRadius: '999px',
                  border: 'none',
                  backgroundColor:
                    scopeMode === 'all' ? 'var(--color-pokemon-primary)' : 'transparent',
                  color: scopeMode === 'all' ? 'var(--color-text-white)' : 'var(--color-text-secondary)',
                  fontWeight: 600,
                }}
              >
                All
              </button>
              <button
                type="button"
                aria-pressed={scopeMode === 'important'}
                onClick={() => handleScopeChange('important')}
                style={{
                  fontSize: '0.85rem',
                  padding: '6px 14px',
                  borderRadius: '999px',
                  border: 'none',
                  backgroundColor:
                    scopeMode === 'important' ? 'var(--color-pokemon-primary)' : 'transparent',
                  color:
                    scopeMode === 'important'
                      ? 'var(--color-text-white)'
                      : 'var(--color-text-secondary)',
                  fontWeight: 600,
                }}
              >
                Important
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: '240px' }}>
            <label
              htmlFor="trainer-search"
              style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem', whiteSpace: 'nowrap' }}
            >
              Search
            </label>
            <input
              id="trainer-search"
              type="text"
              value={searchTerm}
              onChange={(event) => handleSearchChange(event.target.value)}
              placeholder="Type trainer name..."
              className="input"
              style={{ maxWidth: '420px' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: '260px' }}>
            <label
              htmlFor="importance-filter"
              style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem', whiteSpace: 'nowrap' }}
            >
              Sort by
            </label>
            <select
              id="importance-filter"
              className="input"
              value={importanceFilter}
              onChange={(event) => handleImportanceFilterChange(event.target.value)}
              style={{ maxWidth: '260px' }}
            >
              <option value={ALL_IMPORTANCE_FILTER}>All importance types</option>
              {importanceOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div
          className="card"
          style={{
            padding: '10px 14px',
            borderColor: 'var(--color-border)',
            backgroundColor: 'var(--color-bg-card)',
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: '0.85rem',
              color: 'var(--color-text-secondary)',
            }}
          >
            Trainer data is hard to obtain. Information may be missing or inaccurate.
          </p>
        </div>

        {isLoading ? (
          <p style={{ color: 'var(--color-text-secondary)' }}>Loading trainers...</p>
        ) : visibleTrainers.length === 0 ? (
          <p style={{ color: 'var(--color-text-secondary)' }}>
            No trainers found for the selected filters
            {searchTerm.trim() ? ' and search' : ''}.
          </p>
        ) : (
          <>
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
                Trainers
              </h2>
              <p
                style={{
                  color: 'var(--color-text-secondary)',
                  margin: '0 0 16px 0',
                  fontSize: '0.95rem',
                }}
              >
                Ordered by battle order.
              </p>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                {displayedTrainers.map((trainer: Trainer) => (
                  <TrainerCard
                    key={trainer.id}
                    trainer={trainer}
                    highlight={trainer.is_important}
                    gameFileId={gameFileId}
                    canEvaluateMatchup={canEvaluateMatchup}
                  />
                ))}
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
                    Load more ({visibleTrainers.length - displayedTrainerCount} remaining)
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
