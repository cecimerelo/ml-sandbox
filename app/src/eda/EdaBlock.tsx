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

import { spacing } from '../theme/tokens';
import { DistributionPanel } from './DistributionPanel';
import type { ColumnInventory, DistributionsResult } from './types';

const PAGE_SIZE = 12;

/**
 * Block 3 — distributions, the target, and categorical bars, per feature.
 *
 * **Present only when a dataset is uploaded, absent otherwise** (FR-3.1) — not empty, not
 * disabled: there is no "let me look before I have a file" state here to render. Collapsed
 * by default (FR-3.2): a reader who came for a recommendation should not have to close a
 * block they didn't ask to open.
 *
 * **Paginated, never all at once** — a 500-feature file does not mean 500 panels in one
 * accordion. The picker fetches the cheap column inventory first, then only the current
 * page's actual distributions, so a file with hundreds of features costs what is on
 * screen, not what exists.
 */
export function EdaBlock({ file, target }: { file: File; target: string }) {
  const [inventory, setInventory] = useState<ColumnInventory | null>(null);
  const [page, setPage] = useState(0);
  const [distributions, setDistributions] = useState<DistributionsResult | null>(null);
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

  return (
    <Accordion sx={{ my: `${spacing.sectionGap}px` }}>
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

        {!failed && distributions && inventory && (
          <>
            <Grid container spacing={spacing.plotGap / spacing.unit} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6}>
                <DistributionPanel title={`${target} (target)`} data={distributions.target} />
              </Grid>
              {distributions.features.map((feature) => (
                <Grid item key={feature.column} xs={12} sm={6}>
                  <DistributionPanel title={feature.column} data={feature} />
                </Grid>
              ))}
            </Grid>

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
