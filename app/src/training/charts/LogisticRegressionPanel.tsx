import Grid from '@mui/material/Grid';

import { DistributionTable } from '../../eda/DistributionTable';
import { PlotPanel } from '../../eda/PlotPanel';
import { ChartFetchStatus } from './ChartFetchStatus';
import { CoefficientChart, coefficientChartAspect, coefficientRows } from './CoefficientChart';
import { GoalSubtitle } from './GoalSubtitle';
import { RocAndConfusionMatrix } from './RocAndConfusionMatrix';
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

  return (
    <Grid container spacing={2}>
      <RocAndConfusionMatrix roc={data.roc} confusionMatrix={data.confusion_matrix} />

      {data.roc && (
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
