/**
 * Game Files Page
 * Displays game files in a Pokemon-style save screen format
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useGameFile } from '../hooks/useGameFile';
import { usePartyPokemon } from '../hooks/usePokemon';
import { useGymProgress } from '../hooks/useGyms';
import { usePokemon } from '../hooks/usePokemon';
import { useVersions } from '../hooks/useVersions';
import { getGameFiles, createGameFile, deleteGameFile } from '../services/gameFileService';
import { getPokemon } from '../services/pokemonService';
import { useQueryClient } from '@tanstack/react-query';

export const GameFilesPage = () => {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const { gameFiles, setGameFiles, currentGameFile, setCurrentGameFile } = useGameFile();
  const { data: versions = [], isLoading: isLoadingVersions } = useVersions();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [trainerName, setTrainerName] = useState('');
  const [selectedGame, setSelectedGame] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Load game files on mount
  useEffect(() => {
    const loadGameFiles = async () => {
      try {
        const files = await getGameFiles();
        setGameFiles(files);
        // Don't auto-select - user must click "Load" to select a game file
      } catch (error) {
        console.error('Failed to load game files:', error);
      }
    };
    loadGameFiles();
  }, [setGameFiles]);

  const handleLogout = async () => {
    await logout();
    navigate('/login?logout=true', { replace: true });
  };

  const handleDeleteGameFile = async (gameFileId: number) => {
    if (window.confirm('Are you sure you want to delete this game file?')) {
      try {
        await deleteGameFile(gameFileId);
        const updatedFiles = gameFiles.filter((gf) => gf.id !== gameFileId);
        setGameFiles(updatedFiles);
        if (currentGameFile?.id === gameFileId) {
          setCurrentGameFile(null);
        }
      } catch (error) {
        console.error('Failed to delete game file:', error);
      }
    }
  };

  const handleCreateGameFile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (!trainerName.trim()) {
      setError('Trainer name is required');
      return;
    }
    
    if (!selectedGame) {
      setError('Please select a game');
      return;
    }

    setIsCreating(true);
    try {
      const newGameFile = await createGameFile({
        trainer_name: trainerName.trim(),
        game_name: selectedGame,
      });
      
      // Refresh game files list
      const updatedFiles = await getGameFiles();
      setGameFiles(updatedFiles);
      setCurrentGameFile(newGameFile);
      
      // Check if game file has any Pokemon
      const pokemon = await getPokemon(newGameFile.id);
      
      // Reset form
      setTrainerName('');
      setSelectedGame('');
      setShowCreateForm(false);
      
      // If no Pokemon, route to starter selection
      if (pokemon.length === 0) {
        navigate(`/starters?gameFileId=${newGameFile.id}`);
      } else {
        // Otherwise, just stay on this page with the new game file selected
        queryClient.invalidateQueries({ queryKey: ['gameFiles'] });
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create game file');
    } finally {
      setIsCreating(false);
    }
  };

  const formatDate = (dateString: string | null | undefined): string => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${month}/${day}/${year} ${hours}:${minutes}`;
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-bg-light)',
      padding: '40px 20px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '24px',
      position: 'relative',
    }}>
      {/* Header */}
      <div style={{
        width: '100%',
        maxWidth: '600px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
      }}>
        <h1 style={{
          color: 'var(--color-text-primary)',
          fontSize: '2rem',
          margin: 0,
        }}>
          Game Files
        </h1>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn btn-primary"
            style={{ fontSize: '14px', padding: '8px 16px' }}
          >
            {showCreateForm ? 'Cancel' : 'New Game'}
          </button>
          <button
            onClick={handleLogout}
            className="btn btn-outline"
            style={{ fontSize: '14px', padding: '8px 16px' }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Create Game File Form */}
      {showCreateForm && (
        <div className="card" style={{
          maxWidth: '600px',
          width: '100%',
          padding: '28px',
        }}>
          <h2 style={{
            color: 'var(--color-text-primary)',
            fontSize: '1.5rem',
            marginBottom: '20px',
          }}>
            Create New Game File
          </h2>
          <form onSubmit={handleCreateGameFile}>
            <div style={{ marginBottom: '20px' }}>
              <label
                htmlFor="trainer-name"
                style={{
                  display: 'block',
                  marginBottom: '8px',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: 'var(--color-text-primary)',
                }}
              >
                Trainer Name
              </label>
              <input
                id="trainer-name"
                type="text"
                value={trainerName}
                onChange={(e) => setTrainerName(e.target.value)}
                required
                className="input"
                placeholder="Enter trainer name"
                style={{ width: '100%', boxSizing: 'border-box' }}
              />
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label
                htmlFor="game-select"
                style={{
                  display: 'block',
                  marginBottom: '8px',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: 'var(--color-text-primary)',
                }}
              >
                Game Version
              </label>
              <select
                id="game-select"
                value={selectedGame}
                onChange={(e) => setSelectedGame(e.target.value)}
                required
                className="input"
                style={{ width: '100%', boxSizing: 'border-box' }}
                disabled={isLoadingVersions}
              >
                <option value="">Select a game...</option>
                {versions.map((version) => (
                  <option key={version.version_name} value={version.version_name}>
                    {version.version_name}
                  </option>
                ))}
              </select>
            </div>

            {error && (
              <div style={{
                marginBottom: '20px',
                padding: '12px',
                backgroundColor: '#FEE2E2',
                border: '2px solid #F87171',
                borderRadius: '8px',
                color: '#991B1B',
                fontSize: '14px',
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isCreating || isLoadingVersions}
              className="btn btn-primary"
              style={{
                width: '100%',
                fontSize: '16px',
                padding: '14px 24px',
              }}
            >
              {isCreating ? 'Creating...' : 'Create Game File'}
            </button>
          </form>
        </div>
      )}

      {/* Game Files List */}
      {gameFiles.length === 0 ? (
        <div className="card" style={{
          maxWidth: '600px',
          width: '100%',
          padding: '40px',
          textAlign: 'center',
        }}>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '18px' }}>
            No game files found. Create a new game file to get started!
          </p>
        </div>
      ) : (
        <div style={{
          width: '100%',
          maxWidth: '600px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}>
          {gameFiles.map((gameFile) => (
            <GameFileCard
              key={gameFile.id}
              gameFile={gameFile}
              isSelected={currentGameFile?.id === gameFile.id}
              onSelect={() => setCurrentGameFile(gameFile)}
              onDelete={() => handleDeleteGameFile(gameFile.id)}
            />
          ))}
        </div>
      )}

      {/* Last saved info at bottom */}
      {currentGameFile?.created_at && (
        <div style={{
          marginTop: 'auto',
          paddingTop: '20px',
          color: 'var(--color-text-secondary)',
          fontSize: '14px',
        }}>
          Last saved on {formatDate(currentGameFile.created_at)}
        </div>
      )}
    </div>
  );
};

interface GameFileCardProps {
  gameFile: import('../types').GameFile;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

const GameFileCard = ({ gameFile, isSelected, onSelect, onDelete }: GameFileCardProps) => {
  const { data: partyPokemon = [], isLoading: isLoadingParty } = usePartyPokemon(gameFile.id);
  const { data: gymProgress = [], isLoading: isLoadingGyms } = useGymProgress(gameFile.id);
  const { data: allPokemon = [], isLoading: isLoadingPokemon } = usePokemon(gameFile.id);

  const isLoading = isLoadingParty || isLoadingGyms || isLoadingPokemon;

  const gymBadgesCount = gymProgress?.length || 0;
  const pokedexCount = allPokemon?.length || 0;

  // Create array of 6 pokemon slots (fill with party pokemon, pad with nulls)
  const pokemonSlots = Array.from({ length: 6 }, (_, i) => partyPokemon[i] || null);

  return (
    <div className="card" style={{
      padding: '28px',
      border: isSelected ? '2px solid var(--color-pokemon-yellow)' : '2px solid var(--color-border)',
      cursor: 'pointer',
      transition: 'all 150ms ease',
      backgroundColor: 'var(--color-bg-card)',
      maxWidth: '100%',
    }}
    onClick={onSelect}
    >
      {/* Trainer Name */}
      <div style={{
        color: 'var(--color-text-primary)',
        fontSize: '16px',
        marginBottom: '12px',
        fontWeight: '600',
      }}>
        {gameFile.trainer_name}
      </div>

      {/* Location */}
      <div style={{
        color: 'var(--color-text-primary)',
        fontSize: '16px',
        marginBottom: '12px',
      }}>
        {gameFile.game_name}
      </div>

      {/* Stats */}
      <div style={{
        color: 'var(--color-text-primary)',
        fontSize: '16px',
        marginBottom: '20px',
        display: 'flex',
        gap: '16px',
        flexWrap: 'wrap',
      }}>
        {isLoading ? (
          <span style={{ color: 'var(--color-text-secondary)' }}>Loading...</span>
        ) : (
          <>
            <span>Gym Badges: {gymBadgesCount}</span>
            <span>Pokédex: {pokedexCount}</span>
          </>
        )}
      </div>

      {/* Divider */}
      <div style={{
        height: '1px',
        backgroundColor: 'var(--color-border)',
        marginBottom: '20px',
      }} />

      {/* Party Pokemon Sprites */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '24px',
        justifyContent: 'center',
        flexWrap: 'wrap',
      }}>
        {isLoading ? (
          <div style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>Loading party...</div>
        ) : (
          pokemonSlots.map((pokemon, index) => (
            <div
              key={index}
              style={{
                width: '72px',
                height: '72px',
                backgroundColor: pokemon ? 'transparent' : 'var(--color-bg-light)',
                border: pokemon ? 'none' : '1px solid var(--color-border)',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
                flexShrink: 0,
              }}
            >
              {pokemon ? (
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
                    // Fallback if image fails to load
                    e.currentTarget.style.display = 'none';
                  }}
                />
              ) : null}
            </div>
          ))
        )}
      </div>

      {/* Action Buttons */}
      <div style={{
        display: 'flex',
        gap: '12px',
        justifyContent: 'center',
      }}>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
          className="btn btn-primary"
          style={{
            flex: 1,
            maxWidth: '200px',
            backgroundColor: isSelected ? 'var(--color-pokemon-yellow)' : 'var(--color-pokemon-red)',
            borderColor: isSelected ? '#D4AF37' : '#CC0000',
            color: isSelected ? '#1A1A1A' : 'var(--color-text-white)',
          }}
        >
          {isSelected ? 'Selected' : 'Load'}
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="btn btn-outline"
          style={{
            flex: 1,
            maxWidth: '200px',
          }}
        >
          Delete
        </button>
      </div>
    </div>
  );
};
