import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameFile } from '../hooks/useGameFile';
import { usePokemon, usePartyPokemon, useAddPokemon, usePokemonInfoByName, useSearchPokemon } from '../hooks/usePokemon';
import { useUpcomingRoutes } from '../hooks/useRoutes';
import { useUpcomingGyms, useGymProgress } from '../hooks/useGyms';
import { Nature, Status, type NatureValue, type StatusValue } from '../types/enums';
import { getPokemonSpritePath } from '../utils/pokemonSprites';
import type { BasePokemon } from '../types';

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { currentGameFile } = useGameFile();
  const gameFileId = currentGameFile?.id ?? null;

  const { data: partyPokemon = [], isLoading: isLoadingParty } = usePartyPokemon(gameFileId);
  const { data: allPokemon = [] } = usePokemon(gameFileId);
  const { data: gymProgress = [] } = useGymProgress(gameFileId);
  const { isLoading: isLoadingRoutes } = useUpcomingRoutes(gameFileId);
  const { data: upcomingGymsResponse, isLoading: isLoadingGyms } = useUpcomingGyms(gameFileId);
  const addPokemonMutation = useAddPokemon(gameFileId);

  // Add Pokemon modal state
  const [showAddPokemonModal, setShowAddPokemonModal] = useState(false);
  const [pokemonNameInput, setPokemonNameInput] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const [addNickname, setAddNickname] = useState('');
  const [addLevelInput, setAddLevelInput] = useState('5');
  const [addNature, setAddNature] = useState<NatureValue | ''>('');
  const [addAbility, setAddAbility] = useState('');
  const [addGender, setAddGender] = useState<string>('');
  const [addStatus, setAddStatus] = useState<StatusValue | ''>(Status.PARTY);
  const [addError, setAddError] = useState<string | null>(null);
  const pokemonInputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const isClickingSuggestionRef = useRef(false);

  const nextGym = upcomingGymsResponse?.upcoming_gyms?.[0] ?? null;
  const nextGymLabel = nextGym
    ? `Gym ${nextGym.gym_number} - ${nextGym.trainer_name || 'Next Gym'}${
        nextGym.badge_type ? ` (${nextGym.badge_type})` : ''
      }`
    : 'No upcoming gyms';

  const badgesCount = gymProgress.length;
  const pokedexCount = allPokemon.length;

  const addLevel = parseInt(addLevelInput, 10) || 0;

  // Search Pokemon for autocomplete
  const searchQuery = pokemonNameInput.trim().length >= 1 ? pokemonNameInput.trim() : null;
  const { data: searchResults = [], isLoading: isSearching } = useSearchPokemon(searchQuery, 10);
  
  // Fetch Pokemon info for adding Pokemon (when user has entered a name that might be complete)
  // Only fetch if the input matches one of the search results exactly (user likely selected or typed complete name)
  const exactPokemonName = pokemonNameInput.trim().toLowerCase();
  const hasExactMatch = searchResults.some(p => p.name.toLowerCase() === exactPokemonName);
  const { data: addPokemonInfo } = usePokemonInfoByName(
    exactPokemonName && (hasExactMatch || exactPokemonName.length > 3) ? exactPokemonName : null
  );

  const openAddPokemonModal = () => {
    setShowAddPokemonModal(true);
    setPokemonNameInput('');
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);
    setAddNickname('');
    setAddLevelInput('5');
    setAddNature('');
    setAddAbility('');
    setAddGender('');
    setAddStatus(Status.PARTY);
    setAddError(null);
  };

  const closeAddPokemonModal = () => {
    setShowAddPokemonModal(false);
    setPokemonNameInput('');
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);
    setAddNickname('');
    setAddLevelInput('5');
    setAddNature('');
    setAddAbility('');
    setAddGender('');
    setAddStatus(Status.PARTY);
    setAddError(null);
  };

  const selectPokemon = (pokemon: BasePokemon) => {
    isClickingSuggestionRef.current = true;
    setPokemonNameInput(pokemon.name);
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);
    setAddError(null);
    // Reset the flag after a short delay
    setTimeout(() => {
      isClickingSuggestionRef.current = false;
      // Refocus the input after selection
      if (pokemonInputRef.current) {
        pokemonInputRef.current.focus();
      }
    }, 100);
  };

  const handlePokemonInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || searchResults.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedSuggestionIndex(prev => 
        prev < searchResults.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedSuggestionIndex(prev => prev > 0 ? prev - 1 : -1);
    } else if (e.key === 'Enter' && selectedSuggestionIndex >= 0) {
      e.preventDefault();
      selectPokemon(searchResults[selectedSuggestionIndex]);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setSelectedSuggestionIndex(-1);
    }
  };

  const handleAddPokemon = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!pokemonNameInput.trim()) {
      setAddError('Please enter a Pokemon name');
      return;
    }

    if (!addPokemonInfo?.poke_id) {
      setAddError('Pokemon not found. Please check the name and try again.');
      return;
    }

    if (addLevel < 1 || addLevel > 100) {
      setAddError('Level must be between 1 and 100');
      return;
    }

    try {
      setAddError(null);
      await addPokemonMutation.mutateAsync({
        poke_id: addPokemonInfo.poke_id,
        nickname: addNickname.trim() || null,
        nature: addNature || null,
        ability: addAbility.trim() || null,
        level: addLevel,
        gender: addGender || null,
        status: addStatus || Status.PARTY,
        caught_on: null,
      });
      closeAddPokemonModal();
    } catch (err: any) {
      setAddError(err?.response?.data?.detail || 'Failed to add Pokemon');
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
        ['--color-border' as any]: '#A89FE6',
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
                  {nextGymLabel}
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

              {/* Add Pokemon button */}
              <button
                type="button"
                onClick={openAddPokemonModal}
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
                <span style={{ fontWeight: 600 }}>Add Pokemon</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                  Add any Pokemon to cover missed encounters
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
                  position: 'relative',
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
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Pokemon Modal */}
      {showAddPokemonModal && (
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
              Add Pokemon
            </h2>
            <form onSubmit={handleAddPokemon}>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                  marginBottom: '16px',
                }}
              >
                {/* Pokemon Name */}
                <div style={{ position: 'relative' }}>
                  <label
                    htmlFor="pokemon-name"
                    style={{
                      display: 'block',
                      marginBottom: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                    }}
                  >
                    Pokemon Name *
                  </label>
                  <input
                    ref={pokemonInputRef}
                    id="pokemon-name"
                    className="input"
                    type="text"
                    value={pokemonNameInput}
                    onChange={(e) => {
                      setPokemonNameInput(e.target.value);
                      setShowSuggestions(true);
                      setSelectedSuggestionIndex(-1);
                      setAddError(null);
                    }}
                    onFocus={() => {
                      if (searchQuery && searchQuery.length >= 1) {
                        setShowSuggestions(true);
                      }
                    }}
                    onBlur={() => {
                      // Delay hiding suggestions to allow clicks
                      setTimeout(() => {
                        if (!isClickingSuggestionRef.current) {
                          setShowSuggestions(false);
                        }
                      }, 200);
                    }}
                    onKeyDown={handlePokemonInputKeyDown}
                    style={{ width: '100%' }}
                    placeholder="e.g., Pikachu"
                    required
                    autoComplete="off"
                  />
                  
                  {/* Autocomplete Suggestions */}
                  {showSuggestions && searchQuery && searchQuery.length >= 1 && (
                    <div
                      ref={suggestionsRef}
                      style={{
                        position: 'absolute',
                        top: '100%',
                        left: 0,
                        right: 0,
                        marginTop: '4px',
                        backgroundColor: 'var(--color-bg-card)',
                        border: '1px solid var(--color-border)',
                        borderRadius: '8px',
                        maxHeight: '200px',
                        overflowY: 'auto',
                        zIndex: 1000,
                        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                      }}
                      onMouseDown={(e) => {
                        e.preventDefault(); // Prevent input blur
                        isClickingSuggestionRef.current = true;
                      }}
                    >
                      {isSearching ? (
                        <div
                          style={{
                            padding: '12px',
                            textAlign: 'center',
                            color: 'var(--color-text-secondary)',
                            fontSize: '0.85rem',
                          }}
                        >
                          Searching...
                        </div>
                      ) : searchResults.length > 0 ? (
                        searchResults.map((pokemon, index) => (
                          <div
                            key={pokemon.poke_id}
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              selectPokemon(pokemon);
                            }}
                            onMouseDown={(e) => {
                              e.preventDefault();
                              isClickingSuggestionRef.current = true;
                            }}
                            style={{
                              padding: '10px 12px',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '10px',
                              backgroundColor: selectedSuggestionIndex === index 
                                ? 'var(--color-pokemon-primary)' 
                                : 'transparent',
                              color: selectedSuggestionIndex === index 
                                ? 'white' 
                                : 'var(--color-text-primary)',
                              transition: 'background-color 150ms ease',
                            }}
                            onMouseEnter={() => setSelectedSuggestionIndex(index)}
                          >
                            <img
                              src={getPokemonSpritePath(pokemon.name)}
                              alt={pokemon.name}
                              style={{
                                width: '56px',
                                height: '56px',
                                objectFit: 'contain',
                                imageRendering: 'pixelated',
                              }}
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                            <div>
                              <div
                                style={{
                                  fontWeight: 600,
                                  textTransform: 'capitalize',
                                  fontSize: '0.9rem',
                                }}
                              >
                                {pokemon.name}
                              </div>
                              {pokemon.types && pokemon.types.length > 0 && (
                                <div
                                  style={{
                                    fontSize: '0.75rem',
                                    opacity: 0.8,
                                  }}
                                >
                                  {pokemon.types.join(', ')}
                                </div>
                              )}
                            </div>
                          </div>
                        ))
                      ) : (
                        <div
                          style={{
                            padding: '12px',
                            textAlign: 'center',
                            color: 'var(--color-text-secondary)',
                            fontSize: '0.85rem',
                          }}
                        >
                          No Pokemon found
                        </div>
                      )}
                    </div>
                  )}

                  {/* Selected Pokemon Preview */}
                  {addPokemonInfo && !showSuggestions && (
                    <div
                      style={{
                        marginTop: '8px',
                        padding: '8px',
                        backgroundColor: 'var(--color-bg-light)',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                      }}
                    >
                      <img
                        src={getPokemonSpritePath(addPokemonInfo.name)}
                        alt={addPokemonInfo.name}
                        style={{
                          width: '64px',
                          height: '64px',
                          objectFit: 'contain',
                          imageRendering: 'pixelated',
                        }}
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                      <div>
                        <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                          {addPokemonInfo.name}
                        </div>
                        {addPokemonInfo.types && addPokemonInfo.types.length > 0 && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                            {addPokemonInfo.types.join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Nickname */}
                <div>
                  <label
                    htmlFor="add-nickname"
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
                    id="add-nickname"
                    className="input"
                    type="text"
                    value={addNickname}
                    onChange={(e) => setAddNickname(e.target.value)}
                    style={{ width: '100%' }}
                    placeholder="Optional"
                  />
                </div>

                {/* Level */}
                <div>
                  <label
                    htmlFor="add-level"
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
                    id="add-level"
                    className="input"
                    type="number"
                    value={addLevelInput}
                    onChange={(e) => setAddLevelInput(e.target.value)}
                    style={{
                      width: '100%',
                      borderColor:
                        (addLevel < 1 || addLevel > 100) && addLevelInput !== '' ? '#F87171' : undefined,
                      borderWidth:
                        (addLevel < 1 || addLevel > 100) && addLevelInput !== '' ? '2px' : undefined,
                    }}
                    min="1"
                    max="100"
                    required
                  />
                  {(addLevel < 1 || addLevel > 100) && addLevelInput !== '' && (
                    <p style={{ marginTop: '4px', fontSize: '0.75rem', color: '#F87171' }}>
                      Level must be between 1 and 100
                    </p>
                  )}
                </div>

                {/* Nature */}
                <div>
                  <label
                    htmlFor="add-nature"
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
                    id="add-nature"
                    className="input"
                    value={addNature}
                    onChange={(e) => setAddNature(e.target.value as NatureValue | '')}
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
                    htmlFor="add-ability"
                    style={{
                      display: 'block',
                      marginBottom: '4px',
                      fontSize: '0.8rem',
                      fontWeight: 600,
                    }}
                  >
                    Ability
                  </label>
                  {addPokemonInfo?.abilities && addPokemonInfo.abilities.length > 0 ? (
                    <select
                      id="add-ability"
                      className="input"
                      value={addAbility}
                      onChange={(e) => setAddAbility(e.target.value)}
                      style={{ width: '100%' }}
                    >
                      <option value="">None</option>
                      {addPokemonInfo.abilities.map((abil) => (
                        <option key={abil} value={abil}>
                          {abil}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      id="add-ability"
                      className="input"
                      type="text"
                      value={addAbility}
                      onChange={(e) => setAddAbility(e.target.value)}
                      placeholder="Enter ability"
                      style={{ width: '100%' }}
                    />
                  )}
                </div>

                {/* Gender */}
                <div>
                  <label
                    htmlFor="add-gender"
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
                    id="add-gender"
                    className="input"
                    value={addGender}
                    onChange={(e) => setAddGender(e.target.value)}
                    style={{ width: '100%' }}
                  >
                    <option value="">None</option>
                    <option value="m">Male</option>
                    <option value="f">Female</option>
                  </select>
                </div>

                {/* Status */}
                <div>
                  <label
                    htmlFor="add-status"
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
                    id="add-status"
                    className="input"
                    value={addStatus}
                    onChange={(e) => setAddStatus(e.target.value as StatusValue | '')}
                    style={{ width: '100%' }}
                  >
                    <option value={Status.PARTY}>Party</option>
                    <option value={Status.STORED}>Stored</option>
                    <option value={Status.FAINTED}>Fainted</option>
                  </select>
                </div>
              </div>

              {addError && (
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
                  {addError}
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
                  onClick={closeAddPokemonModal}
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
