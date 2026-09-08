import Box from '@mui/material/Box';

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
 * Every truncation lives in the subtitle, never silent (DESIGN.md): the categorical fold
 * and the missing-value count, when either applies.
 */
export function DistributionPanel({ title, data }: { title: string; data: Distribution }) {
  if (data.kind === 'numeric') {
    const subtitle = subtitleFor(data.missing);
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {data.boxplot && (
          <PlotPanel
            title={title}
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
          {...(subtitle ? { subtitle } : {})}
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
  const subtitle = [truncation, subtitleFor(data.missing)].filter(Boolean).join(' ') || undefined;
  return (
    <PlotPanel
      title={title}
      {...(subtitle ? { subtitle } : {})}
      chart={<CategoricalBarChart data={data} />}
      table={<DistributionTable rows={categoricalRows(data)} columnLabel="Category" />}
    />
  );
}

function subtitleFor(missing: number): string | undefined {
  return missing > 0 ? `${missing} value${missing === 1 ? '' : 's'} missing, not shown.` : undefined;
}
