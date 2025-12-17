/**
 * Game File Context
 * Manages current game file selection and game files list
 */
import { createContext, useContext, useState, ReactNode } from 'react';
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

  const selectGameFileById = (gameFileId: number) => {
    const gameFile = gameFiles.find((gf) => gf.id === gameFileId);
    if (gameFile) {
      setCurrentGameFile(gameFile);
    } else {
      console.warn(`Game file with ID ${gameFileId} not found`);
    }
  };

  const clearGameFile = () => {
    setCurrentGameFile(null);
  };

  const value: GameFileContextType = {
    currentGameFile,
    gameFiles,
    setCurrentGameFile,
    setGameFiles,
    selectGameFileById,
    clearGameFile,
  };

  return <GameFileContext.Provider value={value}>{children}</GameFileContext.Provider>;
};

