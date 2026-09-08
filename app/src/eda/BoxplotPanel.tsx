import { BoxplotChart, boxplotRows } from './BoxplotChart';
import { DistributionTable } from './DistributionTable';
import { PlotPanel } from './PlotPanel';
import type { BoxplotSummary } from './types';

/**
 * One numeric column's five-number summary, in its own square panel — matching the
 * histogram and categorical-bars panels beside it in the grid, rather than one wide
 * strip of boxes sharing (or fighting over) a single axis.
 *
 * No subtitle here: the "how to read this" line lives once, at the top of the
 * `Boxplots` section these panels sit inside (`EdaBlock`, #48).
 */
export function BoxplotPanel({ title, data }: { title: string; data: BoxplotSummary }) {
  return (
    <PlotPanel
      title={title}
      chart={<BoxplotChart data={data} />}
      table={
        <DistributionTable rows={boxplotRows(data)} columnLabel="Statistic" valueLabel="Value" />
      }
    />
  );
}
