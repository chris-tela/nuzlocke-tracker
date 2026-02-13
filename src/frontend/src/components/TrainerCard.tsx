import { useState } from 'react';
import type { Trainer, TrainerPokemon, TrainerPokemonStats } from '../types/trainer';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const STAT_MAX = 255;

const IMPORTANCE_BADGES: Record<string, { color: string; label: string }> = {
  rival: { color: '#E74C3C', label: 'Rival' },
  gym_leader: { color: '#3498DB', label: 'Gym Leader' },
  elite_four: { color: '#9B59B6', label: 'Elite Four' },
  champion: { color: '#F39C12', label: 'Champion' },
  evil_team_leader: { color: '#2C3E50', label: 'Evil Team' },
  level_outlier: { color: '#E67E22', label: 'Tough Battle' },
};

const STAT_LABELS: { key: keyof TrainerPokemonStats; label: string }[] = [
  { key: 'hp', label: 'HP' },
  { key: 'attack', label: 'Atk' },
  { key: 'defense', label: 'Def' },
  { key: 'special_attack', label: 'SpA' },
  { key: 'special_defense', label: 'SpD' },
  { key: 'speed', label: 'Spe' },
];

function getStatBarColor(value: number): string {
  if (value >= 100) return '#22C55E';
  if (value >= 60) return '#3B82F6';
  if (value >= 30) return '#FBBF24';
  return '#F87171';
}

interface TrainerCardProps {
  trainer: Trainer;
  highlight?: boolean;
}

export function TrainerCard({ trainer, highlight }: TrainerCardProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const badge = trainer.importance_reason
    ? IMPORTANCE_BADGES[trainer.importance_reason]
    : null;

  const handlePokemonClick = (index: number) => {
    setExpandedIndex((prev) => (prev === index ? null : index));
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--color-bg-card)',
        border: highlight ? '3px solid var(--color-pokemon-primary)' : '2px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-md)',
        boxShadow: highlight ? 'var(--shadow-lg)' : 'var(--shadow-md)',
        transition: 'all 300ms ease',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-sm)',
          marginBottom: 'var(--spacing-md)',
        }}
      >
        {trainer.trainer_image && (
          <img
            src={trainer.trainer_image}
            alt={trainer.trainer_name}
            style={{
              width: 48,
              height: 48,
              imageRendering: 'pixelated',
              objectFit: 'contain',
            }}
          />
        )}

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', flexWrap: 'wrap' }}>
            <span
              style={{
                fontWeight: 700,
                fontSize: '1rem',
                color: 'var(--color-text-primary)',
              }}
            >
              {trainer.trainer_name}
            </span>

            {badge && (
              <span
                style={{
                  display: 'inline-block',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  color: '#FFFFFF',
                  backgroundColor: badge.color,
                }}
              >
                {badge.label}
              </span>
            )}
          </div>

          <div
            style={{
              fontSize: '0.8rem',
              color: 'var(--color-text-secondary)',
              marginTop: 2,
            }}
          >
            {trainer.location}
          </div>
        </div>
      </div>

      {/* Pokemon Lineup */}
      <div
        style={{
          display: 'flex',
          gap: 'var(--spacing-sm)',
          overflowX: 'auto',
          paddingBottom: 'var(--spacing-xs)',
        }}
      >
        {trainer.pokemon.map((poke, index) => (
          <PokemonSlot
            key={`${poke.name}-${index}`}
            pokemon={poke}
            isExpanded={expandedIndex === index}
            onClick={() => handlePokemonClick(index)}
          />
        ))}
      </div>

      {/* Expanded Pokemon Detail */}
      {expandedIndex !== null && trainer.pokemon[expandedIndex] && (
        <PokemonDetail pokemon={trainer.pokemon[expandedIndex]} />
      )}
    </div>
  );
}

function PokemonSlot({
  pokemon,
  isExpanded,
  onClick,
}: {
  pokemon: TrainerPokemon;
  isExpanded: boolean;
  onClick: () => void;
}) {
  const spriteUrl = pokemon.poke_id
    ? `${API_BASE_URL}/assets/sprites/${pokemon.poke_id}.webp`
    : undefined;

  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 2,
        padding: 'var(--spacing-xs)',
        border: isExpanded
          ? '2px solid var(--color-pokemon-primary)'
          : '2px solid transparent',
        borderRadius: 'var(--radius-md)',
        backgroundColor: isExpanded ? 'var(--color-bg-light)' : 'transparent',
        cursor: 'pointer',
        minWidth: 64,
        transition: 'all 150ms ease',
        outline: 'none',
        fontFamily: 'inherit',
      }}
      title={`${pokemon.name} Lv.${pokemon.level}`}
    >
      {spriteUrl ? (
        <img
          src={spriteUrl}
          alt={pokemon.name}
          style={{
            width: 40,
            height: 40,
            imageRendering: 'pixelated',
            objectFit: 'contain',
          }}
        />
      ) : (
        <div
          style={{
            width: 40,
            height: 40,
            backgroundColor: 'var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.6rem',
            color: 'var(--color-text-secondary)',
          }}
        >
          ?
        </div>
      )}

      <span
        style={{
          fontSize: '0.7rem',
          fontWeight: 600,
          color: 'var(--color-text-primary)',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          maxWidth: 64,
        }}
      >
        {pokemon.name}
      </span>

      <span
        style={{
          fontSize: '0.6rem',
          color: 'var(--color-text-secondary)',
        }}
      >
        Lv.{pokemon.level}
      </span>
    </button>
  );
}

function PokemonDetail({ pokemon }: { pokemon: TrainerPokemon }) {
  return (
    <div
      style={{
        marginTop: 'var(--spacing-sm)',
        padding: 'var(--spacing-md)',
        backgroundColor: 'var(--color-bg-light)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-border)',
      }}
    >
      {/* Stat Bars */}
      {pokemon.stats && (
        <div style={{ marginBottom: pokemon.moves.length > 0 ? 'var(--spacing-md)' : 0 }}>
          <div
            style={{
              fontSize: '0.8rem',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--spacing-xs)',
            }}
          >
            Base Stats
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {STAT_LABELS.map(({ key, label }) => {
              const value = pokemon.stats![key];
              const barWidth = Math.min((value / STAT_MAX) * 100, 100);
              const barColor = getStatBarColor(value);

              return (
                <div
                  key={key}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--spacing-sm)',
                  }}
                >
                  <span
                    style={{
                      width: 28,
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      color: 'var(--color-text-secondary)',
                      textAlign: 'right',
                      flexShrink: 0,
                    }}
                  >
                    {label}
                  </span>
                  <div
                    style={{
                      flex: 1,
                      height: 10,
                      backgroundColor: 'var(--color-border)',
                      borderRadius: 'var(--radius-sm)',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        width: `${barWidth}%`,
                        height: '100%',
                        backgroundColor: barColor,
                        borderRadius: 'var(--radius-sm)',
                        transition: 'width 300ms ease',
                      }}
                    />
                  </div>
                  <span
                    style={{
                      width: 28,
                      fontSize: '0.7rem',
                      fontWeight: 600,
                      color: 'var(--color-text-primary)',
                      textAlign: 'right',
                      flexShrink: 0,
                    }}
                  >
                    {value}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Moves */}
      {pokemon.moves.length > 0 && (
        <div>
          <div
            style={{
              fontSize: '0.8rem',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              marginBottom: 'var(--spacing-xs)',
            }}
          >
            Moves
          </div>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 'var(--spacing-xs)',
            }}
          >
            {pokemon.moves.map((move) => (
              <span
                key={move}
                style={{
                  display: 'inline-block',
                  padding: '2px 8px',
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.7rem',
                  color: 'var(--color-text-primary)',
                }}
              >
                {move}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Fallback if no stats and no moves */}
      {!pokemon.stats && pokemon.moves.length === 0 && (
        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
          No detailed data available.
        </div>
      )}
    </div>
  );
}
