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
 * **No "how to read this" subtitle here.** That line is the same sentence for every
 * histogram (or every bar chart) in the block, and repeating it under all twelve panels
 * on a page read as noise rather than as twelve separate explanations — it now lives
 * once, at the top of the section these panels sit inside (`EdaBlock`, #48).
 *
 * What *is* specific to this column — the categorical fold, the missing-value count —
 * still renders here, as the panel's `caption`, never silent (DESIGN.md).
 */
export function DistributionPanel({ title, data }: { title: string; data: Distribution }) {
  if (data.kind === 'numeric') {
    const caption = missingNote(data.missing);
    return (
      <PlotPanel
        title={title}
        {...(caption ? { caption } : {})}
        chart={<HistogramChart data={data} />}
        table={<DistributionTable rows={histogramRows(data)} columnLabel="Range" />}
      />
    );
  }

  const truncation =
    data.other_categories > 0
      ? `Showing the 15 most common categories, plus ${data.other_categories} more folded into "Other".`
      : undefined;
  const caption = [truncation, missingNote(data.missing)].filter(Boolean).join(' ') || undefined;
  return (
    <PlotPanel
      title={title}
      {...(caption ? { caption } : {})}
      chart={<CategoricalBarChart data={data} />}
      table={<DistributionTable rows={categoricalRows(data)} columnLabel="Category" />}
    />
  );
}

function missingNote(missing: number): string | undefined {
  return missing > 0 ? `${missing} value${missing === 1 ? '' : 's'} missing, not shown.` : undefined;
}
