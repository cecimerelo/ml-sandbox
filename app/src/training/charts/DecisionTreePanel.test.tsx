import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';

import { theme } from '../../theme/theme';
import { DecisionTreePanel } from './DecisionTreePanel';
import type { DecisionTreeCharts } from './types';

function file() {
  return new File(['a'], 'houses.csv', { type: 'text/csv' });
}

function charts(): DecisionTreeCharts {
  return {
    tree: {
      nodes: [
        {
          id: 0,
          parent_id: null,
          depth: 0,
          is_leaf: false,
          split_feature: 'size_m2',
          split_threshold: 100,
          n_samples: 200,
          predicted_value: '150.00',
          truncated_splits: null,
        },
        {
          id: 1,
          parent_id: 0,
          depth: 1,
          is_leaf: true,
          split_feature: null,
          split_threshold: null,
          n_samples: 200,
          predicted_value: '150.00',
          truncated_splits: null,
        },
      ],
      rendered_depth: 4,
      total_depth: 9,
    },
    importance: {
      bars: [
        { feature: 'size_m2', value: 0.7 },
        { feature: 'bedrooms', value: 0.3 },
      ],
    },
    pruning: {
      points: [
        { n_leaves: 1, score: 0.5 },
        { n_leaves: 8, score: 0.9 },
        { n_leaves: 20, score: 0.85 },
      ],
      chosen_n_leaves: 20,
      x_label: 'Number of leaves',
    },
  };
}

function stubCharts(body: DecisionTreeCharts) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (url === '/api/train/job-1/decision_tree/charts') {
        return { ok: true, json: async () => body };
      }
      throw new Error(`unexpected fetch: ${url}`);
    }),
  );
}

function show() {
  return render(
    <ThemeProvider theme={theme}>
      <DecisionTreePanel jobId="job-1" file={file()} target="price" />
    </ThemeProvider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

it('renders the tree diagram, feature importance, and pruning curve', async () => {
  stubCharts(charts());
  show();

  expect(await screen.findByText('Tree diagram')).toBeInTheDocument();
  expect(screen.getByText('Feature importance')).toBeInTheDocument();
  expect(screen.getByText('Pruning curve')).toBeInTheDocument();
});

it('states the truncation in the tree diagram subtitle when the real tree is deeper', async () => {
  stubCharts(charts());
  show();
  expect(await screen.findByText('Showing the first 5 of 10 levels.')).toBeInTheDocument();
});

it('says the full tree is shown when nothing was truncated', async () => {
  const shallow = charts();
  shallow.tree.total_depth = shallow.tree.rendered_depth;
  stubCharts(shallow);
  show();
  expect(await screen.findByText('Showing the full tree.')).toBeInTheDocument();
});

it('names the deployed tree\'s own leaf count in the pruning subtitle', async () => {
  stubCharts(charts());
  show();
  expect(await screen.findByText(/has 20 leaves/)).toBeInTheDocument();
});
