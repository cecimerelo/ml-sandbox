import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';

import { theme } from '../../theme/theme';
import { DiscriminantPanel } from './DiscriminantPanel';
import type { DiscriminantCharts } from './types';

function file() {
  return new File(['a'], 'sales.csv', { type: 'text/csv' });
}

function binaryGrid(): DiscriminantCharts['boundary']['grid'] {
  const grid: DiscriminantCharts['boundary']['grid'] = [];
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      grid.push({ x: i, y: j, predicted_class: i < 2 ? 'no' : 'yes' });
    }
  }
  return grid;
}

function binaryCharts(): DiscriminantCharts {
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
    },
    confusion_matrix: { labels: ['no', 'yes'], matrix: [[40, 10], [5, 45]] },
  };
}

function unavailableCharts(overrides: Partial<DiscriminantCharts['boundary']>): DiscriminantCharts {
  return {
    boundary: {
      feature_x: '',
      feature_y: '',
      numeric_features: [],
      classes: ['no', 'yes'],
      grid: [],
      points: [],
      too_many_classes: false,
      ...overrides,
    },
    confusion_matrix: { labels: ['no', 'yes'], matrix: [[40, 10], [5, 45]] },
  };
}

function stubCharts(bodies: DiscriminantCharts[]) {
  const queue = [...bodies];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (url === '/api/train/job-1/lda/charts') {
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
      <DiscriminantPanel jobId="job-1" method="lda" file={file()} target="sold" />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it('renders the decision boundary and confusion matrix', async () => {
  stubCharts([binaryCharts()]);
  show();

  expect(await screen.findByText('Decision boundary')).toBeInTheDocument();
  expect(screen.getByText('Confusion matrix')).toBeInTheDocument();
});

it('says why there is no boundary when there are too many classes, rather than an empty chart', async () => {
  stubCharts([unavailableCharts({ too_many_classes: true, classes: Array(7).fill('c') })]);
  show();

  await screen.findByText('Decision boundary');
  expect(screen.getByText(/too many/i)).toBeInTheDocument();
});

it('says why there is no boundary without two numeric columns', async () => {
  stubCharts([unavailableCharts({})]);
  show();

  await screen.findByText('Decision boundary');
  expect(screen.getByText(/doesn't have two number columns/i)).toBeInTheDocument();
});

it('offers no axis swap when there are fewer than two numeric features', async () => {
  stubCharts([unavailableCharts({})]);
  show();

  await screen.findByText('Decision boundary');
  expect(screen.queryByLabelText(/horizontal axis/i)).toBeNull();
});

it('re-fetches with the chosen pair when the axis selects change', async () => {
  const swapped = binaryCharts();
  swapped.boundary.feature_x = 'bedrooms';
  stubCharts([binaryCharts(), swapped]);
  const user = userEvent.setup();
  show();

  await screen.findByText('Decision boundary');
  await user.click(screen.getByLabelText(/horizontal axis/i));
  await user.click(screen.getByRole('option', { name: 'bedrooms' }));

  await waitFor(() => {
    const calls = vi.mocked(fetch).mock.calls;
    const last = calls[calls.length - 1]!;
    const body = last[1]?.body as FormData;
    expect(body.get('feature_x')).toBe('bedrooms');
  });
});
