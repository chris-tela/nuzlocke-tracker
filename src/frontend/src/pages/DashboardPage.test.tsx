import { render, screen } from '@testing-library/react';
import { test, expect, vi } from 'vitest';
import { DashboardPage } from './DashboardPage';

vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
}));

vi.mock('../hooks/useGameFile', () => ({
  useGameFile: () => ({
    currentGameFile: {
      id: 1,
      trainer_name: 'Ash',
      game_name: 'Red',
    },
  }),
}));

vi.mock('../hooks/usePokemon', () => ({
  usePokemon: () => ({ data: [], isLoading: false }),
  usePartyPokemon: () => ({ data: [], isLoading: false }),
  useUpdatePokemon: () => ({ mutateAsync: vi.fn() }),
  usePokemonInfo: () => ({ data: null }),
  useAddPokemon: () => ({ mutateAsync: vi.fn() }),
  usePokemonInfoByName: () => ({ data: null }),
  useSearchPokemon: () => ({ data: [], isLoading: false }),
}));

vi.mock('../hooks/useRoutes', () => ({
  useUpcomingRoutes: () => ({ data: [], isLoading: false }),
}));

vi.mock('../hooks/useGyms', () => ({
  useUpcomingGyms: () => ({
    data: {
      upcoming_gyms: [
        {
          gym_number: '3',
          trainer_name: 'Lt. Surge',
          badge_type: 'Electric',
        },
      ],
    },
    isLoading: false,
  }),
  useGymProgress: () => ({ data: [], isLoading: false }),
}));

test('shows next gym trainer, type, and number', () => {
  render(<DashboardPage />);

  expect(screen.getByText('Gym 3 - Lt. Surge (Electric)')).toBeInTheDocument();
});
