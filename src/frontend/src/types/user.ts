// Mirrors UserResponse schema in backend api/schemas.py

export interface User {
  id: number;
  username: string;
  email?: string | null;
  oauth_provider?: string | null;
  oauth_provider_id?: string | null;
  created_at?: string | null; // ISO datetime from backend
}


