import { expect, it } from 'vitest';

import { coefficientChartAspect } from './CoefficientChart';
import type { CoefficientBar } from './types';

function bars(n: number): CoefficientBar[] {
  return Array.from({ length: n }, (_, i) => ({ feature: `x${i}`, value: i + 1 }));
}

it('shrinks toward the chart\'s own aspect ratio for very few bars, instead of a fixed 4:3 that would letterbox them', () => {
  // Regression: PlotPanel's default 4/3 box once left two short bars stranded in a
  // mostly-empty box, because the chart's actual content was far shorter and wider
  // than that fixed ratio.
  const aspect = coefficientChartAspect(bars(2));
  const [width, height] = aspect.split(' / ').map(Number);
  expect(width! / height!).toBeGreaterThan(4 / 3);
});

it('grows taller, never past what 20 rows need, for many bars', () => {
  const twenty = coefficientChartAspect(bars(20));
  const fifty = coefficientChartAspect(bars(50));
  expect(fifty).toEqual(twenty);
});

it('never divides by zero for an empty bar list', () => {
  expect(() => coefficientChartAspect([])).not.toThrow();
});
