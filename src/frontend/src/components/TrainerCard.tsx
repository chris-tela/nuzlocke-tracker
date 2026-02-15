import { useMemo, useState } from 'react';
import type { Trainer, TrainerPokemon, TrainerPokemonStats } from '../types/trainer';
import { resolvePokemonSpriteUrl, resolveTrainerSpriteUrl } from '../utils/spriteResolvers';
import { PokemonTypeBadge } from './PokemonTypeBadge';
import { getTrainerMatchupSynergy } from '../services/trainerService';
const STAT_MAX = 255;

const IMPORTANCE_BADGES: Record<string, { color: string; label: string }> = {
  rival: { color: '#E74C3C', label: 'Rival' },
  gym_leader: { color: '#3498DB', label: 'Gym Leader' },
  elite_four: { color: '#9B59B6', label: 'Elite Four' },
  champion: { color: '#F39C12', label: 'Champion' },
  evil_team_leader: { color: '#2C3E50', label: 'Evil Team' },
  level_outlier: { color: '#E67E22', label: 'Level Spike' },
};

const STAT_LABELS: { key: keyof TrainerPokemonStats; label: string }[] = [
  { key: 'hp', label: 'HP' },
  { key: 'attack', label: 'Atk' },
  { key: 'defense', label: 'Def' },
  { key: 'special_attack', label: 'SpA' },
  { key: 'special_defense', label: 'SpD' },
  { key: 'speed', label: 'Spe' },
];

const KNOWN_POKEMON_FIELDS = new Set([
  'name',
  'poke_id',
  'index',
  'types',
  'level',
  'ability',
  'item',
  'nature',
  'moves',
  'stats',
  'ivs',
  'dvs',
  'evs',
]);

interface TrainerCardProps {
  trainer: Trainer;
  highlight?: boolean;
  gameFileId?: number | null;
  canEvaluateMatchup?: boolean;
}

function getStatBarColor(value: number): string {
  if (value >= 140) return '#22C55E';
  if (value >= 100) return '#84CC16';
  if (value >= 70) return '#FACC15';
  if (value >= 40) return '#F59E0B';
  return '#EF4444';
}

function formatLabel(raw: string): string {
  return raw
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatValue(value: unknown): string {
  if (value == null) return 'N/A';
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export function TrainerCard({
  trainer,
  highlight,
  gameFileId = null,
  canEvaluateMatchup = false,
}: TrainerCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [matchupScore, setMatchupScore] = useState<number | null>(null);
  const [isLoadingMatchup, setIsLoadingMatchup] = useState(false);
  const [matchupError, setMatchupError] = useState<string | null>(null);
  const badge = trainer.importance_reason ? IMPORTANCE_BADGES[trainer.importance_reason] : null;
  const trainerSpriteUrl = resolveTrainerSpriteUrl(trainer.trainer_image);

  const metaRows = useMemo(
    () => [
      { label: 'Generation', value: trainer.generation },
      { label: 'Starter Filter', value: trainer.starter_filter ?? 'N/A' },
      { label: 'Important', value: trainer.is_important ? 'Yes' : 'No' },
      { label: 'Game(s)', value: trainer.game_names.join(', ') },
    ],
    [trainer]
  );

  const handleMatchupClick = async () => {
    if (gameFileId == null || !canEvaluateMatchup || isLoadingMatchup) return;

    setIsLoadingMatchup(true);
    setMatchupError(null);
    try {
      const response = await getTrainerMatchupSynergy(trainer.id, gameFileId);
      setMatchupScore(response.score_percent);
    } catch {
      setMatchupError('Could not calculate matchup right now.');
    } finally {
      setIsLoadingMatchup(false);
    }
  };

  return (
    <div
      style={{
        backgroundColor: '#111827',
        border: highlight ? '2px solid #6366F1' : '2px solid #374151',
        borderRadius: 'var(--radius-lg)',
        boxShadow: highlight ? '0 10px 24px rgba(79,70,229,0.35)' : '0 8px 20px rgba(0,0,0,0.2)',
        overflow: 'hidden',
      }}
    >
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        aria-expanded={isExpanded}
        style={{
          width: '100%',
          padding: '14px 16px',
          border: 'none',
          background: 'transparent',
          textAlign: 'left',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          cursor: 'pointer',
        }}
      >
        <SpriteFrame
          src={trainerSpriteUrl}
          alt={trainer.trainer_name}
          width={56}
          height={56}
          fallbackLabel="?"
          rounded
        />

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: '1rem', fontWeight: 700, color: '#F9FAFB' }}>
              {trainer.trainer_name}
            </span>
            {badge && (
              <span
                style={{
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.4px',
                  color: '#FFF',
                  backgroundColor: badge.color,
                }}
              >
                {badge.label}
              </span>
            )}
          </div>
          <div style={{ fontSize: '0.85rem', color: '#CBD5E1' }}>
            {trainer.location || 'Unknown location'}
          </div>
          {trainer.importance_reason && (
            <div style={{ fontSize: '0.8rem', color: '#94A3B8', marginTop: 2 }}>
              Reason: {formatLabel(trainer.importance_reason)}
            </div>
          )}
        </div>

        <span style={{ color: '#94A3B8', fontWeight: 700 }}>
          {isExpanded ? '▲' : '▼'}
        </span>
      </button>

      {isExpanded && (
        <div
          style={{
            borderTop: '1px solid #334155',
            padding: '14px 16px 16px 16px',
            background:
              'radial-gradient(circle at top left, rgba(79,70,229,0.18), rgba(17,24,39,1) 55%)',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}
        >
          <div
            style={{
              border: '1px solid #334155',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(15,23,42,0.85)',
              padding: '10px 12px',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '8px 12px',
            }}
          >
            {metaRows.map((row) => (
              <div key={row.label} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <span style={{ fontSize: '0.7rem', color: '#94A3B8', fontWeight: 700 }}>
                  {row.label}
                </span>
                <span style={{ fontSize: '0.82rem', color: '#F8FAFC' }}>
                  {String(row.value)}
                </span>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {trainer.pokemon.map((pokemon, index) => (
              <PokemonBattlePanel key={`${pokemon.name}-${index}`} pokemon={pokemon} />
            ))}
          </div>

          <div style={{ marginTop: 6, borderTop: '1px solid #334155', paddingTop: 10 }}>
            <button
              type="button"
              className={canEvaluateMatchup ? 'btn btn-outline' : 'btn'}
              onClick={handleMatchupClick}
              disabled={!canEvaluateMatchup || isLoadingMatchup}
              style={{
                width: '100%',
                fontSize: '0.8rem',
                padding: '8px 12px',
                borderColor: '#60A5FA',
                color: canEvaluateMatchup ? '#60A5FA' : '#64748B',
              }}
            >
              {isLoadingMatchup ? 'CALCULATING...' : 'SEE MATCHUP SYNERGY'}
            </button>

            {!canEvaluateMatchup && (
              <div style={{ marginTop: 6, fontSize: '0.72rem', color: '#94A3B8' }}>
                Add PARTY Pokemon to evaluate synergy.
              </div>
            )}

            {matchupError && (
              <div style={{ marginTop: 6, fontSize: '0.75rem', color: '#FCA5A5' }}>{matchupError}</div>
            )}

            {matchupScore != null && !matchupError && (
              <div style={{ marginTop: 8, fontSize: '0.8rem', color: '#E2E8F0' }}>
                Matchup score: <strong style={{ color: '#F8FAFC' }}>{matchupScore}%</strong>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function PokemonBattlePanel({ pokemon }: { pokemon: TrainerPokemon }) {
  const spriteUrl = resolvePokemonSpriteUrl(pokemon.name, pokemon.poke_id);
  const extraFields = Object.entries(pokemon).filter(([key, value]) => {
    if (KNOWN_POKEMON_FIELDS.has(key)) return false;
    if (value == null) return false;
    if (Array.isArray(value)) return value.length > 0;
    return true;
  });

  return (
    <div
      style={{
        border: '1px solid #374151',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'rgba(3,7,18,0.88)',
        padding: '12px',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '12px',
          alignItems: 'stretch',
        }}
      >
        <div
          style={{
            border: '1px solid #334155',
            borderRadius: 'var(--radius-sm)',
            padding: '10px',
            backgroundColor: 'rgba(17,24,39,0.9)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <SpriteFrame src={spriteUrl} alt={pokemon.name} width={52} height={52} fallbackLabel="?" />
            <div style={{ minWidth: 0, flex: 1 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 8,
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ color: '#F8FAFC', fontWeight: 700, fontSize: '1rem' }}>{pokemon.name}</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                  {(pokemon.types ?? []).map((type) => (
                    <PokemonTypeBadge
                      key={`${pokemon.name}-${type}`}
                      type={type}
                      style={{ fontSize: '0.65rem', padding: '3px 8px', borderRadius: '5px' }}
                    />
                  ))}
                </div>
              </div>
              <div style={{ color: '#93C5FD', fontSize: '0.8rem', fontWeight: 600 }}>Lv. {pokemon.level}</div>
            </div>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
              gap: '6px 10px',
              marginBottom: 10,
            }}
          >
            <InfoItem label="Ability" value={pokemon.ability} />
            <InfoItem label="Item" value={pokemon.item} blankWhenNull />
            <InfoItem label="Nature" value={pokemon.nature} />
          </div>

          {pokemon.moves.length > 0 && (
            <div>
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  color: '#94A3B8',
                  marginBottom: 6,
                }}
              >
                Moves
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {pokemon.moves.map((move) => (
                  <span
                    key={move}
                    style={{
                      padding: '3px 8px',
                      borderRadius: '999px',
                      fontSize: '0.72rem',
                      border: '1px solid #475569',
                      backgroundColor: 'rgba(30,41,59,0.8)',
                      color: '#E2E8F0',
                    }}
                  >
                    {move}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div
          style={{
            border: '1px solid #334155',
            borderRadius: 'var(--radius-sm)',
            padding: '10px',
            backgroundColor: 'rgba(2,6,23,0.95)',
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
          }}
        >
          {pokemon.stats && (
            <div>
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  color: '#94A3B8',
                  marginBottom: 6,
                }}
              >
                Battle Stats
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                {STAT_LABELS.map(({ key, label }) => {
                  const value = pokemon.stats![key];
                  return (
                    <div
                      key={key}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '34px 1fr 34px',
                        gap: 8,
                        alignItems: 'center',
                      }}
                    >
                      <span style={{ fontSize: '0.72rem', color: '#94A3B8', textAlign: 'right' }}>
                        {label}
                      </span>
                      <div
                        style={{
                          height: 9,
                          borderRadius: 999,
                          overflow: 'hidden',
                          backgroundColor: '#1E293B',
                        }}
                      >
                        <div
                          style={{
                            width: `${Math.min((value / STAT_MAX) * 100, 100)}%`,
                            height: '100%',
                            backgroundColor: getStatBarColor(value),
                          }}
                        />
                      </div>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          color: '#F8FAFC',
                          textAlign: 'right',
                          fontWeight: 700,
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

          <StatDictRow label="IVs" stats={pokemon.ivs} />
          <StatDictRow label="DVs" stats={pokemon.dvs} />
          <StatDictRow label="EVs" stats={pokemon.evs} />
        </div>
      </div>

      {extraFields.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94A3B8', marginBottom: 6 }}>
            Other Stored Data
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 8 }}>
            {extraFields.map(([key, value]) => (
              <InfoItem key={key} label={formatLabel(key)} value={formatValue(value)} />
            ))}
          </div>
        </div>
      )}

    </div>
  );
}

function StatDictRow({ label, stats }: { label: string; stats?: Record<string, number> | null }) {
  if (!stats || Object.keys(stats).length === 0) return null;
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#94A3B8', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {Object.entries(stats).map(([key, value]) => (
          <span
            key={key}
            style={{
              padding: '3px 8px',
              border: '1px solid #475569',
              borderRadius: '999px',
              fontSize: '0.72rem',
              color: '#E2E8F0',
              backgroundColor: 'rgba(30,41,59,0.8)',
            }}
          >
            {key.toUpperCase()}: {value}
          </span>
        ))}
      </div>
    </div>
  );
}

function InfoItem({
  label,
  value,
  blankWhenNull = false,
}: {
  label: string;
  value: unknown;
  blankWhenNull?: boolean;
}) {
  const displayValue =
    blankWhenNull && (value == null || value === '') ? '' : formatValue(value);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <span style={{ fontSize: '0.7rem', color: '#94A3B8', fontWeight: 700 }}>{label}</span>
      <span style={{ fontSize: '0.8rem', color: '#F1F5F9' }}>{displayValue}</span>
    </div>
  );
}

function SpriteFrame({
  src,
  alt,
  width,
  height,
  fallbackLabel,
  rounded,
}: {
  src: string | null;
  alt: string;
  width: number;
  height: number;
  fallbackLabel: string;
  rounded?: boolean;
}) {
  const [imgError, setImgError] = useState(false);
  const showImage = !!src && !imgError;

  if (showImage) {
    return (
      <img
        src={src}
        alt={alt}
        onError={() => setImgError(true)}
        style={{
          width,
          height,
          objectFit: 'contain',
          imageRendering: 'pixelated',
          borderRadius: rounded ? 8 : 'var(--radius-sm)',
          border: '1px solid #475569',
          backgroundColor: 'rgba(15,23,42,0.75)',
          flexShrink: 0,
        }}
      />
    );
  }

  return (
    <div
      style={{
        width,
        height,
        borderRadius: rounded ? 8 : 'var(--radius-sm)',
        backgroundColor: '#1E293B',
        color: '#94A3B8',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 700,
        border: '1px solid #475569',
        flexShrink: 0,
      }}
    >
      {fallbackLabel}
    </div>
  );
}
