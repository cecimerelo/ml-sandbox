import Grid from '@mui/material/Grid';

import { ChartFetchStatus } from './ChartFetchStatus';
import { RocAndConfusionMatrix } from './RocAndConfusionMatrix';
import type { NaiveBayesCharts } from './types';
import { useChartData } from './useChartData';

/**
 * Naive Bayes's fixed set (FR-4.2, #98): ROC curve, confusion matrix — the same pair
 * Logistic Regression uses, minus a coefficient plot: `GaussianNB` has no single
 * signed weight per feature to draw one from.
 */
export function NaiveBayesPanel({
  jobId,
  file,
  target,
}: {
  jobId: string;
  file: File;
  target: string;
}) {
  const { data, failed } = useChartData<NaiveBayesCharts>(jobId, 'naive_bayes', file, target);

  if (failed || !data) {
    return <ChartFetchStatus failed={failed} loaded={data !== null} />;
  }

  return (
    <Grid container spacing={2}>
      <RocAndConfusionMatrix roc={data.roc} confusionMatrix={data.confusion_matrix} />
    </Grid>
  );
}
