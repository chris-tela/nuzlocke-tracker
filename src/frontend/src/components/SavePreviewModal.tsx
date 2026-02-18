import { useState } from 'react';
import type { ParsedSavePreview, Pokemon } from '../types';
import { getPokemonSpritePath } from '../utils/pokemonSprites';
import { formatGameName } from '../utils/formatGameName';

interface SavePreviewModalProps {
  preview: ParsedSavePreview;
  mode: 'create' | 'update';
  existingPokemon?: Pokemon[];
  onConfirm: (gameName?: string) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const SavePreviewModal = ({
  preview,
  mode,
  existingPokemon = [],
  onConfirm,
  onCancel,
  isLoading,
}: SavePreviewModalProps) => {
  const [selectedVersion, setSelectedVersion] = useState<string>(
    preview.compatible_versions.length === 1 ? preview.compatible_versions[0] : ''
  );

  const needsVersionPicker = mode === 'create' && preview.compatible_versions.length > 1;

  const previewParty = preview.pokemon.filter(p => p.status === 'Party');
  const previewStored = preview.pokemon.filter(p => p.status === 'Stored');

  const handleConfirm = () => {
    if (mode === 'create') {
      onConfirm(selectedVersion);
    } else {
      onConfirm();
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px',
    }}>
      <div className="card" style={{
        maxWidth: '700px',
        width: '100%',
        maxHeight: '80vh',
        overflowY: 'auto',
        padding: '28px',
      }}>
        {/* Header */}
        <h2 style={{
          color: 'var(--color-text-primary)',
          fontSize: '1.5rem',
          marginBottom: '16px',
        }}>
          {mode === 'create' ? 'Import Save File' : 'Update from Save File'}
        </h2>

        {/* Save file info */}
        <div style={{
          marginBottom: '20px',
          padding: '12px',
          backgroundColor: 'var(--color-bg-light)',
          borderRadius: '8px',
        }}>
          <p style={{ margin: '0 0 4px 0', fontSize: '14px', color: 'var(--color-text-primary)' }}>
            <strong>Game:</strong> {preview.game} (Gen {preview.generation})
          </p>
          <p style={{ margin: '0 0 4px 0', fontSize: '14px', color: 'var(--color-text-primary)' }}>
            <strong>Trainer:</strong> {preview.trainer_name}
          </p>
          <p style={{ margin: '0 0 4px 0', fontSize: '14px', color: 'var(--color-text-primary)' }}>
            <strong>Pokemon:</strong> {preview.pokemon.length} total ({previewParty.length} party, {previewStored.length} stored)
          </p>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-text-primary)' }}>
            <strong>Badges:</strong> {preview.badges.length > 0
              ? `${preview.badges.length}/8 — ${preview.badges.join(', ')}`
              : 'None detected'}
          </p>
        </div>

        {/* Version picker for create mode with ambiguous game */}
        {needsVersionPicker && (
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '14px',
              fontWeight: '600',
              color: 'var(--color-text-primary)',
            }}>
              Which version are you playing?
            </label>
            <div style={{ display: 'flex', gap: '12px' }}>
              {preview.compatible_versions.map(version => (
                <button
                  key={version}
                  onClick={() => setSelectedVersion(version)}
                  className={selectedVersion === version ? 'btn btn-primary' : 'btn btn-outline'}
                  style={{ flex: 1, padding: '10px 16px' }}
                >
                  {formatGameName(version)}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Update mode: diff view */}
        {mode === 'update' && (
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ color: '#991B1B', fontSize: '14px', marginBottom: '8px' }}>
              Pokemon being removed ({existingPokemon.length})
            </h3>
            <div style={{
              maxHeight: '150px',
              overflowY: 'auto',
              marginBottom: '16px',
              padding: '8px',
              backgroundColor: '#FEF2F2',
              borderRadius: '8px',
              border: '1px solid #FECACA',
            }}>
              {existingPokemon.length === 0 ? (
                <p style={{ margin: 0, fontSize: '12px', color: '#991B1B' }}>No existing pokemon</p>
              ) : (
                existingPokemon.map((p, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 0' }}>
                    {getPokemonSpritePath(p.name) && (
                      <img
                        src={getPokemonSpritePath(p.name)}
                        alt={p.name}
                        style={{ width: '32px', height: '32px', imageRendering: 'pixelated' }}
                        onError={(e) => { e.currentTarget.style.display = 'none'; }}
                      />
                    )}
                    <span style={{ fontSize: '12px', textTransform: 'capitalize' }}>
                      {p.nickname || p.name} Lv.{p.level} ({p.status})
                    </span>
                  </div>
                ))
              )}
            </div>

            <h3 style={{ color: '#166534', fontSize: '14px', marginBottom: '8px' }}>
              Pokemon being added ({preview.pokemon.length})
            </h3>
          </div>
        )}

        {/* Pokemon list */}
        <div style={{
          maxHeight: mode === 'update' ? '150px' : '250px',
          overflowY: 'auto',
          marginBottom: '20px',
          padding: '8px',
          backgroundColor: mode === 'update' ? '#F0FDF4' : 'var(--color-bg-light)',
          borderRadius: '8px',
          border: mode === 'update' ? '1px solid #BBF7D0' : '1px solid var(--color-border)',
        }}>
          {preview.pokemon.length === 0 ? (
            <p style={{ margin: 0, fontSize: '12px', color: 'var(--color-text-secondary)' }}>No pokemon in save</p>
          ) : (
            preview.pokemon.map((p, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 0' }}>
                {getPokemonSpritePath(p.name) && (
                  <img
                    src={getPokemonSpritePath(p.name)}
                    alt={p.name}
                    style={{ width: '32px', height: '32px', imageRendering: 'pixelated' }}
                    onError={(e) => { e.currentTarget.style.display = 'none'; }}
                  />
                )}
                <span style={{ fontSize: '12px', textTransform: 'capitalize' }}>
                  {p.nickname ? `${p.nickname} (${p.name})` : p.name} Lv.{p.level} ({p.status})
                </span>
              </div>
            ))
          )}
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            className="btn btn-outline"
            disabled={isLoading}
            style={{ padding: '10px 24px' }}
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="btn btn-primary"
            disabled={isLoading || (needsVersionPicker && !selectedVersion)}
            style={{ padding: '10px 24px' }}
          >
            {isLoading ? 'Importing...' : 'Confirm Import'}
          </button>
        </div>
      </div>
    </div>
  );
};
