/**
 * Utility function to generate sprite path for a Pokemon
 * @param pokemonName - The name of the Pokemon (will be lowercased)
 * @returns The sprite path in format {API_BASE_URL}/assets/sprites/pokemon/{pokemon_name}.webp
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const getPokemonSpritePath = (pokemonName: string): string => {
  return `${API_BASE_URL}/assets/sprites/pokemon/${pokemonName.toLowerCase()}.webp`;
};

