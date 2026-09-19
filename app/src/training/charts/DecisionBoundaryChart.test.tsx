import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';

import { boundarySummary, DecisionBoundaryChart } from './DecisionBoundaryChart';
import type { DecisionBoundary } from './types';

function boundary(overrides: Partial<DecisionBoundary> = {}): DecisionBoundary {
  const grid: DecisionBoundary['grid'] = [];
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      grid.push({ x: i, y: j, predicted_class: i < 2 ? 'a' : 'b' });
    }
  }
  return {
    feature_x: 'x1',
    feature_y: 'x2',
    numeric_features: ['x1', 'x2'],
    classes: ['a', 'b'],
    grid,
    points: [
      { x: 0, y: 0, actual_class: 'a' },
      { x: 3, y: 3, actual_class: 'b' },
    ],
    too_many_classes: false,
    ...overrides,
  };
}

it('renders one image for two classes (single frame)', () => {
  render(<DecisionBoundaryChart boundary={boundary()} />);
  expect(screen.getAllByRole('img')).toHaveLength(1);
});

it('renders one small panel per class for 4-6 classes (facets)', () => {
  const grid: DecisionBoundary['grid'] = [];
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) grid.push({ x: i, y: j, predicted_class: String(i % 4) });
  }
  render(
    <DecisionBoundaryChart
      boundary={boundary({ classes: ['0', '1', '2', '3'], grid })}
    />,
  );
  expect(screen.getAllByRole('img')).toHaveLength(4);
});

it('renders a text explanation instead of a chart for too many classes', () => {
  render(
    <DecisionBoundaryChart
      boundary={boundary({ too_many_classes: true, classes: Array(7).fill('c'), grid: [] })}
    />,
  );
  expect(screen.queryByRole('img')).toBeNull();
  expect(screen.getByText(/too many/i)).toBeInTheDocument();
});

it('renders a text explanation instead of a chart without two numeric columns', () => {
  render(<DecisionBoundaryChart boundary={boundary({ grid: [], numeric_features: [] })} />);
  expect(screen.queryByRole('img')).toBeNull();
  expect(screen.getByText(/doesn't have two number columns/i)).toBeInTheDocument();
});

it('summarises the plotted features, class count, and per-class row counts', () => {
  expect(boundarySummary(boundary())).toMatch(/x1 and x2/);
  expect(boundarySummary(boundary())).toMatch(/a: 1/);
  expect(boundarySummary(boundary())).toMatch(/b: 1/);
});
