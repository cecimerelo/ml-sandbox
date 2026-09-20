import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';

import { ShrinkagePathChart, shrinkageRows } from './ShrinkagePathChart';
import type { ShrinkagePoint } from './types';

function points(): ShrinkagePoint[] {
  const alphas = [0.1, 1, 10];
  const coefficients: Record<string, number[]> = {
    size_m2: [3.2, 3.0, 1.5],
    bedrooms: [-2.1, -1.8, -0.4],
    age_years: [0.9, 0.8, 0.2],
  };
  return alphas.flatMap((x, i) =>
    Object.entries(coefficients).map(([feature, values]) => ({
      feature,
      x,
      coefficient: values[i]!,
    })),
  );
}

it('labels the promoted features and describes the rest in the summary', () => {
  render(<ShrinkagePathChart points={points()} promotedFeatures={['size_m2', 'bedrooms']} xLabel="α" />);
  const image = screen.getByRole('img');
  expect(image.getAttribute('aria-label')).toMatch(/Largest magnitude: size_m2, bedrooms/);
});

it('draws one polyline per feature', () => {
  const { container } = render(
    <ShrinkagePathChart points={points()} promotedFeatures={['size_m2']} xLabel="α" />,
  );
  expect(container.querySelectorAll('polyline')).toHaveLength(3);
});

it('draws a direct label only for the promoted features', () => {
  const { container } = render(
    <ShrinkagePathChart points={points()} promotedFeatures={['size_m2']} xLabel="α" />,
  );
  const labels = [...container.querySelectorAll('text')].map((el) => el.textContent);
  expect(labels).toContain('size_m2');
  expect(labels).not.toContain('bedrooms');
  expect(labels).not.toContain('age_years');
});

it('renders nothing broken for an empty shrinkage path', () => {
  render(<ShrinkagePathChart points={[]} promotedFeatures={[]} xLabel="α" />);
  expect(screen.getByRole('img')).toBeInTheDocument();
});

it('builds table rows from each feature\'s value at the largest strength plotted, largest magnitude first', () => {
  const rows = shrinkageRows(points());
  expect(rows.map((r) => r.label)).toEqual(['size_m2', 'bedrooms', 'age_years']);
  expect(rows[0]!.count).toBe(1.5);
});
