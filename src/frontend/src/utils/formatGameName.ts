/**
 * Capitalize game name (e.g., "black-2" -> "Black-2", "firered" -> "Firered")
 */
export const formatGameName = (name: string): string => {
  return name
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join('-');
};
