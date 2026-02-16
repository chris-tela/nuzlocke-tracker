const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function normalizeBaseUrl(url: string): string {
  return url.endsWith('/') ? url.slice(0, -1) : url;
}

function normalizeSlashes(path: string): string {
  return path.replace(/\\/g, '/').trim();
}

export function resolveTrainerSpriteUrl(trainerImage?: string | null): string | null {
  if (!trainerImage) return null;

  const source = normalizeSlashes(trainerImage);
  if (!source) return null;

  if (/^https?:\/\//i.test(source)) {
    return source;
  }

  const baseUrl = normalizeBaseUrl(API_BASE_URL);

  if (source.startsWith('/assets/')) {
    return `${baseUrl}${source}`;
  }

  const assetsIndex = source.indexOf('/assets/');
  if (assetsIndex >= 0) {
    return `${baseUrl}${source.slice(assetsIndex)}`;
  }

  if (source.startsWith('src/')) {
    const dataSprites = source.match(/src\/data\/sprites\/(.+)$/);
    if (dataSprites?.[1]) {
      return `${baseUrl}/data-sprites/${dataSprites[1]}`;
    }

    const backendAssets = source.match(/src\/backend\/assets\/(.+)$/);
    if (backendAssets?.[1]) {
      return `${baseUrl}/assets/${backendAssets[1]}`;
    }
  }

  if (source.startsWith('../data/sprites/')) {
    return `${baseUrl}/data-sprites/${source.replace('../data/sprites/', '')}`;
  }

  if (source.startsWith('data/sprites/')) {
    return `${baseUrl}/data-sprites/${source.replace('data/sprites/', '')}`;
  }

  if (source.startsWith('assets/')) {
    return `${baseUrl}/${source}`;
  }

  return `${baseUrl}/${source.replace(/^\.?\//, '')}`;
}

function normalizePokemonName(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/♀/g, '-f')
    .replace(/♂/g, '-m')
    .replace(/[.\s']/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

export function resolvePokemonSpriteUrl(pokemonName?: string | null, pokeId?: number | null): string | null {
  const base = normalizeBaseUrl(API_BASE_URL);

  if (pokemonName) {
    const normalized = normalizePokemonName(pokemonName);
    if (normalized) {
      return `${base}/assets/sprites/pokemon/${normalized}.webp`;
    }
  }

  if (pokeId != null) {
    return `${base}/assets/sprites/pokemon/${pokeId}.webp`;
  }

  return null;
}

export function resolveDamageClassIconUrl(damageClass?: string | null): string | null {
  if (!damageClass) return null;
  const normalized = damageClass.trim().toLowerCase();
  if (!normalized) return null;
  const frontendBase = (import.meta.env.BASE_URL || '/').replace(/\/$/, '');
  return `${frontendBase}/damage_class/${normalized}.png`;
}
