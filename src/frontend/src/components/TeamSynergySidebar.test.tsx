import { render, screen, fireEvent } from '@testing-library/react';
import { test, expect } from 'vitest';
import { TeamSynergySidebar } from './TeamSynergySidebar';

const mockSynergy = {
  generation: 1,
  team_types: ['fire', 'fire'],
  offense: {
    strengths: [{ type: 'grass', multiplier: 4, contributors: ['Torch', 'Blaze'] }],
    weaknesses: [],
    immunities: [],
  },
  defense: {
    strengths: [],
    weaknesses: [{ type: 'water', multiplier: 4, contributors: ['Torch', 'Blaze'] }],
    immunities: [],
  },
};

test('expands synergy details on toggle', () => {
  render(<TeamSynergySidebar isLoading={false} isError={false} synergy={mockSynergy} />);

  const summary = screen.getByText(/view team synergy/i);
  const details = summary.closest('details');

  expect(details).not.toHaveAttribute('open');

  fireEvent.click(summary);

  expect(details).toHaveAttribute('open');
  expect(screen.getByText('Offense')).toBeInTheDocument();
  expect(screen.getByText('Defense')).toBeInTheDocument();
});
