/**
 * Version and generation service.
 * Handles public endpoints for game versions and generation data.
 */
import { apiHelpers } from './api';
import type { BasePokemon } from '../types';

export interface Version {
  version_id: number;
  version_name: string;
  generation_id: number;
  locations_ordered?: string[] | null;
  region?: string | null;
  // Add other fields as needed based on backend model
}

export interface Generation {
  generation_id: number;
  name?: string | null;
  pokemon?: BasePokemon[] | null;
  // Add other fields as needed based on backend model
}

/**
 * Get all versions
 */
export const getVersions = async (): Promise<Version[]> => {
  return await apiHelpers.get<Version[]>('/api/versions/');
};

/**
 * Get a specific version by name
 */
export const getVersion = async (versionName: string): Promise<Version> => {
  return await apiHelpers.get<Version>(`/api/versions/${versionName}`);
};

/**
 * Get all generations
 */
export const getGenerations = async (): Promise<Generation[]> => {
  return await apiHelpers.get<Generation[]>('/api/versions/generations');
};

/**
 * Get a specific generation by ID
 */
export const getGeneration = async (generationId: number): Promise<Generation> => {
  return await apiHelpers.get<Generation>(`/api/versions/generations/${generationId}`);
};

/**
 * Get starter pokemon for a generation
 */
export const getGenerationStarters = async (generationId: number): Promise<BasePokemon[]> => {
  return await apiHelpers.get<BasePokemon[]>(
    `/api/versions/generations/${generationId}/starters`
  );
};

