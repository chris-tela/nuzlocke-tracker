// Mirrors GameFileResponse schema in backend api/schemas.py

export interface GameFile {
  id: number;
  user_id: number;
  trainer_name: string;
  game_name: string;
  starter_pokemon?: string | null;
  gym_progress?: GymProgressEntry[] | null;
  route_progress?: string[] | null;
  created_at?: string | null;
}

export interface GymProgressEntry {
  gym_number: string;
  location: string;
  badge_name: string;
}


