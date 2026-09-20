import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';

import { theme } from '../../theme/theme';
import { KnnPanel } from './KnnPanel';
import type { KnnCharts } from './types';

function file() {
  return new File(['a'], 'sales.csv', { type: 'text/csv' });
}

function binaryGrid(): KnnCharts['boundary']['grid'] {
  const grid: KnnCharts['boundary']['grid'] = [];
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      grid.push({ x: i, y: j, predicted_class: i < 2 ? 'no' : 'yes' });
    }
  }
  return grid;
}

function charts(): KnnCharts {
  return {
    boundary: {
      feature_x: 'size_m2',
      feature_y: 'bedrooms',
      numeric_features: ['size_m2', 'bedrooms'],
      classes: ['no', 'yes'],
      grid: binaryGrid(),
      points: [
        { x: 0, y: 0, actual_class: 'no' },
        { x: 3, y: 3, actual_class: 'yes' },
      ],
      too_many_classes: false,
      looks_continuous: false,
    },
    tuning: {
      points: [
        { k: 1, score: 0.7 },
        { k: 3, score: 0.9 },
        { k: 5, score: 0.85 },
      ],
      chosen_k: 3,
    },
  };
}

function stubCharts(bodies: KnnCharts[]) {
  const queue = [...bodies];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (url === '/api/train/job-1/knn/charts') {
        const next = queue.length > 1 ? queue.shift()! : queue[0]!;
        return { ok: true, json: async () => next };
      }
      throw new Error(`unexpected fetch: ${url}`);
    }),
  );
}

function show() {
  return render(
    <ThemeProvider theme={theme}>
      <KnnPanel jobId="job-1" file={file()} target="sold" />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it('renders the decision boundary and the accuracy-vs-K curve, with no confusion matrix', async () => {
  stubCharts([charts()]);
  show();

  expect(await screen.findByText('Decision boundary')).toBeInTheDocument();
  expect(screen.getByText('Accuracy vs. K')).toBeInTheDocument();
  expect(screen.queryByText('Confusion matrix')).toBeNull();
});

it('states the chosen K in the subtitle', async () => {
  stubCharts([charts()]);
  show();
  expect(await screen.findByText(/K = 3 was chosen/)).toBeInTheDocument();
});

it('re-fetches with the chosen pair when the axis selects change', async () => {
  const initial = charts();
  initial.boundary.numeric_features = ['size_m2', 'bedrooms', 'age_years'];
  const swapped = charts();
  swapped.boundary.feature_x = 'age_years';
  swapped.boundary.numeric_features = ['size_m2', 'bedrooms', 'age_years'];
  stubCharts([initial, swapped]);
  const user = userEvent.setup();
  show();

  await screen.findByText('Decision boundary');
  await user.click(screen.getByLabelText(/horizontal axis/i));
  await user.click(screen.getByRole('option', { name: 'age_years' }));

  await waitFor(() => {
    const calls = vi.mocked(fetch).mock.calls;
    const last = calls[calls.length - 1]!;
    const body = last[1]?.body as FormData;
    expect(body.get('feature_x')).toBe('age_years');
  });
});
