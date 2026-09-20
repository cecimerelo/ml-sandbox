import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

import { theme } from '../../theme/theme';
import { PcrPlsPanel } from './PcrPlsPanel';
import type { PcrPlsCharts } from './types';

function file() {
  return new File(['a'], 'houses.csv', { type: 'text/csv' });
}

function pcrCharts(): PcrPlsCharts {
  return {
    variance_explained: {
      points: [
        { x: 1, x_variance: 0.3, y_variance: null },
        { x: 2, x_variance: 0.6, y_variance: null },
        { x: 3, x_variance: 0.95, y_variance: null },
      ],
      chosen_x: 2,
      x_label: 'components',
    },
    tuning: {
      points: [
        { x: 1, score: 0.7 },
        { x: 2, score: 0.9 },
        { x: 3, score: 0.85 },
      ],
      chosen_x: 2,
      x_label: 'components',
    },
  };
}

function stubCharts(body: PcrPlsCharts, method: 'pcr' | 'pls' = 'pcr') {
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

function show(method: 'pcr' | 'pls' = 'pcr') {
  return render(
    <ThemeProvider theme={theme}>
      <PcrPlsPanel jobId="job-1" file={file()} target="price" method={method} />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it('renders the variance-explained and tuning curve panels', async () => {
  stubCharts(pcrCharts());
  show();

  expect(await screen.findByText('Variance explained')).toBeInTheDocument();
  expect(screen.getByText('Tuning curve')).toBeInTheDocument();
});

it('states the chosen component count in the tuning subtitle', async () => {
  stubCharts(pcrCharts());
  show();
  expect(await screen.findByText(/components = 2 was chosen/)).toBeInTheDocument();
});

it('fetches pls charts when given method="pls"', async () => {
  stubCharts(pcrCharts(), 'pls');
  show('pls');
  expect(await screen.findByText('Variance explained')).toBeInTheDocument();
});
