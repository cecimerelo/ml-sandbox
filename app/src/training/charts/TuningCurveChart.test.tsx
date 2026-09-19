import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';

import { TuningCurveChart, tuningRows } from './TuningCurveChart';

it('renders an image labelling the chosen value', () => {
  render(
    <TuningCurveChart
      points={[
        { x: 1, score: 0.7 },
        { x: 3, score: 0.9 },
        { x: 5, score: 0.85 },
      ]}
      chosenX={3}
      xLabel="K"
      formatX={(k) => `K = ${k}`}
    />,
  );
  const image = screen.getByRole('img');
  expect(image.getAttribute('aria-label')).toMatch(/Chosen: K = 3/);
});

it('anchors the optimum label so it never hangs off the plot edge (#99)', () => {
  // A grid search choosing its largest candidate (K's own grid is [1, 3, 5, 11, 21] and
  // this is a real, common outcome) puts the optimum at the last point on the curve.
  // Centring an anchor="middle" label there once clipped the last character against the
  // SVG's own viewBox, so "K = 21" rendered as "K = 2" — the digit past the edge was
  // simply gone, not just visually tight.
  const { container } = render(
    <TuningCurveChart
      points={[
        { x: 1, score: 0.7 },
        { x: 3, score: 0.75 },
        { x: 5, score: 0.78 },
        { x: 11, score: 0.8 },
        { x: 21, score: 0.82 },
      ]}
      chosenX={21}
      xLabel="K"
      formatX={(k) => `K = ${k}`}
    />,
  );
  const label = [...container.querySelectorAll('text')].find((el) =>
    el.textContent?.includes('K = 21'),
  );
  expect(label).toBeDefined();
  expect(label?.textContent).toBe('K = 21');
  expect(label?.getAttribute('text-anchor')).toBe('end');
});

it('renders nothing broken for an empty tuning curve', () => {
  render(<TuningCurveChart points={[]} chosenX={0} xLabel="K" />);
  expect(screen.getByRole('img')).toBeInTheDocument();
});

it('sorts table rows by x ascending regardless of input order', () => {
  const rows = tuningRows([
    { x: 5, score: 0.85 },
    { x: 1, score: 0.7 },
    { x: 3, score: 0.9 },
  ]);
  expect(rows.map((r) => r.label)).toEqual(['1', '3', '5']);
});
