import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
  // Each line is a transparent wide hit-area plus a visible stroke, one pair per series.
  expect(container.querySelectorAll('polyline')).toHaveLength(2);
});

it('draws both lines when target variance is present (PLS)', () => {
  const { container } = render(
    <VarianceExplainedChart points={plsPoints()} chosenX={2} xLabel="components" />,
  );
  expect(container.querySelectorAll('polyline')).toHaveLength(4);
});

it('reveals each line\'s identity and value at the chosen component count on hover', async () => {
  const user = userEvent.setup();
  render(<VarianceExplainedChart points={plsPoints()} chosenX={2} xLabel="components" />);

  const predictorsLine = screen.getByLabelText('predictors: 0.500');
  await user.hover(predictorsLine);
  expect(await screen.findByRole('tooltip')).toHaveTextContent('predictors: 0.500');

  const targetLine = screen.getByLabelText('target: 0.950');
  await user.hover(targetLine);
  expect(await screen.findByRole('tooltip')).toHaveTextContent('target: 0.950');
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
