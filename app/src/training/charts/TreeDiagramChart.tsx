import Tooltip from '@mui/material/Tooltip';

import { chart, chartTooltipSx } from '../../theme/tokens';
import type { TreeNode } from './types';

const NODE_WIDTH = 96;
const NODE_HEIGHT = 48;
const H_GAP = 12;
const V_GAP = 36;
const MARGIN = 12;

interface LaidOutNode extends TreeNode {
  x: number;
  y: number;
  children: LaidOutNode[];
}

function buildTree(nodes: TreeNode[]): LaidOutNode | null {
  const byId = new Map<number, LaidOutNode>(
    nodes.map((n) => [n.id, { ...n, x: 0, y: 0, children: [] }]),
  );
  let root: LaidOutNode | null = null;
  for (const node of byId.values()) {
    if (node.parent_id === null) {
      root = node;
    } else {
      byId.get(node.parent_id)?.children.push(node);
    }
  }
  return root;
}

/** Every rendered node has 0 or 2 children (sklearn's binary split, or a
 * truncation stub standing in for a whole subtree) — a simple two-pass layout is
 * enough: leaves get the next slot left to right, an internal node centres over
 * its own children once they're placed. */
function assignPositions(node: LaidOutNode, depth: number, cursor: { x: number }): void {
  node.y = depth * (NODE_HEIGHT + V_GAP);
  if (node.children.length === 0) {
    node.x = cursor.x + NODE_WIDTH / 2;
    cursor.x += NODE_WIDTH + H_GAP;
    return;
  }
  for (const child of node.children) {
    assignPositions(child, depth + 1, cursor);
  }
  const first = node.children[0]!;
  const last = node.children[node.children.length - 1]!;
  node.x = (first.x + last.x) / 2;
}

function flatten(node: LaidOutNode, out: LaidOutNode[] = []): LaidOutNode[] {
  out.push(node);
  for (const child of node.children) flatten(child, out);
  return out;
}

function formatThreshold(value: number): string {
  return Math.abs(value) < 1000 ? value.toFixed(1) : value.toFixed(0);
}

/** Same self-sizing convention as `coefficientChartAspect` — this chart has no
 * fixed aspect at all per DESIGN.md, so the box is sized to match its own laid-out
 * content exactly, rather than letting a generic 4:3 box squash or letterbox it. */
export function treeDiagramAspect(nodes: TreeNode[]): string {
  const root = buildTree(nodes);
  if (!root) return '4 / 3';
  assignPositions(root, 0, { x: 0 });
  const laidOut = flatten(root);
  const width = Math.max(...laidOut.map((n) => n.x)) + NODE_WIDTH / 2 + MARGIN * 2;
  const height = Math.max(...laidOut.map((n) => n.y)) + NODE_HEIGHT + MARGIN * 2;
  return `${width} / ${height}`;
}

/**
 * DESIGN.md's `{components.tree-diagram}`: nodes on `background-paper` with
 * `divider` borders, split conditions and leaf values in `chart-annotation` 11px.
 * A truncation stub gets a dashed border and its own "⋯ N more splits" label —
 * "every truncated branch gets one; a branch never just stops." No fixed aspect,
 * no pan/zoom: this is one of the three chart forms DESIGN.md exempts from the
 * scaled-viewBox convention every other chart uses, rendered instead at its own
 * pixel size inside a horizontally scrolling wrapper.
 */
export function TreeDiagramChart({ nodes }: { nodes: TreeNode[] }) {
  const root = buildTree(nodes);
  if (!root) {
    return <p style={{ color: chart.inkMuted.hex }}>No tree to show.</p>;
  }

  assignPositions(root, 0, { x: 0 });
  const laidOut = flatten(root);
  const width = Math.max(...laidOut.map((n) => n.x)) + NODE_WIDTH / 2 + MARGIN * 2;
  const height = Math.max(...laidOut.map((n) => n.y)) + NODE_HEIGHT + MARGIN * 2;

  const summary = laidOut
    .filter((n) => n.truncated_splits === null)
    .map((n) =>
      n.is_leaf
        ? `leaf, ${n.n_samples} rows, predicts ${n.predicted_value}`
        : `${n.split_feature} <= ${n.split_threshold !== null ? formatThreshold(n.split_threshold) : ''}, ${n.n_samples} rows`,
    )
    .join('; ');

  return (
    <div style={{ width: '100%', height: '100%', overflowX: 'auto' }}>
      <svg
        role="img"
        aria-label={`Decision tree diagram. ${summary}.`}
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
      >
        <g transform={`translate(${MARGIN}, ${MARGIN})`}>
          {laidOut.map(
            (node) =>
              node.parent_id !== null && (
                <line
                  key={`edge-${node.id}`}
                  x1={laidOut.find((n) => n.id === node.parent_id)!.x}
                  y1={laidOut.find((n) => n.id === node.parent_id)!.y + NODE_HEIGHT}
                  x2={node.x}
                  y2={node.y}
                  stroke={chart.axis.hex}
                  strokeWidth={1}
                />
              ),
          )}

          {laidOut.map((node) => {
            const isStub = node.truncated_splits !== null;
            const boxX = node.x - NODE_WIDTH / 2;
            const label = isStub
              ? `⋯ ${node.truncated_splits} more splits`
              : node.is_leaf
                ? node.predicted_value
                : `${node.split_feature} ≤ ${node.split_threshold !== null ? formatThreshold(node.split_threshold) : ''}`;
            const meta = isStub ? '' : `n = ${node.n_samples}`;
            const tooltip = isStub
              ? `${node.truncated_splits} more splits collapsed here`
              : node.is_leaf
                ? `Leaf: predicts ${node.predicted_value}, ${node.n_samples} rows`
                : `${node.split_feature} ≤ ${node.split_threshold !== null ? formatThreshold(node.split_threshold) : ''}, ${node.n_samples} rows`;

            return (
              <Tooltip
                key={node.id}
                title={tooltip}
                disableInteractive
                slotProps={{ tooltip: { sx: chartTooltipSx } }}
              >
                <g>
                  <rect
                    x={boxX}
                    y={node.y}
                    width={NODE_WIDTH}
                    height={NODE_HEIGHT}
                    rx={4}
                    fill={chart.surface.hex}
                    stroke={chart.gridline.hex}
                    strokeWidth={1}
                    strokeDasharray={isStub ? '3 3' : undefined}
                  />
                  <text
                    x={node.x}
                    y={node.y + (meta ? 20 : 27)}
                    fontSize={11}
                    textAnchor="middle"
                    fill={isStub ? chart.inkMuted.hex : chart.ink.hex}
                  >
                    {label.length > 16 ? `${label.slice(0, 15)}…` : label}
                  </text>
                  {meta && (
                    <text x={node.x} y={node.y + 34} fontSize={10} textAnchor="middle" fill={chart.inkMuted.hex}>
                      {meta}
                    </text>
                  )}
                </g>
              </Tooltip>
            );
          })}
        </g>
      </svg>
    </div>
  );
}

/** DESIGN.md's table form for this family: an ordered list of the rendered split
 * conditions, each with its sample count and predicted value, in traversal order —
 * leaves and truncation stubs included, since a "no meaningful table" family still
 * ships a text summary rather than nothing. */
export function treeDiagramRows(nodes: TreeNode[]): { label: string; count: number }[] {
  return nodes.map((n) => ({
    label:
      n.truncated_splits !== null
        ? `⋯ ${n.truncated_splits} more splits`
        : n.is_leaf
          ? `Leaf: ${n.predicted_value}`
          : `${n.split_feature} ≤ ${n.split_threshold !== null ? formatThreshold(n.split_threshold) : ''}`,
    count: n.n_samples,
  }));
}
