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
 * Every truncation lives in the subtitle, never silent (DESIGN.md): the categorical fold
 * and the missing-value count, when either applies.
 */
export function DistributionPanel({ title, data }: { title: string; data: Distribution }) {
  if (data.kind === 'numeric') {
    const subtitle = subtitleFor(data.missing);
    return (
      <PlotPanel
        title={title}
        {...(subtitle ? { subtitle } : {})}
        chart={<HistogramChart data={data} />}
        table={<DistributionTable rows={histogramRows(data)} columnLabel="Range" />}
      />
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
