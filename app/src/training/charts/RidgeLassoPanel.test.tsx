import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

import { theme } from '../../theme/theme';
import { RidgeLassoPanel } from './RidgeLassoPanel';
import type { ShrinkageCharts } from './types';

function file() {
  return new File(['a'], 'houses.csv', { type: 'text/csv' });
}

function charts(): ShrinkageCharts {
  return {
    shrinkage: {
      points: [
        { feature: 'size_m2', x: 0.1, coefficient: 3.2 },
        { feature: 'size_m2', x: 10, coefficient: 1.5 },
        { feature: 'bedrooms', x: 0.1, coefficient: -2.1 },
        { feature: 'bedrooms', x: 10, coefficient: -0.4 },
      ],
      promoted_features: ['size_m2', 'bedrooms'],
      x_label: 'α',
    },
    tuning: {
      points: [
        { x: 0.1, score: 0.7 },
        { x: 1, score: 0.9 },
        { x: 10, score: 0.85 },
      ],
      chosen_x: 1,
      x_label: 'α',
    },
  };
}

function stubCharts(body: ShrinkageCharts, method: 'ridge' | 'lasso' = 'ridge') {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (url === `/api/train/job-1/${method}/charts`) {
        return { ok: true, json: async () => body };
      }
      throw new Error(`unexpected fetch: ${url}`);
    }),
  );
}

function show(method: 'ridge' | 'lasso' = 'ridge') {
  return render(
    <ThemeProvider theme={theme}>
      <RidgeLassoPanel jobId="job-1" file={file()} target="price" method={method} />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it('renders the shrinkage path and the tuning curve', async () => {
  stubCharts(charts());
  show();

  expect(await screen.findByText('Coefficient shrinkage path')).toBeInTheDocument();
  expect(screen.getByText('Tuning curve')).toBeInTheDocument();
});

it('states the chosen regularization strength in the subtitle', async () => {
  stubCharts(charts());
  show();
  expect(await screen.findByText(/α = 1.00 was chosen/)).toBeInTheDocument();
});

it('fetches lasso charts when given method="lasso"', async () => {
  stubCharts(charts(), 'lasso');
  show('lasso');
  expect(await screen.findByText('Coefficient shrinkage path')).toBeInTheDocument();
});

it('explains a missing shrinkage path instead of rendering an empty chart', async () => {
  const multiclass = charts();
  multiclass.shrinkage = { points: [], promoted_features: [], x_label: 'C' };
  stubCharts(multiclass);
  show();

  await screen.findByText('Tuning curve');
  expect(screen.getByText(/only applies to a two-outcome target/)).toBeInTheDocument();
});
