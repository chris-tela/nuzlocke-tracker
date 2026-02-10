// Types related to gyms & trainer data.

// From GymProgressResponse schema
export interface GymProgressResponse {
  gym_progress: GymProgressEntry[];
  upcoming_gyms: GymSummary[];
}

export interface GymProgressEntry {
  gym_number: string;
  location: string;
  badge_name: string;
}

export interface GymSummary {
  gym_number: string;
  location: string;
  badge_name: string;
  trainer_name?: string;
  badge_type?: string;
}

export interface GymTrainer {
  trainer_name: string;
  badge_type?: string;
  pokemon: GymTrainerPokemon[];
}

export interface GymTrainerPokemon {
  name: string;
  level: number;
}

export interface GymDetail {
  gym_number: string;
  location: string;
  badge_name: string;
  trainers: GymTrainer[];
}


