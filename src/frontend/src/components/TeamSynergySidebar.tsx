import { PokemonTypeBadge } from './PokemonTypeBadge';
import type { TeamSynergySummary } from '../types/pokemon';

export const TeamSynergySidebar = ({
  isLoading,
  isError,
  synergy,
}: {
  isLoading: boolean;
  isError: boolean;
  synergy?: TeamSynergySummary;
}) => {
  const formatMultiplier = (value: number) => {
    if (value === 0) {
      return '0x';
    }
    const rounded = Math.round(value * 100) / 100;
    if (Number.isInteger(rounded)) {
      return `${rounded}x`;
    }
    return `${rounded}x`;
  };

  const renderTypeList = (entries: TeamSynergySummary['offense']['strengths']) => {
    if (entries.length === 0) {
      return <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.85rem' }}>None</span>;
    }

    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
        {entries.map((entry) => {
          const contributorCount = entry.contributors.length;
          const contributorLabel =
            contributorCount === 0
              ? 'No contributing party members'
              : entry.contributors.join(', ');

          return (
            <div
              key={`${entry.type}-${entry.multiplier}`}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              title={contributorLabel}
            >
              <PokemonTypeBadge type={entry.type} />
              <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                {formatMultiplier(entry.multiplier)} ({contributorCount})
              </span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div
      className="card"
      style={{
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        position: 'sticky',
        top: '24px',
        minWidth: '320px',
      }}
    >
      <details>
        <summary
          style={{
            cursor: 'pointer',
            fontWeight: 600,
            color: 'var(--color-text-primary)',
            fontSize: '1rem',
          }}
        >
          View team synergy
        </summary>

        <div style={{ marginTop: '12px' }}>
          {isLoading ? (
            <p style={{ color: 'var(--color-text-secondary)' }}>Loading synergy...</p>
          ) : isError ? (
            <p style={{ color: '#B91C1C', fontSize: '0.85rem' }}>Failed to load synergy.</p>
          ) : !synergy ? (
            <p style={{ color: 'var(--color-text-secondary)' }}>No synergy data available.</p>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '16px',
              }}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <h3 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--color-text-primary)' }}>
                  Offense
                </h3>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                    Strengths
                  </div>
                  {renderTypeList(synergy.offense.strengths)}
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                    Weaknesses
                  </div>
                  {renderTypeList(synergy.offense.weaknesses)}
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                    Immunities
                  </div>
                  {renderTypeList(synergy.offense.immunities)}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <h3 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--color-text-primary)' }}>
                  Defense
                </h3>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                    Strengths
                  </div>
                  {renderTypeList(synergy.defense.strengths)}
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                    Weaknesses
                  </div>
                  {renderTypeList(synergy.defense.weaknesses)}
                </div>
                <div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                    Immunities
                  </div>
                  {renderTypeList(synergy.defense.immunities)}
                </div>
              </div>
            </div>
          )}
        </div>
      </details>
    </div>
  );
};
