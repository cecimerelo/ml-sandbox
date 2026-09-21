import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it } from 'vitest';

import { featureImportanceChartAspect, FeatureImportanceChart, featureImportanceRows } from './FeatureImportanceChart';
import type { FeatureImportanceBar } from './types';

function bars(): FeatureImportanceBar[] {
  return [
    { feature: 'size_m2', value: 0.6 },
    { feature: 'bedrooms', value: 0.3 },
    { feature: 'age_years', value: 0.1 },
  ];
}

it('draws one bar per feature, all in one hue', () => {
  const { container } = render(<FeatureImportanceChart bars={bars()} />);
  const rects = container.querySelectorAll('rect');
  expect(rects).toHaveLength(3);
  const fills = new Set([...rects].map((r) => r.getAttribute('fill')));
  expect(fills.size).toBe(1);
});

it('folds bars past the top 20 with a stated count', () => {
  const many = Array.from({ length: 25 }, (_, i) => ({ feature: `f${i}`, value: 25 - i }));
  render(<FeatureImportanceChart bars={many} />);
  const image = screen.getByRole('img');
  expect(image.getAttribute('aria-label')).toMatch(/And 5 more/);
});

it('reveals a bar\'s exact value on hover', async () => {
  const user = userEvent.setup();
  render(<FeatureImportanceChart bars={bars()} />);

  const bar = screen.getByLabelText('size_m2: 0.600');
  await user.hover(bar);
  expect(await screen.findByRole('tooltip')).toHaveTextContent('size_m2: 0.600');
});

it('renders nothing broken with no bars', () => {
  render(<FeatureImportanceChart bars={[]} />);
  expect(screen.getByRole('img')).toBeInTheDocument();
});

it('computes an aspect matching the row count', () => {
  expect(featureImportanceChartAspect(bars())).toMatch(/^320 \/ \d+$/);
});

it('builds table rows in the same order as plotted', () => {
  const rows = featureImportanceRows(bars());
  expect(rows).toEqual([
    { label: 'size_m2', count: 0.6 },
    { label: 'bedrooms', count: 0.3 },
    { label: 'age_years', count: 0.1 },
  ]);
});
