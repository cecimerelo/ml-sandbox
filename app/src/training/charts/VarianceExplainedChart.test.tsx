import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';

import { VarianceExplainedChart, varianceExplainedRows } from './VarianceExplainedChart';
import type { ComponentPoint } from './types';

function pcrPoints(): ComponentPoint[] {
  return [
    { x: 1, x_variance: 0.3, y_variance: null },
    { x: 2, x_variance: 0.6, y_variance: null },
    { x: 3, x_variance: 0.9, y_variance: null },
  ];
}

function plsPoints(): ComponentPoint[] {
  return [
    { x: 1, x_variance: 0.2, y_variance: 0.8 },
    { x: 2, x_variance: 0.5, y_variance: 0.95 },
    { x: 3, x_variance: 0.8, y_variance: 0.96 },
  ];
}

it('draws only the predictors line when there is no target variance (PCR)', () => {
  const { container } = render(
    <VarianceExplainedChart points={pcrPoints()} chosenX={2} xLabel="components" />,
  );
  expect(container.querySelectorAll('polyline')).toHaveLength(1);
  expect(screen.getByText('predictors')).toBeInTheDocument();
  expect(screen.queryByText('target')).toBeNull();
});

it('draws both lines when target variance is present (PLS)', () => {
  const { container } = render(
    <VarianceExplainedChart points={plsPoints()} chosenX={2} xLabel="components" />,
  );
  expect(container.querySelectorAll('polyline')).toHaveLength(2);
  expect(screen.getByText('predictors')).toBeInTheDocument();
  expect(screen.getByText('target')).toBeInTheDocument();
});

it('labels the chosen component count in the image description', () => {
  render(<VarianceExplainedChart points={plsPoints()} chosenX={2} xLabel="components" />);
  const image = screen.getByRole('img');
  expect(image.getAttribute('aria-label')).toMatch(/Chosen: components = 2/);
});

it('renders nothing broken for an empty curve', () => {
  render(<VarianceExplainedChart points={[]} chosenX={0} xLabel="components" />);
  expect(screen.getByRole('img')).toBeInTheDocument();
});

it('builds table rows sorted by component count ascending', () => {
  const rows = varianceExplainedRows([
    { x: 3, x_variance: 0.9, y_variance: null },
    { x: 1, x_variance: 0.3, y_variance: null },
    { x: 2, x_variance: 0.6, y_variance: null },
  ]);
  expect(rows.map((r) => r.label)).toEqual(['1', '2', '3']);
  expect(rows.map((r) => r.count)).toEqual([0.3, 0.6, 0.9]);
});
