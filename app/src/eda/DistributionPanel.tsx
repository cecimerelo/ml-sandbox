import Box from '@mui/material/Box';

import { CHART } from '../copy/catalogue';
import { BoxplotChart, boxplotRows } from './BoxplotChart';
import { CategoricalBarChart, categoricalRows } from './CategoricalBarChart';
import { DistributionTable } from './DistributionTable';
import { HistogramChart, histogramRows } from './HistogramChart';
import { PlotPanel } from './PlotPanel';
import type { Distribution } from './types';

/**
 * One column's distribution, in whichever chart form its kind calls for — the histogram
 * and categorical-bars branches are the same fork `mlsandbox.eda` already made, read
 * back rather than re-decided here.
 *
 * A numeric column gets two panels, stacked: the boxplot first, then the histogram — the
 * five-number summary orients a reader to the column's shape before the finer-grained
 * bar-by-bar view, rather than the other way round.
 *
 * Every subtitle starts from the catalogue's permanent "how to read this" line (#48),
 * with a truncation disclosure — the categorical fold, the missing-value count —
 * appended when either applies. Never silent (DESIGN.md): a reader always has both what
 * the chart is and what was left out of it.
 */
export function DistributionPanel({ title, data }: { title: string; data: Distribution }) {
  if (data.kind === 'numeric') {
    const subtitle = combine(CHART['chart.histogram.subtitle'], missingNote(data.missing));
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {data.boxplot && (
          <PlotPanel
            title={title}
            subtitle={CHART['chart.boxplot.subtitle']}
            aspect="8 / 3"
            chart={<BoxplotChart data={data.boxplot} />}
            table={
              <DistributionTable
                rows={boxplotRows(data.boxplot)}
                columnLabel="Statistic"
                valueLabel="Value"
              />
            }
          />
        )}
        <PlotPanel
          title={title}
          subtitle={subtitle}
          chart={<HistogramChart data={data} />}
          table={<DistributionTable rows={histogramRows(data)} columnLabel="Range" />}
        />
      </Box>
    );
  }

  const truncation =
    data.other_categories > 0
      ? `Showing the 15 most common categories, plus ${data.other_categories} more folded into "Other".`
      : undefined;
  const subtitle = combine(
    CHART['chart.categorical-bars.subtitle'],
    truncation,
    missingNote(data.missing),
  );
  return (
    <PlotPanel
      title={title}
      subtitle={subtitle}
      chart={<CategoricalBarChart data={data} />}
      table={<DistributionTable rows={categoricalRows(data)} columnLabel="Category" />}
    />
  );
}

function missingNote(missing: number): string | undefined {
  return missing > 0 ? `${missing} value${missing === 1 ? '' : 's'} missing, not shown.` : undefined;
}

function combine(base: string, ...extras: (string | undefined)[]): string {
  return [base, ...extras].filter(Boolean).join(' ');
}
