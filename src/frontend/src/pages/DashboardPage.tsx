import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameFile } from '../hooks/useGameFile';
import { usePokemon, usePartyPokemon, useUpdatePokemon, usePokemonInfo } from '../hooks/usePokemon';
import { useUpcomingRoutes } from '../hooks/useRoutes';
import { useUpcomingGyms, useGymProgress } from '../hooks/useGyms';
import { Nature, Status, type NatureValue, type StatusValue } from '../types/enums';
import type { Pokemon } from '../types/pokemon';

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { currentGameFile } = useGameFile();
  const gameFileId = currentGameFile?.id ?? null;

  const { data: partyPokemon = [], isLoading: isLoadingParty } = usePartyPokemon(gameFileId);
  const { data: allPokemon = [], isLoading: isLoadingAllPokemon } = usePokemon(gameFileId);
  const { data: gymProgress = [], isLoading: isLoadingGymProgress } = useGymProgress(gameFileId);
  const { data: upcomingRoutes = [], isLoading: isLoadingRoutes } = useUpcomingRoutes(gameFileId);
  const { data: upcomingGyms = [], isLoading: isLoadingGyms } = useUpcomingGyms(gameFileId);
  const updatePokemonMutation = useUpdatePokemon(gameFileId);

  const [editingPokemon, setEditingPokemon] = useState<Pokemon | null>(null);
  const [nickname, setNickname] = useState('');
  const [levelInput, setLevelInput] = useState('1');
  const [status, setStatus] = useState<StatusValue | ''>('');
  const [nature, setNature] = useState<NatureValue | ''>('');
  const [ability, setAbility] = useState('');
  const [error, setError] = useState<string | null>(null);

  const nextRoute = upcomingRoutes[0] ?? null;
  const nextGym = upcomingGyms[0] ?? null;

  const badgesCount = gymProgress.length;
  const pokedexCount = allPokemon.length;

  const level = parseInt(levelInput, 10) || 0;

  // Fetch base Pokemon info for available abilities when editing
  const { data: basePokemonInfo } = usePokemonInfo(editingPokemon?.poke_id ?? null);

  const openEditModal = (pokemon: Pokemon) => {
    setEditingPokemon(pokemon);
    setNickname(pokemon.nickname || '');
    setLevelInput(String(pokemon.level));
    setStatus((pokemon.status as StatusValue) || Status.PARTY);
    setNature((pokemon.nature as NatureValue) || '');
    setAbility(pokemon.ability || '');
    setError(null);
  };

  const closeEditModal = () => {
    setEditingPokemon(null);
    setError(null);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPokemon) return;

    if (level < 1 || level > 100) {
      setError('Level must be between 1 and 100');
      return;
    }

    try {
      setError(null);
      await updatePokemonMutation.mutateAsync({
        pokemonId: editingPokemon.id,
        update: {
          nickname: nickname.trim() || null,
          level,
          status: status || null,
          nature: nature || null,
          ability: ability.trim() || null,
        },
      });
      closeEditModal();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to update Pokemon');
    }
  };

  useEffect(() => {
    // If there is no selected game file, send the user back to game file selection
    // The GameFileContext will try to load from URL, so give it a moment
    if (!currentGameFile) {
      // Check if gameFileId is in URL - if so, wait a bit for context to load it
      const urlParams = new URLSearchParams(window.location.search);
      const gameFileIdFromUrl = urlParams.get('gameFileId');
      if (!gameFileIdFromUrl) {
        navigate('/game-files');
      }
    }
  }, [currentGameFile, navigate]);

  if (!currentGameFile) {
    return null;
  }

  const isLoading = isLoadingParty || isLoadingRoutes || isLoadingGyms;

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg-light)',
        padding: '40px 20px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '24px',
      }}
    >
      {/* Navigation Header */}
      <div
        style={{
          width: '100%',
          maxWidth: '900px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px',
        }}
      >
        <button
          onClick={() => navigate('/game-files')}
          className="btn btn-outline"
          style={{ fontSize: '14px', padding: '8px 16px' }}
        >
          {'<-'} Back to Game Files
        </button>
      </div>
      {/* Hero Card */}
      <div
        className="card"
        style={{
          maxWidth: '900px',
          width: '100%',
          padding: '28px',
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 3fr)',
          gap: '24px',
        }}
      >
        <div>
          <h1
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '1.8rem',
              marginBottom: '8px',
            }}
          >
            {currentGameFile.trainer_name}'s Run
          </h1>
          <p
            style={{
              color: 'var(--color-text-secondary)',
              fontSize: '0.9rem',
              marginBottom: '16px',
            }}
          >
            {currentGameFile.game_name}
          </p>

          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '16px',
              fontSize: '0.85rem',
              color: 'var(--color-text-primary)',
            }}
          >
            <div>
              <strong>Badges:</strong> {badgesCount}
            </div>
            <div>
              {/* Use plain ASCII to avoid encoding issues */}
              <strong>Pokedex:</strong> {pokedexCount}
            </div>
          </div>
        </div>

        <div
          style={{
            borderRadius: '12px',
            background: 'var(--color-bg-card)',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
          }}
        >
          <div
            style={{
              marginBottom: '4px',
              color: 'var(--color-text-primary)',
              fontWeight: 600,
              fontSize: '0.95rem',
            }}
          >
            Next Actions
          </div>

          {isLoading ? (
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>Loading...</p>
          ) : (
            <>
              {/* Next Routes button */}
              <button
                type="button"
                onClick={() => navigate(`/routes?gameFileId=${gameFileId}`)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg-light)',
                  color: 'var(--color-text-primary)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '2px',
                  fontSize: '0.9rem',
                  transition: 'all 150ms ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-pokemon-primary)';
                  e.currentTarget.style.borderColor = 'var(--color-pokemon-primary)';
                  e.currentTarget.style.color = 'white';
                  const spans = e.currentTarget.querySelectorAll('span');
                  spans.forEach((span) => {
                    (span as HTMLElement).style.color = 'rgba(255, 255, 255, 0.95)';
                  });
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-bg-light)';
                  e.currentTarget.style.borderColor = 'var(--color-border)';
                  e.currentTarget.style.color = 'var(--color-text-primary)';
                  const spans = e.currentTarget.querySelectorAll('span');
                  spans[0].style.color = '';
                  (spans[1] as HTMLElement).style.color = 'var(--color-text-secondary)';
                }}
              >
                <span style={{ fontWeight: 600 }}>Next Routes</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                  View upcoming routes & encounters
                </span>
              </button>

              {/* Next Gyms button */}
              <button
                type="button"
                onClick={() => navigate(`/gyms?gameFileId=${gameFileId}`)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg-light)',
                  color: 'var(--color-text-primary)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '2px',
                  fontSize: '0.9rem',
                  transition: 'all 150ms ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-pokemon-primary)';
                  e.currentTarget.style.borderColor = 'var(--color-pokemon-primary)';
                  e.currentTarget.style.color = 'white';
                  const spans = e.currentTarget.querySelectorAll('span');
                  spans.forEach((span) => {
                    (span as HTMLElement).style.color = 'rgba(255, 255, 255, 0.95)';
                  });
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-bg-light)';
                  e.currentTarget.style.borderColor = 'var(--color-border)';
                  e.currentTarget.style.color = 'var(--color-text-primary)';
                  const spans = e.currentTarget.querySelectorAll('span');
                  spans[0].style.color = '';
                  (spans[1] as HTMLElement).style.color = 'var(--color-text-secondary)';
                }}
              >
                <span style={{ fontWeight: 600 }}>Next Gyms</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                  {nextGym
                    ? `Gym ${nextGym.gym_number} - ${nextGym.trainer_name || 'Next Gym'}`
                    : 'No upcoming gyms'}
                </span>
              </button>

              {/* View Team button */}
              <button
                type="button"
                onClick={() => navigate('/team')}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-bg-light)',
                  color: 'var(--color-text-primary)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '2px',
                  fontSize: '0.9rem',
                  transition: 'all 150ms ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-pokemon-primary)';
                  e.currentTarget.style.borderColor = 'var(--color-pokemon-primary)';
                  e.currentTarget.style.color = 'white';
                  const spans = e.currentTarget.querySelectorAll('span');
                  spans.forEach((span) => {
                    (span as HTMLElement).style.color = 'rgba(255, 255, 255, 0.95)';
                  });
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-bg-light)';
                  e.currentTarget.style.borderColor = 'var(--color-border)';
                  e.currentTarget.style.color = 'var(--color-text-primary)';
                  const spans = e.currentTarget.querySelectorAll('span');
                  spans[0].style.color = '';
                  (spans[1] as HTMLElement).style.color = 'var(--color-text-secondary)';
                }}
              >
                <span style={{ fontWeight: 600 }}>View Team</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                  Manage party, levels, and more
                </span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Party Strip */}
      <div
        className="card"
        style={{
          maxWidth: '900px',
          width: '100%',
          padding: '20px 24px',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
          }}
        >
          <h2
            style={{
              color: 'var(--color-text-primary)',
              fontSize: '1.2rem',
              margin: 0,
            }}
          >
            Party
          </h2>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => navigate(`/team?gameFileId=${gameFileId}`)}
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            Manage Team
          </button>
        </div>

        {isLoadingParty ? (
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>Loading party...</p>
        ) : partyPokemon.length === 0 ? (
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
            {/* Use plain ASCII to avoid encoding issues */}
            No Pokemon in your party yet.
          </p>
        ) : (
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '12px',
              justifyContent: 'flex-start',
            }}
          >
            {partyPokemon.slice(0, 6).map((pokemon) => (
              <div
                key={pokemon.id}
                style={{
                  width: '120px',
                  borderRadius: '10px',
                  backgroundColor: 'var(--color-bg-card)',
                  border: '1px solid var(--color-border)',
                  padding: '8px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <div
                  style={{
                    width: '72px',
                    height: '72px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--color-bg-light)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden',
                  }}
                >
                  <img
                    src={pokemon.sprite}
                    alt={pokemon.nickname || pokemon.name}
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
                <div
                  style={{
                    fontSize: '0.85rem',
                    color: 'var(--color-text-primary)',
                    textAlign: 'center',
                    fontWeight: 600,
                  }}
                >
                  {pokemon.nickname || pokemon.name}
                </div>
                <div
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  Lv. {pokemon.level}
                </div>
                <button
                  type="button"
                  onClick={() => openEditModal(pokemon)}
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-bg-card)',
                    color: 'var(--color-text-primary)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 0,
                    marginTop: '4px',
                    fontSize: '14px',
                    transition: 'all 150ms ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-pokemon-blue)';
                    e.currentTarget.style.borderColor = 'var(--color-pokemon-blue)';
                    e.currentTarget.style.color = 'white';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-bg-card)';
                    e.currentTarget.style.borderColor = 'var(--color-border)';
                    e.currentTarget.style.color = 'var(--color-text-primary)';
                  }}
                  title="Edit Pokemon"
                >
                  ✏️
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editingPokemon && (
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
              maxWidth: '480px',
              padding: '24px',
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: '16px',
                color: 'var(--color-text-primary)',
              }}
            >
              Edit {editingPokemon.nickname || editingPokemon.name}
            </h2>
            <form onSubmit={handleSaveEdit}>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '16px',
                  marginBottom: '16px',
                }}
              >
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
                  />
                </div>

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
                    Level
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
                  />
                  {(level < 1 || level > 100) && levelInput !== '' && (
                    <p style={{ marginTop: '4px', fontSize: '0.75rem', color: '#F87171' }}>
                      Level must be between 1 and 100
                    </p>
                  )}
                </div>

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
                  {basePokemonInfo?.abilities && basePokemonInfo.abilities.length > 0 ? (
                    <select
                      id="ability"
                      className="input"
                      value={ability}
                      onChange={(e) => setAbility(e.target.value)}
                      style={{ width: '100%' }}
                    >
                      <option value="">None</option>
                      {basePokemonInfo.abilities.map((abil) => (
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
                  onClick={closeEditModal}
                  style={{ fontSize: '0.85rem', padding: '8px 14px' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ fontSize: '0.85rem', padding: '8px 14px' }}
                >
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
