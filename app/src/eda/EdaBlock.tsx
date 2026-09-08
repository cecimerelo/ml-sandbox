import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { useEffect, useState } from 'react';
import type React from 'react';

import { CHART } from '../copy/catalogue';
import { spacing } from '../theme/tokens';
import { BoxplotPanel } from './BoxplotPanel';
import { CorrelationHeatmap } from './CorrelationHeatmap';
import { DistributionPanel } from './DistributionPanel';
import type {
  CategoricalBars,
  ColumnInventory,
  CorrelationMatrix,
  Distribution,
  DistributionsResult,
  Histogram,
} from './types';

const PAGE_SIZE = 12;

/**
 * One named group of same-type charts, with the "how to read this" explanation stated
 * once at the top rather than once per panel — the fix for a page of twelve histograms
 * each repeating the identical sentence underneath it.
 */
function Section({
  heading,
  explanation,
  children,
}: {
  heading: string;
  explanation: string;
  children: React.ReactNode;
}) {
  return (
    <Box sx={{ mb: 4 }}>
      <Typography sx={{ fontWeight: 700, mb: 0.5 }}>{heading}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {explanation}
      </Typography>
      {children}
    </Box>
  );
}

interface Entry {
  title: string;
  data: Distribution;
}

function isNumeric(entry: Entry): entry is Entry & { data: Histogram } {
  return entry.data.kind === 'numeric';
}

function isCategorical(entry: Entry): entry is Entry & { data: CategoricalBars } {
  return entry.data.kind === 'categorical';
}

/**
 * Block 3 — distributions, the target, and categorical bars, per feature.
 *
 * **Present only when a dataset is uploaded, absent otherwise** (FR-3.1) — not empty, not
 * disabled: there is no "let me look before I have a file" state here to render. Collapsed
 * by default (FR-3.2): a reader who came for a recommendation should not have to close a
 * block they didn't ask to open.
 *
 * **Grouped by chart type, not by feature.** A first version rendered one column beside
 * the next — histogram, then that same column's boxplot, then the next column's
 * histogram — which repeated the same explanation under every panel. Sections fix that:
 * one explanation stated once at the top of each chart-type group, with each feature
 * still getting its own square panel below it — same grid shape as Distributions and
 * Categories, not one wide strip of boxes fighting over a single shared axis.
 *
 * **Paginated, never all at once** — a 500-feature file does not mean 500 panels in one
 * accordion. The picker fetches the cheap column inventory first, then only the current
 * page's actual distributions, so a file with hundreds of features costs what is on
 * screen, not what exists. All three sections below share that one page.
 */
export function EdaBlock({
  file,
  target,
  collapseSignal,
}: {
  file: File;
  target: string;
  /**
   * Bumped by the caller to force the accordion shut — a successful `Get
   * Recommendation`, specifically. A reader who just asked for a recommendation is
   * looking at the panel that answers it, not at the block they were exploring a
   * moment ago; leaving it open pushes the answer further down the page than the
   * question that produced it.
   */
  collapseSignal?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const [inventory, setInventory] = useState<ColumnInventory | null>(null);
  const [page, setPage] = useState(0);
  const [distributions, setDistributions] = useState<DistributionsResult | null>(null);
  const [correlation, setCorrelation] = useState<CorrelationMatrix | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setInventory(null);
    setPage(0);
    async function load() {
      const body = new FormData();
      body.append('file', file);
      body.append('target', target);
      try {
        const response = await fetch('/api/dataset/eda/columns', { method: 'POST', body });
        if (cancelled) return;
        if (!response.ok) {
          setFailed(true);
          return;
        }
        setInventory(await response.json());
      } catch {
        if (!cancelled) setFailed(true);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [file, target]);

  // Independent of pagination — the heatmap is computed once over every numeric
  // feature, not per page, so it does not re-fetch when the feature picker moves.
  useEffect(() => {
    let cancelled = false;
    setCorrelation(null);
    async function load() {
      const body = new FormData();
      body.append('file', file);
      body.append('target', target);
      try {
        const response = await fetch('/api/dataset/eda/correlation', { method: 'POST', body });
        if (cancelled) return;
        if (!response.ok) {
          setFailed(true);
          return;
        }
        setCorrelation(await response.json());
      } catch {
        if (!cancelled) setFailed(true);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [file, target]);

  useEffect(() => {
    if (collapseSignal !== undefined) setExpanded(false);
  }, [collapseSignal]);

  const totalPages = inventory ? Math.max(1, Math.ceil(inventory.total / PAGE_SIZE)) : 1;
  const pageColumns = inventory
    ? inventory.columns.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE).map((c) => c.column)
    : [];

  useEffect(() => {
    if (!inventory) return;
    let cancelled = false;
    async function load() {
      const body = new FormData();
      body.append('file', file);
      body.append('target', target);
      for (const column of pageColumns) body.append('columns', column);
      try {
        const response = await fetch('/api/dataset/eda/distributions', {
          method: 'POST',
          body,
        });
        if (cancelled) return;
        if (!response.ok) {
          setFailed(true);
          return;
        }
        setDistributions(await response.json());
      } catch {
        if (!cancelled) setFailed(true);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [inventory, page, file, target]);

  const entries = distributions
    ? [
        { title: `${target} (target)`, data: distributions.target },
        ...distributions.features.map((data) => ({ title: data.column, data })),
      ]
    : [];
  const numericEntries = entries.filter(isNumeric);
  const categoricalEntries = entries.filter(isCategorical);
  const boxplotFeatures = numericEntries
    .filter((e) => e.data.boxplot)
    .map((e) => ({ column: e.title, boxplot: e.data.boxplot! }));

  return (
    <Accordion
      expanded={expanded}
      onChange={(_, isExpanded) => setExpanded(isExpanded)}
      sx={{ my: `${spacing.sectionGap}px` }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography sx={{ fontWeight: 700 }}>Explore your data</Typography>
      </AccordionSummary>
      <AccordionDetails>
        {failed && (
          <Typography color="text.secondary">
            We couldn't read your data for this. Try again, or continue without it — nothing
            else on this page depends on it.
          </Typography>
        )}

        {!failed && !distributions && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={24} aria-label="Reading your data" />
          </Box>
        )}

        {/* Not wrapped in `Section` like the three below — those share one explanation
            across many panels of the same chart type; this is already exactly one
            self-contained panel, and adding a heading and an explanation above it would
            duplicate the title and the subtitle already inside it. */}
        {!failed && correlation && (
          <Box sx={{ mb: 4 }}>
            <CorrelationHeatmap data={correlation} />
          </Box>
        )}

        {!failed && distributions && inventory && (
          <>
            {numericEntries.length > 0 && (
              <Section heading="Distributions" explanation={CHART['chart.histogram.subtitle']}>
                <Grid container spacing={spacing.plotGap / spacing.unit}>
                  {numericEntries.map(({ title, data }) => (
                    <Grid item key={title} xs={12} sm={6}>
                      <DistributionPanel title={title} data={data} />
                    </Grid>
                  ))}
                </Grid>
              </Section>
            )}

            {boxplotFeatures.length > 0 && (
              <Section heading="Boxplots" explanation={CHART['chart.boxplot.subtitle']}>
                <Grid container spacing={spacing.plotGap / spacing.unit}>
                  {boxplotFeatures.map(({ column, boxplot }) => (
                    <Grid item key={column} xs={12} sm={6}>
                      <BoxplotPanel title={column} data={boxplot} />
                    </Grid>
                  ))}
                </Grid>
              </Section>
            )}

            {categoricalEntries.length > 0 && (
              <Section heading="Categories" explanation={CHART['chart.categorical-bars.subtitle']}>
                <Grid container spacing={spacing.plotGap / spacing.unit}>
                  {categoricalEntries.map(({ title, data }) => (
                    <Grid item key={title} xs={12} sm={6}>
                      <DistributionPanel title={title} data={data} />
                    </Grid>
                  ))}
                </Grid>
              </Section>
            )}

            {inventory.total > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Showing {pageColumns.length} of {inventory.total} features.
                </Typography>
                <Button
                  size="small"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  size="small"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                >
                  Next
                </Button>
              </Box>
            )}
          </>
        )}
      </AccordionDetails>
    </Accordion>
  );
}
