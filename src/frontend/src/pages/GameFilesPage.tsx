/**
 * Game Files Page
 * Displays game files in a Pokemon-style save screen format
 */
import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useGameFile } from '../hooks/useGameFile';
import { usePartyPokemon } from '../hooks/usePokemon';
import { useGymProgress } from '../hooks/useGyms';
import { usePokemon } from '../hooks/usePokemon';
import { useVersions } from '../hooks/useVersions';
import { getGameFiles, deleteGameFile } from '../services/gameFileService';
import { parseSaveFile, createGameFileFromSave, updateGameFileFromSave } from '../services/saveFileService';
import { SaveFileUpload } from '../components/SaveFileUpload';
import { SavePreviewModal } from '../components/SavePreviewModal';
import { getPokemonSpritePath } from '../utils/pokemonSprites';
import { formatGameName } from '../utils/formatGameName';
import type { ParsedSavePreview, Pokemon } from '../types';

export const GameFilesPage = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { gameFiles, setGameFiles, currentGameFile, setCurrentGameFile } = useGameFile();
  const { data: versions = [], isLoading: isLoadingVersions } = useVersions();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [trainerName, setTrainerName] = useState('');
  const [selectedGame, setSelectedGame] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Save import state
  const [showImportForm, setShowImportForm] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importPreview, setImportPreview] = useState<ParsedSavePreview | null>(null);
  const [importConfirmLoading, setImportConfirmLoading] = useState(false);

  // Update from save state
  const [updateGameFileId, setUpdateGameFileId] = useState<number | null>(null);
  const [updatePreview, setUpdatePreview] = useState<ParsedSavePreview | null>(null);
  const [updateExistingPokemon, setUpdateExistingPokemon] = useState<Pokemon[]>([]);
  const [updateLoading, setUpdateLoading] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateConfirmLoading, setUpdateConfirmLoading] = useState(false);

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
      // Do not create the game file yet; move to starter selection first.
      const params = new URLSearchParams({
        trainerName: trainerName.trim(),
        gameName: selectedGame,
      });
      navigate(`/starters?${params.toString()}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to continue to starter selection');
    } finally {
      setIsCreating(false);
    }
  };

  const handleImportFileSelected = async (file: File) => {
    setImportError(null);
    setImportLoading(true);
    try {
      const preview = await parseSaveFile(file);
      setImportPreview(preview);
    } catch (err: any) {
      setImportError(err?.response?.data?.detail || 'Failed to parse save file');
    } finally {
      setImportLoading(false);
    }
  };

  const handleImportConfirm = async (gameName?: string) => {
    if (!importPreview || !gameName) return;
    setImportConfirmLoading(true);
    try {
      await createGameFileFromSave(importPreview, gameName);
      const files = await getGameFiles();
      setGameFiles(files);
      setImportPreview(null);
      setShowImportForm(false);
    } catch (err: any) {
      setImportError(err?.response?.data?.detail || 'Failed to create game file from save');
    } finally {
      setImportConfirmLoading(false);
    }
  };

  const handleImportCancel = () => {
    setImportPreview(null);
    setImportError(null);
  };

  const handleUpdateFileSelected = async (file: File, gameFileId: number, existingPokemon: Pokemon[]) => {
    setUpdateError(null);
    setUpdateGameFileId(gameFileId);
    setUpdateExistingPokemon(existingPokemon);
    setUpdateLoading(true);
    try {
      const preview = await parseSaveFile(file);
      // Client-side game mismatch pre-check
      const targetGameFile = gameFiles.find(gf => gf.id === gameFileId);
      if (targetGameFile && !preview.compatible_versions.includes(targetGameFile.game_name)) {
        setUpdateError(
          `This save is from ${preview.game} but this game file is ${formatGameName(targetGameFile.game_name)}.`
        );
        setUpdateLoading(false);
        return;
      }
      setUpdatePreview(preview);
    } catch (err: any) {
      setUpdateError(err?.response?.data?.detail || 'Failed to parse save file');
    } finally {
      setUpdateLoading(false);
    }
  };

  const handleUpdateConfirm = async () => {
    if (!updatePreview || !updateGameFileId) return;
    setUpdateConfirmLoading(true);
    try {
      await updateGameFileFromSave(updateGameFileId, updatePreview);
      const files = await getGameFiles();
      setGameFiles(files);
      setUpdatePreview(null);
      setUpdateGameFileId(null);
    } catch (err: any) {
      setUpdateError(err?.response?.data?.detail || 'Failed to update game file from save');
    } finally {
      setUpdateConfirmLoading(false);
    }
  };

  const handleUpdateCancel = () => {
    setUpdatePreview(null);
    setUpdateGameFileId(null);
    setUpdateError(null);
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
          {currentGameFile && (
            <button
              onClick={() => navigate(`/dashboard?gameFileId=${currentGameFile.id}`)}
              className="btn btn-primary"
              style={{ fontSize: '14px', padding: '8px 16px' }}
            >
              Go to Dashboard
            </button>
          )}
          <button
            onClick={() => { setShowImportForm(!showImportForm); setShowCreateForm(false); }}
            className="btn btn-primary"
            style={{ fontSize: '14px', padding: '8px 16px' }}
          >
            {showImportForm ? 'Cancel Import' : 'Import Save'}
          </button>
          <button
            onClick={() => { setShowCreateForm(!showCreateForm); setShowImportForm(false); }}
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
          maxWidth: '900px',
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
                style={{
                  display: 'block',
                  marginBottom: '16px',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: 'var(--color-text-primary)',
                }}
              >
                Game Version
              </label>
              {isLoadingVersions ? (
                <div style={{ textAlign: 'center', padding: '20px', color: 'var(--color-text-secondary)' }}>
                  Loading games...
                </div>
              ) : (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '16px',
                  maxHeight: '500px',
                  overflowY: 'auto',
                  padding: '8px',
                }}>
                  {[...versions]
                    .sort((a, b) => {
                      // First sort by generation_id
                      if (a.generation_id !== b.generation_id) {
                        return a.generation_id - b.generation_id;
                      }
                      // Then sort by version_id within the same generation
                      return a.version_id - b.version_id;
                    })
                    .map((version) => {
                    const gameImageName = GAME_IMAGE_MAP[version.version_name.toLowerCase()];
                    const gameImagePath = gameImageName ? `/images/games/${gameImageName}` : null;
                    const isSelected = selectedGame === version.version_name;

                    return (
                      <div
                        key={version.version_name}
                        onClick={() => setSelectedGame(version.version_name)}
                        style={{
                          padding: '12px',
                          border: isSelected ? '2px solid var(--color-pokemon-yellow)' : '2px solid var(--color-border)',
                          borderRadius: '8px',
                          backgroundColor: isSelected ? 'var(--color-bg-light)' : 'var(--color-bg-card)',
                          cursor: 'pointer',
                          transition: 'all 150ms ease',
                          textAlign: 'center',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '8px',
                        }}
                        onMouseEnter={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.borderColor = 'var(--color-pokemon-blue)';
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.borderColor = 'var(--color-border)';
                          }
                        }}
                      >
                        {gameImagePath ? (
                          <img
                            src={gameImagePath}
                            alt={version.version_name}
                            style={{
                              width: '80px',
                              height: '80px',
                              objectFit: 'contain',
                              display: 'block',
                            }}
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        ) : (
                          <div style={{
                            width: '80px',
                            height: '80px',
                            backgroundColor: 'var(--color-bg-light)',
                            borderRadius: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'var(--color-text-secondary)',
                            fontSize: '10px',
                          }}>
                            No Image
                          </div>
                        )}
                        <div style={{
                          fontSize: '10px',
                          fontFamily: 'var(--font-pokemon)',
                          color: 'var(--color-text-primary)',
                          lineHeight: '1.2',
                          letterSpacing: '0px',
                        }}>
                          {formatGameName(version.version_name)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
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
              {isCreating ? 'Loading...' : 'Next'}
            </button>
          </form>
        </div>
      )}

      {/* Import Save File Form */}
      {showImportForm && (
        <div className="card" style={{
          maxWidth: '900px',
          width: '100%',
          padding: '28px',
        }}>
          <h2 style={{
            color: 'var(--color-text-primary)',
            fontSize: '1.5rem',
            marginBottom: '20px',
          }}>
            Import from Save File
          </h2>
          <SaveFileUpload
            onFileSelected={handleImportFileSelected}
            isLoading={importLoading}
            error={importError}
          />
        </div>
      )}

      {/* Game Files List - Only show when not creating new game */}
      {!showCreateForm && (
        <>
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
                  onSelect={() => {
                    setCurrentGameFile(gameFile);
                    navigate(`/dashboard?gameFileId=${gameFile.id}`);
                  }}
                  onDelete={() => handleDeleteGameFile(gameFile.id)}
                  onUpdateFromSave={handleUpdateFileSelected}
                  updateLoading={updateLoading && updateGameFileId === gameFile.id}
                  updateError={updateGameFileId === gameFile.id ? updateError : null}
                />
              ))}
            </div>
          )}
        </>
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

      {/* Import preview modal */}
      {importPreview && (
        <SavePreviewModal
          preview={importPreview}
          mode="create"
          onConfirm={handleImportConfirm}
          onCancel={handleImportCancel}
          isLoading={importConfirmLoading}
        />
      )}

      {/* Update preview modal */}
      {updatePreview && (
        <SavePreviewModal
          preview={updatePreview}
          mode="update"
          existingPokemon={updateExistingPokemon}
          onConfirm={handleUpdateConfirm}
          onCancel={handleUpdateCancel}
          isLoading={updateConfirmLoading}
        />
      )}
    </div>
  );
};

interface GameFileCardProps {
  gameFile: import('../types').GameFile;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onUpdateFromSave: (file: File, gameFileId: number, existingPokemon: Pokemon[]) => void;
  updateLoading?: boolean;
  updateError?: string | null;
}

// Hardcoded mapping of game names to image filenames
const GAME_IMAGE_MAP: Record<string, string> = {
  'black': 'black.png',
  'black-2': 'black2.png',
  'white': 'white.png',
  'white-2': 'white2.png',
  'red': 'red.png',
  'blue': 'blue.png',
  'yellow': 'yellow.png',
  'gold': 'gold.png',
  'silver': 'silver.png',
  'crystal': 'crystal.png',
  'ruby': 'ruby.png',
  'sapphire': 'sapphire.png',
  'emerald': 'emerald.png',
  'firered': 'firered.png',
  'leafgreen': 'leafgreen.png',
  'diamond': 'diamond.png',
  'pearl': 'pearl.png',
  'platinum': 'platinum.png',
  'heartgold': 'heartgold.jpg',
  'soulsilver': 'soulsilver.jpg',
};

const GameFileCard = ({ gameFile, isSelected, onSelect, onDelete, onUpdateFromSave, updateLoading, updateError }: GameFileCardProps) => {
  const updateFileRef = useRef<HTMLInputElement>(null);
  const { data: partyPokemon = [], isLoading: isLoadingParty } = usePartyPokemon(gameFile.id);
  const { data: gymProgress = [], isLoading: isLoadingGyms } = useGymProgress(gameFile.id);
  const { data: allPokemon = [], isLoading: isLoadingPokemon } = usePokemon(gameFile.id);

  const isLoading = isLoadingParty || isLoadingGyms || isLoadingPokemon;

  const gymBadgesCount = gymProgress?.length || 0;
  const pokedexCount = allPokemon?.length || 0;

  // Create array of 6 pokemon slots (fill with party pokemon, pad with nulls)
  const pokemonSlots = Array.from({ length: 6 }, (_, i) => partyPokemon[i] || null);

  // Get game image filename from mapping
  const gameImageName = GAME_IMAGE_MAP[gameFile.game_name.toLowerCase()];
  const gameImagePath = gameImageName ? `/images/games/${gameImageName}` : null;

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
      {/* Game Image */}
      {gameImagePath && (
        <div style={{
          width: '100%',
          marginBottom: '20px',
          borderRadius: '8px',
          overflow: 'hidden',
          backgroundColor: 'var(--color-bg-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <img
            src={gameImagePath}
            alt={gameFile.game_name}
            style={{
              maxWidth: '100%',
              height: 'auto',
              maxHeight: '300px',
              objectFit: 'contain',
              display: 'block',
            }}
            onError={(e) => {
              // Hide image if it fails to load
              e.currentTarget.style.display = 'none';
            }}
          />
        </div>
      )}

      {/* Trainer Name */}
      <div style={{
        color: 'var(--color-text-primary)',
        fontSize: '14px',
        marginBottom: '12px',
        fontFamily: 'var(--font-pokemon)',
        lineHeight: '1.0',
        letterSpacing: '0px',
      }}>
        {gameFile.trainer_name}
      </div>

      {/* Location */}
      <div style={{
        color: 'var(--color-text-primary)',
        fontSize: '12px',
        marginBottom: '6px',
        fontFamily: 'var(--font-pokemon)',
        lineHeight: '1.4',
        letterSpacing: '0px',
      }}>
        {formatGameName(gameFile.game_name)}
      </div>

      {/* Starter Pokemon */}
      {gameFile.starter_pokemon && (
        <div style={{
          color: 'var(--color-text-secondary)',
          fontSize: '11px',
          marginBottom: '4px',
          fontFamily: 'var(--font-pokemon)',
          lineHeight: '1.2',
          letterSpacing: '0px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
        }}>
          <span>Starter:</span>
          {getPokemonSpritePath(gameFile.starter_pokemon) ? (
            <img
              src={getPokemonSpritePath(gameFile.starter_pokemon)}
              alt={gameFile.starter_pokemon}
              style={{
                width: '48px',
                height: '48px',
                objectFit: 'contain',
                imageRendering: 'pixelated',
              }}
              onError={(e) => {
                e.currentTarget.style.display = 'none';
              }}
            />
          ) : null}
          <span style={{ textTransform: 'capitalize' }}>
            {gameFile.starter_pokemon.replace(/-/g, ' ')}
          </span>
        </div>
      )}

      {/* Stats */}
      <div style={{
        color: 'var(--color-text-primary)',
        fontSize: '10px',
        marginBottom: '20px',
        display: 'flex',
        gap: '16px',
        flexWrap: 'wrap',
        fontFamily: 'var(--font-pokemon)',
        lineHeight: '1.4',
        letterSpacing: '0px',
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
                  src={getPokemonSpritePath(pokemon.name)}
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

      {/* Hidden file input for save update */}
      <input
        ref={updateFileRef}
        type="file"
        accept=".sav"
        style={{ display: 'none' }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            onUpdateFromSave(file, gameFile.id, allPokemon);
            e.target.value = '';
          }
        }}
      />

      {/* Action Buttons */}
      <div style={{
        display: 'flex',
        gap: '12px',
        justifyContent: 'center',
        flexWrap: 'wrap',
      }}>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
          className="btn btn-primary"
          style={{
            flex: 1,
            maxWidth: '160px',
            backgroundColor: isSelected ? 'var(--color-pokemon-yellow)' : 'var(--color-pokemon-primary)',
            borderColor: isSelected ? '#D4AF37' : '#4338CA',
            color: isSelected ? '#1A1A1A' : 'var(--color-text-white)',
          }}
        >
          {isSelected ? 'Selected' : 'Load'}
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            updateFileRef.current?.click();
          }}
          className="btn btn-outline"
          disabled={updateLoading}
          style={{
            flex: 1,
            maxWidth: '160px',
          }}
        >
          {updateLoading ? 'Parsing...' : 'Update Save'}
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="btn btn-outline-danger"
          style={{
            flex: 1,
            maxWidth: '160px',
          }}
        >
          Delete
        </button>
      </div>
      {updateError && (
        <div style={{
          marginTop: '12px',
          padding: '8px',
          backgroundColor: '#FEE2E2',
          border: '1px solid #F87171',
          borderRadius: '8px',
          color: '#991B1B',
          fontSize: '12px',
        }}>
          {updateError}
        </div>
      )}
    </div>
  );
};
