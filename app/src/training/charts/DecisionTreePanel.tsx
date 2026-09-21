import Grid from '@mui/material/Grid';

import { DistributionTable } from '../../eda/DistributionTable';
import { PlotPanel } from '../../eda/PlotPanel';
import { ChartFetchStatus } from './ChartFetchStatus';
import {
  FeatureImportanceChart,
  featureImportanceChartAspect,
  featureImportanceRows,
} from './FeatureImportanceChart';
import { GoalSubtitle } from './GoalSubtitle';
import { TreeDiagramChart, treeDiagramAspect, treeDiagramRows } from './TreeDiagramChart';
import { TuningCurveChart, tuningRows } from './TuningCurveChart';
import type { DecisionTreeCharts } from './types';
import { useChartData } from './useChartData';

/**
 * Decision Tree's fixed set (FR-4.2, #103): a depth-capped tree diagram, a
 * feature-importance bar chart, and a CV-error-vs-tree-size pruning curve. The
 * pruning curve's "chosen" point is the real tree's own leaf count — the tree
 * itself is never pruned, so the curve is a diagnostic about what pruning would
 * do, not a claim about what shipped.
 */
export function DecisionTreePanel({
  jobId,
  file,
  target,
}: {
  jobId: string;
  file: File;
  target: string;
}) {
  const { data, failed } = useChartData<DecisionTreeCharts>(jobId, 'decision_tree', file, target);

  if (failed || !data) {
    return <ChartFetchStatus failed={failed} loaded={data !== null} />;
  }

  const { tree } = data;
  const truncationNote =
    tree.total_depth > tree.rendered_depth
      ? `Showing the first ${tree.rendered_depth + 1} of ${tree.total_depth + 1} levels.`
      : 'Showing the full tree.';

  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <PlotPanel
          title="Tree diagram"
          subtitle={truncationNote}
          chart={<TreeDiagramChart nodes={tree.nodes} />}
          table={<DistributionTable rows={treeDiagramRows(tree.nodes)} columnLabel="Split / leaf" valueLabel="Rows" />}
          aspect={treeDiagramAspect(tree.nodes)}
        />
      </Grid>

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Feature importance"
          subtitle={
            <GoalSubtitle
              description="How much each column reduced impurity across every split that used it, largest first."
              goal="A handful of columns should dominate — a flat importance across everything is a sign the tree isn't finding real structure."
            />
          }
          chart={<FeatureImportanceChart bars={data.importance.bars} />}
          table={
            <DistributionTable
              rows={featureImportanceRows(data.importance.bars)}
              columnLabel="Feature"
              valueLabel="Importance"
            />
          }
          aspect={featureImportanceChartAspect(data.importance.bars)}
        />
      </Grid>

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Pruning curve"
          subtitle={
            <GoalSubtitle
              description="A cost-complexity pruning sweep the trained tree never ran — it shows how CV score would change at every tree size, not what the tree actually did."
              goal={`The deployed tree has ${data.pruning.chosen_n_leaves} leaves — worth checking whether a smaller tree nearby scores about as well.`}
            />
          }
          chart={
            <TuningCurveChart
              points={data.pruning.points.map((p) => ({ x: p.n_leaves, score: p.score }))}
              chosenX={data.pruning.chosen_n_leaves}
              xLabel={data.pruning.x_label}
              formatX={(x) => `${data.pruning.x_label} = ${x}`}
            />
          }
          table={
            <DistributionTable
              rows={tuningRows(data.pruning.points.map((p) => ({ x: p.n_leaves, score: p.score })))}
              columnLabel={data.pruning.x_label}
              valueLabel="Score"
            />
          }
        />
      </Grid>
    </Grid>
  );
}
