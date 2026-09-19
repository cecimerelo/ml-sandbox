import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';

import { DistributionTable } from '../../eda/DistributionTable';
import { PlotPanel } from '../../eda/PlotPanel';
import { spacing } from '../../theme/tokens';
import { ChartFetchStatus } from './ChartFetchStatus';
import { CoefficientChart, coefficientChartAspect, coefficientRows } from './CoefficientChart';
import { ConfusionMatrixChart, ConfusionMatrixTable } from './ConfusionMatrixChart';
import { GoalSubtitle } from './GoalSubtitle';
import { RocCurveChart, rocRows } from './RocCurveChart';
import type { LogisticRegressionCharts } from './types';
import { useChartData } from './useChartData';

/**
 * The Logistic Regression method's fixed chart set (FR-4.2, #96): ROC curve,
 * confusion matrix, coefficient plot. ROC and coefficients are only meaningful for a
 * binary target — `mlsandbox.charts.logistic_regression_charts` omits them for a
 * multiclass one, and this panel says so rather than rendering an empty chart.
 */
export function LogisticRegressionPanel({
  jobId,
  file,
  target,
}: {
  jobId: string;
  file: File;
  target: string;
}) {
  const { data, failed } = useChartData<LogisticRegressionCharts>(
    jobId,
    'logistic_regression',
    file,
    target,
  );

  if (failed || !data) {
    return <ChartFetchStatus failed={failed} loaded={data !== null} />;
  }

  const isMulticlass = data.roc === null;

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6}>
        {data.roc ? (
          <PlotPanel
            title="ROC curve"
            subtitle={
              <GoalSubtitle
                description={`How well the model separates the two outcomes, treating "${data.roc.positive_class}" as positive, across every possible cutoff.`}
                goal={`Hugging the top-left corner, well above the dashed diagonal (a coin flip). AUC = ${data.roc.auc.toFixed(3)} here.`}
              />
            }
            chart={<RocCurveChart points={data.roc.points} auc={data.roc.auc} />}
            table={
              <DistributionTable
                rows={rocRows(data.roc.points)}
                columnLabel="False positive rate"
                valueLabel="True positive rate"
              />
            }
          />
        ) : (
          <Typography color="text.secondary">
            The ROC curve only applies to a two-outcome target — this one has more than two, so
            there's nothing to plot here.
          </Typography>
        )}
      </Grid>

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Confusion matrix"
          subtitle={
            <GoalSubtitle
              description="Each cell is how many rows with that actual outcome (row) the model predicted as that outcome (column)."
              goal="A heavy diagonal and light everywhere else — most rows landing where actual and predicted agree."
            />
          }
          chart={<ConfusionMatrixChart data={data.confusion_matrix} />}
          table={<ConfusionMatrixTable data={data.confusion_matrix} />}
          aspect={spacing.plotAspectSquare}
        />
      </Grid>

      {!isMulticlass && (
        <Grid item xs={12} sm={6}>
          <PlotPanel
            title="Coefficients"
            subtitle={
              <GoalSubtitle
                description="How much each column moves the prediction toward the positive outcome, largest first. Blue pushes toward it, red pushes away."
                goal="Each bar's size and direction should make sense for what its column represents — nothing surprisingly large from a column that shouldn't matter."
              />
            }
            chart={<CoefficientChart bars={data.coefficients.bars} />}
            table={
              <DistributionTable
                rows={coefficientRows(data.coefficients.bars)}
                columnLabel="Feature"
                valueLabel="Coefficient"
              />
            }
            aspect={coefficientChartAspect(data.coefficients.bars)}
          />
        </Grid>
      )}
    </Grid>
  );
}
