import { useMemo, useState } from 'react';
import type {
  Trainer,
  TrainerMoveDetail,
  TrainerPokemon,
  TrainerPokemonStats,
} from '../types/trainer';
import {
  resolvePokemonSpriteUrl,
  resolveTrainerSpriteUrl,
} from '../utils/spriteResolvers';
import { PokemonTypeBadge } from './PokemonTypeBadge';
import { getTrainerMatchupSynergy, getTrainerMoveDetails } from '../services/trainerService';
import { useTheme } from '../contexts/ThemeContext';
const STAT_BAR_DISPLAY_MAX = 170;

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

function getStatBarPercent(value: number): number {
  return Math.min((value / STAT_BAR_DISPLAY_MAX) * 100, 100);
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
  const { theme } = useTheme();
  const isLightTheme = theme === 'light';
  const [isExpanded, setIsExpanded] = useState(false);
  const [matchupScore, setMatchupScore] = useState<number | null>(null);
  const [isLoadingMatchup, setIsLoadingMatchup] = useState(false);
  const [matchupError, setMatchupError] = useState<string | null>(null);
  const [moveDetailsByName, setMoveDetailsByName] = useState<Record<string, TrainerMoveDetail>>({});
  const [isLoadingMoves, setIsLoadingMoves] = useState(false);
  const [movesError, setMovesError] = useState<string | null>(null);
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

  const allMoveNames = useMemo(() => {
    return Array.from(
      new Set(
        trainer.pokemon.flatMap((pokemon) => pokemon.moves ?? []).map((move) => move?.trim()).filter(Boolean) as string[]
      )
    );
  }, [trainer.pokemon]);

  const loadMoveDetails = async () => {
    if (isLoadingMoves || allMoveNames.length === 0) return;

    const missing = allMoveNames.filter((name) => !moveDetailsByName[name]);
    if (missing.length === 0) return;

    setIsLoadingMoves(true);
    setMovesError(null);
    try {
      const details = await getTrainerMoveDetails(missing);
      setMoveDetailsByName((prev) => {
        const next = { ...prev };
        for (const detail of details) {
          next[detail.requested_name] = detail;
        }
        return next;
      });
    } catch {
      setMovesError('Could not load move details.');
    } finally {
      setIsLoadingMoves(false);
    }
  };

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

  const handleToggleExpanded = () => {
    const next = !isExpanded;
    setIsExpanded(next);
    if (next) {
      void loadMoveDetails();
    }
  };

  return (
    <div
      style={{
        backgroundColor: isLightTheme ? '#F8FAFC' : '#111827',
        border: highlight ? '2px solid #6366F1' : '2px solid #374151',
        borderRadius: 'var(--radius-lg)',
        boxShadow: highlight
          ? '0 10px 24px rgba(79,70,229,0.35)'
          : isLightTheme
            ? '0 8px 20px rgba(15,23,42,0.12)'
            : '0 8px 20px rgba(0,0,0,0.2)',
        overflow: 'hidden',
      }}
    >
      <button
        type="button"
        onClick={handleToggleExpanded}
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
          isLightTheme={isLightTheme}
        />

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: '1rem', fontWeight: 700, color: isLightTheme ? '#0F172A' : '#F9FAFB' }}>
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
          {trainer.location && (
            <div style={{ fontSize: '0.85rem', color: isLightTheme ? '#475569' : '#CBD5E1' }}>
              {trainer.location}
            </div>
          )}
          {trainer.importance_reason && (
            <div style={{ fontSize: '0.8rem', color: isLightTheme ? '#64748B' : '#94A3B8', marginTop: 2 }}>
              {formatLabel(trainer.importance_reason)}
            </div>
          )}
        </div>

        <span style={{ color: isLightTheme ? '#64748B' : '#94A3B8', fontWeight: 700 }}>
          {isExpanded ? '▲' : '▼'}
        </span>
      </button>

      {isExpanded && (
        <div
          style={{
            borderTop: '1px solid #334155',
            padding: '14px 16px 16px 16px',
            background: isLightTheme
              ? 'radial-gradient(circle at top left, rgba(79,70,229,0.12), rgba(241,245,249,1) 62%)'
              : 'radial-gradient(circle at top left, rgba(79,70,229,0.18), rgba(17,24,39,1) 55%)',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}
        >
          <div
            style={{
              border: '1px solid #334155',
              borderRadius: 'var(--radius-md)',
              backgroundColor: isLightTheme ? 'rgba(255,255,255,0.9)' : 'rgba(15,23,42,0.85)',
              padding: '10px 12px',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '8px 12px',
            }}
          >
            {metaRows.map((row) => (
              <div key={row.label} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <span style={{ fontSize: '0.7rem', color: isLightTheme ? '#64748B' : '#94A3B8', fontWeight: 700 }}>
                  {row.label}
                </span>
                <span style={{ fontSize: '0.82rem', color: isLightTheme ? '#0F172A' : '#F8FAFC' }}>
                  {String(row.value)}
                </span>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {trainer.pokemon.map((pokemon, index) => (
              <PokemonBattlePanel
                key={`${pokemon.name}-${index}`}
                pokemon={pokemon}
                moveDetailsByName={moveDetailsByName}
                isLightTheme={isLightTheme}
              />
            ))}
          </div>

          {movesError && (
            <div style={{ marginTop: 4, fontSize: '0.75rem', color: '#FCA5A5' }}>{movesError}</div>
          )}

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

function PokemonBattlePanel({
  pokemon,
  moveDetailsByName,
  isLightTheme,
}: {
  pokemon: TrainerPokemon;
  moveDetailsByName: Record<string, TrainerMoveDetail>;
  isLightTheme: boolean;
}) {
  const spriteUrl = resolvePokemonSpriteUrl(pokemon.name, pokemon.poke_id);
  const moveGridTemplateColumns =
    pokemon.moves.length === 1
      ? 'minmax(0, 1fr)'
      : 'repeat(2, minmax(0, 1fr))';
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
        backgroundColor: isLightTheme ? 'rgba(248,250,252,0.96)' : 'rgba(3,7,18,0.88)',
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
            backgroundColor: isLightTheme ? 'rgba(255,255,255,0.96)' : 'rgba(17,24,39,0.9)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <SpriteFrame
              src={spriteUrl}
              alt={pokemon.name}
              width={52}
              height={52}
              fallbackLabel="?"
              isLightTheme={isLightTheme}
            />
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
                <div style={{ color: isLightTheme ? '#0F172A' : '#F8FAFC', fontWeight: 700, fontSize: '1rem' }}>{pokemon.name}</div>
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
              <div style={{ color: isLightTheme ? '#1D4ED8' : '#93C5FD', fontSize: '0.8rem', fontWeight: 600 }}>Lv. {pokemon.level}</div>
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
            <InfoItem label="Ability" value={pokemon.ability} isLightTheme={isLightTheme} />
            <InfoItem label="Item" value={pokemon.item} blankWhenNull isLightTheme={isLightTheme} />
            <InfoItem label="Nature" value={pokemon.nature} isLightTheme={isLightTheme} />
          </div>

          {pokemon.moves.length > 0 && (
            <div>
              <div
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  color: isLightTheme ? '#64748B' : '#94A3B8',
                  marginBottom: 6,
                }}
              >
                Moves
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: moveGridTemplateColumns,
                  gap: 8,
                  width: '100%',
                  minWidth: 0,
                }}
              >
                {pokemon.moves.map((move) => (
                  <MoveCard
                    key={move}
                    moveName={move}
                    detail={moveDetailsByName[move]}
                    isLightTheme={isLightTheme}
                  />
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
            backgroundColor: isLightTheme ? 'rgba(255,255,255,0.92)' : 'rgba(2,6,23,0.95)',
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
                  color: isLightTheme ? '#64748B' : '#94A3B8',
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
                      <span style={{ fontSize: '0.72rem', color: isLightTheme ? '#64748B' : '#94A3B8', textAlign: 'right' }}>
                        {label}
                      </span>
                      <div
                        style={{
                          height: 9,
                          borderRadius: 999,
                          overflow: 'hidden',
                          backgroundColor: isLightTheme ? '#E2E8F0' : '#1E293B',
                        }}
                      >
                        <div
                          style={{
                            width: `${getStatBarPercent(value)}%`,
                            height: '100%',
                            backgroundColor: getStatBarColor(value),
                          }}
                        />
                      </div>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          color: isLightTheme ? '#0F172A' : '#F8FAFC',
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

          <StatDictRow label="IVs" stats={pokemon.ivs} isLightTheme={isLightTheme} />
          <StatDictRow label="DVs" stats={pokemon.dvs} isLightTheme={isLightTheme} />
          <StatDictRow label="EVs" stats={pokemon.evs} isLightTheme={isLightTheme} />
        </div>
      </div>

      {extraFields.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: isLightTheme ? '#64748B' : '#94A3B8', marginBottom: 6 }}>
            Other Stored Data
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 8 }}>
            {extraFields.map(([key, value]) => (
              <InfoItem key={key} label={formatLabel(key)} value={formatValue(value)} isLightTheme={isLightTheme} />
            ))}
          </div>
        </div>
      )}

    </div>
  );
}

function MoveCard({
  moveName,
  detail,
  isLightTheme,
}: {
  moveName: string;
  detail?: TrainerMoveDetail;
  isLightTheme: boolean;
}) {
  const [showDescription, setShowDescription] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const typeName = detail?.type_name ?? 'unknown';
  const typeBorderColor = `var(--color-type-${typeName})`;
  const powerLabel = detail?.power != null ? String(detail.power) : '-';
  const ppLabel = detail?.pp != null ? String(detail.pp) : '-';
  const damageClassLabel = detail?.damage_class?.trim().toLowerCase() || '-';
  const description = detail?.effect || 'No description available.';
  const showTooltip = isHovered || showDescription;

  return (
    <button
      type="button"
      onPointerEnter={() => setIsHovered(true)}
      onPointerLeave={() => setIsHovered(false)}
      onPointerUp={(event) => {
        if (event.pointerType === 'touch') {
          setShowDescription((prev) => !prev);
        }
      }}
      style={{
        position: 'relative',
        width: '100%',
        maxWidth: '100%',
        minWidth: 0,
        boxSizing: 'border-box',
        textAlign: 'left',
        border: `2px solid ${typeBorderColor}`,
        borderRadius: '8px',
        backgroundColor: isLightTheme ? 'rgba(255,255,255,0.95)' : 'rgba(15,23,42,0.9)',
        padding: '8px',
        color: isLightTheme ? '#0F172A' : '#E2E8F0',
        cursor: 'pointer',
        overflow: 'visible',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <span
          style={{
            fontSize: '0.78rem',
            fontWeight: 700,
            color: isLightTheme ? '#0F172A' : '#F8FAFC',
            minWidth: 0,
            overflowWrap: 'anywhere',
          }}
        >
          {moveName}
        </span>
        <PokemonTypeBadge
          type={typeName}
          style={{
            fontSize: '0.52rem',
            padding: '2px 6px',
            borderRadius: '4px',
            flexShrink: 0,
            maxWidth: '100%',
          }}
        />
      </div>

      <div
        style={{
          marginTop: 6,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr auto',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <span style={{ fontSize: '0.68rem', color: isLightTheme ? '#1D4ED8' : '#93C5FD' }}>PP {ppLabel}</span>
        <span style={{ fontSize: '0.68rem', color: isLightTheme ? '#B45309' : '#FCD34D' }}>PWR {powerLabel}</span>
        <span style={{ fontSize: '0.62rem', color: '#94A3B8', textTransform: 'lowercase' }}>
          {damageClassLabel}
        </span>
      </div>

      {showTooltip && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 'calc(100% + 6px)',
            zIndex: 50,
            padding: '8px 10px',
            border: '1px solid #64748B',
            borderRadius: '8px',
            backgroundColor: isLightTheme ? '#FFFFFF' : '#0B1220',
            boxShadow: '0 8px 20px rgba(0,0,0,0.35)',
            fontSize: '0.7rem',
            lineHeight: 1.4,
            color: isLightTheme ? '#334155' : '#CBD5E1',
            pointerEvents: 'none',
          }}
        >
          {description}
        </div>
      )}
    </button>
  );
}

function StatDictRow({
  label,
  stats,
  isLightTheme,
}: {
  label: string;
  stats?: Record<string, number> | null;
  isLightTheme: boolean;
}) {
  if (!stats || Object.keys(stats).length === 0) return null;
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: isLightTheme ? '#64748B' : '#94A3B8', marginBottom: 6 }}>
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
              color: isLightTheme ? '#0F172A' : '#E2E8F0',
              backgroundColor: isLightTheme ? 'rgba(226,232,240,0.9)' : 'rgba(30,41,59,0.8)',
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
  isLightTheme = false,
}: {
  label: string;
  value: unknown;
  blankWhenNull?: boolean;
  isLightTheme?: boolean;
}) {
  const displayValue =
    blankWhenNull && (value == null || value === '') ? '' : formatValue(value);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <span style={{ fontSize: '0.7rem', color: isLightTheme ? '#64748B' : '#94A3B8', fontWeight: 700 }}>{label}</span>
      <span style={{ fontSize: '0.8rem', color: isLightTheme ? '#0F172A' : '#F1F5F9' }}>{displayValue}</span>
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
  isLightTheme = false,
}: {
  src: string | null;
  alt: string;
  width: number;
  height: number;
  fallbackLabel: string;
  rounded?: boolean;
  isLightTheme?: boolean;
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
          backgroundColor: isLightTheme ? 'rgba(226,232,240,0.9)' : 'rgba(15,23,42,0.75)',
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
        backgroundColor: isLightTheme ? '#E2E8F0' : '#1E293B',
        color: isLightTheme ? '#64748B' : '#94A3B8',
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
