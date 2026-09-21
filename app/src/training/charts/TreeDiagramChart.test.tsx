import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it } from 'vitest';

import { TreeDiagramChart, treeDiagramAspect, treeDiagramRows } from './TreeDiagramChart';
import type { TreeNode } from './types';

function nodes(): TreeNode[] {
  return [
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
      n_samples: 90,
      predicted_value: '120.00',
      truncated_splits: null,
    },
    {
      id: 2,
      parent_id: 0,
      depth: 1,
      is_leaf: false,
      split_feature: null,
      split_threshold: null,
      n_samples: 110,
      predicted_value: '',
      truncated_splits: 4,
    },
  ];
}

it('draws one box per node and one edge per non-root node', () => {
  const { container } = render(<TreeDiagramChart nodes={nodes()} />);
  expect(container.querySelectorAll('rect')).toHaveLength(3);
  expect(container.querySelectorAll('line')).toHaveLength(2);
});

it('dashes the border of a truncation stub, not a real node', () => {
  const { container } = render(<TreeDiagramChart nodes={nodes()} />);
  const dashed = [...container.querySelectorAll('rect')].filter((r) =>
    r.getAttribute('stroke-dasharray'),
  );
  expect(dashed).toHaveLength(1);
});

it('reveals the split condition and sample count on hover', async () => {
  const user = userEvent.setup();
  render(<TreeDiagramChart nodes={nodes()} />);

  const root = screen.getByLabelText('size_m2 ≤ 100.0, 200 rows');
  await user.hover(root);
  expect(await screen.findByRole('tooltip')).toHaveTextContent('size_m2 ≤ 100.0, 200 rows');
});

it('reveals a truncation stub\'s collapsed-split count on hover', async () => {
  const user = userEvent.setup();
  render(<TreeDiagramChart nodes={nodes()} />);

  const stub = screen.getByLabelText('4 more splits collapsed here');
  await user.hover(stub);
  expect(await screen.findByRole('tooltip')).toHaveTextContent('4 more splits collapsed here');
});

it('renders nothing broken with no nodes', () => {
  render(<TreeDiagramChart nodes={[]} />);
  expect(screen.getByText('No tree to show.')).toBeInTheDocument();
});

it('computes an aspect matching the laid-out content', () => {
  expect(treeDiagramAspect(nodes())).toMatch(/^\d+ \/ \d+$/);
});

it('builds one table row per node, split/leaf label against sample count', () => {
  const rows = treeDiagramRows(nodes());
  expect(rows).toEqual([
    { label: 'size_m2 ≤ 100.0', count: 200 },
    { label: 'Leaf: 120.00', count: 90 },
    { label: '⋯ 4 more splits', count: 110 },
  ]);
});
