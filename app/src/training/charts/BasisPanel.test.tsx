import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

import { theme } from '../../theme/theme';
import { BasisPanel } from './BasisPanel';
import type { BasisCharts } from './types';

function file() {
  return new File(['a'], 'houses.csv', { type: 'text/csv' });
}

function charts(): BasisCharts {
  return {
    fitted_curve: {
      feature: 'size_m2',
      curve: [
        { x: 60, y: 100 },
        { x: 100, y: 200 },
        { x: 140, y: 320 },
      ],
      actual: [
        { x: 65, y: 95 },
        { x: 95, y: 210 },
      ],
    },
    residual: {
      points: [
        { x: 100, y: -5 },
        { x: 200, y: 3 },
      ],
    },
  };
}

function stubCharts(
  body: BasisCharts,
  method: 'polynomial' | 'polynomial_interactions' | 'splines' = 'polynomial',
) {
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

function show(method: 'polynomial' | 'polynomial_interactions' | 'splines' = 'polynomial') {
  return render(
    <ThemeProvider theme={theme}>
      <BasisPanel jobId="job-1" file={file()} target="price" method={method} />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it('renders the fitted curve and residual panels', async () => {
  stubCharts(charts());
  show();

  expect(await screen.findByText('Fitted curve')).toBeInTheDocument();
  expect(screen.getByText('Residual plot')).toBeInTheDocument();
});

it('names the swept feature in the subtitle', async () => {
  stubCharts(charts());
  show();
  expect(await screen.findByText(/as size_m2 varies/)).toBeInTheDocument();
});

it('fetches splines charts when given method="splines"', async () => {
  stubCharts(charts(), 'splines');
  show('splines');
  expect(await screen.findByText('Fitted curve')).toBeInTheDocument();
});

it('fetches polynomial_interactions charts when given that method', async () => {
  stubCharts(charts(), 'polynomial_interactions');
  show('polynomial_interactions');
  expect(await screen.findByText('Fitted curve')).toBeInTheDocument();
});
