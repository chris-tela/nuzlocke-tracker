import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameFile } from '../hooks/useGameFile';
import { usePartyPokemon, useStoredPokemon, useFaintedPokemon, useUpdatePokemon, useEvolvePokemon, useSwapPokemon, useRemovePokemon, usePokemonInfo, usePokemonInfoByName, useTeamSynergy } from '../hooks/usePokemon';
import { PokemonTypeBadge } from '../components/PokemonTypeBadge';
import { TeamSynergySidebar } from '../components/TeamSynergySidebar';
import { Nature, Status, type NatureValue, type StatusValue } from '../types/enums';
import type { Pokemon } from '../types/pokemon';
import { getPokemonSpritePath } from '../utils/pokemonSprites';

export const TeamPage = () => {
  const navigate = useNavigate();
  const { currentGameFile } = useGameFile();
  const gameFileId = currentGameFile?.id ?? null;

  const { data: partyPokemon = [], isLoading: isLoadingParty } = usePartyPokemon(gameFileId);
  const { data: storedPokemon = [], isLoading: isLoadingStored } = useStoredPokemon(gameFileId);
  const { data: faintedPokemon = [], isLoading: isLoadingFainted } = useFaintedPokemon(gameFileId);
  const { data: teamSynergy, isLoading: isLoadingSynergy, isError: isErrorSynergy } = useTeamSynergy(gameFileId);
  const updatePokemonMutation = useUpdatePokemon(gameFileId);
  const evolvePokemonMutation = useEvolvePokemon(gameFileId);
  const swapPokemonMutation = useSwapPokemon(gameFileId);
  const removePokemonMutation = useRemovePokemon(gameFileId);

  const isLoading = isLoadingParty || isLoadingStored || isLoadingFainted;

  const [editingPokemon, setEditingPokemon] = useState<Pokemon | null>(null);
  const [evolvingPokemon, setEvolvingPokemon] = useState<Pokemon | null>(null);
  const [selectedEvolution, setSelectedEvolution] = useState<string | null>(null);
  const [faintingPokemon, setFaintingPokemon] = useState<Pokemon | null>(null);
  const [deletingPokemon, setDeletingPokemon] = useState<Pokemon | null>(null);
  const [swappingPokemon, setSwappingPokemon] = useState<Pokemon | null>(null);
  const [selectedPartyPokemonForSwap, setSelectedPartyPokemonForSwap] = useState<number | null>(null);
  const [nickname, setNickname] = useState('');
  const [levelInput, setLevelInput] = useState('1');
  const [status, setStatus] = useState<StatusValue | ''>('');
  const [nature, setNature] = useState<NatureValue | ''>('');
  const [ability, setAbility] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Fetch base Pokemon info for available abilities when editing
  const { data: basePokemonInfo } = usePokemonInfo(editingPokemon?.poke_id ?? null);

  const level = parseInt(levelInput, 10) || 0;

  // Check if Pokemon can evolve based on level requirements and evolution conditions
  // Returns true if at least one evolution option is available
  const canEvolve = (pokemon: Pokemon): boolean => {
    if (!pokemon.evolution_data || pokemon.evolution_data.length === 0) {
      return false;
    }

    // Check each possible evolution
    for (const evolution of pokemon.evolution_data) {
      const evolutionDetails = evolution.evolves_to?.evolution_details;
      
      if (!evolutionDetails || evolutionDetails.length === 0) {
        // No evolution details means it can evolve
        return true;
      }

      // Check each evolution detail
      for (const detail of evolutionDetails) {
        const minLevel = detail.min_level as number | null | undefined;
        const trigger = detail.trigger as { name?: string } | null | undefined;
        const triggerName = trigger?.name;

        // If min_level is null/undefined, it's a non-level evolution (item, trade, etc.) - can evolve
        if (minLevel === null || minLevel === undefined) {
          return true;
        }

        // If it's a level-up evolution, check if Pokemon meets the level requirement
        if (triggerName === 'level-up' && minLevel !== null && minLevel !== undefined) {
          if (pokemon.level >= minLevel) {
            return true;
          }
        }
      }
    }

    return false;
  };

  if (!currentGameFile || !gameFileId) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'var(--color-bg-light)',
        }}
      >
        <div className="card" style={{ padding: '32px', textAlign: 'center' }}>
          <p style={{ marginBottom: '16px', color: 'var(--color-text-secondary)' }}>
            No game file selected.
          </p>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/game-files')}
          >
            Back to Game Files
          </button>
        </div>
      </div>
    );
  }

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

  const handleSetStatus = async (pokemon: Pokemon, newStatus: StatusValue) => {
    try {
      await updatePokemonMutation.mutateAsync({
        pokemonId: pokemon.id,
        update: { status: newStatus },
      });
    } catch (err: any) {
      // Optionally surface a toast or inline error later
      console.error('Failed to update status', err);
    }
  };

  const isPartyFull = partyPokemon.length >= 6;

  const openSwapModal = (pokemon: Pokemon) => {
    setSwappingPokemon(pokemon);
    setSelectedPartyPokemonForSwap(null);
    setError(null);
  };

  const closeSwapModal = () => {
    setSwappingPokemon(null);
    setSelectedPartyPokemonForSwap(null);
    setError(null);
  };

  const handleConfirmSwap = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!swappingPokemon || !selectedPartyPokemonForSwap) {
      setError('Please select a Pokemon to swap with');
      return;
    }

    try {
      setError(null);
      await swapPokemonMutation.mutateAsync({
        pokemonPartyId: selectedPartyPokemonForSwap,
        pokemonSwitchId: swappingPokemon.id,
      });
      closeSwapModal();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to swap Pokemon');
    }
  };

  const openFaintConfirmation = (pokemon: Pokemon) => {
    setFaintingPokemon(pokemon);
    setError(null);
  };

  const closeFaintConfirmation = () => {
    setFaintingPokemon(null);
    setError(null);
  };

  const handleConfirmFaint = async () => {
    if (!faintingPokemon) return;

    try {
      setError(null);
      await updatePokemonMutation.mutateAsync({
        pokemonId: faintingPokemon.id,
        update: { status: Status.FAINTED },
      });
      closeFaintConfirmation();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to mark Pokemon as fainted');
    }
  };

  const openDeleteConfirmation = (pokemon: Pokemon) => {
    setDeletingPokemon(pokemon);
    setError(null);
  };

  const closeDeleteConfirmation = () => {
    setDeletingPokemon(null);
    setError(null);
  };

  const handleConfirmDelete = async () => {
    if (!deletingPokemon) return;

    try {
      setError(null);
      await removePokemonMutation.mutateAsync(deletingPokemon.id);
      closeDeleteConfirmation();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to delete Pokemon');
    }
  };

  // Helper function to get all evolution options with their requirements
  const getEvolutionOptions = (pokemon: Pokemon) => {
    const evoData = pokemon.evolution_data || [];
    const options: Array<{
      species: string;
      minLevel: number | null;
      canEvolve: boolean;
      reason?: string;
    }> = [];

    for (const evolution of evoData) {
      const species = evolution.evolves_to?.species;
      if (!species) continue;

      const details = evolution.evolves_to?.evolution_details || [];
      let minLevel: number | null = null;
      let canEvolve = false;
      let reason: string | undefined;

      // Check all evolution details to find level requirements
      for (const detail of details) {
        const trigger = detail.trigger as { name?: string } | null | undefined;
        const triggerName = trigger?.name;
        const levelReq = detail.min_level as number | null | undefined;

        if (triggerName === 'level-up' && levelReq !== null && levelReq !== undefined) {
          minLevel = levelReq;
          if (pokemon.level >= levelReq) {
            canEvolve = true;
          } else {
            reason = `Requires level ${levelReq}`;
          }
        } else if (levelReq === null || levelReq === undefined) {
          // Non-level evolution (item, trade, etc.)
          canEvolve = true;
        }
      }

      // If no level requirement found, it's evolvable
      if (minLevel === null && details.length > 0) {
        canEvolve = true;
      }

      options.push({ species, minLevel, canEvolve, reason });
    }

    return options;
  };

  const openEvolveModal = (pokemon: Pokemon) => {
    setEvolvingPokemon(pokemon);
    setSelectedEvolution(null);
    setError(null);
  };

  const closeEvolveModal = () => {
    setEvolvingPokemon(null);
    setSelectedEvolution(null);
    setError(null);
  };

  const handleConfirmEvolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!evolvingPokemon || !selectedEvolution) {
      setError('Please select an evolution option');
      return;
    }

    try {
      setError(null);
      await evolvePokemonMutation.mutateAsync({
        pokemonId: evolvingPokemon.id,
        evolvedPokemonName: selectedEvolution,
      });
      closeEvolveModal();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to evolve Pokemon');
    }
  };

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
      <div
        style={{
          width: '100%',
          maxWidth: '1300px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h1
          style={{
            color: 'var(--color-text-primary)',
            fontSize: '1.8rem',
            margin: 0,
          }}
        >
          Team
        </h1>
        <button
          className="btn btn-outline"
          onClick={() => navigate(`/dashboard?gameFileId=${gameFileId}`)}
          style={{ fontSize: '0.9rem', padding: '8px 16px' }}
        >
          {'<-'} Back to Dashboard
        </button>
      </div>

      <div
        style={{
          width: '100%',
          maxWidth: '1300px',
          display: 'flex',
          gap: '24px',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ flex: '1 1 620px', minWidth: 0, maxWidth: '900px' }}>
          <div style={{ width: '100%' }}>
        <h2
          style={{
            color: 'var(--color-text-primary)',
            fontSize: '1.5rem',
            marginBottom: '16px',
            fontWeight: 600,
          }}
        >
          Party
        </h2>
        {isLoading ? (
          <p style={{ color: 'var(--color-text-secondary)' }}>Loading team...</p>
        ) : partyPokemon.length === 0 ? (
          <p style={{ color: 'var(--color-text-secondary)' }}>No Pokemon in your party yet.</p>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
            }}
          >
            {partyPokemon.map((pokemon) => (
              <div
                key={pokemon.id}
                style={{
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  border: '1px solid var(--color-border)',
                  borderRadius: '12px',
                  backgroundColor: 'var(--color-bg-card)',
                  position: 'relative',
                }}
              >
                <button
                  type="button"
                  onClick={() => openDeleteConfirmation(pokemon)}
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    border: '1px solid #dc2626',
                    backgroundColor: 'transparent',
                    color: '#dc2626',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 0,
                    lineHeight: 1,
                    transition: 'all 150ms ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#dc2626';
                    e.currentTarget.style.color = 'white';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = '#dc2626';
                  }}
                  title="Delete Pokemon"
                >
                  −
                </button>
                <div
                  style={{
                    display: 'flex',
                    gap: '12px',
                  }}
                >
                  <div
                    style={{
                      width: '80px',
                      height: '80px',
                      borderRadius: '8px',
                      backgroundColor: 'var(--color-bg-light)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      overflow: 'hidden',
                    }}
                  >
                    <img
                      src={getPokemonSpritePath(pokemon.name)}
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

                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div
                      style={{
                        fontSize: '1rem',
                        fontWeight: 600,
                        color: 'var(--color-text-primary)',
                      }}
                    >
                      {pokemon.nickname || pokemon.name}
                    </div>
                    <div
                      style={{
                        fontSize: '0.85rem',
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      Lv. {pokemon.level}
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '6px',
                      }}
                    >
                      {pokemon.types.map((type) => (
                        <PokemonTypeBadge key={type} type={type} />
                      ))}
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    gap: '8px',
                    marginTop: 'auto',
                  }}
                >
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ flex: 1, fontSize: '0.8rem', padding: '6px 8px' }}
                    onClick={() => openEditModal(pokemon)}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline"
                    style={{ flex: 1, fontSize: '0.8rem', padding: '6px 8px' }}
                    onClick={() => openEvolveModal(pokemon)}
                    disabled={!canEvolve(pokemon)}
                  >
                    Evolve
                  </button>
                </div>

                <div
                  style={{
                    display: 'flex',
                    gap: '8px',
                    marginTop: '4px',
                  }}
                >
                  <button
                    type="button"
                    className="btn btn-outline"
                    style={{ flex: 1, fontSize: '0.75rem', padding: '4px 6px' }}
                    onClick={() => handleSetStatus(pokemon, Status.STORED)}
                  >
                    Move to Storage
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline-danger"
                    style={{ flex: 1, fontSize: '0.75rem', padding: '4px 6px' }}
                    onClick={() => openFaintConfirmation(pokemon)}
                  >
                    Mark Fainted
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Storage Section */}
      <div style={{ width: '100%', marginTop: '32px' }}>
        <h2
          style={{
            color: 'var(--color-text-primary)',
            fontSize: '1.5rem',
            marginBottom: '16px',
            fontWeight: 600,
          }}
        >
          Storage
        </h2>
        {isLoadingStored ? (
          <p style={{ color: 'var(--color-text-secondary)' }}>Loading storage...</p>
        ) : storedPokemon.length === 0 ? (
          <p style={{ color: 'var(--color-text-secondary)' }}>No Pokemon in storage yet.</p>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
            }}
          >
            {storedPokemon.map((pokemon) => (
              <div
                key={pokemon.id}
                style={{
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  border: '1px solid var(--color-border)',
                  borderRadius: '12px',
                  backgroundColor: 'var(--color-bg-card)',
                  position: 'relative',
                }}
              >
                <button
                  type="button"
                  onClick={() => openDeleteConfirmation(pokemon)}
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    border: '1px solid #dc2626',
                    backgroundColor: 'transparent',
                    color: '#dc2626',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 0,
                    lineHeight: 1,
                    transition: 'all 150ms ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#dc2626';
                    e.currentTarget.style.color = 'white';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = '#dc2626';
                  }}
                  title="Delete Pokemon"
                >
                  −
                </button>
                <div
                  style={{
                    display: 'flex',
                    gap: '12px',
                  }}
                >
                  <div
                    style={{
                      width: '80px',
                      height: '80px',
                      borderRadius: '8px',
                      backgroundColor: 'var(--color-bg-light)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      overflow: 'hidden',
                    }}
                  >
                    <img
                      src={getPokemonSpritePath(pokemon.name)}
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

                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div
                      style={{
                        fontSize: '1rem',
                        fontWeight: 600,
                        color: 'var(--color-text-primary)',
                      }}
                    >
                      {pokemon.nickname || pokemon.name}
                    </div>
                    <div
                      style={{
                        fontSize: '0.85rem',
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      Lv. {pokemon.level}
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '6px',
                      }}
                    >
                      {pokemon.types.map((type) => (
                        <PokemonTypeBadge key={type} type={type} />
                      ))}
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    gap: '8px',
                    marginTop: '8px',
                  }}
                >
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ flex: 1, fontSize: '0.8rem', padding: '6px 8px' }}
                    onClick={() => openEditModal(pokemon)}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline"
                    style={{ flex: 1, fontSize: '0.8rem', padding: '6px 8px' }}
                    onClick={() => openEvolveModal(pokemon)}
                    disabled={!canEvolve(pokemon)}
                  >
                    Evolve
                  </button>
                </div>

                <div
                  style={{
                    display: 'flex',
                    gap: '8px',
                    marginTop: '4px',
                  }}
                >
                  <button
                    type="button"
                    className="btn btn-outline"
                    style={{ flex: 1, fontSize: '0.75rem', padding: '4px 6px' }}
                    onClick={() => {
                      if (isPartyFull) {
                        openSwapModal(pokemon);
                      } else {
                        handleSetStatus(pokemon, Status.PARTY);
                      }
                    }}
                  >
                    {isPartyFull ? 'Swap' : 'Move to Party'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline-danger"
                    style={{ flex: 1, fontSize: '0.75rem', padding: '4px 6px' }}
                    onClick={() => openFaintConfirmation(pokemon)}
                  >
                    Mark Fainted
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Fainted Section */}
      <div style={{ width: '100%', marginTop: '32px' }}>
        <h2
          style={{
            color: 'var(--color-text-primary)',
            fontSize: '1.5rem',
            marginBottom: '16px',
            fontWeight: 600,
          }}
        >
          Fainted
        </h2>
        {isLoadingFainted ? (
          <p style={{ color: 'var(--color-text-secondary)' }}>Loading fainted Pokemon...</p>
        ) : faintedPokemon.length === 0 ? (
          <p style={{ color: 'var(--color-text-secondary)' }}>No fainted Pokemon yet.</p>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
            }}
          >
            {faintedPokemon.map((pokemon) => (
              <div
                key={pokemon.id}
                style={{
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  border: '1px solid var(--color-border)',
                  borderRadius: '12px',
                  backgroundColor: 'var(--color-bg-card)',
                  opacity: 0.7,
                  position: 'relative',
                }}
              >
                <button
                  type="button"
                  onClick={() => openDeleteConfirmation(pokemon)}
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    border: '1px solid #dc2626',
                    backgroundColor: 'transparent',
                    color: '#dc2626',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: 0,
                    lineHeight: 1,
                    transition: 'all 150ms ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#dc2626';
                    e.currentTarget.style.color = 'white';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = '#dc2626';
                  }}
                  title="Delete Pokemon"
                >
                  −
                </button>
                <div
                  style={{
                    display: 'flex',
                    gap: '12px',
                  }}
                >
                  <div
                    style={{
                      width: '80px',
                      height: '80px',
                      borderRadius: '8px',
                      backgroundColor: 'var(--color-bg-light)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      overflow: 'hidden',
                    }}
                  >
                    <img
                      src={getPokemonSpritePath(pokemon.name)}
                      alt={pokemon.nickname || pokemon.name}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'contain',
                        imageRendering: 'pixelated',
                        filter: 'grayscale(100%)',
                      }}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  </div>

                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div
                      style={{
                        fontSize: '1rem',
                        fontWeight: 600,
                        color: 'var(--color-text-primary)',
                      }}
                    >
                      {pokemon.nickname || pokemon.name}
                    </div>
                    <div
                      style={{
                        fontSize: '0.85rem',
                        color: 'var(--color-text-secondary)',
                      }}
                    >
                      Lv. {pokemon.level}
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '6px',
                      }}
                    >
                      {pokemon.types.map((type) => (
                        <PokemonTypeBadge key={type} type={type} />
                      ))}
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    gap: '8px',
                    marginTop: '8px',
                  }}
                >
                  <button
                    type="button"
                    className="btn btn-outline"
                    style={{ flex: 1, fontSize: '0.8rem', padding: '6px 8px' }}
                    onClick={() => handleSetStatus(pokemon, Status.STORED)}
                  >
                    Revive
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
          </div>
        </div>
        <div style={{ flex: '0 0 420px', width: '420px', paddingTop: '40px' }}>
          <TeamSynergySidebar
            isLoading={isLoadingSynergy}
            isError={isErrorSynergy}
            synergy={teamSynergy}
          />
        </div>
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

      {/* Evolve Modal */}
      {evolvingPokemon && (() => {
        const evolutionOptions = getEvolutionOptions(evolvingPokemon);
        
        return (
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
              }}
            >
              <h2
                style={{
                  marginTop: 0,
                  marginBottom: '12px',
                  color: 'var(--color-text-primary)',
                }}
              >
                Evolve {evolvingPokemon.nickname || evolvingPokemon.name}?
              </h2>

              <p
                style={{
                  marginBottom: '16px',
                  fontSize: '0.9rem',
                  color: 'var(--color-text-secondary)',
                }}
              >
                Select which evolution you want:
              </p>

              {evolutionOptions.length === 0 ? (
                <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
                  No evolution options available.
                </p>
              ) : (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                    marginBottom: '16px',
                  }}
                >
                  {evolutionOptions.map((option, index) => {
                    const isSelected = selectedEvolution === option.species;
                    const isDisabled = !option.canEvolve;
                    
                    return (
                      <EvolutionOptionButton
                        key={`${option.species}-${index}`}
                        species={option.species}
                        minLevel={option.minLevel}
                        canEvolve={option.canEvolve}
                        reason={option.reason}
                        isSelected={isSelected}
                        isDisabled={isDisabled}
                        onSelect={() => {
                          if (option.canEvolve) {
                            setSelectedEvolution(option.species);
                            setError(null);
                          }
                        }}
                      />
                    );
                  })}
                </div>
              )}

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
                  onClick={closeEvolveModal}
                  style={{ fontSize: '0.85rem', padding: '8px 14px' }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleConfirmEvolve}
                  disabled={!selectedEvolution}
                  style={{ fontSize: '0.85rem', padding: '8px 14px' }}
                >
                  Evolve
                </button>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Swap Modal */}
      {swappingPokemon && (
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
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: '12px',
                color: 'var(--color-text-primary)',
              }}
            >
              Swap {swappingPokemon.nickname || swappingPokemon.name} into Party
            </h2>

            <p
              style={{
                marginBottom: '16px',
                fontSize: '0.9rem',
                color: 'var(--color-text-secondary)',
              }}
            >
              Your party is full. Select which Pokemon to swap out:
            </p>

            {partyPokemon.length === 0 ? (
              <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
                No Pokemon in party to swap with.
              </p>
            ) : (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  marginBottom: '16px',
                  maxHeight: '400px',
                  overflowY: 'auto',
                }}
              >
                {partyPokemon.map((partyPoke) => {
                  const isSelected = selectedPartyPokemonForSwap === partyPoke.id;
                  
                  return (
                    <button
                      key={partyPoke.id}
                      type="button"
                      onClick={() => {
                        setSelectedPartyPokemonForSwap(partyPoke.id);
                        setError(null);
                      }}
                      style={{
                        padding: '12px 16px',
                        borderRadius: '8px',
                        border: isSelected
                          ? '2px solid var(--color-pokemon-primary)'
                          : '1px solid var(--color-border)',
                        backgroundColor: isSelected
                          ? 'var(--color-bg-light)'
                          : 'var(--color-bg-card)',
                        color: 'var(--color-text-primary)',
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'all 150ms ease',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.borderColor = 'var(--color-pokemon-primary)';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.borderColor = 'var(--color-border)';
                        }
                      }}
                    >
                      {/* Sprite */}
                      <div
                        style={{
                          width: '48px',
                          height: '48px',
                          borderRadius: '8px',
                          backgroundColor: 'var(--color-bg-light)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          overflow: 'hidden',
                          flexShrink: 0,
                        }}
                      >
                        <img
                          src={getPokemonSpritePath(partyPoke.name)}
                          alt={partyPoke.nickname || partyPoke.name}
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

                      {/* Info */}
                      <div style={{ flex: 1 }}>
                        <div
                          style={{
                            fontWeight: 600,
                            fontSize: '0.95rem',
                          }}
                        >
                          {partyPoke.nickname || partyPoke.name}
                        </div>
                        <div
                          style={{
                            fontSize: '0.8rem',
                            color: 'var(--color-text-secondary)',
                            marginTop: '2px',
                          }}
                        >
                          Lv. {partyPoke.level}
                        </div>
                      </div>

                      {/* Selection indicator */}
                      {isSelected && (
                        <span style={{ fontSize: '1.2rem', flexShrink: 0 }}>✓</span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}

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
                onClick={closeSwapModal}
                style={{ fontSize: '0.85rem', padding: '8px 14px' }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleConfirmSwap}
                disabled={!selectedPartyPokemonForSwap}
                style={{ fontSize: '0.85rem', padding: '8px 14px' }}
              >
                Swap
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mark Fainted Confirmation Modal */}
      {faintingPokemon && (
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
              maxWidth: '420px',
              padding: '24px',
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: '12px',
                color: 'var(--color-text-primary)',
              }}
            >
              Mark {faintingPokemon.nickname || faintingPokemon.name} as Fainted?
            </h2>

            <p
              style={{
                marginBottom: '16px',
                fontSize: '0.9rem',
                color: 'var(--color-text-secondary)',
              }}
            >
              Are you sure? This will mark your Pokemon as fainted and move them out of your party.
            </p>

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
                onClick={closeFaintConfirmation}
                style={{ fontSize: '0.85rem', padding: '8px 14px' }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={handleConfirmFaint}
                style={{ fontSize: '0.85rem', padding: '8px 14px' }}
              >
                Mark Fainted
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingPokemon && (
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
              maxWidth: '420px',
              padding: '24px',
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: '12px',
                color: 'var(--color-text-primary)',
              }}
            >
              Delete {deletingPokemon.nickname || deletingPokemon.name}?
            </h2>

            <p
              style={{
                marginBottom: '16px',
                fontSize: '0.9rem',
                color: 'var(--color-text-secondary)',
              }}
            >
              Are you sure? This will permanently delete this Pokemon from your team. This action cannot be undone.
            </p>

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
                onClick={closeDeleteConfirmation}
                style={{ fontSize: '0.85rem', padding: '8px 14px' }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={handleConfirmDelete}
                style={{ fontSize: '0.85rem', padding: '8px 14px' }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Component to display evolution option with sprite
const EvolutionOptionButton = ({
  species,
  minLevel,
  canEvolve,
  reason,
  isSelected,
  isDisabled,
  onSelect,
}: {
  species: string;
  minLevel: number | null;
  canEvolve: boolean;
  reason?: string;
  isSelected: boolean;
  isDisabled: boolean;
  onSelect: () => void;
}) => {
  const { data: pokemonInfo, isLoading } = usePokemonInfoByName(species);

  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={isDisabled}
      style={{
        padding: '12px 16px',
        borderRadius: '8px',
        border: isSelected
          ? '2px solid var(--color-pokemon-primary)'
          : '1px solid var(--color-border)',
        backgroundColor: isSelected
          ? 'var(--color-bg-light)'
          : isDisabled
          ? 'var(--color-bg-card)'
          : 'var(--color-bg-light)',
        color: isDisabled
          ? 'var(--color-text-secondary)'
          : 'var(--color-text-primary)',
        cursor: isDisabled ? 'not-allowed' : 'pointer',
        textAlign: 'left',
        opacity: isDisabled ? 0.5 : 1,
        transition: 'all 150ms ease',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}
      onMouseEnter={(e) => {
        if (!isDisabled) {
          e.currentTarget.style.borderColor = 'var(--color-pokemon-primary)';
        }
      }}
      onMouseLeave={(e) => {
        if (!isDisabled && !isSelected) {
          e.currentTarget.style.borderColor = 'var(--color-border)';
        }
      }}
    >
      {/* Sprite */}
      <div
        style={{
          width: '48px',
          height: '48px',
          borderRadius: '8px',
          backgroundColor: 'var(--color-bg-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          flexShrink: 0,
        }}
      >
        {isLoading ? (
          <div
            style={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.7rem',
              color: 'var(--color-text-secondary)',
            }}
          >
            ...
          </div>
        ) : pokemonInfo?.name ? (
          <img
            src={getPokemonSpritePath(pokemonInfo.name)}
            alt={species}
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
        ) : null}
      </div>

      {/* Info */}
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontWeight: 600,
            fontSize: '0.95rem',
            textTransform: 'capitalize',
          }}
        >
          {species.split('-').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
          ).join('-')}
        </div>
        {minLevel !== null && (
          <div
            style={{
              fontSize: '0.8rem',
              color: 'var(--color-text-secondary)',
              marginTop: '2px',
            }}
          >
            {canEvolve
              ? `Level ${minLevel} required`
              : reason || `Requires level ${minLevel}`}
          </div>
        )}
      </div>

      {/* Selection indicator */}
      {isSelected && (
        <span style={{ fontSize: '1.2rem', flexShrink: 0 }}>✓</span>
      )}
    </button>
  );
};

