/**
 * Game File Context
 * Manages current game file selection and game files list
 */
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useSearchParams, useLocation } from 'react-router-dom';
import { getGameFile, getGameFiles } from '../services/gameFileService';
import type { GameFile } from '../types';

interface GameFileContextType {
  currentGameFile: GameFile | null;
  gameFiles: GameFile[];
  setCurrentGameFile: (gameFile: GameFile | null) => void;
  setGameFiles: (gameFiles: GameFile[]) => void;
  selectGameFileById: (gameFileId: number) => void;
  clearGameFile: () => void;
}

const GameFileContext = createContext<GameFileContextType | undefined>(undefined);

export const useGameFile = () => {
  const context = useContext(GameFileContext);
  if (context === undefined) {
    throw new Error('useGameFile must be used within a GameFileProvider');
  }
  return context;
};

interface GameFileProviderProps {
  children: ReactNode;
}

export const GameFileProvider = ({ children }: GameFileProviderProps) => {
  const [currentGameFile, setCurrentGameFile] = useState<GameFile | null>(null);
  const [gameFiles, setGameFiles] = useState<GameFile[]>([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const [isLoadingFromUrl, setIsLoadingFromUrl] = useState(false);

  // Load game files on mount
  useEffect(() => {
    const loadGameFiles = async () => {
      try {
        const files = await getGameFiles();
        setGameFiles(files);
      } catch (error) {
        console.error('Failed to load game files:', error);
      }
    };
    loadGameFiles();
  }, []);

  // Load game file from URL if gameFileId is present
  useEffect(() => {
    const gameFileIdParam = searchParams.get('gameFileId');
    const gameFileIdFromUrl = gameFileIdParam ? parseInt(gameFileIdParam, 10) : null;
    
    if (gameFileIdFromUrl) {
      if (isNaN(gameFileIdFromUrl)) {
        // Invalid gameFileId, remove from URL
        const newParams = new URLSearchParams(searchParams);
        newParams.delete('gameFileId');
        setSearchParams(newParams, { replace: true });
        return;
      }
      
      // Only load if we don't already have this game file loaded
      if (!currentGameFile || currentGameFile.id !== gameFileIdFromUrl) {
        // First check if it's in the gameFiles list
        const gameFileFromList = gameFiles.find((gf) => gf.id === gameFileIdFromUrl);
        if (gameFileFromList) {
          setCurrentGameFile(gameFileFromList);
        } else if (!isLoadingFromUrl) {
          // If not in list, fetch it from API
          setIsLoadingFromUrl(true);
          getGameFile(gameFileIdFromUrl)
            .then((gameFile) => {
              setCurrentGameFile(gameFile);
              // Also add it to the gameFiles list if not already there
              setGameFiles((prev) => {
                if (!prev.find((gf) => gf.id === gameFile.id)) {
                  return [...prev, gameFile];
                }
                return prev;
              });
            })
            .catch((error) => {
              console.error('Failed to load game file from URL:', error);
              // Remove invalid gameFileId from URL
              const newParams = new URLSearchParams(searchParams);
              newParams.delete('gameFileId');
              setSearchParams(newParams, { replace: true });
            })
            .finally(() => {
              setIsLoadingFromUrl(false);
            });
        }
      }
    }
    // Note: We don't clear currentGameFile when gameFileId is removed from URL
    // because the user might be navigating to game-files page intentionally
  }, [searchParams, gameFiles, currentGameFile?.id, isLoadingFromUrl, setSearchParams]);

  const selectGameFileById = (gameFileId: number) => {
    const gameFile = gameFiles.find((gf) => gf.id === gameFileId);
    if (gameFile) {
      setCurrentGameFile(gameFile);
      // Update URL with gameFileId
      searchParams.set('gameFileId', gameFileId.toString());
      setSearchParams(searchParams, { replace: true });
    } else {
      console.warn(`Game file with ID ${gameFileId} not found`);
    }
  };

  const clearGameFile = () => {
    setCurrentGameFile(null);
    // Remove gameFileId from URL
    searchParams.delete('gameFileId');
    setSearchParams(searchParams, { replace: true });
  };

  // Override setCurrentGameFile to also update URL
  const setCurrentGameFileWithUrl = (gameFile: GameFile | null) => {
    setCurrentGameFile(gameFile);
    if (gameFile) {
      searchParams.set('gameFileId', gameFile.id.toString());
      setSearchParams(searchParams, { replace: true });
    } else {
      searchParams.delete('gameFileId');
      setSearchParams(searchParams, { replace: true });
    }
  };

  const value: GameFileContextType = {
    currentGameFile,
    gameFiles,
    setCurrentGameFile: setCurrentGameFileWithUrl,
    setGameFiles,
    selectGameFileById,
    clearGameFile,
  };

  return <GameFileContext.Provider value={value}>{children}</GameFileContext.Provider>;
};

