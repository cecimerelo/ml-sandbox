import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';

import { DistributionTable } from '../../eda/DistributionTable';
import { PlotPanel } from '../../eda/PlotPanel';
import { spacing } from '../../theme/tokens';
import { ConfusionMatrixChart, ConfusionMatrixTable } from './ConfusionMatrixChart';
import { GoalSubtitle } from './GoalSubtitle';
import { RocCurveChart, rocRows } from './RocCurveChart';
import type { ConfusionMatrix, RocCurve } from './types';

/**
 * The ROC-curve-plus-confusion-matrix pair Logistic Regression (#96) and Naive Bayes
 * (#98) both use unchanged — the only difference between the two methods' fixed sets
 * is whether a coefficient plot follows, which each panel adds for itself.
 */
export function RocAndConfusionMatrix({
  roc,
  confusionMatrix,
}: {
  roc: RocCurve | null;
  confusionMatrix: ConfusionMatrix;
}) {
  return (
    <>
      <Grid item xs={12} sm={6}>
        {roc ? (
          <PlotPanel
            title="ROC curve"
            subtitle={
              <GoalSubtitle
                description={`How well the model separates the two outcomes, treating "${roc.positive_class}" as positive, across every possible cutoff.`}
                goal={`Hugging the top-left corner, well above the dashed diagonal (a coin flip). AUC = ${roc.auc.toFixed(3)} here.`}
              />
            }
            chart={<RocCurveChart points={roc.points} auc={roc.auc} />}
            table={
              <DistributionTable
                rows={rocRows(roc.points)}
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
          chart={<ConfusionMatrixChart data={confusionMatrix} />}
          table={<ConfusionMatrixTable data={confusionMatrix} />}
          aspect={spacing.plotAspectSquare}
        />
      </Grid>
    </>
  );
}
